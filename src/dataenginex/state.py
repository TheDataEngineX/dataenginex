"""The state store (decision 0007): owned from day one.

SQLite locally, Postgres in cloud, ONE schema: pipeline intervals,
snapshots and the receipt index. M0 ships the SQLite store; the
cloud reuses the same schema on Postgres.

shortcut: snapshots fold into the intervals table (state column)
until the first backfill needs per-snapshot records (M2).
"""

from __future__ import annotations

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    pipeline TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS intervals (
    pipeline TEXT PRIMARY KEY,
    interval_start TEXT NOT NULL,
    interval_end TEXT NOT NULL,
    state TEXT NOT NULL,
    definition_hash TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS receipts (
    run_id TEXT PRIMARY KEY,
    path TEXT NOT NULL
);
"""


class StateStore:
    def __init__(self, path: str):
        self._con = sqlite3.connect(path)
        self._con.executescript(_SCHEMA)

    def record_run(
        self,
        run_id: str,
        pipeline: str,
        started_at: str,
        finished_at: str,
        status: str,
    ) -> None:
        self._con.execute(
            "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?)",
            (run_id, pipeline, started_at, finished_at, status),
        )
        self._con.commit()

    def record_interval(
        self,
        pipeline: str,
        interval_start: str,
        interval_end: str,
        state: str,
        definition_hash: str = "",
    ) -> None:
        self._con.execute(
            "INSERT OR REPLACE INTO intervals VALUES (?, ?, ?, ?, ?)",
            (pipeline, interval_start, interval_end, state, definition_hash),
        )
        self._con.commit()

    def last_interval(
        self, pipeline: str
    ) -> tuple[str, str, str] | None:
        """(interval_end, state, definition_hash) of the last run, or None."""
        row = self._con.execute(
            "SELECT interval_end, state, definition_hash"
            " FROM intervals WHERE pipeline = ?",
            (pipeline,),
        ).fetchone()
        return row

    def index_receipt(self, run_id: str, path: str) -> None:
        self._con.execute(
            "INSERT OR REPLACE INTO receipts VALUES (?, ?)",
            (run_id, path),
        )
        self._con.commit()

    def close(self) -> None:
        self._con.close()
