"""Tests for DexStore — the DuckDB-backed persistence layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from dataenginex.store import (
    CatalogEntry,
    DexStore,
    Episode,
    MemoryEntry,
    ModelArtifact,
)


@pytest.fixture()
def store(tmp_path: Path) -> DexStore:
    return DexStore(tmp_path / "store.duckdb")


class TestPipelineRuns:
    def test_record_and_retrieve(self, store: DexStore) -> None:
        rec = store.record_pipeline_run("ingest", True)
        runs = store.get_pipeline_runs()
        assert len(runs) == 1
        assert runs[0].run_id == rec.run_id
        assert runs[0].pipeline_name == "ingest"

    def test_filter_by_pipeline_name(self, store: DexStore) -> None:
        store.record_pipeline_run("a", True)
        store.record_pipeline_run("b", False)
        assert len(store.get_pipeline_runs("a")) == 1
        assert len(store.get_pipeline_runs()) == 2

    def test_record_with_details(self, store: DexStore) -> None:
        rec = store.record_pipeline_run(
            "etl", True, rows_input=100, rows_output=95, steps_completed=3,
        )
        assert rec.rows_input == 100
        assert rec.rows_output == 95

    def test_get_last_pipeline_run(self, store: DexStore) -> None:
        store.record_pipeline_run("p", True)
        last = store.get_last_pipeline_run("p")
        assert last is not None
        assert last.pipeline_name == "p"

    def test_get_last_missing_returns_none(self, store: DexStore) -> None:
        assert store.get_last_pipeline_run("ghost") is None


class TestLineage:
    def test_record_event(self, store: DexStore) -> None:
        ev = store.record(
            operation="ingest", layer="bronze",
            source="csv", destination="raw_data",
            input_count=100, output_count=100,
        )
        assert ev.event_id
        assert ev.operation == "ingest"

    def test_all_events(self, store: DexStore) -> None:
        store.record(operation="ingest", layer="bronze", source="s", destination="d")
        store.record(operation="transform", layer="silver", source="s2", destination="d2")
        assert len(store.all_events) == 2

    def test_get_lineage_event(self, store: DexStore) -> None:
        ev = store.record(operation="ingest", layer="bronze", source="s", destination="d")
        found = store.get_lineage_event(ev.event_id)
        assert found is not None
        assert found.event_id == ev.event_id

    def test_get_lineage_children(self, store: DexStore) -> None:
        parent = store.record(operation="ingest", layer="bronze", source="s", destination="d")
        child = store.record(
            operation="transform", layer="silver",
            source="d", destination="d2", parent_id=parent.event_id,
        )
        children = store.get_lineage_children(parent.event_id)
        assert len(children) == 1
        assert children[0].event_id == child.event_id

    def test_lineage_summary(self, store: DexStore) -> None:
        store.record(operation="ingest", layer="bronze", source="s", destination="d")
        summary = store.lineage_summary()
        assert summary["total_events"] == 1
        assert "bronze" in summary["by_layer"]

    def test_get_missing_event_returns_none(self, store: DexStore) -> None:
        assert store.get_lineage_event("nonexistent") is None

    def test_get_lineage_by_pipeline(self, store: DexStore) -> None:
        store.record(operation="ingest", layer="bronze", source="s", destination="d",
                     pipeline_name="pipe_a")
        store.record(operation="ingest", layer="bronze", source="s2", destination="d2",
                     pipeline_name="pipe_b")
        results = store.get_lineage_by_pipeline("pipe_a")
        assert len(results) == 1

    def test_get_lineage_by_layer(self, store: DexStore) -> None:
        store.record(operation="ingest", layer="bronze", source="s", destination="d")
        store.record(operation="transform", layer="silver", source="s2", destination="d2")
        bronze = store.get_lineage_by_layer("bronze")
        assert len(bronze) == 1


class TestAuditLog:
    def test_log_and_retrieve(self, store: DexStore) -> None:
        store.log_audit(
            actor="user", action="run_pipeline",
            resource="ingest", resource_type="pipeline",
        )
        entries = store.get_audit_events()
        assert len(entries) == 1
        assert entries[0].actor == "user"

    def test_filter_by_actor(self, store: DexStore) -> None:
        store.log_audit(actor="alice", action="run", resource="p", resource_type="pipeline")
        store.log_audit(actor="bob", action="run", resource="p", resource_type="pipeline")
        alice_events = store.get_audit_events(actor="alice")
        assert len(alice_events) == 1


class TestAIMemory:
    def test_save_and_recall(self, store: DexStore) -> None:
        entry = MemoryEntry(content="hello world", role="user", metadata={}, timestamp=1.0)
        store.save_memory(entry)
        recalled = store.get_recent_memory(n=10)
        assert len(recalled) == 1
        assert recalled[0].content == "hello world"

    def test_search_memory(self, store: DexStore) -> None:
        def _mem(content: str, ts: float) -> MemoryEntry:
            return MemoryEntry(content=content, role="user", metadata={}, timestamp=ts)
        store.save_memory(_mem("python rocks", 1.0))
        store.save_memory(_mem("duckdb fast", 2.0))
        results = store.search_memory("python")
        assert len(results) >= 1
        assert any("python" in r.content for r in results)


class TestEpisodes:
    def test_add_and_recall(self, store: DexStore) -> None:
        ep = Episode(task="summarise", steps=[], outcome="done", reward=1.0, timestamp=1.0)
        store.add_episode(ep)
        recalled = store.recall_episodes("summarise")
        assert len(recalled) == 1
        assert recalled[0].task == "summarise"

    def test_recall_filters_by_task(self, store: DexStore) -> None:
        store.add_episode(Episode(task="a", steps=[], outcome="ok", reward=1.0, timestamp=1.0))
        store.add_episode(Episode(task="b", steps=[], outcome="ok", reward=1.0, timestamp=2.0))
        recalled = store.recall_episodes("a")
        assert all(e.task == "a" for e in recalled)


class TestModelArtifacts:
    def _artifact(self, name: str = "model", version: str = "1.0.0") -> ModelArtifact:
        return ModelArtifact(
            name=name, version=version, stage="development",
            artifact_path="/tmp/m.pkl", metrics={}, parameters={},
        )

    def test_register_and_get(self, store: DexStore) -> None:
        art = self._artifact()
        store.register_model(art)
        found = store.get_model("model", "1.0.0")
        assert found is not None
        assert found.name == "model"

    def test_list_model_names(self, store: DexStore) -> None:
        store.register_model(self._artifact("a", "1.0"))
        store.register_model(self._artifact("b", "1.0"))
        names = store.list_model_names()
        assert "a" in names and "b" in names

    def test_list_model_versions(self, store: DexStore) -> None:
        store.register_model(self._artifact("m", "1.0"))
        store.register_model(self._artifact("m", "2.0"))
        versions = store.list_model_versions("m")
        assert "1.0" in versions and "2.0" in versions

    def test_promote_model(self, store: DexStore) -> None:
        store.register_model(self._artifact())
        promoted = store.promote_model("model", "1.0.0", "production")
        assert promoted.stage == "production"

    def test_promote_archives_previous_production(self, store: DexStore) -> None:
        store.register_model(self._artifact("m", "1.0"))
        store.register_model(self._artifact("m", "2.0"))
        store.promote_model("m", "1.0", "production")
        store.promote_model("m", "2.0", "production")
        v1 = store.get_model("m", "1.0")
        assert v1 is not None
        assert v1.stage == "archived"

    def test_get_missing_returns_none(self, store: DexStore) -> None:
        assert store.get_model("ghost", "9.9.9") is None

    def test_get_latest_model(self, store: DexStore) -> None:
        store.register_model(self._artifact("m", "1.0"))
        store.register_model(self._artifact("m", "2.0"))
        latest = store.get_latest_model("m")
        assert latest is not None

    def test_get_production_model(self, store: DexStore) -> None:
        store.register_model(self._artifact())
        store.promote_model("model", "1.0.0", "production")
        prod = store.get_production_model("model")
        assert prod is not None
        assert prod.stage == "production"

    def test_delete_model(self, store: DexStore) -> None:
        store.register_model(self._artifact())
        store.delete_model("model", "1.0.0")
        assert store.get_model("model", "1.0.0") is None


class TestQualityRuns:
    def test_record_and_history(self, store: DexStore) -> None:
        store.record_quality_run({"table_a": {"score": 0.9}})
        history = store.get_quality_history()
        assert len(history["runs"]) == 1


class TestCatalog:
    def test_register_and_get(self, store: DexStore) -> None:
        entry = CatalogEntry(
            name="bronze_jobs", layer="bronze", format="parquet",
            location="/data/bronze/jobs.parquet",
        )
        store.register_catalog(entry)
        found = store.get_catalog("bronze_jobs")
        assert found is not None
        assert found.layer == "bronze"

    def test_all_catalog(self, store: DexStore) -> None:
        store.register_catalog(CatalogEntry(
            name="a", layer="bronze", format="parquet", location="/a",
        ))
        store.register_catalog(CatalogEntry(
            name="b", layer="silver", format="parquet", location="/b",
        ))
        assert len(store.all_catalog()) == 2

    def test_search_catalog(self, store: DexStore) -> None:
        store.register_catalog(CatalogEntry(
            name="bronze_jobs", layer="bronze", format="parquet",
            location="/data/bronze/jobs.parquet",
        ))
        store.register_catalog(CatalogEntry(
            name="silver_jobs", layer="silver", format="parquet",
            location="/data/silver/jobs.parquet",
        ))
        results = store.search_catalog(layer="bronze")
        assert len(results) == 1
        assert results[0].layer == "bronze"

    def test_upsert_catalog_entry(self, store: DexStore) -> None:
        store.register_catalog(CatalogEntry(
            name="tbl", layer="gold", format="parquet", location="/x",
        ))
        store.register_catalog(CatalogEntry(
            name="tbl", layer="gold", format="parquet", location="/x", record_count=42,
        ))
        found = store.get_catalog("tbl")
        assert found is not None
        assert found.record_count == 42

    def test_get_missing_returns_none(self, store: DexStore) -> None:
        assert store.get_catalog("ghost") is None


class TestConnection:
    def test_raw_connection_property(self, store: DexStore) -> None:
        conn = store.connection
        result = conn.execute("SELECT 42 AS n").fetchone()
        assert result is not None
        assert result[0] == 42

    def test_close(self, store: DexStore) -> None:
        store.close()
