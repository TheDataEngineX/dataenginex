"""Entry point for the ``dex`` CLI.

Usage::

    dex --help
    dex validate dex.yaml
    dex version
"""

from __future__ import annotations

from pathlib import Path

import click
import structlog

from dataenginex.config.loader import load_config, validate_config
from dataenginex.core.exceptions import ConfigError

logger = structlog.get_logger()


def _print_table(title: str, rows: list[tuple[str, str]]) -> None:
    col_w = max(len(r[0]) for r in rows) + 2
    click.echo(f"\n{title}")
    click.echo("-" * (col_w + 20))
    for key, val in rows:
        click.echo(f"  {key:<{col_w}}{val}")
    click.echo()


@click.group()
@click.version_option(package_name="dataenginex")
def dex() -> None:
    """DataEngineX — unified Data + ML + AI framework."""


@dex.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--overlay",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Overlay config file (e.g. dex.prod.yaml).",
)
def validate(config_path: Path, overlay: Path | None) -> None:
    """Validate a dex.yaml config file."""
    try:
        cfg = load_config(config_path, overlay=overlay)
    except ConfigError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    issues = validate_config(cfg)
    warnings = [i for i in issues if i.startswith("Warning:")]
    hard_errors = [i for i in issues if not i.startswith("Warning:")]

    if warnings:
        click.echo(f"  {len(warnings)} warning(s):")
        for w in warnings:
            click.echo(f"  ! {w}")

    if hard_errors:
        click.echo(f"  {len(hard_errors)} error(s):", err=True)
        for err in hard_errors:
            click.echo(f"  x {err}", err=True)
        raise SystemExit(1)

    _print_table(
        f"Config: {cfg.project.name} v{cfg.project.version}",
        [
            ("Data Sources", str(len(cfg.data.sources))),
            ("Data Pipelines", str(len(cfg.data.pipelines))),
            ("ML Experiments", str(len(cfg.ml.experiments))),
            ("AI Agents", str(len(cfg.ai.agents))),
            ("AI Collections", str(len(cfg.ai.collections))),
        ],
    )
    click.echo("Config is valid.")


@dex.command()
def version() -> None:
    """Show DataEngineX version and environment info."""
    import importlib.metadata
    import platform
    import sys

    ver = importlib.metadata.version("dataenginex")
    click.echo(f"DataEngineX {ver}")
    click.echo(f"Python {sys.version}")
    click.echo(f"Platform {platform.platform()}")


from dataenginex.cli.run import run  # noqa: E402
from dataenginex.cli.secops import secops  # noqa: E402
from dataenginex.cli.train import train  # noqa: E402

dex.add_command(run)
dex.add_command(secops)
dex.add_command(train)

if __name__ == "__main__":
    dex()
