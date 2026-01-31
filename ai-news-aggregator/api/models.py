"""User registration ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Table,
    Column,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

UTC_NOW = lambda: datetime.now(timezone.utc)


# Association table for user interests (max 7 per user enforced at API level)
user_interests = Table(
    "user_interests",
    Base.metadata,
    Column("user_id", String, ForeignKey("registered_users.id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", Integer, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)


class InterestORM(Base):
    """Interest topics with hierarchical tagging."""

    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("interests.id"), nullable=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Self-referential relationship for hierarchy
    children: Mapped[list["InterestORM"]] = relationship("InterestORM", back_populates="parent")
    parent: Mapped["InterestORM | None"] = relationship("InterestORM", back_populates="children", remote_side=[id])


class RegisteredUserORM(Base):
    """Registered newsletter subscribers."""

    __tablename__ = "registered_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    # Email confirmation
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmation_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    unsubscribe_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    
    # Trial period (3 days)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=UTC_NOW, nullable=False)
    trial_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(days=3),
        nullable=False
    )
    
    # Relationships
    interests: Mapped[list[InterestORM]] = relationship("InterestORM", secondary=user_interests)
    preferences: Mapped["UserPreferencesORM"] = relationship("UserPreferencesORM", back_populates="user", uselist=False, cascade="all, delete-orphan")
    youtube_channels: Mapped[list["UserYouTubeChannelORM"]] = relationship("UserYouTubeChannelORM", back_populates="user", cascade="all, delete-orphan")


class UserPreferencesORM(Base):
    """User delivery preferences."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("registered_users.id", ondelete="CASCADE"), nullable=False, unique=True)
    hours_window: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    top_articles: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    
    # Constraint: hours_window between 18 and 36
    __table_args__ = (
        CheckConstraint("hours_window >= 18 AND hours_window <= 36", name="check_hours_window"),
    )
    
    user: Mapped[RegisteredUserORM] = relationship("RegisteredUserORM", back_populates="preferences")


class UserYouTubeChannelORM(Base):
    """User's preferred YouTube channels to scrape."""

    __tablename__ = "user_youtube_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("registered_users.id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(24), nullable=False)
    channel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_url: Mapped[str] = mapped_column(String(500), nullable=False)  # Store original URL for reference
    
    user: Mapped[RegisteredUserORM] = relationship("RegisteredUserORM", back_populates="youtube_channels")


class ArticleCacheORM(Base):
    """Cache for article summaries per interest to avoid OpenAI/HF quota spikes."""

    __tablename__ = "article_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interest_id: Mapped[int] = mapped_column(Integer, ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)
    run_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    top5_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of top 5 articles
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=UTC_NOW, nullable=False)
