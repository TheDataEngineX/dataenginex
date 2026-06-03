"""`dex secops` — inspect and test the PrivacyGuard from the command line.

Subcommands::

    dex secops status            # show guard config from the loaded dex.yaml
    dex secops scan "some text"  # run PII detection and show matches
"""

from __future__ import annotations

from pathlib import Path

import click

_DEFAULT_CONFIG = "dex.yaml"


@click.group()
def secops() -> None:
    """SecOps — PrivacyGuard inspection and PII scanning."""


@secops.command()
@click.option("--config", "config_path", default=_DEFAULT_CONFIG, help="dex.yaml path")
def status(config_path: str) -> None:
    """Show the PrivacyGuard configuration from dex.yaml."""
    from dataenginex.config import load_config

    cfg = load_config(Path(config_path))
    g = cfg.secops.guard
    a = cfg.secops.audit

    _section("Guard")
    _row("Enabled", _yn(g.enabled))
    _row("Block on detect", _yn(g.block_on_detect))
    _row("Allow local bypass", _yn(g.allow_local))
    _row("Log all outbound", _yn(g.log_all_outbound))
    _row(
        "Local targets",
        ", ".join(sorted(g.local_targets)) if g.local_targets else "(none)",
    )

    if g.strategies:
        click.echo()
        _section("PII Strategies")
        for pii_type, strategy in sorted(g.strategies.items()):
            _row(pii_type, strategy)
    else:
        _row("PII strategies", "default (REDACT all)")

    click.echo()
    _section("Audit Logger")
    _row("Enabled", _yn(a.enabled))
    if a.enabled:
        _row("DB path", a.db_path if a.db_path else ":memory: (no persistence)")

    click.echo()


@secops.command()
@click.argument("text")
@click.option("--config", "config_path", default=_DEFAULT_CONFIG, help="dex.yaml path")
@click.option(
    "--target",
    default="openai",
    show_default=True,
    help="Provider target name (affects local-bypass logic).",
)
def scan(text: str, config_path: str, target: str) -> None:
    """Scan TEXT for PII using the guard configured in dex.yaml.

    Prints each match (type, confidence, matched value) and shows the masked
    output the guard would send to the provider.
    """
    from dataenginex.config import load_config
    from dataenginex.secops import PrivacyGuard, PrivacyGuardConfig

    cfg = load_config(Path(config_path))
    guard_cfg = PrivacyGuardConfig.from_dict(cfg.secops.guard.model_dump())
    guard = PrivacyGuard(config=guard_cfg)

    result = guard.process(text, target=target)

    if result.bypassed_local:
        click.echo(click.style(f"⊘  Bypassed — '{target}' is a local provider", fg="yellow"))
        return

    if result.detections:
        _section(f"Detections ({len(result.detections)})")
        for m in result.detections:
            conf = f"{m.confidence:.0%}" if m.confidence is not None else ""
            click.echo(
                f"  {click.style(m.pii_type.value, fg='red', bold=True):<20}"
                f"  {conf:<8}"
                f"  {m.value!r}"
            )
        click.echo()
        if result.blocked:
            click.echo(click.style("✗  BLOCKED — prompt would not be sent", fg="red", bold=True))
        else:
            _section("Masked output")
            click.echo(f"  {result.safe_prompt}")
    else:
        click.echo(click.style("✓  No PII detected", fg="green"))
        click.echo(f"  {text}")

    click.echo()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _section(title: str) -> None:
    click.echo(click.style(f"  {title}", bold=True))
    click.echo(click.style("  " + "─" * (len(title) + 2), fg="bright_black"))


def _row(key: str, value: str) -> None:
    click.echo(f"    {key:<28}{value}")


def _yn(flag: bool) -> str:
    return click.style("yes", fg="green") if flag else click.style("no", fg="red")
