"""ORM models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base

UTC_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


class YouTubeVideoORM(Base):
    __tablename__ = "youtube_videos"

    video_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    channel_id: Mapped[str] = mapped_column(String(24), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )


class OpenAIArticleORM(Base):
    """Articles from OpenAI blog."""

    __tablename__ = "openai_articles"

    guid: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=UTC_NOW, nullable=False)


class AnthropicArticleORM(Base):
    """Articles from Anthropic feeds."""

    __tablename__ = "anthropic_articles"

    guid: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=UTC_NOW, nullable=False)


class DigestORM(Base):
    """Digest summaries for articles from all sources."""

    __tablename__ = "digests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    article_type: Mapped[str] = mapped_column(String, nullable=False)
    article_id: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=UTC_NOW, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False)
