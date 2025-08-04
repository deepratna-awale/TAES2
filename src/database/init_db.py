"""
Database initialization and configuration
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.models import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:taes2_secure_password@localhost:5432/taes2_db")
print(f"Using DATABASE_URL: {DATABASE_URL}")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_database():
    """Initialize database tables"""
    try:
        print("Testing database connection...")
        # Test connection first
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
        
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        print(f"Database URL being used: {DATABASE_URL}")
        raise
