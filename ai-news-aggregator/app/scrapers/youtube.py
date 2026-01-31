"""YouTube scraping utilities.

Utility functions for pulling the latest videos (and transcripts) for **one or
more YouTube *channel IDs*** using the official RSS feed:
    https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>

Features:
- Fetch recent uploads within a configurable look-back window (default 24 h)
- Retrieve English transcripts via `youtube-transcript-api` (if available)

Only public videos are returned; very new uploads may not have transcripts yet.
"""
from __future__ import annotations

import logging
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

import feedparser
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class Video(BaseModel):
    """Lightweight representation of a YouTube video scraped from RSS."""

    video_id: str  # YouTube video ID (11-char)
    title: str
    url: str
    published_at: datetime
    description: str
    channel_id: str
    channel_title: str
    transcript: Optional[str] = Field(default=None)

    def to_dict(self) -> Dict:
        """Dictionary-serialisable representation."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "description": self.description,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "transcript": self.transcript,
        }


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------


class YouTubeScraper(BaseModel):
    """Scrapes YouTube channels using the public RSS feed & retrieves transcripts."""

    channels: List[str]
    FEED_CHANNEL: str = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def get_latest_videos(
        self,
        since_hours: int = 24,
        include_failed_transcripts: bool = False,
        languages: Optional[List[str]] = None,
    ) -> List[Video]:
        """Fetches and returns videos uploaded in the last `since_hours` hours.

        Parameters
        ----------
        since_hours : int
            Look-back window for filtering videos. Default 24.
        include_failed_transcripts : bool
            If False (default) videos for which no transcript could be fetched
            are excluded from results. If True the Video object is returned
            with `transcript=None`.
        languages : List[str] | None
            Ordered list of language codes to pass to youtube-transcript-api. If
            None defaults to `["en"]`.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        results: List[Video] = []
        languages = languages or ["en"]

        for ch in self.channels:
            logger.info("Fetching RSS for %s", ch)
            feed_url = self._build_feed_url(ch)
            if not feed_url:
                logger.warning("Could not build feed URL for channel %s", ch)
                continue

            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logger.warning("Failed to parse RSS feed for %s: %s", ch, feed.bozo_exception)
                continue

            channel_title = getattr(feed.feed, "title", "")

            for entry in feed.entries:
                # `published_parsed` is time.struct_time in UTC
                published_dt = (
                    datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    if hasattr(entry, "published_parsed") and entry.published_parsed
                    else None
                )
                if not published_dt or published_dt < cutoff:
                    continue  # old video

                video_id = getattr(entry, "yt_videoid", None)
                if not video_id:
                    continue

                transcript = self._fetch_transcript_text(video_id, languages)
                if transcript is None and not include_failed_transcripts:
                    continue

                description = (
                    getattr(entry, "summary", None)
                    or getattr(entry, "media_description", None)
                    or ""
                )

                video = Video(
                    video_id=video_id,
                    title=entry.title,
                    url=entry.link,
                    published_at=published_dt,
                    description=description,
                    channel_id=entry.yt_channelid,
                    channel_title=channel_title or entry.author,
                    transcript=transcript,
                )
                results.append(video)

        logger.info("Found %d new videos", len(results))
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_feed_url(self, channel_id: str) -> Optional[str]:
        """Return the RSS feed URL for a 24-char `UC…` YouTube *channel_id*."""
        channel_id = channel_id.strip()
        if channel_id.startswith("UC") and len(channel_id) == 24:
            return self.FEED_CHANNEL.format(cid=channel_id)
        logger.warning("Invalid YouTube channel ID: %s", channel_id)
        return None

    @staticmethod
    def _fetch_transcript_text(video_id: str, languages: List[str]):
        """Return transcript as plain text string or None."""
        try:
            api = YouTubeTranscriptApi()
            fetched = api.fetch(video_id, languages=languages)
            segments: List[dict] = fetched.to_raw_data()
            import re
            raw = " ".join(seg["text"].strip() for seg in segments if seg["text"].strip())
            # Remove placeholder captions like [MUSIC PLAYING]
            cleaned = re.sub(r"\[ ?music playing ?\]", "", raw, flags=re.IGNORECASE).strip()
            if not cleaned:
                return None
            return cleaned
        except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript) as exc:
            logger.info("Transcript not available for %s: %s", video_id, exc)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unexpected error fetching transcript for %s: %s", video_id, exc)
            return None

if __name__ == "__main__":
    scraper = YouTubeScraper(["UCdR7eGozLjafYMTd2BFnJaQ"])
    videos = scraper.get_latest_videos(since_hours=36)
    for video in videos:
        print(video)