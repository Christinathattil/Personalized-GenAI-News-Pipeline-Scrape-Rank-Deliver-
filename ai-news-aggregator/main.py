"""AI-News pipeline command-line entry point.

Runs scrape → digest → email once or on a 24-hour schedule.
"""

from __future__ import annotations

import argparse
import logging
import time

from app.daily_runner import run_scraper, run_digest_generation, run_email

###############################################################################
# Helpers
###############################################################################

def run_pipeline(hours: int, model: str, top: int) -> None:
    """Run the three pipeline phases once."""
    run_scraper(hours)
    run_digest_generation(model)
    run_email(hours, top)

###############################################################################
# CLI parser
###############################################################################

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the AI-News pipeline once or on a fixed schedule",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--hours", type=int, default=24,
                        help="Look-back window for scraper & ranking (h)")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of articles to include in the email")
    parser.add_argument("--model", default="sshleifer/distilbart-cnn-12-6",
                        help="HF summarisation model")
    parser.add_argument("--schedule", action="store_true",
                        help="Run repeatedly every --interval hours")
    parser.add_argument("--interval", type=int, default=24,
                        help="Hours between scheduled runs (when --schedule)")
    parser.add_argument("--stop-after", type=int, default=0,
                        help="Stop after N scheduled runs (0 = unlimited)")
    return parser

###############################################################################
# Main
###############################################################################

def main() -> None:  # noqa: D401
    args = build_parser().parse_args()

    # Immediate run
    run_pipeline(args.hours, args.model, args.top)

    # Scheduling
    if not args.schedule:
        return

    log = logging.getLogger(__name__)
    run_count = 1
    log.info("Scheduling enabled – every %s h (Ctrl+C to stop)", args.interval)
    try:
        while True:
            if args.stop_after and run_count >= args.stop_after:
                log.info("Reached --stop-after=%s – exiting", args.stop_after)
                break
            log.info("Sleeping %s h…", args.interval)
            time.sleep(args.interval * 3600)
            run_count += 1
            log.info("=== Scheduled run #%s ===", run_count)
            run_pipeline(args.hours, args.model, args.top)
    except KeyboardInterrupt:
        log.info("Interrupted by user – exiting")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s · %(levelname)s · %(message)s")
    main()

