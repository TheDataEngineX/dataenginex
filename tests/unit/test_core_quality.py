"""Tests for dataenginex.core.quality — QualityGate, QualityStore and friends."""

from __future__ import annotations

import pytest

from dataenginex.core.medallion_architecture import DataLayer
from dataenginex.core.quality import (
    QualityDimension,
    QualityGate,
    QualityResult,
    QualityStore,
)

# ── QualityDimension ──────────────────────────────────────────────────────────


class TestQualityDimension:
    def test_all_values(self) -> None:
        values = {d.value for d in QualityDimension}
        assert values == {"completeness", "accuracy", "consistency", "timeliness", "uniqueness"}

    def test_str_enum(self) -> None:
        assert QualityDimension.COMPLETENESS == "completeness"
        assert QualityDimension.UNIQUENESS == "uniqueness"


# ── QualityResult ─────────────────────────────────────────────────────────────


class TestQualityResult:
    def _make(self, passed: bool = True, score: float = 0.9) -> QualityResult:
        return QualityResult(
            passed=passed,
            layer="silver",
            quality_score=score,
            threshold=0.75,
            record_count=100,
            valid_count=90,
            dimensions={"completeness": 0.9, "uniqueness": 0.95},
        )

    def test_fields_accessible(self) -> None:
        r = self._make()
        assert r.passed is True
        assert r.layer == "silver"
        assert r.record_count == 100

    def test_to_dict_structure(self) -> None:
        d = self._make().to_dict()
        assert d["passed"] is True
        assert d["layer"] == "silver"
        assert d["quality_score"] == 0.9
        assert "dimensions" in d
        assert "evaluated_at" in d

    def test_to_dict_rounding(self) -> None:
        r = QualityResult(
            passed=True,
            layer="bronze",
            quality_score=0.123456789,
            threshold=0.0,
            record_count=1,
            valid_count=1,
            dimensions={"completeness": 0.999999},
        )
        d = r.to_dict()
        assert len(str(d["quality_score"]).split(".")[-1]) <= 4

    def test_frozen_immutable(self) -> None:
        r = self._make()
        with pytest.raises((AttributeError, TypeError)):
            r.passed = False  # type: ignore[misc]

    def test_profile_defaults_none(self) -> None:
        r = self._make()
        assert r.profile is None


# ── QualityStore ──────────────────────────────────────────────────────────────


class TestQualityStore:
    def _make_result(self, layer: str, score: float, passed: bool = True) -> QualityResult:
        return QualityResult(
            passed=passed,
            layer=layer,
            quality_score=score,
            threshold=0.75,
            record_count=10,
            valid_count=9,
            dimensions={},
        )

    def test_init_empty(self) -> None:
        store = QualityStore()
        assert store.latest("bronze") is None
        assert store.latest("silver") is None

    def test_record_and_latest(self) -> None:
        store = QualityStore()
        r = self._make_result("silver", 0.85)
        store.record(r)
        assert store.latest("silver") is r

    def test_latest_returns_most_recent(self) -> None:
        store = QualityStore()
        r1 = self._make_result("gold", 0.80)
        r2 = self._make_result("gold", 0.95)
        store.record(r1)
        store.record(r2)
        assert store.latest("gold") is r2

    def test_unknown_layer_in_record(self) -> None:
        store = QualityStore()
        r = self._make_result("custom_layer", 0.7)
        store.record(r)
        assert store.latest("custom_layer") is r

    def test_summary_all_layers_present(self) -> None:
        store = QualityStore()
        summary = store.summary()
        assert set(summary["layer_scores"].keys()) == {"bronze", "silver", "gold"}
        assert summary["overall_score"] == 0.0

    def test_summary_with_data(self) -> None:
        store = QualityStore()
        store.record(self._make_result("bronze", 0.6))
        store.record(self._make_result("silver", 0.8))
        store.record(self._make_result("gold", 0.9))
        s = store.summary()
        assert s["layer_scores"]["bronze"] == 0.6
        assert s["layer_scores"]["silver"] == 0.8
        assert s["overall_score"] > 0

    def test_summary_includes_all_dimensions(self) -> None:
        store = QualityStore()
        store.record(
            QualityResult(
                passed=True,
                layer="silver",
                quality_score=0.8,
                threshold=0.75,
                record_count=10,
                valid_count=9,
                dimensions={"completeness": 0.9},
            )
        )
        s = store.summary()
        for dim in QualityDimension:
            assert dim.value in s["dimensions"]

    def test_history_empty(self) -> None:
        store = QualityStore()
        assert store.history("bronze") == []

    def test_history_returns_dicts(self) -> None:
        store = QualityStore()
        store.record(self._make_result("bronze", 0.7))
        store.record(self._make_result("bronze", 0.8))
        h = store.history("bronze")
        assert len(h) == 2
        assert all(isinstance(entry, dict) for entry in h)

    def test_history_limit(self) -> None:
        store = QualityStore()
        for score in [0.6, 0.7, 0.8, 0.9]:
            store.record(self._make_result("silver", score))
        assert len(store.history("silver", limit=2)) == 2

    def test_history_unknown_layer(self) -> None:
        store = QualityStore()
        assert store.history("unknown") == []


