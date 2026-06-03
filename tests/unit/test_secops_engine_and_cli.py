"""Tests for secops engine wiring (AuditLogger) + validate_secops + dex secops CLI."""

from __future__ import annotations

from typing import Any

import pytest
from click.testing import CliRunner

from dataenginex.cli.main import dex
from dataenginex.config.loader import validate_config
from dataenginex.config.schema import (
    AuditConfig,
    DexConfig,
    GuardConfig,
    ProjectConfig,
    SecopsConfig,
)

# ---------------------------------------------------------------------------
# _validate_secops — part of validate_config
# ---------------------------------------------------------------------------


class TestValidateSecops:
    def test_valid_strategies_produce_no_errors(self) -> None:
        cfg = DexConfig(
            project=ProjectConfig(name="t"),
            secops=SecopsConfig(guard=GuardConfig(strategies={"email": "hash", "ssn": "redact"})),
        )
        hard = [e for e in validate_config(cfg) if not e.startswith("Warning:")]
        assert hard == []

    def test_unknown_pii_type_is_hard_error(self) -> None:
        cfg = DexConfig(
            project=ProjectConfig(name="t"),
            secops=SecopsConfig(guard=GuardConfig(strategies={"unicorn": "hash"})),
        )
        errors = validate_config(cfg)
        assert any("unknown PII type" in e and "unicorn" in e for e in errors)

    def test_unknown_masking_strategy_is_hard_error(self) -> None:
        cfg = DexConfig(
            project=ProjectConfig(name="t"),
            secops=SecopsConfig(guard=GuardConfig(strategies={"email": "obfuscate_lol"})),
        )
        errors = validate_config(cfg)
        assert any("unknown masking strategy" in e and "obfuscate_lol" in e for e in errors)

    def test_both_unknown_generates_two_errors(self) -> None:
        cfg = DexConfig(
            project=ProjectConfig(name="t"),
            secops=SecopsConfig(guard=GuardConfig(strategies={"bad_type": "bad_strat"})),
        )
        errors = validate_config(cfg)
        secops_errors = [e for e in errors if "secops.guard" in e]
        assert len(secops_errors) == 2

    def test_empty_strategies_is_valid(self) -> None:
        cfg = DexConfig(project=ProjectConfig(name="t"))
        hard = [e for e in validate_config(cfg) if not e.startswith("Warning:")]
        assert hard == []


# ---------------------------------------------------------------------------
# AuditConfig schema
# ---------------------------------------------------------------------------


class TestAuditConfigSchema:
    def test_defaults(self) -> None:
        a = AuditConfig()
        assert a.enabled is False
        assert a.db_path == ""

    def test_enabled_with_memory_path(self) -> None:
        a = AuditConfig(enabled=True, db_path="")
        assert a.enabled is True
        assert a.db_path == ""

    def test_enabled_with_file_path(self) -> None:
        a = AuditConfig(enabled=True, db_path="audit.db")
        assert a.db_path == "audit.db"


# ---------------------------------------------------------------------------
# Engine — AuditLogger wiring
# ---------------------------------------------------------------------------


@pytest.fixture
def _yaml_audit_disabled(tmp_path: Any) -> Any:
    p = tmp_path / "dex.yaml"
    p.write_text(
        """
project:
  name: AuditWiringTest
  version: 0.1.0
secops:
  audit:
    enabled: false
  guard:
    enabled: true
"""
    )
    return p


@pytest.fixture
def _yaml_audit_memory(tmp_path: Any) -> Any:
    p = tmp_path / "dex.yaml"
    p.write_text(
        """
project:
  name: AuditMemoryTest
  version: 0.1.0
secops:
  audit:
    enabled: true
    db_path: ""
  guard:
    enabled: true
"""
    )
    return p


@pytest.fixture
def _yaml_audit_file(tmp_path: Any) -> Any:
    p = tmp_path / "dex.yaml"
    p.write_text(
        """
project:
  name: AuditFileTest
  version: 0.1.0
secops:
  audit:
    enabled: true
    db_path: "secops_audit.db"
  guard:
    enabled: true
"""
    )
    return p


