"""Anthropic News/Research/Engineering RSS scraper.

Combines three separate RSS feeds (news, research, engineering) into one
interface. Mirrors the behaviour of `OpenAINewsScraper`: fetch feeds,
filter by publication time, and return `Article` objects.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional, Set

import feedparser
import requests
from pydantic import BaseModel, Field
try:
    from docling.datamodel.base_models import InputFormat  # type: ignore
except ImportError:  # pragma: no cover
    InputFormat = None  # type: ignore

try:
    from docling.document_converter import DocumentConverter  # type: ignore
except ImportError:  # pragma: no cover
    DocumentConverter = None  # type: ignore[assignment]

__all__ = ["Article", "AnthropicScraper"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Article(BaseModel):
    """Representation of a single Anthropic article."""

    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    categories: List[str] = Field(default_factory=list)
    markdown: str | None = None


def url_to_markdown(url: str) -> str | None:
    """Convert an Anthropic article URL to Markdown using Docling."""
    try:
        html = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (AggregatorBot)"},
            timeout=10,
        ).text
        if DocumentConverter is None or InputFormat is None:
            return None
        conv = DocumentConverter()
        result = conv.convert_string(html, format=InputFormat.HTML, name=url)
        return result.document.export_to_markdown()
    except Exception as exc:  # noqa: BLE001
        logger.warning("markdown conversion failed for %s: %s", url, exc)
        return None


class AnthropicScraper(BaseModel):
    """Fetches Anthropic RSS feeds and returns recent `Article`s."""

    feed_urls: List[str] = [
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
    ]

    def get_articles(self, since_hours: int = 24) -> List[Article]:
        """Return articles published in the last `since_hours` hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        seen: Set[str] = set()  # deduplicate by guid/url
        results: List[Article] = []

        headers = {"User-Agent": "Mozilla/5.0 (AggregatorBot)"}

        for feed_url in self.feed_urls:
            try:
                resp = requests.get(feed_url, headers=headers, timeout=10)
                resp.raise_for_status()
            except Exception as err:  # noqa: BLE001
                logger.warning("HTTP error fetching Anthropic RSS %s: %s", feed_url, err)
                continue

            parsed = feedparser.parse(resp.content)
            if parsed.bozo:
                logger.warning("Failed to parse RSS %s: %s", feed_url, parsed.bozo_exception)
                continue

            for entry in parsed.entries:
                # Parse publication date
                pub_raw: Optional[str] = getattr(entry, "published", None) or getattr(entry, "pubDate", None)
                if not pub_raw:
                    continue
                try:
                    published_dt = parsedate_to_datetime(pub_raw)
                    if published_dt.tzinfo is None:
                        published_dt = published_dt.replace(tzinfo=timezone.utc)
                except Exception:  # noqa: BLE001
                    continue

                if published_dt < cutoff:
                    continue

                guid = entry.get("id") or entry.get("guid") or entry.get("link", "")
                dedup_key = guid or entry.get("link", "")
                if dedup_key in seen:
                    continue  # duplicate across feeds
                seen.add(dedup_key)

                categories = [tag.term for tag in getattr(entry, "tags", []) if hasattr(tag, "term")]

                article = Article(
                    title=entry.title.strip(),
                    description=(getattr(entry, "summary", "") or "").strip(),
                    url=entry.link.strip(),
                    guid=guid.strip(),
                    published_at=published_dt,
                    categories=categories,
                    markdown=url_to_markdown(entry.link.strip()),
                )
                results.append(article)

        logger.info("Found %d Anthropic articles in last %d h", len(results), since_hours)
        # Sort by newest first
        results.sort(key=lambda a: a.published_at, reverse=True)
        return results


if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles = scraper.get_articles(since_hours=168)
    print("Total:", len(articles))
    for art in articles[:1]:
        print(art.model_dump())
    markdown = url_to_markdown(articles[1].url)
    print(markdown)
