"""
AEOS Workspace Doctor — local environment diagnostic.

Read-only. No network. No AI. No secrets. No .env.
Never modifies the registry or any project file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

CheckStatus = Literal["OK", "WARNING", "ERROR"]


@dataclass
class CheckItem:
    """Result of one diagnostic check."""

    name: str
    status: CheckStatus
    detail: str


@dataclass
class DoctorResult:
    """Aggregated result of all workspace doctor checks."""

    checks: list[CheckItem] = field(default_factory=list)
    overall_status: CheckStatus = "OK"
    suggested_command: str = ""


def _worst(checks: list[CheckItem]) -> CheckStatus:
    if any(c.status == "ERROR" for c in checks):
        return "ERROR"
    if any(c.status == "WARNING" for c in checks):
        return "WARNING"
    return "OK"


def workspace_doctor(
    registry_path: Path | None = None,
    workspace_dir: Path | None = None,
) -> DoctorResult:
    """Run all workspace health checks and return a DoctorResult.

    Pure read — never writes files, never modifies the registry,
    never contacts a network endpoint.
    """
    from aeos.project.registry import AEOS_HOME, DEFAULT_REGISTRY
    from aeos.workspace.ux import DEFAULT_WORKSPACE_DIR

    reg_path = registry_path if registry_path is not None else DEFAULT_REGISTRY
    ws_dir = workspace_dir if workspace_dir is not None else DEFAULT_WORKSPACE_DIR
    aeos_home = reg_path.parent if registry_path is not None else AEOS_HOME

    checks: list[CheckItem] = []

    # ------------------------------------------------------------------
    # 1. AEOS home
    # ------------------------------------------------------------------
    if aeos_home.exists():
        checks.append(CheckItem("AEOS home", "OK", str(aeos_home)))
    else:
        checks.append(
            CheckItem(
                "AEOS home",
                "ERROR",
                f"{aeos_home}  (not found — run: aeos workspace init)",
            )
        )

    # ------------------------------------------------------------------
    # 2. Registry exists
    # ------------------------------------------------------------------
    if not reg_path.exists():
        checks.append(
            CheckItem(
                "Registry",
                "ERROR",
                f"{reg_path}  (not found — run: aeos workspace init)",
            )
        )
        return DoctorResult(
            checks=checks,
            overall_status=_worst(checks),
            suggested_command="aeos workspace init",
        )
    checks.append(CheckItem("Registry", "OK", str(reg_path)))

    # ------------------------------------------------------------------
    # 3. Registry readable JSON
    # ------------------------------------------------------------------
    try:
        raw_text = reg_path.read_text(encoding="utf-8")
        raw: dict[str, object] = json.loads(raw_text)
    except (json.JSONDecodeError, OSError) as exc:
        checks.append(
            CheckItem("Registry readable", "ERROR", f"cannot parse JSON: {exc}")
        )
        return DoctorResult(
            checks=checks,
            overall_status="ERROR",
            suggested_command="aeos workspace init",
        )

    raw_projects = raw.get("projects", [])
    project_count = len(raw_projects) if isinstance(raw_projects, list) else 0
    checks.append(
        CheckItem(
            "Registry readable",
            "OK",
            f"valid JSON · {project_count} project(s)",
        )
    )

    # ------------------------------------------------------------------
    # 4. Registry flags
    # ------------------------------------------------------------------
    local_only = bool(raw.get("local_only", False))
    read_only = bool(raw.get("read_only", False))
    flag_detail = (
        f"local_only={str(local_only).lower()}  ·  read_only={str(read_only).lower()}"
    )
    checks.append(
        CheckItem(
            "Registry flags",
            "OK" if (local_only and read_only) else "WARNING",
            flag_detail,
        )
    )

    # ------------------------------------------------------------------
    # 5. Projects registered
    # ------------------------------------------------------------------
    if project_count == 0:
        checks.append(
            CheckItem(
                "Projects registered",
                "WARNING",
                "0 projects  (run: aeos project register ...)",
            )
        )
    else:
        noun = "project" if project_count == 1 else "projects"
        checks.append(CheckItem("Projects registered", "OK", f"{project_count} {noun}"))

    # ------------------------------------------------------------------
    # 6. Per-project checks
    # ------------------------------------------------------------------
    from aeos.project.registry import load_registry

    reg = load_registry(reg_path)
    for proj in reg.projects:
        mem_ok = proj.memory_dir.exists()
        checks.append(
            CheckItem(
                f"[{proj.name}] memory_dir",
                "OK" if mem_ok else "ERROR",
                f"{proj.memory_dir}  {'✓' if mem_ok else '✗ not found'}",
            )
        )

        if proj.evidence_dir is not None:
            ev_ok = proj.evidence_dir.exists()
            checks.append(
                CheckItem(
                    f"[{proj.name}] evidence_dir",
                    "OK" if ev_ok else "WARNING",
                    f"{proj.evidence_dir}  {'✓' if ev_ok else '✗ not found'}",
                )
            )

        proj_local = proj.local_only
        proj_ro = proj.read_only
        checks.append(
            CheckItem(
                f"[{proj.name}] flags",
                "OK" if (proj_local and proj_ro) else "WARNING",
                f"local_only={str(proj_local).lower()}"
                f"  ·  read_only={str(proj_ro).lower()}",
            )
        )

    # ------------------------------------------------------------------
    # 7. Workspace index
    # ------------------------------------------------------------------
    index_path = ws_dir / "index.html"
    if index_path.exists():
        checks.append(CheckItem("Workspace index", "OK", str(index_path)))
    else:
        checks.append(
            CheckItem(
                "Workspace index",
                "WARNING",
                f"{index_path}  (not found)",
            )
        )

    # ------------------------------------------------------------------
    # Suggested next command
    # ------------------------------------------------------------------
    overall = _worst(checks)
    if overall == "ERROR":
        suggested = "aeos workspace init"
    elif project_count == 0:
        suggested = "aeos project register --name <project> --memory-dir <path>/memory"
    elif not index_path.exists():
        suggested = f"aeos workspace demo --output-dir {ws_dir}"
    else:
        suggested = f"aeos workspace open --path {index_path}"

    return DoctorResult(
        checks=checks,
        overall_status=overall,
        suggested_command=suggested,
    )
