"""Shared resource-limit helpers for self-hosted, container-constrained deployments."""

from __future__ import annotations

from pathlib import Path

__all__ = ["duckdb_memory_limit"]


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

    Each caller (a pipeline run) opens its own DuckDB connection, and
    dex-studio's job executor runs up to 2 pipelines concurrently — so this
    is 30%, not 60%: two connections at once must still sum to well under
    the container's cap, or an ordinary pipeline run OOMs the whole
    container just from overlapping with a scheduled one.
    """
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
            return f"{max(1, int(limit_bytes * 0.3 / 1024**3))}GB"
    return "1GB"