class TestEngineAuditWiring:
    def test_audit_disabled_secops_audit_is_none(self, _yaml_audit_disabled: Any) -> None:
        from dataenginex.engine import DexEngine

        engine = DexEngine(_yaml_audit_disabled)
        assert engine.secops_audit is None
        assert engine.privacy_guard._audit is None  # noqa: SLF001

    def test_audit_memory_creates_audit_logger(self, _yaml_audit_memory: Any) -> None:
        from dataenginex.engine import DexEngine
        from dataenginex.secops import AuditLogger

        engine = DexEngine(_yaml_audit_memory)
        assert isinstance(engine.secops_audit, AuditLogger)
        assert engine.privacy_guard._audit is engine.secops_audit  # noqa: SLF001

    def test_audit_file_resolves_under_dex_dir(self, _yaml_audit_file: Any) -> None:
        from dataenginex.engine import DexEngine
        from dataenginex.secops import AuditLogger

        engine = DexEngine(_yaml_audit_file)
        assert isinstance(engine.secops_audit, AuditLogger)
        # The db file should exist under the project's .dex/ directory
        expected = engine._dex_dir / "secops_audit.db"  # noqa: SLF001
        assert expected.exists()
        # Clean up
        engine.secops_audit.close()

    def test_audit_guard_records_event_on_pii(self, _yaml_audit_memory: Any) -> None:
        from dataenginex.engine import DexEngine

        engine = DexEngine(_yaml_audit_memory)
        # allow_local is True by default, so use a cloud target
        engine.privacy_guard.process("Email me at alice@example.com", target="openai")
        assert len(engine.secops_audit.events) >= 1


# ---------------------------------------------------------------------------
# dex secops CLI
# ---------------------------------------------------------------------------


@pytest.fixture
def _minimal_yaml(tmp_path: Any) -> Any:
    p = tmp_path / "dex.yaml"
    p.write_text(
        """
project:
  name: CLITest
  version: 0.1.0
secops:
  guard:
    enabled: true
    allow_local: true
    block_on_detect: false
    strategies:
      email: hash
  audit:
    enabled: false
"""
    )
    return p


class TestSecopsStatusCommand:
    def test_status_exits_zero(self, _minimal_yaml: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(dex, ["secops", "status", "--config", str(_minimal_yaml)])
        assert result.exit_code == 0, result.output

    def test_status_shows_enabled(self, _minimal_yaml: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(dex, ["secops", "status", "--config", str(_minimal_yaml)])
        assert "Enabled" in result.output

    def test_status_shows_strategy(self, _minimal_yaml: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(dex, ["secops", "status", "--config", str(_minimal_yaml)])
        assert "email" in result.output
        assert "hash" in result.output

    def test_status_shows_audit_section(self, _minimal_yaml: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(dex, ["secops", "status", "--config", str(_minimal_yaml)])
        assert "Audit" in result.output


class TestSecopsScanCommand:
    def test_scan_clean_text_exits_zero(self, _minimal_yaml: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(
            dex, ["secops", "scan", "hello world", "--config", str(_minimal_yaml)]
        )
        assert result.exit_code == 0, result.output
        assert "No PII" in result.output

    def test_scan_email_detected(self, _minimal_yaml: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(
            dex,
            ["secops", "scan", "Email me at alice@example.com", "--config", str(_minimal_yaml)],
        )
        assert result.exit_code == 0, result.output
        assert "email" in result.output.lower()

    def test_scan_local_target_bypassed(self, _minimal_yaml: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(
            dex,
            [
                "secops",
                "scan",
                "alice@example.com",
                "--config",
                str(_minimal_yaml),
                "--target",
                "ollama",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Bypass" in result.output or "local" in result.output.lower()

    def test_scan_block_on_detect(self, tmp_path: Any) -> None:
        p = tmp_path / "block.yaml"
        p.write_text(
            """
project:
  name: BlockScan
  version: 0.1.0
secops:
  guard:
    enabled: true
    allow_local: false
    block_on_detect: true
"""
        )
        runner = CliRunner()
        result = runner.invoke(
            dex,
            ["secops", "scan", "SSN 123-45-6789", "--config", str(p), "--target", "openai"],
        )
        assert result.exit_code == 0, result.output
        assert "BLOCK" in result.output.upper()
