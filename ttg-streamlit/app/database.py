import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# On Streamlit Cloud the app root is read-only; /tmp is writable.
# Locally, write next to the app file.
_DB_PATH = os.environ.get("TTG_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "ttg_streamlit.db"))
DATABASE_URL = f"sqlite:///{os.path.abspath(_DB_PATH)}"

Base = declarative_base()


@st.cache_resource
def get_engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    return engine


def init_db():
    """Create all tables (idempotent)."""
    from app import models  # noqa — registers all ORM models with Base
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_session():
    engine = get_engine()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()
