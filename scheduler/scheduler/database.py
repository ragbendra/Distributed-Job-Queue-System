"""
Database connection for scheduler.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from scheduler.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session.
    
    Returns:
        Database session
    """
    return SessionLocal()
