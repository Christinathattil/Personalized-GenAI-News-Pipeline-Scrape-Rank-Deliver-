"""FastAPI application for newsletter signup."""
from __future__ import annotations

import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session, engine
from api.models import (
    Base,
    RegisteredUserORM,
    InterestORM,
    UserPreferencesORM,
    UserYouTubeChannelORM,
    user_interests,
)
from api.schemas import (
    SignupRequest,
    SignupResponse,
    ConfirmResponse,
    UnsubscribeResponse,
    InterestOut,
)
from api.youtube_utils import validate_and_extract_channels
from api.email_service import send_confirmation_email
from api.interests_data import get_interests_for_seeding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_interests(session: Session) -> None:
    """Seed the interests table if empty."""
    existing = session.scalar(select(InterestORM).limit(1))
    if existing:
        logger.info("Interests already seeded, skipping...")
        return
    
    logger.info("Seeding interests...")
    interests_data = get_interests_for_seeding()
    
    # First pass: create all interests without parent relationships
    tag_to_id = {}
    for data in interests_data:
        interest = InterestORM(
            tag=data["tag"],
            display_name=data["display_name"],
            parent_id=None,
        )
        session.add(interest)
        session.flush()
        tag_to_id[data["tag"]] = interest.id
    
    # Second pass: update parent relationships
    for data in interests_data:
        if data["parent_tag"]:
            interest = session.scalar(
                select(InterestORM).where(InterestORM.tag == data["tag"])
            )
            if interest and data["parent_tag"] in tag_to_id:
                interest.parent_id = tag_to_id[data["parent_tag"]]
    
    session.commit()
    logger.info(f"Seeded {len(interests_data)} interests")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create tables and seed data on startup."""
    # Import all models to ensure they're registered
    from api import models  # noqa
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Seed interests
    with get_session() as session:
        seed_interests(session)
    
    yield


app = FastAPI(
    title="AI News Digest - Newsletter Signup",
    description="Register for personalized AI news delivered to your inbox",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Dependency to get database session."""
    with get_session() as session:
        yield session


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/interests", response_model=list[InterestOut])
async def get_interests(db: Session = Depends(get_db)):
    """Get all available interests for selection."""
    interests = db.scalars(select(InterestORM).order_by(InterestORM.id)).all()
    return interests


@app.post("/api/signup", response_model=SignupResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user for the newsletter.
    
    - Validates all inputs (name, email, interests, YouTube URLs)
    - Extracts channel IDs from YouTube URLs
    - Creates user with 3-day trial
    - Sends confirmation email (double opt-in)
    """
    # Check if email already exists
    existing = db.scalar(
        select(RegisteredUserORM).where(RegisteredUserORM.email == request.email)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please use a different email or check your inbox for confirmation."
        )
    
    # Validate interests exist
    valid_interests = db.scalars(
        select(InterestORM).where(InterestORM.id.in_(request.interest_ids))
    ).all()
    if len(valid_interests) != len(request.interest_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected interests are invalid"
        )
    
    # Extract YouTube channel IDs
    channels = validate_and_extract_channels(request.youtube_urls)
    if not channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract channel information from any of the provided YouTube URLs. Please check the URLs and try again."
        )
    
    # Generate tokens
    confirmation_token = secrets.token_urlsafe(32)
    unsubscribe_token = secrets.token_urlsafe(32)
    
    # Create user
    user = RegisteredUserORM(
        name=request.name,
        email=request.email,
        confirmation_token=confirmation_token,
        unsubscribe_token=unsubscribe_token,
        active=False,
        trial_expires_at=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db.add(user)
    db.flush()  # Get user ID
    
    # Add interests
    for interest in valid_interests:
        db.execute(
            user_interests.insert().values(user_id=user.id, interest_id=interest.id)
        )
    
    # Add preferences
    preferences = UserPreferencesORM(
        user_id=user.id,
        hours_window=request.hours_window,
        top_articles=5,
    )
    db.add(preferences)
    
    # Add YouTube channels
    for channel in channels:
        yt_channel = UserYouTubeChannelORM(
            user_id=user.id,
            channel_id=channel["channel_id"],
            channel_name=channel.get("channel_name"),
            original_url=channel["original_url"],
        )
        db.add(yt_channel)
    
    db.commit()
    
    # Send confirmation email
    email_sent = send_confirmation_email(
        to_email=request.email,
        user_name=request.name,
        confirmation_token=confirmation_token,
    )
    
    if email_sent:
        message = "Registration successful! Please check your email to confirm your subscription."
    else:
        message = "Registration successful! Email confirmation is pending (SMTP not configured)."
    
    return SignupResponse(success=True, message=message, user_id=user.id)


@app.get("/api/confirm/{token}", response_class=HTMLResponse)
async def confirm_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm user's email address (double opt-in).
    Returns an HTML page with confirmation status.
    """
    user = db.scalar(
        select(RegisteredUserORM).where(RegisteredUserORM.confirmation_token == token)
    )
    
    if not user:
        return HTMLResponse(
            content=_confirmation_page("Invalid Link", "This confirmation link is invalid or has expired.", False),
            status_code=404
        )
    
    if user.active:
        return HTMLResponse(
            content=_confirmation_page("Already Confirmed", "Your email has already been confirmed. You're all set!", True)
        )
    
    # Activate user
    user.active = True
    user.confirmation_token = None  # Invalidate token
    db.commit()
    
    return HTMLResponse(
        content=_confirmation_page(
            "Email Confirmed! 🎉",
            f"Welcome aboard, {user.name}! Your 3-day free trial has started. You'll receive your first personalized AI news digest soon.",
            True
        )
    )


@app.get("/api/unsubscribe/{token}", response_class=HTMLResponse)
async def unsubscribe(token: str, db: Session = Depends(get_db)):
    """
    Unsubscribe user from newsletter (GDPR/CAN-SPAM compliant).
    """
    user = db.scalar(
        select(RegisteredUserORM).where(RegisteredUserORM.unsubscribe_token == token)
    )
    
    if not user:
        return HTMLResponse(
            content=_confirmation_page("Invalid Link", "This unsubscribe link is invalid.", False),
            status_code=404
        )
    
    # Deactivate user
    user.active = False
    db.commit()
    
    return HTMLResponse(
        content=_confirmation_page(
            "Unsubscribed",
            f"You've been unsubscribed from the AI News Digest, {user.name}. We're sorry to see you go!",
            True
        )
    )


def _confirmation_page(title: str, message: str, success: bool) -> str:
    """Generate HTML confirmation page."""
    color = "#10b981" if success else "#ef4444"
    icon = "✓" if success else "✗"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - AI News Digest</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                padding: 40px;
                max-width: 500px;
                text-align: center;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }}
            .icon {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: {color};
                color: white;
                font-size: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px;
            }}
            h1 {{ color: #1f2937; margin-bottom: 16px; font-size: 24px; }}
            p {{ color: #6b7280; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">{icon}</div>
            <h1>{title}</h1>
            <p>{message}</p>
        </div>
    </body>
    </html>
    """


# -----------------------------------------------------------------------------
# Run with: uvicorn api.main:app --reload --port 8000
# -----------------------------------------------------------------------------
