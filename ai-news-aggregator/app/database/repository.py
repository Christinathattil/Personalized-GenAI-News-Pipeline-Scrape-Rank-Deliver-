"""Lightweight CRUD helpers."""
from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .models import (
    YouTubeVideoORM,
    OpenAIArticleORM,
    AnthropicArticleORM,
    DigestORM,
)


class Repository:  # noqa: D101
    def __init__(self, session: Session):
        self.session = session

    # ---------------------------------------------------------------------
    # YouTube videos
    # ---------------------------------------------------------------------
    def add_videos(self, videos: Iterable[dict]) -> int:
        """Insert YouTube videos, skipping duplicates."""
        count = 0
        for data in videos:
            # Skip YouTube Shorts (identified by '/shorts/' in URL)
            if '/shorts/' in data.get('url', ''):
                continue
            if self.session.scalar(select(YouTubeVideoORM).filter_by(video_id=data["video_id"])):
                continue
            safe = dict(data)
            txt = safe.get("transcript")
            if not txt or not txt.strip():
                safe["transcript"] = "TRANSCRIPT IS NOT AVAILABLE"
            # Use published date as created_at for consistency
            safe["created_at"] = safe.get("published_at")
            self.session.add(YouTubeVideoORM(**safe))
            count += 1
        return count

    # ------------------------------------------------------------------
    # Articles
    # ------------------------------------------------------------------
    def add_openai_articles(self, articles: Iterable[dict]) -> int:
        count = 0
        for data in articles:
            if self.session.scalar(select(OpenAIArticleORM).filter_by(guid=data["guid"])):
                continue
            safe = dict(data)
            md = safe.get("markdown")
            if not md or not md.strip():
                safe["markdown"] = "MARKDOWN CONVERSION IS NOT AVAILABLE"
            # Ensure created_at mirrors the original publish time
            safe["created_at"] = safe.get("published_at")
            self.session.add(OpenAIArticleORM(**safe))
            count += 1
        return count

    def add_anthropic_articles(self, articles: Iterable[dict]) -> int:
        count = 0
        for data in articles:
            if self.session.scalar(select(AnthropicArticleORM).filter_by(guid=data["guid"])):
                continue
            safe = dict(data)
            md = safe.get("markdown")
            if not md or not md.strip():
                safe["markdown"] = "MARKDOWN CONVERSION IS NOT AVAILABLE"
            # Ensure created_at mirrors the original publish time
            safe["created_at"] = safe.get("published_at")
            self.session.add(AnthropicArticleORM(**safe))
            count += 1
        return count

    # ------------------------------------------------------------------
    # Digest operations
    # ------------------------------------------------------------------
    def get_all_articles_without_digests(self):
        """Get all articles from all sources that don't have digests yet."""
        # Get YouTube videos without digests
        youtube_query = select(YouTubeVideoORM).outerjoin(
            DigestORM, (DigestORM.article_type == "youtube") & (DigestORM.article_id == YouTubeVideoORM.video_id)
        ).where(DigestORM.id.is_(None))
        youtube_videos = self.session.scalars(youtube_query).all()
        
        # Get OpenAI articles without digests
        openai_query = select(OpenAIArticleORM).outerjoin(
            DigestORM, (DigestORM.article_type == "openai") & (DigestORM.article_id == OpenAIArticleORM.guid)
        ).where(DigestORM.id.is_(None))
        openai_articles = self.session.scalars(openai_query).all()
        
        # Get Anthropic articles without digests
        anthropic_query = select(AnthropicArticleORM).outerjoin(
            DigestORM, (DigestORM.article_type == "anthropic") & (DigestORM.article_id == AnthropicArticleORM.guid)
        ).where(DigestORM.id.is_(None))
        anthropic_articles = self.session.scalars(anthropic_query).all()
        
        return {
            "youtube": youtube_videos,
            "openai": openai_articles,
            "anthropic": anthropic_articles
        }

    def add_digest(self, digest_data: dict) -> None:
        """Add a new digest entry."""
        self.session.add(DigestORM(**digest_data))

    def get_digest_by_article(self, article_type: str, article_id: str) -> DigestORM | None:
        """Get existing digest for an article."""
        return self.session.scalar(
            select(DigestORM).filter_by(article_type=article_type, article_id=article_id)
        )

    def get_recent_digests(self, hours: int = 24):
        """Return digests created within the last `hours` hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.scalars(select(DigestORM).where(DigestORM.created_at >= cutoff)).all()

    def get_all_digests(self):
        """Get all digest entries."""
        return self.session.scalars(select(DigestORM)).all()
