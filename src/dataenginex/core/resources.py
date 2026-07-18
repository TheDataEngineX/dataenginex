"""Shared resource-limit helpers for self-hosted, container-constrained deployments."""

from __future__ import annotations

import threading
from pathlib import Path

__all__ = ["duckdb_memory_limit", "note_duckdb_connection_closed", "note_duckdb_connection_opened"]

# ponytail: process-global counter (not per-container-cgroup) — fine because
# every DuckDB connection this process opens shares the same cgroup ceiling.
_lock = threading.Lock()
_active_connections = 0


def note_duckdb_connection_opened() -> None:
    """Record that a DuckDB connection is about to be opened.

    Call before ``duckdb.connect(...)`` so ``duckdb_memory_limit()`` sees an
    accurate count (including the connection being opened) when sizing it.
    """
    global _active_connections
    with _lock:
        _active_connections += 1


def note_duckdb_connection_closed() -> None:
    """Record that a previously-opened DuckDB connection has been closed."""
    global _active_connections
    with _lock:
        _active_connections = max(0, _active_connections - 1)


def duckdb_memory_limit() -> str:
    """Cap DuckDB's memory to a fraction of the container's cgroup limit.

    Without an explicit cap, a large operation (a hash join build side, or a
    big CSV-to-Parquet conversion) can grow past the container's actual RAM
    before DuckDB's own accounting decides to spill to temp_directory, taking
    the whole process down with it. On a resource-constrained self-hosted
    deployment the limit can't just be raised, so read the real cgroup
    ceiling (v2, then v1) and target a fraction of it, leaving headroom for
    the rest of the process. Falls back to a conservative fixed value
    outside a container.

    Each caller opens its own DuckDB connection and must bracket it with
    ``note_duckdb_connection_opened()``/``note_duckdb_connection_closed()``.
    When this is the only connection open (the common case — e.g.
    max_concurrent_pipelines=1) we can safely use 50% of container RAM. When
    another connection is already open at the same time — e.g. a pipeline's
    own DuckDB connection is still open while its HttpConnector opens a
    second, nested one to convert a downloaded file — 30% each keeps both
    from summing past the container's RAM.
    """
    fraction = 0.30 if _active_connections > 1 else 0.50
    for path in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            raw = Path(path).read_text().strip()
        except OSError:
            continue
        if raw == "max":
            continue
        try:
            limit_bytes = int(raw)
        except ValueError:
            continue
        # cgroup v1 reports a huge sentinel (close to 2**63) when unset.
        if 0 < limit_bytes < (1 << 60):
            return f"{max(1, round(limit_bytes * fraction / 1024**3))}GB"
    return "1GB"
