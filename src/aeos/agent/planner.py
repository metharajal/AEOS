"""
AEOS Agent Planner — deterministic, read-only local planning.

No LLM. No network. No secrets. No .env.
Reads the project registry and MemoryRecords, produces a structured plan.
Every output is marked read_only: true · applied: false.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from aeos.project.registry import ProjectRegistration

PlanStatus = Literal["OK", "WARNING", "ERROR"]

AGENT_MODE = "deterministic read-only planner"
_DEFAULT_WS = Path(tempfile.gettempdir()) / "aeos-workspace-demo"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ProjectPlanEntry:
    """Deterministic plan for one registered project."""

    name: str
    project_type: str
    memory_dir: Path
    memory_dir_exists: bool
    evidence_dir: Path | None
    evidence_dir_exists: bool | None  # None = no evidence_dir configured
    record_count: int
    critical: int
    important: int
    status: PlanStatus
    risks: list[str]
    actions: list[str]


@dataclass
class AgentPlan:
    """Full deterministic plan across one or more projects."""

    agent_mode: str
    registry_path: Path
    projects: list[ProjectPlanEntry]
    global_status: PlanStatus
    risks: list[str]
    suggested_actions: list[str]
    workspace_index_path: Path
    workspace_index_exists: bool
    human_validation_required: bool = True
    applied: bool = False
    read_only: bool = True
    generated_at: str = field(default="")

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Per-project analysis
# ---------------------------------------------------------------------------


def _analyse_project(
    proj: ProjectRegistration,
    workspace_dir: Path,
) -> ProjectPlanEntry:
    risks: list[str] = []
    actions: list[str] = []
    status: PlanStatus = "OK"

    mem_exists = proj.memory_dir.exists()
    if not mem_exists:
        risks.append(f"memory_dir not found: {proj.memory_dir}")
        actions.append(
            "Fix memory_dir path in registry or re-run: "
            "aeos reclaim harden --path <project-path>"
        )
        return ProjectPlanEntry(
            name=proj.name,
            project_type=proj.project_type,
            memory_dir=proj.memory_dir,
            memory_dir_exists=False,
            evidence_dir=proj.evidence_dir,
            evidence_dir_exists=None,
            record_count=0,
            critical=0,
            important=0,
            status="ERROR",
            risks=risks,
            actions=actions,
        )

    # Load records to inspect findings
    record_count = 0
    critical = 0
    important = 0
    try:
        from aeos.memory.timeline import load_project_records

        records = load_project_records(proj.memory_dir, proj.name)
        record_count = len(records)
        if records:
            latest = records[-1]
            fs = latest.findings_summary
            critical = fs.get("critical", 0)
            important = fs.get("important", 0)
    except (FileNotFoundError, ValueError):
        pass

    if record_count == 0:
        risks.append("No MemoryRecords found in memory_dir")
        actions.append("Run: aeos reclaim harden --path <project-path>")
        status = "WARNING"

    if critical > 0:
        risks.append(f"{critical} critical finding(s) — NOT READY FOR PRODUCTION")
        actions.append(
            f"Human review required before production deploy "
            f"({critical} critical risk(s))"
        )
        if status != "ERROR":
            status = "WARNING"

    if important > 0:
        risks.append(f"{important} important finding(s) pending review")
        actions.append(
            "Review evidence pack: "
            "aeos ui evidence-pack "
            "--memory-dir <path> --project <name> --output-dir <dir>"
        )
        if status == "OK":
            status = "WARNING"

    # Evidence dir
    ev_exists: bool | None = None
    if proj.evidence_dir is not None:
        ev_exists = proj.evidence_dir.exists()
        if not ev_exists:
            risks.append(f"evidence_dir not found: {proj.evidence_dir}")
            actions.append(
                "Regenerate: "
                f"aeos workspace demo --output-dir {workspace_dir} --overwrite"
            )
            if status == "OK":
                status = "WARNING"

    if status == "OK":
        actions.append(
            f"Open workspace: aeos workspace open --path {workspace_dir / 'index.html'}"
        )

    return ProjectPlanEntry(
        name=proj.name,
        project_type=proj.project_type,
        memory_dir=proj.memory_dir,
        memory_dir_exists=True,
        evidence_dir=proj.evidence_dir,
        evidence_dir_exists=ev_exists,
        record_count=record_count,
        critical=critical,
        important=important,
        status=status,
        risks=risks,
        actions=actions,
    )


# ---------------------------------------------------------------------------
# Top-level plan generation
# ---------------------------------------------------------------------------


def generate_plan(
    registry_path: Path | None = None,
    project_filter: str | None = None,
    workspace_dir: Path | None = None,
) -> AgentPlan:
    """Generate a deterministic local plan from the project registry.

    Pure read — never writes files, never modifies the registry,
    never contacts any network endpoint.  No LLM.  No .env access.
    """
    from aeos.project.registry import DEFAULT_REGISTRY, load_registry

    reg_path = registry_path if registry_path is not None else DEFAULT_REGISTRY
    ws_dir = workspace_dir if workspace_dir is not None else _DEFAULT_WS
    index_path = ws_dir / "index.html"

    global_risks: list[str] = []
    global_actions: list[str] = []
    project_entries: list[ProjectPlanEntry] = []

    # ------------------------------------------------------------------
    # Gate 1 — registry
    # ------------------------------------------------------------------
    if not reg_path.exists():
        global_risks.append(f"Registry not found: {reg_path}")
        global_actions.append("Run: aeos workspace init")
        return AgentPlan(
            agent_mode=AGENT_MODE,
            registry_path=reg_path,
            projects=[],
            global_status="ERROR",
            risks=global_risks,
            suggested_actions=global_actions,
            workspace_index_path=index_path,
            workspace_index_exists=False,
        )

    registry = load_registry(reg_path)

    # ------------------------------------------------------------------
    # Gate 2 — projects
    # ------------------------------------------------------------------
    projects = registry.projects
    if project_filter:
        projects = [p for p in projects if p.name == project_filter]
        if not projects:
            global_risks.append(f"Project '{project_filter}' not found in registry")
            global_actions.append(
                f"Register it: aeos project register --name {project_filter} "
                "--memory-dir <path>/memory"
            )
            return AgentPlan(
                agent_mode=AGENT_MODE,
                registry_path=reg_path,
                projects=[],
                global_status="ERROR",
                risks=global_risks,
                suggested_actions=global_actions,
                workspace_index_path=index_path,
                workspace_index_exists=index_path.exists(),
            )

    if not projects:
        global_risks.append("No projects registered")
        global_actions.append(
            "Register a project: "
            "aeos project register --name <project> --memory-dir <path>/memory"
        )
        return AgentPlan(
            agent_mode=AGENT_MODE,
            registry_path=reg_path,
            projects=[],
            global_status="WARNING",
            risks=global_risks,
            suggested_actions=global_actions,
            workspace_index_path=index_path,
            workspace_index_exists=index_path.exists(),
        )

    # ------------------------------------------------------------------
    # Per-project analysis
    # ------------------------------------------------------------------
    for proj in projects:
        project_entries.append(_analyse_project(proj, ws_dir))

    # ------------------------------------------------------------------
    # Workspace index
    # ------------------------------------------------------------------
    index_exists = index_path.exists()
    if not index_exists:
        has_actionable = any(e.status in ("OK", "WARNING") for e in project_entries)
        if has_actionable:
            global_risks.append(f"Workspace index not found: {index_path}")
            global_actions.append(
                f"Generate workspace: aeos workspace demo --output-dir {ws_dir}"
            )

    # ------------------------------------------------------------------
    # Global status
    # ------------------------------------------------------------------
    worst: PlanStatus = "OK"
    for entry in project_entries:
        if entry.status == "ERROR":
            worst = "ERROR"
            break
        if entry.status == "WARNING" and worst == "OK":
            worst = "WARNING"
    if not index_exists and worst == "OK":
        worst = "WARNING"

    if index_exists and worst == "OK":
        global_actions.append(
            f"Open workspace: aeos workspace open --path {index_path}"
        )

    return AgentPlan(
        agent_mode=AGENT_MODE,
        registry_path=reg_path,
        projects=project_entries,
        global_status=worst,
        risks=global_risks,
        suggested_actions=global_actions,
        workspace_index_path=index_path,
        workspace_index_exists=index_exists,
    )


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def render_plan_markdown(plan: AgentPlan) -> str:
    lines: list[str] = []
    a = lines.append

    a("# AEOS Agent Plan")
    a("")
    a(f"**Mode:** {plan.agent_mode}")
    a(f"**Registry:** {plan.registry_path}")
    a(f"**Generated:** {plan.generated_at}")
    a(f"**Global status:** {plan.global_status}")
    a(f"**Projects inspected:** {len(plan.projects)}")
    a("")
    a("---")
    a("")

    # Global risks
    if plan.risks:
        a("## Global Risks / Blockers")
        a("")
        for r in plan.risks:
            a(f"- {r}")
        a("")

    # Global actions
    if plan.suggested_actions:
        a("## Suggested Next Actions")
        a("")
        for i, act in enumerate(plan.suggested_actions, 1):
            a(f"{i}. {act}")
        a("")

    # Per-project
    if plan.projects:
        a("## Per-Project Summary")
        a("")
        for entry in plan.projects:
            a(f"### {entry.name}")
            a("")
            a("| Field | Value |")
            a("|-------|-------|")
            a(f"| Status | {entry.status} |")
            a(f"| Type | {entry.project_type} |")
            a(f"| memory_dir | {entry.memory_dir} |")
            a(f"| memory_dir exists | {'yes' if entry.memory_dir_exists else 'no'} |")
            a(f"| MemoryRecords | {entry.record_count} |")
            a(f"| Critical findings | {entry.critical} |")
            a(f"| Important findings | {entry.important} |")
            if entry.evidence_dir is not None:
                a(f"| evidence_dir | {entry.evidence_dir} |")
                a(
                    f"| evidence_dir exists | "
                    f"{'yes' if entry.evidence_dir_exists else 'no'} |"
                )
            a("")
            if entry.risks:
                a("**Risks:**")
                a("")
                for r in entry.risks:
                    a(f"- {r}")
                a("")
            if entry.actions:
                a("**Actions:**")
                a("")
                for i, act in enumerate(entry.actions, 1):
                    a(f"{i}. {act}")
                a("")

    # Footer
    a("---")
    a("")
    a("## Agent Statement")
    a("")
    a(
        "This plan was generated by a deterministic read-only planner. "
        "No model was called. No data was transmitted. "
        "No files were modified."
    )
    a("")
    a("**Human validation required before any action is taken.**")
    a("")
    a("```")
    a("read_only: true  ·  applied: false  ·  human validation required")
    a("```")
    a("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON renderer
# ---------------------------------------------------------------------------


def render_plan_json(plan: AgentPlan) -> str:
    def _entry(e: ProjectPlanEntry) -> dict[str, object]:
        return {
            "name": e.name,
            "project_type": e.project_type,
            "memory_dir": str(e.memory_dir),
            "memory_dir_exists": e.memory_dir_exists,
            "evidence_dir": str(e.evidence_dir) if e.evidence_dir else None,
            "evidence_dir_exists": e.evidence_dir_exists,
            "record_count": e.record_count,
            "critical": e.critical,
            "important": e.important,
            "status": e.status,
            "risks": e.risks,
            "actions": e.actions,
        }

    payload: dict[str, object] = {
        "agent_mode": plan.agent_mode,
        "registry_path": str(plan.registry_path),
        "generated_at": plan.generated_at,
        "global_status": plan.global_status,
        "projects_inspected": len(plan.projects),
        "workspace_index_path": str(plan.workspace_index_path),
        "workspace_index_exists": plan.workspace_index_exists,
        "risks": plan.risks,
        "suggested_actions": plan.suggested_actions,
        "projects": [_entry(e) for e in plan.projects],
        "human_validation_required": plan.human_validation_required,
        "applied": plan.applied,
        "read_only": plan.read_only,
    }
    return json.dumps(payload, indent=2)
