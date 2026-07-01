"""Unit tests for aeos.ui.portfolio and the `aeos ui portfolio` CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record
from aeos.ui.portfolio import (
    PortfolioData,
    _derive_next_action,
    _derive_verdict,
    _discover_projects,
    load_portfolio_data,
    render_portfolio,
)


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
        strategic_options=["opt-a"],
        human_validated=False,
        notes=None,
    )


def _write(tmp_path: Path, record: MemoryRecord) -> Path:
    return save_record(record, tmp_path)


runner = CliRunner()


# ---------------------------------------------------------------------------
# _discover_projects
# ---------------------------------------------------------------------------


def test_discover_projects_finds_one(tmp_path: Path) -> None:
    _write(tmp_path, _make_record(project_name="proj-a"))
    found = _discover_projects(tmp_path)
    assert found == ["proj-a"]


def test_discover_projects_finds_multiple(tmp_path: Path) -> None:
    _write(tmp_path, _make_record(project_name="proj-a", record_suffix="aa1"))
    _write(tmp_path, _make_record(project_name="proj-b", record_suffix="bb1"))
    found = _discover_projects(tmp_path)
    assert found == ["proj-a", "proj-b"]


def test_discover_projects_deduplicates(tmp_path: Path) -> None:
    _write(tmp_path, _make_record(project_name="proj-a", record_suffix="r1"))
    _write(tmp_path, _make_record(project_name="proj-a", record_suffix="r2"))
    found = _discover_projects(tmp_path)
    assert found == ["proj-a"]


def test_discover_projects_empty_dir(tmp_path: Path) -> None:
    assert _discover_projects(tmp_path) == []


def test_discover_projects_ignores_dirs_without_json(tmp_path: Path) -> None:
    (tmp_path / "empty-subdir").mkdir()
    assert _discover_projects(tmp_path) == []


# ---------------------------------------------------------------------------
# _derive_verdict
# ---------------------------------------------------------------------------


def test_derive_verdict_not_ready_critical() -> None:
    rec = _make_record(critical=3, generated=0, manual=0, control_level="strong")
    ready, verdict, reasons = _derive_verdict(rec)
    assert not ready
    assert "NOT READY" in verdict
    assert any("critical" in r for r in reasons)


def test_derive_verdict_ready_all_clear() -> None:
    rec = _make_record(critical=0, generated=0, manual=0, control_level="strong")
    ready, verdict, reasons = _derive_verdict(rec)
    assert ready
    assert "READY FOR PRODUCTION" in verdict
    assert reasons == []


def test_derive_verdict_not_ready_weak() -> None:
    rec = _make_record(critical=0, generated=0, manual=0, control_level="weak")
    ready, _verdict, reasons = _derive_verdict(rec)
    assert not ready
    assert any("weak" in r for r in reasons)


# ---------------------------------------------------------------------------
# _derive_next_action
# ---------------------------------------------------------------------------


def test_next_action_generated_first(tmp_path: Path) -> None:
    rec = _make_record(generated=10, critical=0, manual=0)
    action = _derive_next_action(rec)
    assert "SQL" in action


def test_next_action_supabase_rotate(tmp_path: Path) -> None:
    rec = _make_record(generated=0, providers=["supabase"], critical=0, manual=0)
    action = _derive_next_action(rec)
    assert "Supabase" in action or "credentials" in action.lower()


def test_next_action_fallback_clear() -> None:
    rec = _make_record(
        critical=0,
        important=0,
        manual=0,
        generated=0,
        providers=[],
        control_level="strong",
    )
    action = _derive_next_action(rec)
    assert "harden" in action.lower()


# ---------------------------------------------------------------------------
# load_portfolio_data
# ---------------------------------------------------------------------------


def test_load_portfolio_single_project(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="proj-a"))
    data = load_portfolio_data([mem])
    assert isinstance(data, PortfolioData)
    assert len(data.projects) == 1
    assert data.projects[0].project_name == "proj-a"


def test_load_portfolio_multi_project(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="proj-a", record_suffix="r1"))
    _write(mem, _make_record(project_name="proj-b", record_suffix="r2"))
    data = load_portfolio_data([mem])
    assert len(data.projects) == 2
    names = [p.project_name for p in data.projects]
    assert "proj-a" in names
    assert "proj-b" in names


def test_load_portfolio_projects_sorted(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="zzz", record_suffix="r1"))
    _write(mem, _make_record(project_name="aaa", record_suffix="r2"))
    data = load_portfolio_data([mem])
    names = [p.project_name for p in data.projects]
    assert names == sorted(names)


def test_load_portfolio_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_portfolio_data([tmp_path / "no-such"])


def test_load_portfolio_empty_dir(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    data = load_portfolio_data([mem])
    assert data.projects == []


def test_load_portfolio_entry_fields(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="p", critical=3, important=59))
    data = load_portfolio_data([mem])
    entry = data.projects[0]
    assert entry.critical == 3
    assert entry.important == 59
    assert entry.record_count == 1
    assert "NOT READY" in entry.verdict


def test_load_portfolio_multi_dir_dedup(tmp_path: Path) -> None:
    mem1 = tmp_path / "mem1"
    mem2 = tmp_path / "mem2"
    mem1.mkdir()
    mem2.mkdir()
    _write(mem1, _make_record(project_name="shared", record_suffix="r1"))
    _write(mem2, _make_record(project_name="shared", record_suffix="r2"))
    data = load_portfolio_data([mem1, mem2])
    names = [p.project_name for p in data.projects]
    assert names.count("shared") == 1


def test_load_portfolio_does_not_touch_records(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    saved = _write(mem, _make_record())
    mtime = saved.stat().st_mtime
    load_portfolio_data([mem])
    assert saved.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# render_portfolio
# ---------------------------------------------------------------------------


def test_render_portfolio_is_html(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    data = load_portfolio_data([mem])
    html = render_portfolio(data)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_portfolio_shows_project(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="my-proj"))
    data = load_portfolio_data([mem])
    html = render_portfolio(data)
    assert "my-proj" in html


def test_render_portfolio_shows_verdict(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(critical=3))
    data = load_portfolio_data([mem])
    html = render_portfolio(data)
    assert "NOT READY" in html


def test_render_portfolio_shows_links(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="my-proj"))
    data = load_portfolio_data([mem])
    html = render_portfolio(data)
    assert "dashboard.html" in html
    assert "project-workspace.html" in html
    assert "evidence-pack" in html


def test_render_portfolio_read_only_badges(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    data = load_portfolio_data([mem])
    html = render_portfolio(data)
    assert "read-only" in html
    assert "local-first" in html
    assert "no backend" in html
    assert "no secrets" in html


def test_render_portfolio_empty_state(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    data = load_portfolio_data([mem])
    html = render_portfolio(data)
    assert "No projects found" in html


def test_render_portfolio_no_secrets(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    data = load_portfolio_data([mem])
    html = render_portfolio(data)
    for bad in ["SECRET=", "eyJ", "password=", "SUPABASE_KEY="]:
        assert bad not in html


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_portfolio_basic(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="proj-a"))
    out = tmp_path / "index.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--memory-dir",
            str(mem),
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "Portfolio:" in result.output
    assert "proj-a" in result.output
    assert "read_only: true" in result.output


def test_cli_portfolio_no_overwrite(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "index.html"
    out.write_text("old", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--memory-dir",
            str(mem),
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_cli_portfolio_overwrite(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "index.html"
    out.write_text("old", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--memory-dir",
            str(mem),
            "--output",
            str(out),
            "--overwrite",
        ],
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_cli_portfolio_missing_memory_dir(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--memory-dir",
            str(tmp_path / "no-such"),
            "--output",
            str(tmp_path / "out.html"),
        ],
    )
    assert result.exit_code == 1


def test_cli_portfolio_creates_parent_dirs(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record())
    out = tmp_path / "deep" / "nested" / "index.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--memory-dir",
            str(mem),
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_cli_portfolio_output_is_immutable(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    saved = _write(mem, _make_record())
    mtime = saved.stat().st_mtime
    runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--memory-dir",
            str(mem),
            "--output",
            str(tmp_path / "index.html"),
        ],
    )
    assert saved.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# CLI: --registry mode (MVP-UI-6)
# ---------------------------------------------------------------------------


def _register_project(
    tmp_path: Path,
    name: str,
    mem: Path,
    reg_path: Path,
    evidence_dir: Path | None = None,
) -> None:
    """Helper: register a project into reg_path via aeos project register."""
    args = [
        "project",
        "register",
        "--name",
        name,
        "--memory-dir",
        str(mem),
        "--registry",
        str(reg_path),
    ]
    if evidence_dir is not None:
        args += ["--evidence-dir", str(evidence_dir)]
    runner.invoke(app, args)


def test_cli_portfolio_from_registry_basic(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="proj-a"))
    reg_path = tmp_path / "registry.json"
    _register_project(tmp_path, "proj-a", mem, reg_path)

    out = tmp_path / "index.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--registry",
            str(reg_path),
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "Portfolio:" in result.output
    assert "Source:" in result.output
    assert "registry" in result.output
    assert "proj-a" in result.output


def test_cli_portfolio_registry_and_memory_dir_exclusive(tmp_path: Path) -> None:
    mem = tmp_path / "memory"
    mem.mkdir()
    reg_path = tmp_path / "registry.json"
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--memory-dir",
            str(mem),
            "--registry",
            str(reg_path),
            "--output",
            str(tmp_path / "index.html"),
        ],
    )
    assert result.exit_code == 1
    assert "mutually exclusive" in result.output


def test_cli_portfolio_default_registry_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no --memory-dir or --registry given, default registry must exist."""
    import aeos.cli as cli_mod
    import aeos.project.registry as reg_mod

    fake_default = tmp_path / "projects.json"  # does not exist
    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY", fake_default)
    monkeypatch.setattr(cli_mod, "DEFAULT_REGISTRY", fake_default, raising=False)

    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--output",
            str(tmp_path / "index.html"),
        ],
    )
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_cli_portfolio_no_flags_uses_default_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no --memory-dir or --registry given, use DEFAULT_REGISTRY automatically."""
    import aeos.cli as cli_mod
    import aeos.project.registry as reg_mod
    from aeos.project.registry import (
        ProjectRegistration,
        ProjectRegistry,
        save_registry,
    )

    # Seed memory dir and default registry
    mem = tmp_path / "memory"
    mem.mkdir()
    _write(mem, _make_record(project_name="default-proj"))

    fake_default = tmp_path / "projects.json"
    reg = ProjectRegistration(
        name="default-proj", project_type="recovered-project", memory_dir=mem
    )
    save_registry(ProjectRegistry(registry_path=fake_default, projects=[reg]))

    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY", fake_default)
    monkeypatch.setattr(cli_mod, "DEFAULT_REGISTRY", fake_default, raising=False)

    out = tmp_path / "index.html"
    result = runner.invoke(
        app,
        ["ui", "portfolio", "--output", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "default-proj" in result.output
    assert "registry" in result.output


def test_cli_portfolio_registry_not_found(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--registry",
            str(tmp_path / "no-such.json"),
            "--output",
            str(tmp_path / "index.html"),
        ],
    )
    assert result.exit_code == 1


def test_cli_portfolio_registry_empty_renders_no_projects(tmp_path: Path) -> None:
    from aeos.project.registry import ProjectRegistry, save_registry

    reg_path = tmp_path / "registry.json"
    save_registry(ProjectRegistry(registry_path=reg_path))

    out = tmp_path / "index.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--registry",
            str(reg_path),
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "No projects found" in out.read_text(encoding="utf-8")


def test_cli_portfolio_registry_skips_missing_memory_dir(tmp_path: Path) -> None:
    from aeos.project.registry import (
        ProjectRegistration,
        ProjectRegistry,
        save_registry,
    )

    reg_path = tmp_path / "registry.json"
    absent = tmp_path / "ghost-memory"  # never created
    reg = ProjectRegistration(
        name="ghost",
        project_type="recovered-project",
        memory_dir=absent,
    )
    save_registry(ProjectRegistry(registry_path=reg_path, projects=[reg]))

    out = tmp_path / "index.html"
    result = runner.invoke(
        app,
        [
            "ui",
            "portfolio",
            "--registry",
            str(reg_path),
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "No projects found" in out.read_text(encoding="utf-8")
