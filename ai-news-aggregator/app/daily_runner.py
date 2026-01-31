"""Daily Pipeline Runner

This script orchestrates the full AI-news pipeline in three sequential phases:

1. **Scrape articles/videos** from YouTube, OpenAI and Anthropic sources and persist
   them to the database (`app.runner.aggregate`).
2. **Generate digests** for new articles (`DigestProcessor`).
3. **Rank digests & send email** to the end-user (`send_digest_email`).

It is designed to be triggered once per day via cron, Airflow, GitHub Actions or
similar schedulers. All heavy-lifting is delegated to the underlying agents so
this wrapper stays thin.

Run manually with for example:

    uv run python -m app.daily_runner --hours 24 --top 10
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

# Phase 1 – Scraping
from app.runner import aggregate  # noqa: WPS433 (internal import ok)

# Phase 2 – Digest generation
from app.agents.processors.digest_processor import DigestProcessor

# Phase 3 – Email creation & sending
from app.agents.processors.process_email import send_digest_email


logger = logging.getLogger("daily_runner")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


###############################################################################
# Helper functions
###############################################################################

def json_preview(data: Any, limit: int = 1000) -> str:  # noqa: D401
    """Return pretty-printed JSON truncated to *limit* characters."""
    txt = json.dumps(data, default=str, ensure_ascii=False, indent=2)
    return (txt[: limit] + "…") if len(txt) > limit else txt


def run_scraper(hours: int) -> dict:
    logger.info("Running scraper (look-back: %s h)…", hours)
    scraped = aggregate(hours)
    logger.info("Scraper done: %s videos, %s OpenAI articles, %s Anthropic articles inserted", scraped.get("inserted_videos"), scraped.get("inserted_openai"), scraped.get("inserted_anthropic"))
    logger.debug("Scraper output:\n%s", json_preview(scraped))
    return scraped


def run_digest_generation(model: str) -> dict:
    logger.info("Generating digests with model %s…", model)
    processor = DigestProcessor(model_name=model)
    result = processor.process_pending_articles()
    logger.info("Digest generation done. New digests: %s, failed: %s", result.get("total_processed"), result.get("total_failed"))
    logger.debug("Digest processor output:\n%s", json_preview(result))
    return result


def run_email(hours: int, top_n: int) -> dict:
    logger.info("Creating & sending digest email (top %s, %s h window)…", top_n, hours)
    outcome = send_digest_email(hours=hours, top_n=top_n)
    if outcome.get("success") and outcome.get("email_sent"):
        logger.info("Email successfully sent – subject: %s", outcome.get("subject"))
    elif outcome.get("success"):
        logger.warning("Email generated but failed to send (see logs). Subject: %s", outcome.get("subject"))
    else:
        logger.error("Email generation failed: %s", outcome.get("error"))
    logger.debug("Email outcome:\n%s", json_preview(outcome))
    return outcome


###############################################################################
# Main orchestration
###############################################################################

def main() -> None:  # noqa: D401
    parser = argparse.ArgumentParser(description="Run full daily AI news pipeline")
    parser.add_argument("--hours", type=int, default=24, help="Look-back window in hours (default 24)")
    parser.add_argument("--top", type=int, default=10, help="Number of top articles to include in email (default 10)")
    parser.add_argument("--model", default="sshleifer/distilbart-cnn-12-6", help="HF summarisation model for digests")
    parser.add_argument("--skip_scrape", action="store_true", help="Skip scraping phase")
    parser.add_argument("--skip_digest", action="store_true", help="Skip digest generation phase")
    parser.add_argument("--skip_email", action="store_true", help="Skip email phase")

    args = parser.parse_args()

    # Print banner
    logger.info("=== Daily AI-News Pipeline ===")
    logger.info("Working directory: %s", Path.cwd())

    if not args.skip_scrape:
        run_scraper(args.hours)
    else:
        logger.info("Skipping scraping phase as requested")

    if not args.skip_digest:
        run_digest_generation(args.model)
    else:
        logger.info("Skipping digest generation phase as requested")

    if not args.skip_email:
        run_email(args.hours, args.top)
    else:
        logger.info("Skipping email phase as requested")

    logger.info("Pipeline finished ✔️")


if __name__ == "__main__":
    main()
