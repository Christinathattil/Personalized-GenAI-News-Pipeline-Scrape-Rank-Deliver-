"""Utility to delete all rows from all database tables.

Run with:

    uv run python -m app.database.reset_db --yes

The script will ask for confirmation unless you pass --yes.
"""
from __future__ import annotations

import argparse
import sys
from typing import Dict

from sqlalchemy import text

from . import get_session
from .models import (
    YouTubeVideoORM,
    OpenAIArticleORM,
    AnthropicArticleORM,
    DigestORM,
)


TABLES = [
    YouTubeVideoORM,
    OpenAIArticleORM,
    AnthropicArticleORM,
    DigestORM,
]


def reset_db() -> Dict[str, int]:  # noqa: D401
    """Delete all rows in every table and return counts deleted."""
    with get_session() as session:
        counts: Dict[str, int] = {}
        for orm in TABLES:
            # Use SQLAlchemy bulk delete for efficiency
            deleted = session.query(orm).delete(synchronize_session=False)
            counts[orm.__tablename__] = deleted
        session.commit()
        return counts


def main() -> None:  # noqa: D401
    parser = argparse.ArgumentParser(description="Delete ALL rows from the database")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive operation")
    args = parser.parse_args()

    if not args.yes:
        print("❌  Refusing to wipe database without --yes flag. Abort.")
        sys.exit(1)

    counts = reset_db()
    print("✅  Database cleared. Rows deleted:")
    for table, cnt in counts.items():
        print(f"- {table}: {cnt}")


if __name__ == "__main__":
    main()
