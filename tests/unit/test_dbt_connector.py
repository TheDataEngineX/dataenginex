"""Tests for dataenginex.data.connectors.dbt — DbtConnector."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import duckdb
import pytest

from dataenginex.data.connectors.dbt import DbtConnector


@pytest.fixture()
def dbt_project(tmp_path: Path) -> Path:
    """Create a minimal dbt project directory structure."""
    (tmp_path / "dbt_project.yml").write_text("name: test_project\n")
    return tmp_path


@pytest.fixture()
def dbt_database(dbt_project: Path) -> Path:
    """Create a DuckDB file with a model table pre-populated."""
    db_path = dbt_project / "dev.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE users_cleaned AS SELECT 1 AS id, 'alice' AS name")
    conn.close()
    return db_path


def _ok_run(*args: object, **kwargs: object) -> CompletedProcess[str]:
    return CompletedProcess(args=[], returncode=0, stdout="", stderr="")


def _fail_run(*args: object, **kwargs: object) -> CompletedProcess[str]:
    return CompletedProcess(args=[], returncode=1, stdout="Error output", stderr="stderr msg")


class TestDbtConnectorImportGuard:
    def test_raises_import_error_when_dbt_missing(self, tmp_path: Path) -> None:
        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", False),
            pytest.raises(ImportError, match="dbt CLI not found"),
        ):
            DbtConnector(project_dir=str(tmp_path), model="my_model")

    def test_registered_as_dbt(self) -> None:
        from dataenginex.data.connectors import connector_registry

        cls = connector_registry.get("dbt")
        assert cls is DbtConnector


class TestDbtConnectorConnect:
    def test_connect_succeeds_when_project_exists(self, dbt_project: Path) -> None:
        with patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True):
            c = DbtConnector(project_dir=str(dbt_project), model="users_cleaned")
            c.connect()  # should not raise

    def test_connect_raises_when_project_missing(self, tmp_path: Path) -> None:
        with patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True):
            c = DbtConnector(project_dir=str(tmp_path), model="m")
            with pytest.raises(FileNotFoundError, match="dbt project not found"):
                c.connect()

    def test_disconnect_is_idempotent(self, dbt_project: Path) -> None:
        with patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True):
            c = DbtConnector(project_dir=str(dbt_project), model="m")
            c.disconnect()
            c.disconnect()  # should not raise

    def test_health_check_true_when_project_exists(self, dbt_project: Path) -> None:
        with patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True):
            c = DbtConnector(project_dir=str(dbt_project), model="m")
            assert c.health_check() is True

    def test_health_check_false_when_project_missing(self, tmp_path: Path) -> None:
        with patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True):
            c = DbtConnector(project_dir=str(tmp_path), model="m")
            assert c.health_check() is False


class TestDbtConnectorRead:
    def test_read_runs_dbt_and_returns_rows(self, dbt_project: Path, dbt_database: Path) -> None:
        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True),
            patch("subprocess.run", side_effect=_ok_run),
        ):
            c = DbtConnector(project_dir=str(dbt_project), model="users_cleaned")
            rows = c.read()

        assert len(rows) == 1
        assert rows[0]["name"] == "alice"

    def test_read_table_arg_overrides_model(self, dbt_project: Path, dbt_database: Path) -> None:
        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True),
            patch("subprocess.run", side_effect=_ok_run) as mock_sub,
        ):
            c = DbtConnector(project_dir=str(dbt_project), model="default_model")
            c.read(table="users_cleaned")

        cmd = mock_sub.call_args[0][0]
        assert "users_cleaned" in cmd

    def test_read_dbt_failure_raises(self, dbt_project: Path) -> None:
        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True),
            patch("subprocess.run", side_effect=_fail_run),
        ):
            c = DbtConnector(project_dir=str(dbt_project), model="m")
            with pytest.raises(RuntimeError, match="dbt run failed"):
                c.read()

    def test_read_missing_database_returns_default(self, dbt_project: Path) -> None:
        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True),
            patch("subprocess.run", side_effect=_ok_run),
        ):
            c = DbtConnector(project_dir=str(dbt_project), model="m")
            rows = c.read(default=[])

        assert rows == []

    def test_read_missing_database_raises_without_default(self, dbt_project: Path) -> None:
        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True),
            patch("subprocess.run", side_effect=_ok_run),
        ):
            c = DbtConnector(project_dir=str(dbt_project), model="m")
            with pytest.raises(FileNotFoundError, match="dbt target database not found"):
                c.read()

    def test_read_missing_model_in_db_returns_default(
        self, dbt_project: Path, dbt_database: Path
    ) -> None:
        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True),
            patch("subprocess.run", side_effect=_ok_run),
        ):
            c = DbtConnector(project_dir=str(dbt_project), model="nonexistent_model")
            rows = c.read(default=[])

        assert rows == []

    def test_read_custom_target_database(self, dbt_project: Path, tmp_path: Path) -> None:
        custom_db = tmp_path / "custom.duckdb"
        conn = duckdb.connect(str(custom_db))
        conn.execute("CREATE TABLE orders AS SELECT 99 AS order_id")
        conn.close()

        with (
            patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True),
            patch("subprocess.run", side_effect=_ok_run),
        ):
            c = DbtConnector(
                project_dir=str(dbt_project),
                model="orders",
                target_database=str(custom_db),
            )
            rows = c.read()

        assert rows[0]["order_id"] == 99


class TestDbtConnectorWrite:
    def test_write_raises_not_implemented(self, dbt_project: Path) -> None:
        with patch("dataenginex.data.connectors.dbt._DBT_AVAILABLE", True):
            c = DbtConnector(project_dir=str(dbt_project), model="m")
            with pytest.raises(NotImplementedError, match="read-only"):
                c.write([{"x": 1}])
