"""The local DuckDB engine: one pipeline run to completion.

Sources land in Bronze as-is, transforms run per layer in order,
contract gates quarantine bad rows after each layer (before the next
one consumes them), every produced table is materialized to Parquet
under the workspace lakehouse (the DuckLake pattern: metadata in
SQL, data in Parquet - decision 0004), and one receipt is written
no matter what. Re-runs of an unchanged definition after a
successful run are refused unless forced (decision 0007).

shortcut: writes Parquet + state-store metadata directly instead of
going through a DuckLake library; the table-format adapter (M2) is
where a real DuckLake/Iceberg implementation plugs in.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from dataenginex.definitions import Pipeline, Project, Source, Transform
from dataenginex.receipt import JobInfo, QualityResult, Receipt, RunInfo, write_receipt
from dataenginex.state import StateStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _qpath(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def _find_pipeline(project: Project, pipeline_name: str) -> Pipeline:
    for pipeline in project.pipelines:
        if pipeline.name == pipeline_name:
            return pipeline
    raise ValueError("unknown pipeline: " + pipeline_name)


def _load_source(
    con: duckdb.DuckDBPyConnection,
    source: Source,
    root: Path,
    layer_tables: dict[str, list[str]],
    rows: dict[str, dict[str, int]],
) -> None:
    path = root / source.path
    if not path.exists():
        raise FileNotFoundError("source not found: " + str(path))
    table = source.table or path.stem
    reader = "read_csv_auto" if path.suffix.lower() == ".csv" else "read_parquet"
    con.execute(
        f"CREATE OR REPLACE TABLE {_q(table)} AS "
        f"SELECT * FROM {reader}({_qpath(path)})"
    )
    _count(con, table, "bronze", layer_tables, rows)


def _run_transform(
    con: duckdb.DuckDBPyConnection,
    transform: Transform,
    layer: str,
    layer_tables: dict[str, list[str]],
    rows: dict[str, dict[str, int]],
) -> None:
    con.execute(f"CREATE OR REPLACE TABLE {_q(transform.name)} AS {transform.sql}")
    _count(con, transform.name, layer, layer_tables, rows)


def _count(
    con: duckdb.DuckDBPyConnection,
    table: str,
    layer: str,
    layer_tables: dict[str, list[str]],
    rows: dict[str, dict[str, int]],
) -> None:
    count = con.execute(f"SELECT COUNT(*) FROM {_q(table)}").fetchone()[0]
    layer_tables[layer].append(table)
    rows[layer][table] = count


def _materialize(
    con: duckdb.DuckDBPyConnection, table: str, layer: str, lakehouse: Path
) -> None:
    out = lakehouse / layer / (table + ".parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY (SELECT * FROM {_q(table)}) TO {_qpath(out)} (FORMAT PARQUET)")


def _definition_hash(pipeline: Pipeline) -> str:
    return hashlib.sha256(pipeline.model_dump_json().encode()).hexdigest()


def _quarantine_not_null(
    con: duckdb.DuckDBPyConnection, table: str, col: str
) -> int:
    """Move rows violating not-null into a quarantine table; return count."""
    qt = f"quarantine__{table}__{col}__not_null"
    n = con.execute(
        f"SELECT COUNT(*) FROM {_q(table)} WHERE {_q(col)} IS NULL"
    ).fetchone()[0]
    if n == 0:
        return 0
    con.execute(
        f"CREATE OR REPLACE TABLE {_q(qt)} AS "
        f"SELECT * FROM {_q(table)} WHERE {_q(col)} IS NULL"
    )
    con.execute(f"DELETE FROM {_q(table)} WHERE {_q(col)} IS NULL")
    return n


def _quarantine_duplicates(
    con: duckdb.DuckDBPyConnection, table: str, col: str
) -> int:
    """Move duplicate rows (beyond the first occurrence) into quarantine."""
    qt = f"quarantine__{table}__{col}__unique"
    dupes = (
        f"SELECT rowid FROM (SELECT rowid, ROW_NUMBER() OVER "
        f"(PARTITION BY {_q(col)} ORDER BY rowid) AS rn FROM {_q(table)}) "
        f"WHERE rn > 1"
    )
    con.execute(
        f"CREATE OR REPLACE TABLE {_q(qt)} AS "
        f"SELECT * FROM {_q(table)} WHERE rowid IN ({dupes})"
    )
    n = con.execute(f"SELECT COUNT(*) FROM {_q(qt)}").fetchone()[0]
    if n:
        con.execute(f"DELETE FROM {_q(table)} WHERE rowid IN ({dupes})")
    return n


def _gate_layer(
    con: duckdb.DuckDBPyConnection,
    project: Project,
    layer: str,
    layer_tables: dict[str, list[str]],
    quality: list[QualityResult],
) -> list[str]:
    """Run the contract slice (not-null, unique) on a layer's tables.

    Violating rows move to quarantine tables; the layer's tables keep
    only the rows that passed. Returns the quarantine table names.
    """
    quarantined: list[str] = []
    for contract in project.contracts:
        if contract.structure not in layer_tables[layer]:
            continue
        table = contract.structure
        for col in contract.not_null:
            n = _quarantine_not_null(con, table, col)
            if n:
                quarantined.append(f"quarantine__{table}__{col}__not_null")
            quality.append(
                QualityResult(
                    structure=table, column=col, rule="not_null", passed=n == 0, violations=n
                )
            )
        for col in contract.unique:
            n = _quarantine_duplicates(con, table, col)
            if n:
                quarantined.append(f"quarantine__{table}__{col}__unique")
            quality.append(
                QualityResult(
                    structure=table, column=col, rule="unique", passed=n == 0, violations=n
                )
            )
    return quarantined


def _missing_structure_results(
    project: Project, layer_tables: dict[str, list[str]]
) -> list[QualityResult]:
    produced = {table for tables in layer_tables.values() for table in tables}
    return [
        QualityResult(structure=c.structure, rule="structure", passed=False)
        for c in project.contracts
        if c.structure not in produced
    ]


def run_pipeline(
    project: Project,
    pipeline_name: str,
    project_dir: str,
    workspace: str | None = None,
    force: bool = False,
) -> Receipt:
    """Run one pipeline to completion and write its receipt.

    Sources land in Bronze, transforms run per layer, contract gates
    quarantine bad rows after each layer (before the next one
    consumes them), every table is materialized to Parquet under the
    workspace lakehouse, and one receipt is written no matter what.

    The workspace (default <project_dir>/.dex) holds the SQLite state
    store, the lakehouse Parquet files and the receipts. A re-run of
    the same pipeline definition after a successful run is refused
    unless force=True (idempotent re-runs, decision 0007).
    """
    pipeline = _find_pipeline(project, pipeline_name)
    root = Path(project_dir)
    ws = Path(workspace) if workspace is not None else root / ".dex"
    lakehouse = ws / "lakehouse"
    receipts_dir = ws / "receipts"
    lakehouse.mkdir(parents=True, exist_ok=True)
    receipts_dir.mkdir(parents=True, exist_ok=True)

    run_id = uuid.uuid4().hex
    started_at = _now()
    definition_hash = _definition_hash(pipeline)
    state = StateStore(str(ws / "state.sqlite"))
    if not force:
        last = state.last_interval(pipeline.name)
        if (
            last is not None
            and last[1] == "succeeded"
            and last[2] == definition_hash
        ):
            raise ValueError(
                "pipeline " + pipeline.name
                + " already ran with this definition; pass force=True to re-run"
            )
    con = duckdb.connect()
    layer_tables: dict[str, list[str]] = {"bronze": [], "silver": [], "gold": []}
    rows: dict[str, dict[str, int]] = {"bronze": {}, "silver": {}, "gold": {}}
    quality: list[QualityResult] = []
    quarantined: list[str] = []
    status = "succeeded"
    try:
        for source in pipeline.sources:
            _load_source(con, source, root, layer_tables, rows)
        for layer in ("bronze", "silver", "gold"):
            for transform in getattr(pipeline, layer):
                _run_transform(con, transform, layer, layer_tables, rows)
            quarantined.extend(_gate_layer(con, project, layer, layer_tables, quality))
        quality.extend(_missing_structure_results(project, layer_tables))
        # re-count: gates may have removed quarantined rows
        for layer, tables in layer_tables.items():
            for table in tables:
                rows[layer][table] = con.execute(
                    f"SELECT COUNT(*) FROM {_q(table)}"
                ).fetchone()[0]
        for layer, tables in layer_tables.items():
            for table in tables:
                _materialize(con, table, layer, lakehouse)
        for table in quarantined:
            _materialize(con, table, "quarantine", lakehouse)
    except Exception:
        status = "failed"
        raise
    finally:
        finished_at = _now()
        storage = sum(p.stat().st_size for p in lakehouse.rglob("*.parquet"))
        receipt = Receipt(
            run=RunInfo(
                run_id=run_id,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
            ),
            job=JobInfo(namespace=project.name, name=pipeline.name),
            layers=rows,
            quality=quality,
            cost={"compute": 0.0, "storage": float(storage)},
        )
        receipt_path = write_receipt(receipt, receipts_dir)
        state.record_run(run_id, pipeline.name, started_at, finished_at, status)
        state.record_interval(
            pipeline.name, started_at, finished_at, status, definition_hash
        )
        state.index_receipt(run_id, str(receipt_path))
        state.close()
        con.close()
    return receipt
