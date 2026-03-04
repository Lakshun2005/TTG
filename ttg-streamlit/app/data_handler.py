"""
Centralized database session management.
Usage:
    from app.data_handler import db_session
    with db_session() as db:
        result = db.query(Model).all()
"""

from contextlib import contextmanager
from app.database import get_engine
from sqlalchemy.orm import sessionmaker
from app.logger import get_logger

logger = get_logger(__name__)


@contextmanager
def db_session():
    """Context manager that yields a SQLAlchemy session and auto-closes it."""
    engine = get_engine()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}", exc_info=True)
        raise
    finally:
        session.close()
