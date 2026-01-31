"""Pydantic schemas for API validation."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional


class InterestOut(BaseModel):
    """Interest response schema."""
    id: int
    tag: str
    display_name: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class YouTubeChannelInput(BaseModel):
    """YouTube channel/video URL input."""
    url: str = Field(..., min_length=10, description="YouTube video, playlist, or channel URL")


class UserPreferencesInput(BaseModel):
    """User preferences input."""
    hours_window: int = Field(default=24, ge=18, le=36, description="Delivery window in hours (18-36)")


class SignupRequest(BaseModel):
    """Complete signup request."""
    name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    interest_ids: List[int] = Field(..., min_length=1, max_length=7, description="List of interest IDs (1-7)")
    youtube_urls: List[str] = Field(..., min_length=1, description="List of YouTube URLs")
    hours_window: int = Field(default=24, ge=18, le=36, description="Delivery window in hours")

    @field_validator("interest_ids")
    @classmethod
    def validate_interest_count(cls, v):
        if len(v) > 7:
            raise ValueError("Maximum 7 interests allowed")
        if len(v) < 1:
            raise ValueError("At least 1 interest required")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate interests not allowed")
        return v

    @field_validator("youtube_urls")
    @classmethod
    def validate_youtube_urls(cls, v):
        if len(v) < 1:
            raise ValueError("At least 1 YouTube URL required")
        for url in v:
            if "youtube.com" not in url and "youtu.be" not in url:
                raise ValueError(f"Invalid YouTube URL: {url}")
        return v


class SignupResponse(BaseModel):
    """Signup response."""
    success: bool
    message: str
    user_id: Optional[str] = None


class ConfirmResponse(BaseModel):
    """Email confirmation response."""
    success: bool
    message: str


class UnsubscribeResponse(BaseModel):
    """Unsubscribe response."""
    success: bool
    message: str


class UserProfileOut(BaseModel):
    """User profile response."""
    id: str
    name: str
    email: str
    active: bool
    interests: List[InterestOut]
    hours_window: int
    youtube_channels: List[str]
    trial_expires_at: str

    class Config:
        from_attributes = True
