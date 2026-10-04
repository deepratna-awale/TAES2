"""
Database initialization and configuration
"""

import time
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings
from src.database.models import Base

DATABASE_URL = settings.DATABASE_URL


def _engine_url(url: str) -> str:
    """Pin plain postgres URLs to the psycopg (v3) driver we install, since
    SQLAlchemy's default driver for "postgresql://" differs between versions"""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


# Never print the password
SAFE_DATABASE_URL = make_url(DATABASE_URL).render_as_string(hide_password=True)

# pool_pre_ping drops stale connections (RDS failover, idle timeouts)
engine = create_engine(_engine_url(DATABASE_URL), echo=False, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_database(retries: int = settings.DB_CONNECT_RETRIES):
    """Wait for the database to accept connections, then create tables"""
    print(f"Using DATABASE_URL: {SAFE_DATABASE_URL}")
    attempt = 1
    while True:
        try:
            print("Testing database connection...")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            break
        except Exception as e:
            if attempt >= retries:
                print(f"❌ Could not connect to the database after {attempt} attempts: {e}")
                raise
            delay = min(2 ** attempt, 30)
            print(f"Database not ready (attempt {attempt}/{retries}), retrying in {delay}s: {e}")
            time.sleep(delay)
            attempt += 1

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
