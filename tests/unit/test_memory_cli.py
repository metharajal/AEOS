"""
Unit tests for aeos memory CLI commands: memory list and memory show.

Covers:
- list on non-existent directory
- list on empty directory
- list with valid record(s)
- list --json output
- show with valid record
- show --json output
- show with unknown record_id
- show with invalid JSON
- no secret values in any output
- read-only: no files modified after list or show
- compatibility with records created by save_record
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    project_name: str = "test-project",
    status: str = "WARNING",
    generator: str | None = "lovable",
    providers: list[str] | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        record_id=f"{project_name}-20260629T120000-abcd1234",
        created_at="2026-06-29T12:00:00+00:00",
        project_path=f"/fake/{project_name}",
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status=status,
        generator=generator,
        providers=providers if providers is not None else ["supabase"],
        control_level="weak",
        read_only=True,
        applied=False,
        findings_summary={"critical": 2, "important": 5, "manual": 3, "generated": 10},
        remediation_summary={
            "phases_count": 3,
            "immediate": 2,
            "manual": 3,
            "generatable": 10,
            "strategic": 2,
        },
        strategic_options=[
            "1. [low/partial] Stay on current provider",
            "2. [high/high] Migrate to self-hosted",
        ],
        human_validated=False,
        notes=None,
    )


def _write_record(tmp_path: Path, record: MemoryRecord) -> Path:
    return save_record(record, tmp_path)


# ---------------------------------------------------------------------------
# memory list — directory errors
# ---------------------------------------------------------------------------


def test_memory_list_nonexistent_dir(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(missing)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_memory_list_empty_dir(tmp_path: Path) -> None:
    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No records found" in result.output


# ---------------------------------------------------------------------------
# memory list — valid records
# ---------------------------------------------------------------------------


def test_memory_list_one_record(tmp_path: Path) -> None:
    record = _make_record()
    _write_record(tmp_path, record)

    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert record.record_id in result.output
    assert record.project_name in result.output
    assert "reclaim harden" in result.output
    assert record.status in result.output


def test_memory_list_shows_generator(tmp_path: Path) -> None:
    record = _make_record(generator="lovable")
    _write_record(tmp_path, record)

    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "lovable" in result.output


def test_memory_list_no_generator_hidden(tmp_path: Path) -> None:
    record = _make_record(generator=None)
    _write_record(tmp_path, record)

    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "  generator:" not in result.output


def test_memory_list_provider_count(tmp_path: Path) -> None:
    record = _make_record(providers=["supabase", "clerk"])
    _write_record(tmp_path, record)

    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "2" in result.output


# ---------------------------------------------------------------------------
# memory list --json
# ---------------------------------------------------------------------------


def test_memory_list_json_valid(tmp_path: Path) -> None:
    record = _make_record()
    _write_record(tmp_path, record)

    result = runner.invoke(
        app, ["memory", "list", "--memory-dir", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total"] == 1
    assert len(payload["records"]) == 1
    assert payload["records"][0]["record_id"] == record.record_id
    assert payload["records"][0]["project_name"] == record.project_name
    assert "source_command" in payload["records"][0]
    assert "status" in payload["records"][0]
    assert "generator_detected" in payload["records"][0]
    assert "provider_count" in payload["records"][0]
    assert payload["skipped_files"] == []


def test_memory_list_json_empty(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["memory", "list", "--memory-dir", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total"] == 0
    assert payload["records"] == []


# ---------------------------------------------------------------------------
# memory list — invalid JSON file is skipped with warning
# ---------------------------------------------------------------------------


def test_memory_list_skips_invalid_json(tmp_path: Path) -> None:
    record = _make_record()
    record_path = _write_record(tmp_path, record)

    bad_file = record_path.parent / "corrupted-record.json"
    bad_file.write_text("{ not valid json }", encoding="utf-8")

    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert record.record_id in result.output
    assert "Warning" in result.output
    assert "corrupted-record.json" in result.output


def test_memory_list_invalid_json_appears_in_skipped(tmp_path: Path) -> None:
    record = _make_record()
    record_path = _write_record(tmp_path, record)

    bad_file = record_path.parent / "bad.json"
    bad_file.write_text("not json at all", encoding="utf-8")

    result = runner.invoke(
        app, ["memory", "list", "--memory-dir", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert len(payload["skipped_files"]) == 1
    assert "bad.json" in payload["skipped_files"][0]


# ---------------------------------------------------------------------------
# memory show — valid record
# ---------------------------------------------------------------------------


def test_memory_show_valid_record(tmp_path: Path) -> None:
    record = _make_record()
    _write_record(tmp_path, record)

    result = runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(tmp_path), "--record", record.record_id],
    )
    assert result.exit_code == 0
    assert record.record_id in result.output
    assert record.project_name in result.output
    assert record.project_path in result.output
    assert "reclaim harden" in result.output
    assert record.status in result.output
    assert "read_only" in result.output
    assert "applied" in result.output


def test_memory_show_displays_findings_summary(tmp_path: Path) -> None:
    record = _make_record()
    _write_record(tmp_path, record)

    result = runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(tmp_path), "--record", record.record_id],
    )
    assert result.exit_code == 0
    assert "critical" in result.output
    assert "important" in result.output


def test_memory_show_displays_strategic_options(tmp_path: Path) -> None:
    record = _make_record()
    _write_record(tmp_path, record)

    result = runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(tmp_path), "--record", record.record_id],
    )
    assert result.exit_code == 0
    assert "Stay on current provider" in result.output


# ---------------------------------------------------------------------------
# memory show --json
# ---------------------------------------------------------------------------


def test_memory_show_json_valid(tmp_path: Path) -> None:
    record = _make_record()
    _write_record(tmp_path, record)

    result = runner.invoke(
        app,
        [
            "memory",
            "show",
            "--memory-dir",
            str(tmp_path),
            "--record",
            record.record_id,
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["record_id"] == record.record_id
    assert payload["project_name"] == record.project_name
    assert payload["project_path"] == record.project_path
    assert payload["source_command"] == "reclaim harden"
    assert payload["read_only"] is True
    assert payload["applied"] is False
    assert "findings_summary" in payload
    assert "remediation_summary" in payload
    assert "strategic_options" in payload


# ---------------------------------------------------------------------------
# memory show — error cases
# ---------------------------------------------------------------------------


def test_memory_show_record_not_found(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(tmp_path), "--record", "nonexistent-id"],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_memory_show_nonexistent_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    result = runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(missing), "--record", "any-id"],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_memory_show_invalid_json_raises(tmp_path: Path) -> None:
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    bad_file = project_dir / "test-project-20260629T120000-abcd1234.json"
    bad_file.write_text("{ broken json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "memory",
            "show",
            "--memory-dir",
            str(tmp_path),
            "--record",
            "test-project-20260629T120000-abcd1234",
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# Security: no secret values in any output
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # JWT header
    "sk_live_supersecret",
    "A" * 64,  # long base64-like string (64 chars)
]


@pytest.mark.parametrize("secret", _SECRET_PATTERNS)
def test_memory_list_no_secret_in_output(tmp_path: Path, secret: str) -> None:
    record = _make_record(project_name="safe-project")
    _write_record(tmp_path, record)

    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert secret not in result.output


@pytest.mark.parametrize("secret", _SECRET_PATTERNS)
def test_memory_show_no_secret_in_output(tmp_path: Path, secret: str) -> None:
    record = _make_record()
    _write_record(tmp_path, record)

    result = runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(tmp_path), "--record", record.record_id],
    )
    assert secret not in result.output


# ---------------------------------------------------------------------------
# Read-only: list and show must not modify any file
# ---------------------------------------------------------------------------


def test_memory_list_does_not_modify_files(tmp_path: Path) -> None:
    record = _make_record()
    record_path = _write_record(tmp_path, record)
    mtime_before = record_path.stat().st_mtime

    runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])

    assert record_path.stat().st_mtime == mtime_before, "list must not modify any file"


def test_memory_show_does_not_modify_files(tmp_path: Path) -> None:
    record = _make_record()
    record_path = _write_record(tmp_path, record)
    mtime_before = record_path.stat().st_mtime

    runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(tmp_path), "--record", record.record_id],
    )

    assert record_path.stat().st_mtime == mtime_before, "show must not modify any file"


# ---------------------------------------------------------------------------
# Compatibility: records created by save_record are readable by list/show
# ---------------------------------------------------------------------------


def test_save_record_then_list(tmp_path: Path) -> None:
    record = _make_record(project_name="compat-project")
    _write_record(tmp_path, record)

    result = runner.invoke(app, ["memory", "list", "--memory-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "compat-project" in result.output


def test_save_record_then_show(tmp_path: Path) -> None:
    record = _make_record(project_name="compat-show")
    _write_record(tmp_path, record)

    result = runner.invoke(
        app,
        ["memory", "show", "--memory-dir", str(tmp_path), "--record", record.record_id],
    )
    assert result.exit_code == 0
    assert "compat-show" in result.output


def test_save_record_then_show_json(tmp_path: Path) -> None:
    record = _make_record(project_name="compat-json")
    _write_record(tmp_path, record)

    result = runner.invoke(
        app,
        [
            "memory",
            "show",
            "--memory-dir",
            str(tmp_path),
            "--record",
            record.record_id,
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["project_name"] == "compat-json"
    assert payload["read_only"] is True
    assert payload["applied"] is False
