import sqlite3

from dataenginex import StateStore


def test_state_store_records_run_interval_and_receipt(tmp_path):
    store = StateStore(str(tmp_path / "state.sqlite"))
    store.record_run("r1", "retail_pipeline", "s1", "e1", "succeeded")
    store.record_interval("retail_pipeline", "s1", "e1", "succeeded")
    store.index_receipt("r1", "/x/r1.json")
    store.close()

    con = sqlite3.connect(tmp_path / "state.sqlite")
    assert con.execute("SELECT status FROM runs WHERE run_id = 'r1'").fetchone() == (
        "succeeded",
    )
    assert con.execute(
        "SELECT state FROM intervals WHERE pipeline = 'retail_pipeline'"
    ).fetchone() == ("succeeded",)
    assert con.execute("SELECT path FROM receipts WHERE run_id = 'r1'").fetchone() == (
        "/x/r1.json",
    )


def test_interval_is_replaced_on_rerun(tmp_path):
    store = StateStore(str(tmp_path / "state.sqlite"))
    store.record_interval("retail_pipeline", "s1", "e1", "succeeded")
    store.record_interval("retail_pipeline", "s2", "e2", "failed")
    store.close()

    con = sqlite3.connect(tmp_path / "state.sqlite")
    assert con.execute(
        "SELECT interval_start, state FROM intervals WHERE pipeline = 'retail_pipeline'"
    ).fetchone() == ("s2", "failed")
