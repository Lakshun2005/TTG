import os
import sys
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# On Streamlit Cloud the app root is read-only; /tmp is writable.
# Detect cloud by checking for /mount/src (Streamlit Cloud mount point).
_ON_CLOUD = os.path.exists("/mount/src") or "STREAMLIT_SHARING_MODE" in os.environ

if _ON_CLOUD:
    _DB_PATH = "/tmp/ttg_streamlit.db"
else:
    _DB_PATH = os.environ.get(
        "TTG_DB_PATH",
        os.path.join(os.path.dirname(__file__), "..", "ttg_streamlit.db"),
    )

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.abspath(_DB_PATH)}")

Base = declarative_base()

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
        _engine = create_engine(DATABASE_URL, connect_args=connect_args)
    return _engine


def init_db():
    """Create all tables (idempotent)."""
    from app import models  # noqa — registers all ORM models with Base
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_session():
    engine = get_engine()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()
