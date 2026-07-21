"""Tests for the new-tables ORM package (dataenginex.orm).

In-memory SQLite only — no filesystem, no network.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from dataenginex.orm import (
    EntityResolutionMatch,
    JobState,
    create_all,
    get_engine,
    get_session,
)


@pytest.fixture
def session():
    engine = get_engine("sqlite:///:memory:")
    create_all(engine)
    sess = get_session(engine)
    yield sess
    sess.close()
    engine.dispose()


def test_entity_resolution_match_insert_and_query(session):
    match = EntityResolutionMatch(
        source_a_id="tt0111161",
        source_b_id="278",
        match_confidence=0.95,
        resolved_at=datetime(2026, 7, 6, 12, 0, 0),
    )
    session.add(match)
    session.commit()

    fetched = session.get(EntityResolutionMatch, ("tt0111161", "278"))
    assert fetched is not None
    assert fetched.match_confidence == 0.95


def test_entity_resolution_match_pk_uniqueness(session):
    session.add(
        EntityResolutionMatch(
            source_a_id="tt1",
            source_b_id="1",
            match_confidence=1.0,
            resolved_at=datetime(2026, 1, 1),
        )
    )
    session.commit()

    session.add(
        EntityResolutionMatch(
            source_a_id="tt1",
            source_b_id="1",
            match_confidence=0.5,
            resolved_at=datetime(2026, 1, 2),
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_job_state_insert_update_and_query(session):
    job = JobState(
        job_id="job-1",
        job_type="movie_enrichment",
        status="queued",
        payload={"movie_id": 42},
        created_at=datetime(2026, 7, 6, 0, 0, 0),
        updated_at=datetime(2026, 7, 6, 0, 0, 0),
        error_message=None,
    )
    session.add(job)
    session.commit()

    fetched = session.get(JobState, "job-1")
    assert fetched is not None
    assert fetched.status == "queued"
    assert fetched.payload == {"movie_id": 42}

    fetched.status = "failed"
    fetched.error_message = "TMDB fetch failed"
    fetched.updated_at = datetime(2026, 7, 6, 0, 5, 0)
    session.commit()

    refetched = session.get(JobState, "job-1")
    assert refetched.status == "failed"
    assert refetched.error_message == "TMDB fetch failed"


def test_job_state_pk_uniqueness(session):
    session.add(
        JobState(
            job_id="dup",
            job_type="x",
            status="queued",
            payload={},
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
    )
    session.commit()

    session.add(
        JobState(
            job_id="dup",
            job_type="y",
            status="queued",
            payload={},
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
