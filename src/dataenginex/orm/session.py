"""Thin engine/session helpers for the new ORM tables.

Not a unit-of-work framework — just the three calls a caller needs:
create an engine, create the tables, get a session.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from dataenginex.orm.models import Base


def get_engine(db_url: str) -> Engine:
    """Create a SQLAlchemy engine for ``db_url`` (e.g. ``sqlite:///:memory:``)."""
    return create_engine(db_url)


def create_all(engine: Engine) -> None:
    """Create all tables defined on :class:`dataenginex.orm.models.Base`."""
    Base.metadata.create_all(engine)


def get_session(engine: Engine) -> Session:
    """Return a new session bound to ``engine``."""
    return sessionmaker(bind=engine)()
