"""
Unit tests for aeos.ui.dashboard and the 'aeos ui dashboard' CLI command.

Covers:
- load_dashboard_data: nonexistent dir, no records, success
- render_dashboard: HTML structure, project name, badges, record IDs
- render_dashboard: delta annotations, synthesis section, next actions
- render_dashboard: no secret values in output
- CLI: missing dir → exit 1, no records → exit 1
- CLI: writes HTML file, contains project name
- CLI: overwrite protection (default and --overwrite)
- CLI: --output creates parent dirs
- CLI: read_only / applied=false mentioned in output
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record
from aeos.ui.dashboard import load_dashboard_data, render_dashboard

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "sk_live_supersecret",
    "A" * 64,
]


def _make_record(
    project_name: str = "test-proj",
    status: str = "ERROR",
    control_level: str = "weak",
    critical: int = 3,
    important: int = 72,
    manual: int = 15,
    generated: int = 25,
    created_at: str = "2026-06-30T11:00:00+00:00",
    record_suffix: str = "aa001100",
) -> MemoryRecord:
    return MemoryRecord(
        record_id=f"{project_name}-20260630T110000-{record_suffix}",
        created_at=created_at,
        project_path=f"/fake/{project_name}",
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status=status,
        generator="lovable",
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
            "phases_count": 5,
            "immediate": 3,
            "manual": manual,
            "generatable": generated,
            "strategic": 5,
        },
        strategic_options=[
            "1. [low/partial] Stay on current provider but secure",
            "2. [high/high] Migrate to self-hosted Supabase",
        ],
        human_validated=False,
        notes=None,
    )


def _write(tmp_path: Path, record: MemoryRecord) -> Path:
    return save_record(record, tmp_path)


# ---------------------------------------------------------------------------
# load_dashboard_data
# ---------------------------------------------------------------------------


def test_load_dashboard_data_nonexistent_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        load_dashboard_data(missing, "any-project")


def test_load_dashboard_data_no_records(tmp_path: Path) -> None:
    other = _make_record(project_name="other-proj")
    _write(tmp_path, other)
    with pytest.raises(ValueError, match="No records found"):
        load_dashboard_data(tmp_path, "ghost-project")


def test_load_dashboard_data_returns_data(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    assert data.project_name == "test-proj"
    assert len(data.records) == 1
    assert len(data.timeline.entries) == 1


def test_load_dashboard_data_multiple_records_sorted(tmp_path: Path) -> None:
    r1 = _make_record(created_at="2026-06-28T10:00:00+00:00", record_suffix="first001")
    r2 = _make_record(created_at="2026-06-30T10:00:00+00:00", record_suffix="last0002")
    _write(tmp_path, r2)
    _write(tmp_path, r1)
    data = load_dashboard_data(tmp_path, "test-proj")
    assert len(data.records) == 2
    assert data.records[0].created_at < data.records[1].created_at


# ---------------------------------------------------------------------------
# render_dashboard — structure
# ---------------------------------------------------------------------------


def test_render_dashboard_is_html(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_dashboard_contains_project_name(tmp_path: Path) -> None:
    r = _make_record(project_name="ma-mairie-digitale")
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "ma-mairie-digitale")
    html = render_dashboard(data)
    assert "ma-mairie-digitale" in html


def test_render_dashboard_contains_badges(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert "read_only: true" in html
    assert "applied: false" in html
    assert "human validation required" in html


def test_render_dashboard_contains_record_id(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert r.record_id in html


def test_render_dashboard_contains_timeline_table(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html


def test_render_dashboard_contains_synthesis_section(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert "Synthesis" in html


def test_render_dashboard_contains_next_actions(tmp_path: Path) -> None:
    r = _make_record(critical=3, generated=15, manual=5)
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert "Recommended Next Actions" in html
    assert "CRITICAL" in html


def test_render_dashboard_contains_strategic_options(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert "Strategic Exit Options" in html
    assert "Stay on current provider" in html


# ---------------------------------------------------------------------------
# render_dashboard — delta annotations
# ---------------------------------------------------------------------------


def test_render_dashboard_delta_for_two_records(tmp_path: Path) -> None:
    r1 = _make_record(
        important=72,
        created_at="2026-06-30T10:00:00+00:00",
        record_suffix="rr000001",
    )
    r2 = _make_record(
        important=59,
        created_at="2026-07-01T10:00:00+00:00",
        record_suffix="rr000002",
    )
    _write(tmp_path, r1)
    _write(tmp_path, r2)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    # The delta -13 should appear in the second row
    assert "(-13)" in html


def test_render_dashboard_synthesis_trend_when_improved(tmp_path: Path) -> None:
    r1 = _make_record(
        important=72,
        created_at="2026-06-30T10:00:00+00:00",
        record_suffix="aa000001",
    )
    r2 = _make_record(
        important=59,
        created_at="2026-07-01T10:00:00+00:00",
        record_suffix="bb000002",
    )
    _write(tmp_path, r1)
    _write(tmp_path, r2)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert "improved" in html


def test_render_dashboard_synthesis_insufficient_single_record(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    assert "Insufficient data" in html


# ---------------------------------------------------------------------------
# render_dashboard — no secrets
# ---------------------------------------------------------------------------


def test_render_dashboard_no_secret_values(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    data = load_dashboard_data(tmp_path, "test-proj")
    html = render_dashboard(data)
    for secret in _SECRET_PATTERNS:
        assert secret not in html, f"Secret pattern found in HTML: {secret[:20]}..."


# ---------------------------------------------------------------------------
# CLI — error paths
# ---------------------------------------------------------------------------


def test_cli_dashboard_missing_memory_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    out = tmp_path / "out.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(missing),
            "--project",
            "any",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_dashboard_no_records_for_project(tmp_path: Path) -> None:
    r = _make_record(project_name="other-proj")
    _write(tmp_path, r)
    out = tmp_path / "out.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "ghost",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# CLI — success path
# ---------------------------------------------------------------------------


def test_cli_dashboard_writes_html_file(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    out = tmp_path / "dashboard.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "test-proj" in content


def test_cli_dashboard_output_mentions_records_count(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    out = tmp_path / "dashboard.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert "Records:" in result.output
    assert "1" in result.output


def test_cli_dashboard_mentions_read_only(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    out = tmp_path / "dashboard.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert "read_only: true" in result.output
    assert "applied: false" in result.output


# ---------------------------------------------------------------------------
# CLI — overwrite protection
# ---------------------------------------------------------------------------


def test_cli_dashboard_refuses_existing_output(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    out = tmp_path / "dashboard.html"
    out.write_text("existing", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output
    # original file must not be overwritten
    assert out.read_text(encoding="utf-8") == "existing"


def test_cli_dashboard_overwrite_flag_replaces_file(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    out = tmp_path / "dashboard.html"
    out.write_text("old content", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--output",
            str(out),
            "--overwrite",
        ],
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8") != "old content"
    assert "<!DOCTYPE html>" in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI — creates parent directories
# ---------------------------------------------------------------------------


def test_cli_dashboard_creates_parent_dirs(tmp_path: Path) -> None:
    r = _make_record()
    _write(tmp_path, r)
    out = tmp_path / "nested" / "deep" / "dashboard.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert out.exists()


# ---------------------------------------------------------------------------
# CLI — does not modify memory records
# ---------------------------------------------------------------------------


def test_cli_dashboard_does_not_modify_memory_files(tmp_path: Path) -> None:
    r = _make_record()
    record_path = _write(tmp_path, r)
    mtime_before = record_path.stat().st_mtime
    out = tmp_path / "dashboard.html"
    runner.invoke(
        app,
        [
            "ui",
            "dashboard",
            "--memory-dir",
            str(tmp_path),
            "--project",
            "test-proj",
            "--output",
            str(out),
        ],
    )
    assert record_path.stat().st_mtime == mtime_before
