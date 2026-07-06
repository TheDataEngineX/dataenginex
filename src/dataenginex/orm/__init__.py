"""SQLAlchemy ORM package — new tables only.

Self-contained: does NOT import from or touch ``dataenginex.store`` (the
existing raw-sqlite3 persistence layer used by e.g. ModelRegistry). Migrating
that layer to SQLAlchemy is a separate, riskier effort and explicitly out of
scope here — see
``dataenginex/docs/superpowers/specs/2026-07-06-tmdb-data-intelligence-rearchitecture-design.md``.
"""

from __future__ import annotations

from dataenginex.orm.models import Base, EntityResolutionMatch, JobState
from dataenginex.orm.session import create_all, get_engine, get_session

__all__ = [
    "Base",
    "EntityResolutionMatch",
    "JobState",
    "create_all",
    "get_engine",
    "get_session",
]
