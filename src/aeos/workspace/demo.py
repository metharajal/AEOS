"""
AEOS Workspace Demo — full workspace generator from a Project Registry.

Orchestrates: portfolio index + per-project dashboard, workspace, evidence-pack.
Read-only. No network. No AI. No secrets. No .env.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ProjectDemoResult:
    """Outcome for one project processed by the workspace demo."""

    name: str
    output_dir: Path
    files_written: list[Path] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class WorkspaceDemoResult:
    """Full result of a workspace demo generation."""

    output_dir: Path
    registry_path: Path
    portfolio: Path
    projects: list[ProjectDemoResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def generated_count(self) -> int:
        return sum(1 for p in self.projects if not p.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for p in self.projects if p.skipped)


# ---------------------------------------------------------------------------
# Core orchestrator
# ---------------------------------------------------------------------------


def generate_workspace_demo(
    registry_path: Path,
    output_dir: Path,
    overwrite: bool = False,
) -> WorkspaceDemoResult:
    """Generate a full workspace from a project registry.

    Raises FileNotFoundError if registry_path does not exist.
    Raises ValueError if the registry is empty.

    Projects whose memory_dir is missing are skipped with a warning;
    they do not cause the whole command to fail.
    """
    from aeos.project.registry import load_registry
    from aeos.ui.dashboard import load_dashboard_data, render_dashboard
    from aeos.ui.evidence_pack import generate_evidence_pack
    from aeos.ui.portfolio import load_portfolio_data, render_portfolio
    from aeos.ui.workspace import load_workspace_data, render_workspace

    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file '{registry_path}' does not exist.")

    registry = load_registry(registry_path)

    if not registry.projects:
        raise ValueError(
            f"Registry '{registry_path}' contains no projects. "
            "Run 'aeos project register' to add one."
        )

    warnings: list[str] = []
    project_results: list[ProjectDemoResult] = []
    valid_memory_dirs: list[Path] = []

    for reg_proj in registry.projects:
        proj_name = reg_proj.name
        mem_dir = reg_proj.memory_dir

        if not mem_dir.exists():
            msg = f"Skipping '{proj_name}': memory_dir '{mem_dir}' does not exist."
            warnings.append(msg)
            project_results.append(
                ProjectDemoResult(
                    name=proj_name,
                    output_dir=output_dir / proj_name,
                    skipped=True,
                    skip_reason=str(mem_dir),
                )
            )
            continue

        proj_out = output_dir / proj_name
        proj_out.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []

        # dashboard.html
        dash_data = load_dashboard_data(mem_dir, proj_name)
        dash_path = proj_out / "dashboard.html"
        if not dash_path.exists() or overwrite:
            dash_path.write_text(render_dashboard(dash_data), encoding="utf-8")
        written.append(dash_path)

        # project-workspace.html
        ws_data = load_workspace_data(mem_dir, proj_name)
        ws_path = proj_out / "project-workspace.html"
        if not ws_path.exists() or overwrite:
            ws_path.write_text(render_workspace(ws_data), encoding="utf-8")
        written.append(ws_path)

        # evidence-pack/
        ep_out = proj_out / "evidence-pack"
        ep_result = generate_evidence_pack(mem_dir, proj_name, ep_out, overwrite)
        written.extend(ep_result.files)

        project_results.append(
            ProjectDemoResult(
                name=proj_name,
                output_dir=proj_out,
                files_written=written,
            )
        )
        valid_memory_dirs.append(mem_dir)

    # Portfolio index at root (empty list is fine — renders 0-project page)
    output_dir.mkdir(parents=True, exist_ok=True)
    portfolio_data = load_portfolio_data(valid_memory_dirs)
    portfolio_path = output_dir / "index.html"
    if not portfolio_path.exists() or overwrite:
        portfolio_path.write_text(render_portfolio(portfolio_data), encoding="utf-8")

    return WorkspaceDemoResult(
        output_dir=output_dir,
        registry_path=registry_path,
        portfolio=portfolio_path,
        projects=project_results,
        warnings=warnings,
    )
