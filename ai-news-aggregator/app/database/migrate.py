"""Simple database migration script to create tables."""

from sqlalchemy import create_engine
from app.database import Base, get_session
from app.database.models import DigestORM


def create_tables():
    """Create all tables defined in models."""
    # Get database URL from session config
    with get_session() as session:
        engine = session.get_bind()
        
        print("Creating database tables...")
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
        
        # Verify digest table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'digests' in tables:
            print("✅ Digest table created successfully!")
        else:
            print("❌ Digest table was not created!")
            
        print(f"Available tables: {', '.join(tables)}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration utilities")
    parser.add_argument(
        "action",
        choices=["create", "tables"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action in ["create", "tables"]:
        create_tables()


if __name__ == "__main__":
    main()
