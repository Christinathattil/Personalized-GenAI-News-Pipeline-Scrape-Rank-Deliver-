"""Create all tables defined in ORM models."""
from __future__ import annotations

from . import Base, engine  # noqa: WPS433 (import from internal)
import app.database.models  # noqa: F401  # ensure models are registered


def main() -> None:  # noqa: D401
    print("Creating tables if not present…")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")


if __name__ == "__main__":
    main()
