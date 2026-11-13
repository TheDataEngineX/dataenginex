import importlib.util
import json
import shutil
from pathlib import Path

import duckdb
import pytest

from dataenginex import (
    Column,
    Contract,
    Pipeline,
    Project,
    Source,
    Structure,
    Transform,
    run_pipeline,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "retail"


def load_example_project() -> Project:
    spec = importlib.util.spec_from_file_location(
        "retail_project", EXAMPLES / "project.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.project


@pytest.fixture()
def retail_project(tmp_path: Path) -> Project:
    for csv in EXAMPLES.glob("*.csv"):
        shutil.copy(csv, tmp_path / csv.name)
    return load_example_project()


def test_retail_pipeline_runs_end_to_end(tmp_path, retail_project):
    receipt = run_pipeline(retail_project, "retail_pipeline", str(tmp_path))

    assert receipt.run.status == "succeeded"
    assert receipt.layers["bronze"]["orders"] == 8
    assert receipt.layers["silver"]["orders_joined"] == 8
    assert receipt.layers["gold"]["gold_daily_sales"] == 4

    # every contract rule passed on the golden data
    assert receipt.quality
    assert all(q.passed for q in receipt.quality)

    # lakehouse parquet files exist and read back with the same rows
    gold_file = tmp_path / ".dex" / "lakehouse" / "gold" / "gold_daily_sales.parquet"
    assert gold_file.exists()
    con = duckdb.connect()
    n = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{gold_file}')"
    ).fetchone()[0]
    assert n == receipt.layers["gold"]["gold_daily_sales"]

    # the receipt file is the record, and the state store indexed it
    receipt_file = tmp_path / ".dex" / "receipts" / (receipt.run.run_id + ".json")
    assert receipt_file.exists()
    data = json.loads(receipt_file.read_text())
    assert data["run"]["status"] == "succeeded"


def test_failed_run_writes_failed_receipt(tmp_path):
    project = Project(
        name="bad",
        pipelines=[
            Pipeline(
                name="p",
                gold=[Transform(name="boom", sql="SELECT * FROM no_such_table")],
            )
        ],
    )
    with pytest.raises(Exception):
        run_pipeline(project, "p", str(tmp_path))
    receipts = list((tmp_path / ".dex" / "receipts").glob("*.json"))
    assert len(receipts) == 1
    assert json.loads(receipts[0].read_text())["run"]["status"] == "failed"


def test_unknown_pipeline_is_an_error(tmp_path):
    project = Project(name="retail")
    with pytest.raises(ValueError):
        run_pipeline(project, "p", str(tmp_path))


def _dirty_project(tmp_path):
    (tmp_path / "orders.csv").write_text(
        "order_id,ordered_at\n"
        "o1,2026-10-01 09:00:00\n"
        "o1,2026-10-01 10:00:00\n"
        ",2026-10-01 11:00:00\n"
    )
    return Project(
        name="dirty",
        structures=[Structure(name="orders", columns=[Column(name="order_id", dtype="string")])],
        contracts=[Contract(structure="orders", not_null=["order_id"], unique=["order_id"])],
        pipelines=[Pipeline(name="p", sources=[Source(name="orders", path="orders.csv")])],
    )


def test_dirty_rows_are_quarantined(tmp_path):
    project = _dirty_project(tmp_path)
    receipt = run_pipeline(project, "p", str(tmp_path))

    # the null row and the duplicate row were quarantined; one row remains
    assert receipt.layers["bronze"]["orders"] == 1
    rules = {q.rule: q for q in receipt.quality}
    assert rules["not_null"].violations == 1
    assert rules["unique"].violations == 1
    assert not rules["not_null"].passed
    assert not rules["unique"].passed

    quarantine = tmp_path / ".dex" / "lakehouse" / "quarantine"
    con = duckdb.connect()
    null_rows = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{quarantine / 'quarantine__orders__order_id__not_null.parquet'}')"
    ).fetchone()[0]
    dupe_rows = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{quarantine / 'quarantine__orders__order_id__unique.parquet'}')"
    ).fetchone()[0]
    assert (null_rows, dupe_rows) == (1, 1)

    # the materialized bronze table is clean
    clean = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{tmp_path / '.dex' / 'lakehouse' / 'bronze' / 'orders.parquet'}')"
    ).fetchone()[0]
    assert clean == 1


def test_rerun_of_same_definition_is_refused_without_force(tmp_path):
    project = _dirty_project(tmp_path)
    run_pipeline(project, "p", str(tmp_path))
    with pytest.raises(ValueError, match="already ran"):
        run_pipeline(project, "p", str(tmp_path))
    # force re-runs
    receipt = run_pipeline(project, "p", str(tmp_path), force=True)
    assert receipt.run.status == "succeeded"


def test_rerun_after_definition_change_is_allowed(tmp_path):
    project = _dirty_project(tmp_path)
    run_pipeline(project, "p", str(tmp_path))
    changed = project.model_copy(deep=True)
    changed.pipelines[0].silver.append(Transform(name="copy", sql="SELECT * FROM orders"))
    receipt = run_pipeline(changed, "p", str(tmp_path))
    assert receipt.layers["silver"]["copy"] == 1
