"""dbt connector — runs a dbt model and reads back its materialized output.

Uses the dbt-duckdb adapter: shells out to ``dbt run --select <model>``,
then reads the model table from the DuckDB target database.

Install dbt with::

    uv sync --group dbt
    # or: pip install dbt-core dbt-duckdb

Configure a DuckDB profile in ``{project_dir}/profiles.yml`` that writes
to ``{target_database}`` (default: ``{project_dir}/dev.duckdb``).

Usage in dex.yaml::

    data:
      sources:
        transformed_users:
          type: dbt
          connection:
            project_dir: ./dbt_project
            model: users_cleaned
            target_database: ./dbt_project/dev.duckdb
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import duckdb
import structlog

from dataenginex.core.interfaces import BaseConnector
from dataenginex.data.connectors import connector_registry
from dataenginex.data.connectors._utils import rows_to_dicts

logger = structlog.get_logger()

_DBT_AVAILABLE = shutil.which("dbt") is not None

_IMPORT_ERROR = (
    "dbt CLI not found. Install dbt externally: "
    "https://docs.getdbt.com/docs/core/pip-install  "
    "For local DuckDB projects: pip install dbt-core dbt-duckdb"
)


@connector_registry.decorator("dbt")
class DbtConnector(BaseConnector):
    """dbt connector — runs a model and reads its DuckDB-materialized output.

    Requires dbt-core and dbt-duckdb (install with: uv sync --group dbt).
    DataEngineX shells out to ``dbt run``, then queries the DuckDB target file that
    the dbt-duckdb adapter writes to.

    Args:
        project_dir: Path to the dbt project root (must contain dbt_project.yml).
        model: dbt model name to run and read.
        target_database: Path to the DuckDB file dbt writes to.
                         Defaults to ``{project_dir}/dev.duckdb``.
        profiles_dir: Path to the dbt profiles directory.
                      Defaults to ``project_dir``.
        target: dbt target name (default ``"dev"``).
    """

    def __init__(
        self,
        project_dir: str,
        model: str,
        target_database: str | None = None,
        profiles_dir: str | None = None,
        target: str = "dev",
        timeout_s: float = 600,
        **kwargs: Any,
    ) -> None:
        if not _DBT_AVAILABLE:
            raise ImportError(_IMPORT_ERROR)
        self._project_dir = Path(project_dir)
        self._model = model
        self._target_db = (
            Path(target_database) if target_database else self._project_dir / "dev.duckdb"
        )
        self._profiles_dir = Path(profiles_dir) if profiles_dir else self._project_dir
        self._target = target
        self._timeout_s = timeout_s

    def connect(self) -> None:
        project_file = self._project_dir / "dbt_project.yml"
        if not project_file.exists():
            msg = f"dbt project not found: {project_file}"
            raise FileNotFoundError(msg)
        logger.debug("dbt connector ready", project=str(self._project_dir), model=self._model)

    def disconnect(self) -> None:
        # No persistent connection — each read() opens and closes its own DuckDB handle.
        pass

    def read(
        self,
        *,
        table: str | None = None,
        default: Any = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        model = table or self._model
        self._run_dbt(model)
        return self._read_model(model, default=default)

    def write(self, data: Any, *, table: str = "output", **kwargs: Any) -> None:
        msg = "DbtConnector is read-only — writes are managed by dbt models"
        raise NotImplementedError(msg)

    def health_check(self) -> bool:
        return (self._project_dir / "dbt_project.yml").exists()

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _run_dbt(self, model: str) -> None:
        cmd = [
            "dbt",
            "run",
            "--select",
            model,
            "--project-dir",
            str(self._project_dir),
            "--profiles-dir",
            str(self._profiles_dir),
            "--target",
            self._target,
        ]
        try:
            proc = subprocess.run(  # noqa: S603,S607
                cmd, capture_output=True, text=True, timeout=self._timeout_s
            )
        except subprocess.TimeoutExpired as exc:
            msg = f"dbt run timed out for model '{model}' after {self._timeout_s}s"
            raise RuntimeError(msg) from exc
        if proc.returncode != 0:
            msg = f"dbt run failed for model '{model}':\n{proc.stdout}\n{proc.stderr}"
            raise RuntimeError(msg)
        logger.info("dbt run complete", model=model, target=self._target)

    def _read_model(self, model: str, *, default: Any) -> list[dict[str, Any]]:
        if not self._target_db.exists():
            if default is not None:
                return list(default)
            msg = f"dbt target database not found: {self._target_db}. Run dbt first."
            raise FileNotFoundError(msg)
        conn = duckdb.connect(str(self._target_db), read_only=True)
        try:
            result = conn.execute(f"SELECT * FROM {model}")  # noqa: S608
            rows = rows_to_dicts(result)
        except duckdb.CatalogException:
            if default is not None:
                conn.close()
                return list(default)
            conn.close()
            raise
        conn.close()
        logger.info("dbt model read", model=model, database=str(self._target_db), rows=len(rows))
        return rows
