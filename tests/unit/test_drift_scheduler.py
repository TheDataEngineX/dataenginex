"""Tests for dataenginex.ml.scheduler — drift monitoring scheduler."""

from __future__ import annotations

import time

import pytest

from dataenginex.ml.drift import DriftReport
from dataenginex.orchestration.scheduler import (
    DriftCheckResult,
    DriftMonitorConfig,
    DriftScheduler,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reference() -> dict[str, list[float]]:
    """Stable reference distribution (no drift)."""
    return {
        "feature_a": [float(i) for i in range(100)],
        "feature_b": [float(i) for i in range(100)],
    }


def _make_current_no_drift() -> dict[str, list[float]]:
    """Current data identical to reference — no drift expected."""
    return _make_reference()


def _make_current_drifted() -> dict[str, list[float]]:
    """Shifted distribution — drift expected."""
    return {
        "feature_a": [float(i + 500) for i in range(100)],
        "feature_b": [float(i + 500) for i in range(100)],
    }


# ---------------------------------------------------------------------------
# DriftMonitorConfig
# ---------------------------------------------------------------------------


class TestDriftMonitorConfig:
    def test_defaults(self) -> None:
        config = DriftMonitorConfig(
            model_name="m1",
            reference_data={"f": [1.0, 2.0]},
        )
        assert config.psi_threshold == 0.20
        assert config.check_interval_seconds == 300.0
        assert config.n_bins == 10

    def test_custom_values(self) -> None:
        config = DriftMonitorConfig(
            model_name="m2",
            reference_data={"f": [1.0]},
            psi_threshold=0.10,
            check_interval_seconds=60.0,
            n_bins=20,
        )
        assert config.psi_threshold == 0.10
        assert config.check_interval_seconds == 60.0
        assert config.n_bins == 20


# ---------------------------------------------------------------------------
# DriftCheckResult
# ---------------------------------------------------------------------------


class TestDriftCheckResult:
    def test_to_dict(self) -> None:
        report = DriftReport(
            feature_name="x",
            psi=0.05,
            drift_detected=False,
            severity="none",
        )
        result = DriftCheckResult(
            model_name="test",
            reports=[report],
            drift_detected=False,
            max_psi=0.05,
        )
        d = result.to_dict()
        assert d["model_name"] == "test"
        assert d["drift_detected"] is False
        assert d["max_psi"] == 0.05
        assert len(d["features"]) == 1
        assert d["features"][0]["feature_name"] == "x"

    def test_drift_detected_true(self) -> None:
        report = DriftReport(
            feature_name="y",
            psi=0.35,
            drift_detected=True,
            severity="severe",
        )
        result = DriftCheckResult(
            model_name="m",
            reports=[report],
            drift_detected=True,
            max_psi=0.35,
        )
        assert result.drift_detected is True
        assert result.max_psi == 0.35


# ---------------------------------------------------------------------------
# DriftScheduler — Registration
# ---------------------------------------------------------------------------


class TestSchedulerRegistration:
    def test_register_and_list(self) -> None:
        scheduler = DriftScheduler()
        config = DriftMonitorConfig(
            model_name="m1",
            reference_data=_make_reference(),
        )
        scheduler.register(config, data_fn=_make_current_no_drift)
        assert "m1" in scheduler.registered_models

    def test_register_empty_reference_raises(self) -> None:
        scheduler = DriftScheduler()
        config = DriftMonitorConfig(model_name="bad", reference_data={})
        with pytest.raises(ValueError, match="empty"):
            scheduler.register(config, data_fn=_make_current_no_drift)

    def test_unregister(self) -> None:
        scheduler = DriftScheduler()
        config = DriftMonitorConfig(
            model_name="m1",
            reference_data=_make_reference(),
        )
        scheduler.register(config, data_fn=_make_current_no_drift)
        scheduler.unregister("m1")
        assert "m1" not in scheduler.registered_models

    def test_unregister_not_found_raises(self) -> None:
        scheduler = DriftScheduler()
        with pytest.raises(KeyError, match="not registered"):
            scheduler.unregister("ghost")

    def test_register_replaces_existing(self) -> None:
        scheduler = DriftScheduler()
        ref = _make_reference()
        config1 = DriftMonitorConfig(
            model_name="m1",
            reference_data=ref,
            check_interval_seconds=100,
        )
        config2 = DriftMonitorConfig(
            model_name="m1",
            reference_data=ref,
            check_interval_seconds=200,
        )
        scheduler.register(config1, data_fn=_make_current_no_drift)
        scheduler.register(config2, data_fn=_make_current_no_drift)
        assert scheduler.registered_models == ["m1"]


# ---------------------------------------------------------------------------
# DriftScheduler — Manual Check
# ---------------------------------------------------------------------------


class TestSchedulerManualCheck:
    def test_run_check_no_drift(self) -> None:
        scheduler = DriftScheduler()
        config = DriftMonitorConfig(
            model_name="stable",
            reference_data=_make_reference(),
        )
        scheduler.register(config, data_fn=_make_current_no_drift)
        result = scheduler.run_check("stable")
        assert isinstance(result, DriftCheckResult)
        assert result.drift_detected is False
        assert result.model_name == "stable"
        assert len(result.reports) == 2

    def test_run_check_drift_detected(self) -> None:
        scheduler = DriftScheduler()
        config = DriftMonitorConfig(
            model_name="drifted",
            reference_data=_make_reference(),
            psi_threshold=0.01,  # low threshold to trigger
        )
        scheduler.register(config, data_fn=_make_current_drifted)
        result = scheduler.run_check("drifted")
        assert result.drift_detected is True
        assert result.max_psi > 0
        assert any(r.drift_detected for r in result.reports)

    def test_run_check_not_registered_raises(self) -> None:
        scheduler = DriftScheduler()
        with pytest.raises(KeyError, match="not registered"):
            scheduler.run_check("nope")

    def test_get_last_result_after_check(self) -> None:
        scheduler = DriftScheduler()
        config = DriftMonitorConfig(
            model_name="m1",
            reference_data=_make_reference(),
        )
        scheduler.register(config, data_fn=_make_current_no_drift)
        assert scheduler.get_last_result("m1") is None
        scheduler.run_check("m1")
        result = scheduler.get_last_result("m1")
        assert result is not None
        assert result.model_name == "m1"

    def test_run_check_publishes_metrics(self) -> None:
        """Verify Prometheus gauges are updated after a check."""
        from dataenginex.ml.metrics import model_drift_psi

        scheduler = DriftScheduler()
        config = DriftMonitorConfig(
            model_name="metrics_test",
            reference_data=_make_reference(),
        )
        scheduler.register(config, data_fn=_make_current_no_drift)
        scheduler.run_check("metrics_test")

        # PSI gauge should exist for each feature
        sample_value = model_drift_psi.labels(
            model="metrics_test", feature="feature_a"
        )._value.get()
        assert sample_value >= 0.0


# ---------------------------------------------------------------------------
# DriftScheduler — Background Thread
# ---------------------------------------------------------------------------


class TestSchedulerBackground:
    def test_start_stop(self) -> None:
        scheduler = DriftScheduler(tick_seconds=0.1)
        config = DriftMonitorConfig(
            model_name="bg",
            reference_data=_make_reference(),
            check_interval_seconds=0.1,
        )
        scheduler.register(config, data_fn=_make_current_no_drift)
        scheduler.start()
        assert scheduler.is_running is True
        time.sleep(0.4)
        scheduler.stop()
        assert scheduler.is_running is False
        # Should have completed at least one check
        result = scheduler.get_last_result("bg")
        assert result is not None

    def test_start_twice_raises(self) -> None:
        scheduler = DriftScheduler(tick_seconds=0.1)
        config = DriftMonitorConfig(
            model_name="bg2",
            reference_data=_make_reference(),
            check_interval_seconds=999,
        )
        scheduler.register(config, data_fn=_make_current_no_drift)
        scheduler.start()
        try:
            with pytest.raises(RuntimeError, match="already running"):
                scheduler.start()
        finally:
            scheduler.stop()

    def test_callback_exception_does_not_crash(self) -> None:
        """A failing data_fn should be logged, not crash the scheduler."""

        def bad_callback() -> dict[str, list[float]]:
            msg = "data source unavailable"
            raise ConnectionError(msg)

        scheduler = DriftScheduler(tick_seconds=0.1)
        config = DriftMonitorConfig(
            model_name="fail",
            reference_data=_make_reference(),
            check_interval_seconds=0.1,
        )
        scheduler.register(config, data_fn=bad_callback)
        scheduler.start()
        time.sleep(0.4)
        scheduler.stop()
        # Scheduler should still be stoppable — no crash
        assert scheduler.is_running is False

    def test_stop_without_start(self) -> None:
        """Stopping a scheduler that was never started should be a no-op."""
        scheduler = DriftScheduler()
        scheduler.stop()  # Should not raise
        assert scheduler.is_running is False

    def test_drift_alert_counter_incremented(self) -> None:
        """When drift is detected, model_drift_alerts_total should increment."""
        from dataenginex.ml.metrics import model_drift_alerts_total

        # Get baseline
        before = model_drift_alerts_total.labels(model="alert_test", severity="severe")._value.get()

        scheduler = DriftScheduler(tick_seconds=0.1)
        config = DriftMonitorConfig(
            model_name="alert_test",
            reference_data=_make_reference(),
            psi_threshold=0.01,
            check_interval_seconds=0.1,
        )
        scheduler.register(config, data_fn=_make_current_drifted)
        scheduler.start()
        time.sleep(0.4)
        scheduler.stop()

        after = model_drift_alerts_total.labels(model="alert_test", severity="severe")._value.get()
        assert after > before
