"""Sesión de base de datos SQLAlchemy."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_url = settings.database_url
_connect_args: dict = {}
if _url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    _url,
    pool_pre_ping=not _url.startswith("sqlite"),
    echo=False,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
