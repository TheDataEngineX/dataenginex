import importlib.util
import json
import shutil
from pathlib import Path

import duckdb
import pytest

from dataenginex import Pipeline, Project, Transform, run_pipeline

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
        run_pipeline(project, "nope", str(tmp_path))
