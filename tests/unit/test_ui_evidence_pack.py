"""Unit tests for aeos.ui.evidence_pack and the `aeos ui evidence-pack` CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record
from aeos.ui.evidence_pack import (
    _PACK_FILES,
    EvidencePackResult,
    generate_evidence_pack,
    render_human_gates,
    render_index,
    render_next_actions,
    render_recovery_summary,
    render_risk_register,
)
from aeos.ui.workspace import load_workspace_data


def _make_record(
    project_name: str = "test-proj",
    status: str = "ERROR",
    control_level: str = "weak",
    critical: int = 3,
    important: int = 72,
    manual: int = 15,
    generated: int = 25,
    generator: str | None = "lovable",
    providers: list[str] | None = None,
    record_suffix: str = "aa001100",
) -> MemoryRecord:
    if providers is None:
        providers = ["supabase"]
    return MemoryRecord(
        record_id=f"{project_name}-20260630T110000-{record_suffix}",
        created_at="2026-06-30T11:00:00",
        project_path=f"/private/tmp/{project_name}",
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status=status,
        generator=generator,
        providers=providers,
        control_level=control_level,
        read_only=True,
        applied=False,
        findings_summary={
            "critical": critical,
            "important": important,
            "manual": manual,
            "generated": generated,
        },
        remediation_summary=None,
        strategic_options=["opt-a", "opt-b"],
        human_validated=False,
        notes=None,
    )


def _write(tmp_path: Path, record: MemoryRecord) -> Path:
    return save_record(record, tmp_path)


runner = CliRunner()


# ---------------------------------------------------------------------------
# generate_evidence_pack
# ---------------------------------------------------------------------------


def test_generate_creates_all_files(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    result = generate_evidence_pack(mem, "test-proj", out)
    assert isinstance(result, EvidencePackResult)
    for fname in _PACK_FILES:
        assert (out / fname).exists(), f"Missing: {fname}"


def test_generate_result_fields(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    result = generate_evidence_pack(mem, "test-proj", out)
    assert result.project_name == "test-proj"
    assert result.record_count == 1
    assert "NOT READY" in result.verdict
    assert len(result.files) == len(_PACK_FILES)


def test_generate_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        generate_evidence_pack(tmp_path / "no-such", "proj", tmp_path / "out")


def test_generate_raises_value_error_no_records(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="other"))
    with pytest.raises(ValueError, match="No records found"):
        generate_evidence_pack(mem, "test-proj", tmp_path / "out")


def test_generate_raises_value_error_nonempty_dir(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    out.mkdir()
    (out / "stale.txt").write_text("old", encoding="utf-8")
    with pytest.raises(ValueError, match="not empty"):
        generate_evidence_pack(mem, "test-proj", out, overwrite=False)


def test_generate_overwrite_nonempty_dir(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    out.mkdir()
    (out / "stale.txt").write_text("old", encoding="utf-8")
    result = generate_evidence_pack(mem, "test-proj", out, overwrite=True)
    assert result.record_count == 1


def test_generate_creates_output_dir(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "deep" / "nested" / "pack"
    generate_evidence_pack(mem, "test-proj", out)
    assert out.is_dir()


def test_generate_does_not_touch_memory_records(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    saved = _write(mem, _make_record())
    mtime = saved.stat().st_mtime
    generate_evidence_pack(mem, "test-proj", tmp_path / "pack")
    assert saved.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# render_recovery_summary
# ---------------------------------------------------------------------------


def test_recovery_summary_has_baseline_and_current(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    r1 = _make_record(important=72, generated=25, record_suffix="aa001")
    r2 = _make_record(important=59, generated=15, record_suffix="bb002")
    _write(mem, r1)
    _write(mem, r2)
    ws = load_workspace_data(mem, "test-proj")
    md = render_recovery_summary(ws)
    assert "72" in md
    assert "59" in md
    assert "Recovery Summary" in md
    assert "read_only: true" in md


def test_recovery_summary_verdict(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(critical=3))
    ws = load_workspace_data(mem, "test-proj")
    md = render_recovery_summary(ws)
    assert "NOT READY" in md


def test_recovery_summary_blocking_reasons(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(critical=2, generated=5))
    ws = load_workspace_data(mem, "test-proj")
    md = render_recovery_summary(ws)
    assert "Blocking reasons" in md


# ---------------------------------------------------------------------------
# render_risk_register
# ---------------------------------------------------------------------------


def test_risk_register_has_all_categories(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(critical=3, important=59, manual=15, generated=15))
    ws = load_workspace_data(mem, "test-proj")
    md = render_risk_register(ws)
    assert "Critical" in md
    assert "Important" in md
    assert "Manual" in md
    assert "Generatable SQL" in md


def test_risk_register_has_counts(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(critical=3, important=59, manual=15, generated=15))
    ws = load_workspace_data(mem, "test-proj")
    md = render_risk_register(ws)
    assert "3" in md
    assert "59" in md
    assert "15" in md


def test_risk_register_read_only_banner(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    ws = load_workspace_data(mem, "test-proj")
    md = render_risk_register(ws)
    assert "read_only: true" in md


# ---------------------------------------------------------------------------
# render_human_gates
# ---------------------------------------------------------------------------


def test_human_gates_supabase_gates(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(providers=["supabase"]))
    ws = load_workspace_data(mem, "test-proj")
    md = render_human_gates(ws)
    assert "Supabase" in md
    assert "Gate" in md
    assert "Validated by" in md


def test_human_gates_no_gates_message(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(
        mem,
        _make_record(
            providers=[],
            critical=0,
            manual=0,
            control_level="strong",
        ),
    )
    ws = load_workspace_data(mem, "test-proj")
    md = render_human_gates(ws)
    assert "No open human gates" in md


def test_human_gates_has_sign_off_fields(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(providers=["supabase"]))
    ws = load_workspace_data(mem, "test-proj")
    md = render_human_gates(ws)
    assert "Date:" in md


# ---------------------------------------------------------------------------
# render_next_actions
# ---------------------------------------------------------------------------


def test_next_actions_has_ordered_items(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(generated=10))
    ws = load_workspace_data(mem, "test-proj")
    md = render_next_actions(ws)
    assert "Action 1" in md
    assert "Assigned to" in md


def test_next_actions_fallback_clear(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(
        mem,
        _make_record(
            critical=0,
            important=0,
            manual=0,
            generated=0,
            providers=[],
            control_level="strong",
        ),
    )
    ws = load_workspace_data(mem, "test-proj")
    md = render_next_actions(ws)
    assert "harden" in md.lower()


# ---------------------------------------------------------------------------
# render_index
# ---------------------------------------------------------------------------


def test_index_is_valid_html(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    ws = load_workspace_data(mem, "test-proj")
    html = render_index(ws)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_index_has_links_to_all_files(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    ws = load_workspace_data(mem, "test-proj")
    html = render_index(ws)
    for fname, _ in [
        ("dashboard.html", ""),
        ("project-workspace.html", ""),
        ("recovery-summary.md", ""),
        ("risk-register.md", ""),
        ("human-gates.md", ""),
        ("next-actions.md", ""),
    ]:
        assert fname in html, f"Missing link: {fname}"


def test_index_shows_verdict_not_ready(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(critical=3))
    ws = load_workspace_data(mem, "test-proj")
    html = render_index(ws)
    assert "NOT READY" in html


def test_index_shows_verdict_ready(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(
        mem,
        _make_record(
            critical=0,
            important=0,
            manual=0,
            generated=0,
            control_level="strong",
        ),
    )
    ws = load_workspace_data(mem, "test-proj")
    html = render_index(ws)
    assert "READY FOR PRODUCTION" in html


def test_index_read_only_badges(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    ws = load_workspace_data(mem, "test-proj")
    html = render_index(ws)
    assert "read_only: true" in html
    assert "applied: false" in html
    assert "human validation required" in html


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_evidence_pack_basic(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(mem),
            "--project",
            "test-proj",
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Pack:" in result.output
    assert "read_only: true" in result.output
    for fname in _PACK_FILES:
        assert (out / fname).exists()


def test_cli_evidence_pack_no_overwrite(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    out.mkdir()
    (out / "stale.txt").write_text("x", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(mem),
            "--project",
            "test-proj",
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_evidence_pack_overwrite(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    out.mkdir()
    (out / "stale.txt").write_text("x", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(mem),
            "--project",
            "test-proj",
            "--output-dir",
            str(out),
            "--overwrite",
        ],
    )
    assert result.exit_code == 0


def test_cli_evidence_pack_missing_memory_dir(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(tmp_path / "no-such"),
            "--project",
            "test-proj",
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 1


def test_cli_evidence_pack_wrong_project(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="real-proj"))
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(mem),
            "--project",
            "wrong-proj",
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_evidence_pack_creates_nested_dir(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "deep" / "nested" / "pack"
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(mem),
            "--project",
            "test-proj",
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert out.is_dir()


def test_cli_evidence_pack_file_list_in_output(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "pack"
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(mem),
            "--project",
            "test-proj",
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0
    for fname in _PACK_FILES:
        assert fname in result.output


def test_cli_evidence_pack_verdict_in_output(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(critical=3))
    out = tmp_path / "pack"
    result = runner.invoke(
        app,
        [
            "ui",
            "evidence-pack",
            "--memory-dir",
            str(mem),
            "--project",
            "test-proj",
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert "NOT READY" in result.output
