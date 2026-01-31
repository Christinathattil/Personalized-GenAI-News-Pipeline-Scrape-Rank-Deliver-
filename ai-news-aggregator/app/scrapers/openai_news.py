"""OpenAI News RSS scraper.

Lightweight helper to fetch recent articles from the OpenAI News feed
( https://openai.com/news/rss ). Uses `feedparser` and Pydantic for a clean
interface.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

import feedparser
import requests
from pydantic import BaseModel, Field
try:
    from docling.datamodel.base_models import InputFormat  # type: ignore
except ImportError:  # pragma: no cover
    InputFormat = None  # type: ignore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from docling.document_converter import DocumentConverter
except ImportError:  # pragma: no cover
    DocumentConverter = None  # type: ignore[assignment]



class Article(BaseModel):
    """Representation of a single OpenAI News article."""

    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    categories: List[str] = Field(default_factory=list)
    markdown: str | None = None


def url_to_markdown(url: str) -> str | None:
    try:
        html = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (AggregatorBot)"},
            timeout=10,
        ).text
        conv = DocumentConverter()
        if InputFormat is None:
            return None
        result = conv.convert_string(html, format=InputFormat.HTML, name=url)   # note: url used for relative links
        return result.document.export_to_markdown()
    except Exception as exc:
        logger.warning("markdown conversion failed for %s: %s", url, exc)
        return None


class OpenAINewsScraper(BaseModel):
    """Fetches the OpenAI News RSS feed and returns recent `Article`s."""

    feed_url: str = "https://openai.com/news/rss.xml"

    def get_articles(self, since_hours: int = 24) -> List[Article]:
        """Return articles published in the last `since_hours` hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        urls_to_try = [self.feed_url, self.feed_url.rstrip(".xml"), self.feed_url.rstrip("rss.xml") + "rss"]
        response = None
        for url in urls_to_try:
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (AggregatorBot)"},
                    timeout=10,
                )
                response.raise_for_status()
                break  # success
            except Exception:
                response = None
                continue
        if response is None or response.status_code >= 400:
            logger.warning("Could not fetch OpenAI RSS from tried URLs: %s", urls_to_try)
            return []

        parsed = feedparser.parse(response.content)
        if parsed.bozo:
            logger.warning("Failed to parse OpenAI feed: %s", parsed.bozo_exception)
            return []

        results: List[Article] = []
        for entry in parsed.entries:
            pub_raw: Optional[str] = getattr(entry, "published", None) or getattr(entry, "pubDate", None)
            if not pub_raw:
                continue
            try:
                published_dt = parsedate_to_datetime(pub_raw).astimezone(timezone.utc)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Cannot parse pubDate '%s': %s", pub_raw, exc)
                continue

            if published_dt < cutoff:
                continue

            guid = entry.get("id") or entry.get("guid") or entry.get("link", "")
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

        logger.info("Found %d OpenAI articles in last %d h", len(results), since_hours)
        return results


if __name__ == "__main__":
    scraper = OpenAINewsScraper()
    articles = scraper.get_articles(since_hours=168)
    print("No of articles: ", len(articles))
    for i, a in enumerate(articles):
        print("\n\n")
        print(i)
        print(a.model_dump())
    markdown = url_to_markdown(articles[11].url)
    print(markdown[:400])