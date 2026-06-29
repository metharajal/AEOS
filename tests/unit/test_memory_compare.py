"""
Unit tests for aeos memory compare.

Covers:
- compare_records: status improved/degraded/unchanged
- compare_records: control_level improved/degraded
- compare_records: critical/important/manual findings improved/degraded
- compare_records: incompatible project names
- compare_records: synthesis categories (improved, degraded, unchanged, mixed)
- compare_records: phases_count comparison
- CLI: memory compare text output
- CLI: memory compare --json output
- CLI: memory compare with --left / --right as direct file paths
- CLI: error on missing left / right record
- CLI: read-only (no files modified)
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.memory.compare import (
    compare_records,
    compute_trend,
)
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    project_name: str = "test-project",
    status: str = "WARNING",
    control_level: str = "partial",
    critical: int = 3,
    important: int = 5,
    manual: int = 4,
    generated: int = 8,
    phases_count: int | None = 3,
    record_suffix: str = "aaaa1111",
) -> MemoryRecord:
    remediation: dict[str, int] | None = None
    if phases_count is not None:
        remediation = {
            "phases_count": phases_count,
            "immediate": 2,
            "manual": manual,
            "generatable": generated,
            "strategic": 2,
        }
    return MemoryRecord(
        record_id=f"{project_name}-20260629T120000-{record_suffix}",
        created_at="2026-06-29T12:00:00+00:00",
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
        remediation_summary=remediation,
        strategic_options=[],
        human_validated=False,
        notes=None,
    )


def _write(tmp_path: Path, record: MemoryRecord) -> Path:
    return save_record(record, tmp_path)


# ---------------------------------------------------------------------------
# compute_trend unit tests
# ---------------------------------------------------------------------------


def test_compute_trend_higher_is_better_improved() -> None:
    assert compute_trend(0, 2, higher_is_better=True) == "improved"


def test_compute_trend_higher_is_better_degraded() -> None:
    assert compute_trend(2, 1, higher_is_better=True) == "degraded"


def test_compute_trend_lower_is_better_improved() -> None:
    assert compute_trend(5, 2, higher_is_better=False) == "improved"


def test_compute_trend_lower_is_better_degraded() -> None:
    assert compute_trend(1, 4, higher_is_better=False) == "degraded"


def test_compute_trend_unchanged() -> None:
    assert compute_trend(3, 3, higher_is_better=True) == "unchanged"
    assert compute_trend(3, 3, higher_is_better=False) == "unchanged"


# ---------------------------------------------------------------------------
# compare_records — status field
# ---------------------------------------------------------------------------


def test_compare_status_improved() -> None:
    left = _make_record(status="ERROR", record_suffix="left0001")
    right = _make_record(status="OK", record_suffix="rght0001")
    result = compare_records(left, right)
    assert result.synthesis in ("improved", "mixed")
    status_deltas = [d for d in result.improved if d.field == "status"]
    assert len(status_deltas) == 1
    assert status_deltas[0].left_value == "ERROR"
    assert status_deltas[0].right_value == "OK"
    assert status_deltas[0].trend == "improved"


def test_compare_status_degraded() -> None:
    left = _make_record(status="OK", record_suffix="left0002")
    right = _make_record(status="WARNING", record_suffix="rght0002")
    result = compare_records(left, right)
    status_deltas = [d for d in result.degraded if d.field == "status"]
    assert len(status_deltas) == 1
    assert status_deltas[0].trend == "degraded"


def test_compare_status_unchanged() -> None:
    left = _make_record(status="WARNING", record_suffix="left0003")
    right = _make_record(status="WARNING", record_suffix="rght0003")
    result = compare_records(left, right)
    status_deltas = [d for d in result.unchanged if d.field == "status"]
    assert len(status_deltas) == 1
    assert status_deltas[0].trend == "unchanged"


# ---------------------------------------------------------------------------
# compare_records — control_level field
# ---------------------------------------------------------------------------


def test_compare_control_level_improved() -> None:
    left = _make_record(control_level="weak", record_suffix="left0004")
    right = _make_record(control_level="controlled", record_suffix="rght0004")
    result = compare_records(left, right)
    cl_deltas = [d for d in result.improved if d.field == "control_level"]
    assert len(cl_deltas) == 1
    assert cl_deltas[0].trend == "improved"


def test_compare_control_level_degraded() -> None:
    left = _make_record(control_level="controlled", record_suffix="left0005")
    right = _make_record(control_level="partial", record_suffix="rght0005")
    result = compare_records(left, right)
    cl_deltas = [d for d in result.degraded if d.field == "control_level"]
    assert len(cl_deltas) == 1
    assert cl_deltas[0].trend == "degraded"


# ---------------------------------------------------------------------------
# compare_records — findings fields
# ---------------------------------------------------------------------------


def test_compare_critical_improved() -> None:
    left = _make_record(critical=5, record_suffix="left0006")
    right = _make_record(critical=1, record_suffix="rght0006")
    result = compare_records(left, right)
    crit_deltas = [d for d in result.improved if d.field == "critical"]
    assert len(crit_deltas) == 1
    assert crit_deltas[0].left_value == "5"
    assert crit_deltas[0].right_value == "1"


def test_compare_critical_degraded() -> None:
    left = _make_record(critical=1, record_suffix="left0007")
    right = _make_record(critical=6, record_suffix="rght0007")
    result = compare_records(left, right)
    crit_deltas = [d for d in result.degraded if d.field == "critical"]
    assert len(crit_deltas) == 1
    assert crit_deltas[0].trend == "degraded"


# ---------------------------------------------------------------------------
# compare_records — incompatible project names
# ---------------------------------------------------------------------------


def test_compare_incompatible_projects() -> None:
    left = _make_record(project_name="project-alpha", record_suffix="left0008")
    right = _make_record(project_name="project-beta", record_suffix="rght0008")
    result = compare_records(left, right)
    assert result.compatible is False
    assert result.synthesis == "incompatible"
    assert not result.improved
    assert not result.degraded
    assert len(result.incompatible_fields) == 1
    assert result.incompatible_fields[0].field == "project_name"


# ---------------------------------------------------------------------------
# compare_records — synthesis categories
# ---------------------------------------------------------------------------


def test_compare_synthesis_all_unchanged() -> None:
    left = _make_record(record_suffix="left0009")
    right = _make_record(record_suffix="rght0009")
    result = compare_records(left, right)
    assert result.synthesis == "unchanged"
    assert not result.improved
    assert not result.degraded


def test_compare_synthesis_improved() -> None:
    left = _make_record(
        status="ERROR",
        control_level="weak",
        critical=5,
        important=8,
        manual=6,
        record_suffix="left0010",
    )
    right = _make_record(
        status="OK",
        control_level="controlled",
        critical=0,
        important=1,
        manual=0,
        record_suffix="rght0010",
    )
    result = compare_records(left, right)
    assert result.synthesis == "improved"
    assert len(result.improved) >= 3
    assert not result.degraded


def test_compare_synthesis_degraded() -> None:
    left = _make_record(
        status="OK",
        control_level="controlled",
        critical=0,
        record_suffix="left0011",
    )
    right = _make_record(
        status="ERROR",
        control_level="weak",
        critical=5,
        record_suffix="rght0011",
    )
    result = compare_records(left, right)
    assert result.synthesis == "degraded"
    assert not result.improved


def test_compare_synthesis_mixed() -> None:
    left = _make_record(
        status="ERROR",
        control_level="controlled",
        critical=3,
        record_suffix="left0012",
    )
    right = _make_record(
        status="OK",
        control_level="weak",
        critical=3,
        record_suffix="rght0012",
    )
    result = compare_records(left, right)
    assert result.synthesis == "mixed"
    assert result.improved
    assert result.degraded


# ---------------------------------------------------------------------------
# compare_records — phases_count
# ---------------------------------------------------------------------------


def test_compare_phases_count_improved() -> None:
    left = _make_record(phases_count=5, record_suffix="left0013")
    right = _make_record(phases_count=2, record_suffix="rght0013")
    result = compare_records(left, right)
    phases_deltas = [d for d in result.improved if d.field == "phases_count"]
    assert len(phases_deltas) == 1
    assert phases_deltas[0].trend == "improved"


def test_compare_phases_count_absent_skipped() -> None:
    left = _make_record(phases_count=None, record_suffix="left0014")
    right = _make_record(phases_count=None, record_suffix="rght0014")
    result = compare_records(left, right)
    all_fields = (
        [d.field for d in result.improved]
        + [d.field for d in result.degraded]
        + [d.field for d in result.unchanged]
    )
    assert "phases_count" not in all_fields


# ---------------------------------------------------------------------------
# CLI — memory compare text output
# ---------------------------------------------------------------------------


def test_memory_compare_text_output(tmp_path: Path) -> None:
    left = _make_record(
        status="ERROR", control_level="weak", critical=5, record_suffix="left0015"
    )
    right = _make_record(
        status="OK", control_level="controlled", critical=0, record_suffix="rght0015"
    )
    _write(tmp_path, left)
    _write(tmp_path, right)

    result = runner.invoke(
        app,
        [
            "memory",
            "compare",
            "--memory-dir",
            str(tmp_path),
            "--left",
            left.record_id,
            "--right",
            right.record_id,
        ],
    )
    assert result.exit_code == 0
    assert "Memory Compare" in result.output
    assert left.record_id in result.output
    assert right.record_id in result.output
    assert "Synthesis" in result.output
    assert "Improved" in result.output
    assert "Read-only" in result.output


# ---------------------------------------------------------------------------
# CLI — memory compare --json output
# ---------------------------------------------------------------------------


def test_memory_compare_json_output(tmp_path: Path) -> None:
    left = _make_record(status="WARNING", critical=3, record_suffix="left0016")
    right = _make_record(status="OK", critical=1, record_suffix="rght0016")
    _write(tmp_path, left)
    _write(tmp_path, right)

    result = runner.invoke(
        app,
        [
            "memory",
            "compare",
            "--memory-dir",
            str(tmp_path),
            "--left",
            left.record_id,
            "--right",
            right.record_id,
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["left_id"] == left.record_id
    assert payload["right_id"] == right.record_id
    assert payload["project_name"] == "test-project"
    assert payload["compatible"] is True
    assert "synthesis" in payload
    assert "improved" in payload
    assert "degraded" in payload
    assert "unchanged" in payload
    assert "incompatible_fields" in payload


# ---------------------------------------------------------------------------
# CLI — memory compare with direct file paths
# ---------------------------------------------------------------------------


def test_memory_compare_with_file_paths(tmp_path: Path) -> None:
    left = _make_record(status="ERROR", record_suffix="left0017")
    right = _make_record(status="OK", record_suffix="rght0017")
    left_path = _write(tmp_path, left)
    right_path = _write(tmp_path, right)

    result = runner.invoke(
        app,
        [
            "memory",
            "compare",
            "--memory-dir",
            str(tmp_path),
            "--left",
            str(left_path),
            "--right",
            str(right_path),
        ],
    )
    assert result.exit_code == 0
    assert "Memory Compare" in result.output
    assert "improved" in result.output.lower()


# ---------------------------------------------------------------------------
# CLI — error on missing record
# ---------------------------------------------------------------------------


def test_memory_compare_left_not_found(tmp_path: Path) -> None:
    right = _make_record(record_suffix="rght0018")
    _write(tmp_path, right)

    result = runner.invoke(
        app,
        [
            "memory",
            "compare",
            "--memory-dir",
            str(tmp_path),
            "--left",
            "nonexistent-left-record",
            "--right",
            right.record_id,
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_memory_compare_right_not_found(tmp_path: Path) -> None:
    left = _make_record(record_suffix="left0019")
    _write(tmp_path, left)

    result = runner.invoke(
        app,
        [
            "memory",
            "compare",
            "--memory-dir",
            str(tmp_path),
            "--left",
            left.record_id,
            "--right",
            "nonexistent-right-record",
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# CLI — incompatible project names
# ---------------------------------------------------------------------------


def test_memory_compare_incompatible_projects_cli(tmp_path: Path) -> None:
    left = _make_record(project_name="alpha", record_suffix="left0020")
    right = _make_record(project_name="beta", record_suffix="rght0020")
    _write(tmp_path, left)
    _write(tmp_path, right)

    result = runner.invoke(
        app,
        [
            "memory",
            "compare",
            "--memory-dir",
            str(tmp_path),
            "--left",
            left.record_id,
            "--right",
            right.record_id,
        ],
    )
    assert result.exit_code == 0
    assert "incompatible" in result.output.lower()


# ---------------------------------------------------------------------------
# CLI — read-only: no files modified
# ---------------------------------------------------------------------------


def test_memory_compare_does_not_modify_files(tmp_path: Path) -> None:
    left = _make_record(status="ERROR", record_suffix="left0021")
    right = _make_record(status="OK", record_suffix="rght0021")
    left_path = _write(tmp_path, left)
    right_path = _write(tmp_path, right)
    mtime_left = left_path.stat().st_mtime
    mtime_right = right_path.stat().st_mtime

    runner.invoke(
        app,
        [
            "memory",
            "compare",
            "--memory-dir",
            str(tmp_path),
            "--left",
            left.record_id,
            "--right",
            right.record_id,
        ],
    )

    assert left_path.stat().st_mtime == mtime_left, "compare must not modify left file"
    assert right_path.stat().st_mtime == mtime_right, (
        "compare must not modify right file"
    )
