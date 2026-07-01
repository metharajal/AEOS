"""
AEOS Workspace Init — create the AEOS home directory and default registry.

Idempotent. Does not overwrite an existing registry.
No network. No AI. No secrets. No .env. Never modifies client projects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkspaceInitResult:
    """Result of a workspace_init() call."""

    aeos_home: Path
    registry_path: Path
    initialized: bool  # True = registry just created; False = already existed
    project_count: int
    suggested_command: str


def workspace_init(
    aeos_home: Path | None = None,
    registry_path: Path | None = None,
) -> WorkspaceInitResult:
    """Create ~/.aeos and ~/.aeos/projects.json if absent.

    Safe to call multiple times — if the registry already exists it is
    read but never overwritten.  Never reads .env, never modifies client
    project files, no network.
    """
    from aeos.project.registry import (
        AEOS_HOME,
        DEFAULT_REGISTRY,
        ProjectRegistry,
        load_registry,
        save_registry,
    )

    home = aeos_home if aeos_home is not None else AEOS_HOME
    reg_path = registry_path if registry_path is not None else DEFAULT_REGISTRY

    home.mkdir(parents=True, exist_ok=True)

    if reg_path.exists():
        initialized = False
        reg = load_registry(reg_path)
        project_count = len(reg.projects)
    else:
        empty = ProjectRegistry(registry_path=reg_path)
        save_registry(empty)
        initialized = True
        project_count = 0

    if project_count == 0:
        suggested = "aeos project register --name <project> --memory-dir <path>/memory"
    else:
        suggested = "aeos workspace status"

    return WorkspaceInitResult(
        aeos_home=home,
        registry_path=reg_path,
        initialized=initialized,
        project_count=project_count,
        suggested_command=suggested,
    )
