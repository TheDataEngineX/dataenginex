"""New-table ORM models: entity-resolution match confidence + job state.

Naming judgment call (``EntityResolutionMatch``): the pipeline that produces
this data (``silver_entity_resolution`` / ``gold_cross_source_match_confidence``
in dex-studio/examples/movie-dex/dex.yaml) uses TMDB/IMDB-specific column
names (``tconst``, ``tmdb_id``). This table is core dataenginex infrastructure
shared by any project's entity-resolution pipeline, not moviedex-specific, so
it uses generic ``source_a_id`` / ``source_b_id`` (both ``str`` — numeric ids
such as a TMDB id are stored as their string form) instead of hardcoding
``tconst``/``tmdb_id``. A moviedex-specific loader maps the two shapes at the
project-plugin boundary.

Primary key: composite ``(source_a_id, source_b_id)`` rather than a surrogate
id — a match between two given source records is naturally unique, so the
composite key enforces that for free without an extra unique index.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for new ORM tables only (see package docstring)."""


class EntityResolutionMatch(Base):
    """A cross-source entity match and its confidence score."""

    __tablename__ = "entity_resolution_match"

    source_a_id: Mapped[str] = mapped_column(String, primary_key=True)
    source_b_id: Mapped[str] = mapped_column(String, primary_key=True)
    match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class JobState(Base):
    """State of a RabbitMQ-dispatched job (e.g. "enrich movie X")."""

    __tablename__ = "job_state"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # queued/running/done/failed
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
