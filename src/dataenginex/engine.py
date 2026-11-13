"""The local DuckDB engine: one pipeline run to completion.

Sources land in Bronze as-is, transforms run per layer in order,
every produced table is materialized to Parquet under the workspace
lakehouse (the DuckLake pattern: metadata in SQL, data in Parquet -
decision 0004), contract checks run at the end, and one receipt is
written no matter what.

shortcut: writes Parquet + state-store metadata directly instead of
going through a DuckLake library; the table-format adapter (M2) is
where a real DuckLake/Iceberg implementation plugs in.
"""

from __future__ import annotations

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


def _check_contracts(
    con: duckdb.DuckDBPyConnection,
    project: Project,
    layer_tables: dict[str, list[str]],
) -> list[QualityResult]:
    """Run the contract slice that exists (not-null, unique) per table.

    Only tables produced by THIS run are checked; a contract on a
    table another pipeline produces reports a structure failure.
    """
    produced = {table for tables in layer_tables.values() for table in tables}
    results: list[QualityResult] = []
    for contract in project.contracts:
        if contract.structure not in produced:
            results.append(
                QualityResult(
                    structure=contract.structure,
                    rule="structure",
                    passed=False,
                )
            )
            continue
        table = contract.structure
        for col in contract.not_null:
            n = con.execute(
                f"SELECT COUNT(*) FROM {_q(table)} WHERE {_q(col)} IS NULL"
            ).fetchone()[0]
            results.append(
                QualityResult(
                    structure=table, column=col, rule="not_null", passed=n == 0, violations=n
                )
            )
        for col in contract.unique:
            n = con.execute(
                f"SELECT COUNT(*) FROM (SELECT {_q(col)} FROM {_q(table)} "
                f"GROUP BY {_q(col)} HAVING COUNT(*) > 1)"
            ).fetchone()[0]
            results.append(
                QualityResult(
                    structure=table, column=col, rule="unique", passed=n == 0, violations=n
                )
            )
    return results


def run_pipeline(
    project: Project,
    pipeline_name: str,
    project_dir: str,
    workspace: str | None = None,
) -> Receipt:
    """Run one pipeline to completion and write its receipt.

    The workspace (default <project_dir>/.dex) holds the SQLite state
    store, the lakehouse Parquet files and the receipts. On failure
    the receipt is still written with status "failed" and the error
    is re-raised.
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
    state = StateStore(str(ws / "state.sqlite"))
    con = duckdb.connect()
    layer_tables: dict[str, list[str]] = {"bronze": [], "silver": [], "gold": []}
    rows: dict[str, dict[str, int]] = {"bronze": {}, "silver": {}, "gold": {}}
    quality: list[QualityResult] = []
    status = "succeeded"
    try:
        for source in pipeline.sources:
            _load_source(con, source, root, layer_tables, rows)
        for layer in ("bronze", "silver", "gold"):
            for transform in getattr(pipeline, layer):
                _run_transform(con, transform, layer, layer_tables, rows)
        for layer, tables in layer_tables.items():
            for table in tables:
                _materialize(con, table, layer, lakehouse)
        quality = _check_contracts(con, project, layer_tables)
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
        state.record_interval(pipeline.name, started_at, finished_at, status)
        state.index_receipt(run_id, str(receipt_path))
        state.close()
        con.close()
    return receipt
