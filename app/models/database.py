from sqlalchemy import create_engine
from collections.abc import Generator
from sqlalchemy.orm import sessionmaker,DeclarativeBase,session

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

session_local = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

def get_db()-> Generator[session.Session, None, None]:
    """Yield a database session for one request and always close it afterward."""

    db = session_local()
    try:
        yield db
    finally:
        db.close()

