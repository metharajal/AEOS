"""Unit tests for aeos.workspace.demo and the `aeos workspace demo` CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record
from aeos.project.registry import ProjectRegistration, register_project
from aeos.workspace.demo import (
    ProjectDemoResult,
    WorkspaceDemoResult,
    generate_workspace_demo,
)

runner = CliRunner()

_PACK_FILES = [
    "index.html",
    "dashboard.html",
    "project-workspace.html",
    "recovery-summary.md",
    "risk-register.md",
    "human-gates.md",
    "next-actions.md",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    project_name: str = "test-proj",
    status: str = "ERROR",
    control_level: str = "weak",
    critical: int = 3,
    important: int = 5,
    manual: int = 2,
    generated: int = 1,
    record_suffix: str = "aa001100",
) -> MemoryRecord:
    return MemoryRecord(
        record_id=f"{project_name}-20260630T110000-{record_suffix}",
        created_at="2026-06-30T11:00:00",
        project_path=f"/private/tmp/{project_name}",
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
        remediation_summary=None,
        strategic_options=[],
        human_validated=False,
        notes=None,
    )


def _seed_project(tmp_path: Path, name: str) -> Path:
    """Write one MemoryRecord for a project and return memory_dir."""
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    save_record(_make_record(project_name=name), mem_dir)
    return mem_dir


def _make_registry(
    tmp_path: Path,
    projects: list[tuple[str, Path]],
) -> Path:
    """Register projects and return registry path."""
    reg_path = tmp_path / "registry.json"
    for name, mem_dir in projects:
        reg = ProjectRegistration(
            name=name,
            project_type="recovered-project",
            memory_dir=mem_dir,
        )
        register_project(reg, reg_path)
    return reg_path


# ---------------------------------------------------------------------------
# WorkspaceDemoResult properties
# ---------------------------------------------------------------------------


def test_result_generated_count() -> None:
    base = Path("/nonexistent/out")
    r = WorkspaceDemoResult(
        output_dir=base,
        registry_path=Path("/nonexistent/reg.json"),
        portfolio=base / "index.html",
        projects=[
            ProjectDemoResult(name="a", output_dir=base / "a"),
            ProjectDemoResult(
                name="b", output_dir=base / "b", skipped=True, skip_reason="/x"
            ),
        ],
    )
    assert r.generated_count == 1
    assert r.skipped_count == 1


# ---------------------------------------------------------------------------
# generate_workspace_demo — library function
# ---------------------------------------------------------------------------


def test_generate_workspace_demo_basic(tmp_path: Path) -> None:
    mem_dir = _seed_project(tmp_path / "proj-a", "proj-a")
    reg_path = _make_registry(tmp_path, [("proj-a", mem_dir)])
    out = tmp_path / "workspace"

    result = generate_workspace_demo(reg_path, out, overwrite=True)

    assert result.portfolio.exists()
    assert result.generated_count == 1
    assert result.skipped_count == 0
    assert not result.warnings

    proj = result.projects[0]
    assert proj.name == "proj-a"
    assert not proj.skipped
    assert (proj.output_dir / "dashboard.html").exists()
    assert (proj.output_dir / "project-workspace.html").exists()
    ep = proj.output_dir / "evidence-pack"
    for f in _PACK_FILES:
        assert (ep / f).exists(), f"Missing evidence-pack file: {f}"


def test_generate_workspace_demo_multi_project(tmp_path: Path) -> None:
    mem_a = _seed_project(tmp_path / "a", "proj-a")
    mem_b = _seed_project(tmp_path / "b", "proj-b")
    reg_path = _make_registry(tmp_path, [("proj-a", mem_a), ("proj-b", mem_b)])
    out = tmp_path / "workspace"

    result = generate_workspace_demo(reg_path, out, overwrite=True)

    assert result.generated_count == 2
    assert result.skipped_count == 0
    assert result.portfolio.exists()
    assert (out / "proj-a" / "dashboard.html").exists()
    assert (out / "proj-b" / "dashboard.html").exists()


def test_generate_workspace_demo_skips_missing_memory_dir(tmp_path: Path) -> None:
    mem_dir = tmp_path / "ghost" / "memory"  # intentionally not created
    reg_path = _make_registry(tmp_path, [("ghost-proj", mem_dir)])
    out = tmp_path / "workspace"

    result = generate_workspace_demo(reg_path, out, overwrite=True)

    assert result.generated_count == 0
    assert result.skipped_count == 1
    assert len(result.warnings) == 1
    assert "ghost-proj" in result.warnings[0]
    proj = result.projects[0]
    assert proj.skipped
    assert str(mem_dir) in proj.skip_reason


def test_generate_workspace_demo_mixed_valid_and_missing(tmp_path: Path) -> None:
    mem_ok = _seed_project(tmp_path / "ok", "ok-proj")
    mem_missing = tmp_path / "missing" / "memory"  # not created
    reg_path = _make_registry(
        tmp_path, [("ok-proj", mem_ok), ("missing-proj", mem_missing)]
    )
    out = tmp_path / "workspace"

    result = generate_workspace_demo(reg_path, out, overwrite=True)

    assert result.generated_count == 1
    assert result.skipped_count == 1
    assert result.portfolio.exists()
    assert (out / "ok-proj" / "dashboard.html").exists()
    assert len(result.warnings) == 1


def test_generate_workspace_demo_registry_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        generate_workspace_demo(
            tmp_path / "no-such-registry.json",
            tmp_path / "out",
        )


def test_generate_workspace_demo_empty_registry(tmp_path: Path) -> None:
    reg_path = tmp_path / "empty.json"
    reg_path.write_text('{"projects": [], "local_only": true, "read_only": true}')
    with pytest.raises(ValueError, match="no projects"):
        generate_workspace_demo(reg_path, tmp_path / "out")


def test_generate_workspace_demo_portfolio_html_content(tmp_path: Path) -> None:
    mem_dir = _seed_project(tmp_path / "p", "my-project")
    reg_path = _make_registry(tmp_path, [("my-project", mem_dir)])
    out = tmp_path / "workspace"

    result = generate_workspace_demo(reg_path, out, overwrite=True)

    html = result.portfolio.read_text()
    assert "my-project" in html


def test_generate_workspace_demo_overwrite_false_raises_on_existing_pack(
    tmp_path: Path,
) -> None:
    mem_dir = _seed_project(tmp_path / "p", "proj-x")
    reg_path = _make_registry(tmp_path, [("proj-x", mem_dir)])
    out = tmp_path / "workspace"

    # First run — creates files
    generate_workspace_demo(reg_path, out, overwrite=True)

    # Second run without overwrite — evidence-pack dir is non-empty → ValueError
    with pytest.raises(ValueError, match="already exists"):
        generate_workspace_demo(reg_path, out, overwrite=False)


# ---------------------------------------------------------------------------
# CLI — aeos workspace demo
# ---------------------------------------------------------------------------


def test_cli_workspace_demo_basic(tmp_path: Path) -> None:
    mem_dir = _seed_project(tmp_path / "proj", "alpha")
    reg_path = _make_registry(tmp_path, [("alpha", mem_dir)])
    out = tmp_path / "ws"

    result = runner.invoke(
        app,
        [
            "workspace",
            "demo",
            "--registry",
            str(reg_path),
            "--output-dir",
            str(out),
            "--overwrite",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Workspace:" in result.output
    assert "Portfolio:" in result.output
    assert "alpha" in result.output
    assert "read_only: true" in result.output
    assert (out / "index.html").exists()
    assert (out / "alpha" / "dashboard.html").exists()
    assert (out / "alpha" / "project-workspace.html").exists()
    assert (out / "alpha" / "evidence-pack" / "index.html").exists()


def test_cli_workspace_demo_registry_not_found(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "workspace",
            "demo",
            "--registry",
            str(tmp_path / "no-such.json"),
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_workspace_demo_empty_registry(tmp_path: Path) -> None:
    reg_path = tmp_path / "empty.json"
    reg_path.write_text('{"projects": [], "local_only": true, "read_only": true}')

    result = runner.invoke(
        app,
        [
            "workspace",
            "demo",
            "--registry",
            str(reg_path),
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_workspace_demo_skips_missing_memory_dir(tmp_path: Path) -> None:
    mem_dir = tmp_path / "ghost" / "memory"  # not created
    reg_path = _make_registry(tmp_path, [("ghost", mem_dir)])
    out = tmp_path / "ws"

    result = runner.invoke(
        app,
        [
            "workspace",
            "demo",
            "--registry",
            str(reg_path),
            "--output-dir",
            str(out),
            "--overwrite",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "SKIP" in result.output
    assert "ghost" in result.output
    assert "Warning" in result.output or "warning" in result.output.lower()


def test_cli_workspace_demo_multi_project(tmp_path: Path) -> None:
    mem_a = _seed_project(tmp_path / "a", "alpha")
    mem_b = _seed_project(tmp_path / "b", "beta")
    reg_path = _make_registry(tmp_path, [("alpha", mem_a), ("beta", mem_b)])
    out = tmp_path / "ws"

    result = runner.invoke(
        app,
        [
            "workspace",
            "demo",
            "--registry",
            str(reg_path),
            "--output-dir",
            str(out),
            "--overwrite",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "2 generated" in result.output
    assert (out / "alpha" / "dashboard.html").exists()
    assert (out / "beta" / "dashboard.html").exists()


def test_cli_workspace_demo_output_structure(tmp_path: Path) -> None:
    mem_dir = _seed_project(tmp_path / "proj", "my-proj")
    reg_path = _make_registry(tmp_path, [("my-proj", mem_dir)])
    out = tmp_path / "ws"

    runner.invoke(
        app,
        [
            "workspace",
            "demo",
            "--registry",
            str(reg_path),
            "--output-dir",
            str(out),
            "--overwrite",
        ],
    )

    # Verify full expected file tree
    assert (out / "index.html").exists()
    assert (out / "my-proj" / "dashboard.html").exists()
    assert (out / "my-proj" / "project-workspace.html").exists()
    ep = out / "my-proj" / "evidence-pack"
    for f in _PACK_FILES:
        assert (ep / f).exists(), f"Missing: {ep / f}"


# ---------------------------------------------------------------------------
# CLI — default registry (MVP-CORE-3)
# ---------------------------------------------------------------------------


def test_cli_workspace_demo_default_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without --registry, DEFAULT_REGISTRY (~/.aeos/projects.json) is used."""
    import aeos.project.registry as reg_mod

    mem_dir = _seed_project(tmp_path / "proj", "default-proj")
    fake_default = tmp_path / "projects.json"
    reg = ProjectRegistration(
        name="default-proj",
        project_type="recovered-project",
        memory_dir=mem_dir,
    )
    register_project(reg, fake_default)

    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY", fake_default)

    out = tmp_path / "ws"
    result = runner.invoke(
        app,
        ["workspace", "demo", "--output-dir", str(out), "--overwrite"],
    )

    assert result.exit_code == 0, result.output
    assert "default-proj" in result.output
    assert (out / "index.html").exists()
    assert (out / "default-proj" / "dashboard.html").exists()


def test_cli_workspace_demo_default_registry_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without --registry and default missing, exit 1 with clear error."""
    import aeos.project.registry as reg_mod

    fake_default = tmp_path / "projects.json"  # intentionally not created
    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY", fake_default)

    result = runner.invoke(
        app,
        ["workspace", "demo", "--output-dir", str(tmp_path / "ws")],
    )

    assert result.exit_code == 1
    assert "Error" in result.output
