from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

_engine = None
_SessionLocal = None


def init_db(database_url: str):
    """Initialize database and create tables"""
    global _engine, _SessionLocal

    _engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(bind=_engine)

    return _SessionLocal()


def get_session() -> Session:
    """Get a new database session"""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _SessionLocal()