# ── QualityGate ───────────────────────────────────────────────────────────────


class TestQualityGateEmptyBatch:
    def test_empty_records_passes(self) -> None:
        gate = QualityGate()
        result = gate.evaluate([], layer=DataLayer.BRONZE)
        assert result.passed is True
        assert result.record_count == 0

    def test_empty_records_with_store(self) -> None:
        store = QualityStore()
        gate = QualityGate(store=store)
        gate.evaluate([], layer=DataLayer.SILVER)
        assert store.latest("silver") is not None

    def test_store_property(self) -> None:
        store = QualityStore()
        gate = QualityGate(store=store)
        assert gate.store is store

    def test_no_store_property(self) -> None:
        gate = QualityGate()
        assert gate.store is None


class TestQualityGateWithRecords:
    def _records(self, n: int = 5) -> list[dict]:
        return [{"id": str(i), "name": f"item_{i}", "value": i} for i in range(n)]

    def test_basic_evaluation(self) -> None:
        gate = QualityGate()
        result = gate.evaluate(self._records(), layer=DataLayer.SILVER)
        assert result.record_count == 5
        assert result.layer == "silver"
        assert 0.0 <= result.quality_score <= 1.0

    def test_passes_bronze_always(self) -> None:
        gate = QualityGate()
        result = gate.evaluate(self._records(), layer=DataLayer.BRONZE)
        assert result.passed is True

    def test_dimensions_present(self) -> None:
        gate = QualityGate()
        result = gate.evaluate(self._records(), layer=DataLayer.BRONZE)
        for dim in QualityDimension:
            assert dim.value in result.dimensions

    def test_required_fields_completeness(self) -> None:
        gate = QualityGate(required_fields={"id", "name"})
        records = [{"id": "1", "name": "a"}, {"id": None, "name": "b"}]
        result = gate.evaluate(records, layer=DataLayer.BRONZE)
        assert result.valid_count < result.record_count

    def test_required_fields_override_at_call_site(self) -> None:
        gate = QualityGate()
        records = [{"id": "1"}, {"id": None}]
        result = gate.evaluate(records, layer=DataLayer.BRONZE, required_fields={"id"})
        assert result.valid_count == 1

    def test_injected_scorer(self) -> None:
        gate = QualityGate(scorer=lambda r: float(r.get("value", 0)) / 10)
        records = [{"value": 8}, {"value": 6}]
        result = gate.evaluate(records, layer=DataLayer.BRONZE)
        assert result.dimensions["accuracy"] > 0.0

    def test_uniqueness_key(self) -> None:
        gate = QualityGate(uniqueness_key="name")
        records = [{"name": "dup"}, {"name": "dup"}, {"name": "unique"}]
        result = gate.evaluate(records, layer=DataLayer.BRONZE)
        assert result.dimensions["uniqueness"] < 1.0

    def test_result_stored_in_store(self) -> None:
        store = QualityStore()
        gate = QualityGate(store=store)
        gate.evaluate(self._records(), layer=DataLayer.GOLD)
        assert store.latest("gold") is not None

    def test_gold_threshold_may_fail(self) -> None:
        gate = QualityGate(scorer=lambda _: 0.0)
        records = [{"id": None}] * 10
        result = gate.evaluate(records, layer=DataLayer.GOLD)
        assert result.threshold == 0.90
        assert result.passed is False

    def test_profile_attached(self) -> None:
        gate = QualityGate()
        result = gate.evaluate(self._records(), layer=DataLayer.BRONZE)
        assert result.profile is not None
