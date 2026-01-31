"""Aggregator runner that scrapes YouTube, OpenAI, and Anthropic surfaces.

Channels are sourced from `app.services.config.YOUTUBE_CHANNELS`.
Run with::

    uv run python -m app.services.runner --hours 24
"""
from __future__ import annotations

import argparse
import json
from typing import List

from app.database import get_session
from app.database.repository import Repository

from app.config import YOUTUBE_CHANNELS
from app.scrapers.youtube import YouTubeScraper, Video
from app.scrapers.openai_news import OpenAINewsScraper, Article as OpenAIArticle
from app.scrapers.anthropic_news import AnthropicScraper, Article as AnthropicArticle


def aggregate(since_hours: int = 24) -> dict:  # noqa: D401
    """Scrape all sources and return combined dict."""
    # YouTube
    yt_videos: List[Video] = []
    if YOUTUBE_CHANNELS:
        yt_scraper = YouTubeScraper(channels=YOUTUBE_CHANNELS)
        yt_videos = yt_scraper.get_latest_videos(since_hours=since_hours, include_failed_transcripts=True)

    # OpenAI & Anthropic
    openai_articles: List[OpenAIArticle] = (
        OpenAINewsScraper().get_articles(since_hours=since_hours)
    )
    anthropic_articles: List[AnthropicArticle] = (
        AnthropicScraper().get_articles(since_hours=since_hours)
    )

    combined = {
        "youtube": [v.model_dump(exclude={"channel_title"}) for v in yt_videos],
        "openai": [a.model_dump() for a in openai_articles],
        "anthropic": [a.model_dump() for a in anthropic_articles],
    }
    # adapt schemas
    for item in combined["openai"]:
        item["category"] = ", ".join(item.pop("categories", [])) or None
    for item in combined["anthropic"]:
        item["category"] = ", ".join(item.pop("categories", [])) or None

    # Persist to DB
    with get_session() as session:
        repo = Repository(session)
        inserted_v = repo.add_videos(combined["youtube"]) 
        inserted_openai = repo.add_openai_articles(combined["openai"])
        inserted_anth = repo.add_anthropic_articles(combined["anthropic"])
        session.commit()
    combined["inserted_videos"] = inserted_v
    combined["inserted_openai"] = inserted_openai
    combined["inserted_anthropic"] = inserted_anth
    return combined


def main() -> None:  # noqa: D401
    parser = argparse.ArgumentParser(description="Run AI news aggregator runner")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Look-back window in hours (default: 24)",
    )
    args = parser.parse_args()

    combined = aggregate(args.hours)
    print("Summary JSON (truncated to first 1000 chars):\n")
    pretty = json.dumps(combined, default=str, ensure_ascii=False, indent=2)
    print(pretty)

#The first 1 000 characters are shown; add | wc -c if you want the full JSON.

if __name__ == "__main__":
    main()
