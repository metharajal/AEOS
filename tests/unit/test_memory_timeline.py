"""
Unit tests for aeos memory timeline.

Covers:
- load_project_records: no records, one record, multiple records sorted
- compute_timeline_synthesis: insufficient_data, improved, degraded, unchanged
- build_timeline: entries + synthesis
- CLI: no project dir → error, no records → error
- CLI: single record → synthesis insufficient_data
- CLI: multiple records → correct text output
- CLI: --json output valid
- CLI: status trend (ERROR→OK improved, OK→ERROR degraded)
- CLI: findings trends (critical, important, manual improved/degraded)
- CLI: read-only, no secrets in output, no files modified
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record
from aeos.memory.timeline import (
    build_timeline,
    compute_timeline_synthesis,
    load_project_records,
)

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    project_name: str = "test-proj",
    status: str = "WARNING",
    control_level: str = "partial",
    critical: int = 3,
    important: int = 10,
    manual: int = 5,
    generated: int = 8,
    created_at: str = "2026-06-29T12:00:00+00:00",
    record_suffix: str = "aaaa1111",
) -> MemoryRecord:
    return MemoryRecord(
        record_id=f"{project_name}-20260629T120000-{record_suffix}",
        created_at=created_at,
        project_path=f"/fake/{project_name}",
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status=status,
        generator=None,
        providers=["supabase"],
        control_level=control_level,
        read_only=True,
        applied=False,
        findings_summary={
            "critical": critical,
            "important": important,
            "manual": manual,
            "generated": generated,
        },
        remediation_summary={
            "phases_count": 3,
            "immediate": 2,
            "manual": manual,
            "generatable": generated,
            "strategic": 2,
        },
        strategic_options=[],
        human_validated=False,
        notes=None,
    )


def _write(tmp_path: Path, record: MemoryRecord) -> Path:
    return save_record(record, tmp_path)


# ---------------------------------------------------------------------------
# load_project_records
# ---------------------------------------------------------------------------


def test_load_project_records_nonexistent_memdir(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    try:
        load_project_records(missing, "any-project")
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError:
        pass


def test_load_project_records_no_project_dir(tmp_path: Path) -> None:
    records = load_project_records(tmp_path, "ghost-project")
    assert records == []


def test_load_project_records_one_record(tmp_path: Path) -> None:
    r = _make_record(project_name="alpha")
    _write(tmp_path, r)
    records = load_project_records(tmp_path, "alpha")
    assert len(records) == 1
    assert records[0].record_id == r.record_id


def test_load_project_records_sorted_chronologically(tmp_path: Path) -> None:
    r1 = _make_record(created_at="2026-06-28T10:00:00+00:00", record_suffix="first001")
    r2 = _make_record(created_at="2026-06-29T10:00:00+00:00", record_suffix="secnd002")
    r3 = _make_record(created_at="2026-06-30T10:00:00+00:00", record_suffix="third003")
    # write out of order
    _write(tmp_path, r3)
    _write(tmp_path, r1)
    _write(tmp_path, r2)
    records = load_project_records(tmp_path, "test-proj")
    assert [r.created_at for r in records] == [
        "2026-06-28T10:00:00+00:00",
        "2026-06-29T10:00:00+00:00",
        "2026-06-30T10:00:00+00:00",
    ]


# ---------------------------------------------------------------------------
# compute_timeline_synthesis
# ---------------------------------------------------------------------------


def test_synthesis_insufficient_data_single_record(tmp_path: Path) -> None:
    r = _make_record()
    syn = compute_timeline_synthesis([r])
    assert syn.overall == "insufficient_data"
    assert syn.critical_trend == "insufficient_data"
    assert syn.record_count == 1


def test_synthesis_status_improved_error_to_ok() -> None:
    r1 = _make_record(status="ERROR", record_suffix="aaaa0001")
    r2 = _make_record(status="OK", record_suffix="bbbb0002")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.overall == "improved"
    assert syn.first_status == "ERROR"
    assert syn.last_status == "OK"


def test_synthesis_status_improved_warning_to_ok() -> None:
    r1 = _make_record(status="WARNING", record_suffix="aaaa0003")
    r2 = _make_record(status="OK", record_suffix="bbbb0004")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.overall == "improved"


def test_synthesis_status_degraded_ok_to_error() -> None:
    r1 = _make_record(status="OK", record_suffix="aaaa0005")
    r2 = _make_record(status="ERROR", record_suffix="bbbb0006")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.overall == "degraded"


def test_synthesis_status_unchanged() -> None:
    r1 = _make_record(status="WARNING", record_suffix="aaaa0007")
    r2 = _make_record(status="WARNING", record_suffix="bbbb0008")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.overall == "unchanged"


def test_synthesis_critical_improved() -> None:
    r1 = _make_record(critical=5, record_suffix="aaaa0009")
    r2 = _make_record(critical=1, record_suffix="bbbb0010")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.critical_trend == "improved"


def test_synthesis_critical_degraded() -> None:
    r1 = _make_record(critical=1, record_suffix="aaaa0011")
    r2 = _make_record(critical=5, record_suffix="bbbb0012")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.critical_trend == "degraded"


def test_synthesis_important_improved() -> None:
    r1 = _make_record(important=20, record_suffix="aaaa0013")
    r2 = _make_record(important=5, record_suffix="bbbb0014")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.important_trend == "improved"


def test_synthesis_manual_improved() -> None:
    r1 = _make_record(manual=10, record_suffix="aaaa0015")
    r2 = _make_record(manual=2, record_suffix="bbbb0016")
    syn = compute_timeline_synthesis([r1, r2])
    assert syn.manual_trend == "improved"


# ---------------------------------------------------------------------------
# build_timeline
# ---------------------------------------------------------------------------


def test_build_timeline_entries_count() -> None:
    r1 = _make_record(record_suffix="aaaa0017")
    r2 = _make_record(record_suffix="bbbb0018")
    result = build_timeline([r1, r2])
    assert len(result.entries) == 2
    assert result.project_name == "test-proj"


def test_build_timeline_entry_fields() -> None:
    r = _make_record(status="ERROR", critical=4, important=12, manual=6, generated=9)
    result = build_timeline([r])
    e = result.entries[0]
    assert e.status == "ERROR"
    assert e.critical == 4
    assert e.important == 12
    assert e.manual == 6
    assert e.generated == 9


# ---------------------------------------------------------------------------
# CLI — no records / project not found
# ---------------------------------------------------------------------------


def test_cli_timeline_nonexistent_memory_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    result = runner.invoke(
        app,
        ["memory", "timeline", "--memory-dir", str(missing), "--project", "any"],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_timeline_no_records_for_project(tmp_path: Path) -> None:
    r = _make_record(project_name="other-proj")
    _write(tmp_path, r)
    result = runner.invoke(
        app,
        ["memory", "timeline", "--memory-dir", str(tmp_path), "--project", "ghost"],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# CLI — single record → insufficient_data
# ---------------------------------------------------------------------------


def test_cli_timeline_single_record(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    result = runner.invoke(
        app,
        ["memory", "timeline", "--memory-dir", str(tmp_path), "--project", "test-proj"],
    )
    assert result.exit_code == 0
    assert "insufficient_data" in result.output
    assert r.record_id in result.output


# ---------------------------------------------------------------------------
# CLI — multiple records, text output
# ---------------------------------------------------------------------------


def test_cli_timeline_text_output_multiple_records(tmp_path: Path) -> None:
    r1 = _make_record(
        status="ERROR",
        critical=5,
        created_at="2026-06-28T10:00:00+00:00",
        record_suffix="aaaa0019",
    )
    r2 = _make_record(
        status="OK",
        critical=0,
        created_at="2026-06-30T10:00:00+00:00",
        record_suffix="bbbb0020",
    )
    _write(tmp_path, r1)
    _write(tmp_path, r2)
    result = runner.invoke(
        app,
        ["memory", "timeline", "--memory-dir", str(tmp_path), "--project", "test-proj"],
    )
    assert result.exit_code == 0
    assert "Memory Timeline" in result.output
    assert r1.record_id in result.output
    assert r2.record_id in result.output
    assert "Synthesis" in result.output
    assert "improved" in result.output
    assert "Read-only" in result.output


# ---------------------------------------------------------------------------
# CLI — --json output
# ---------------------------------------------------------------------------


def test_cli_timeline_json_valid(tmp_path: Path) -> None:
    r1 = _make_record(
        status="ERROR",
        critical=5,
        created_at="2026-06-28T10:00:00+00:00",
        record_suffix="aaaa0021",
    )
    r2 = _make_record(
        status="WARNING",
        critical=2,
        created_at="2026-06-29T10:00:00+00:00",
        record_suffix="bbbb0022",
    )
    _write(tmp_path, r1)
    _write(tmp_path, r2)
    result = runner.invoke(
        app,
        [
            "memory",
            "timeline",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["project_name"] == "test-proj"
    assert payload["record_count"] == 2
    assert len(payload["entries"]) == 2
    assert payload["synthesis"]["overall"] == "improved"
    assert payload["synthesis"]["critical_trend"] == "improved"
    assert payload["synthesis"]["first_status"] == "ERROR"
    assert payload["synthesis"]["last_status"] == "WARNING"


# ---------------------------------------------------------------------------
# CLI — read-only: no files modified
# ---------------------------------------------------------------------------


def test_cli_timeline_does_not_modify_files(tmp_path: Path) -> None:
    r = _make_record()
    record_path = _write(tmp_path, r)
    mtime_before = record_path.stat().st_mtime

    runner.invoke(
        app,
        ["memory", "timeline", "--memory-dir", str(tmp_path), "--project", "test-proj"],
    )

    assert record_path.stat().st_mtime == mtime_before, "timeline must not modify files"


# ---------------------------------------------------------------------------
# CLI — no secrets in output
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "sk_live_supersecret",
    "A" * 64,
]


def test_cli_timeline_no_secret_in_output(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    result = runner.invoke(
        app,
        ["memory", "timeline", "--memory-dir", str(tmp_path), "--project", "test-proj"],
    )
    for secret in _SECRET_PATTERNS:
        assert secret not in result.output
