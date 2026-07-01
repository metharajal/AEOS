"""
AEOS Workspace UX helpers — status and open commands.

Read-only. No network. No AI. No secrets. No .env.
Uses webbrowser.open() for cross-platform file opening.
"""

from __future__ import annotations

import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORKSPACE_DIR: Path = Path(tempfile.gettempdir()) / "aeos-workspace-demo"


# ---------------------------------------------------------------------------
# workspace status
# ---------------------------------------------------------------------------


@dataclass
class WorkspaceStatusResult:
    """Snapshot of the current AEOS workspace state."""

    registry_path: Path
    registry_exists: bool
    project_count: int
    workspace_dir: Path
    index_exists: bool
    suggested_command: str


def workspace_status(
    registry_path: Path,
    workspace_dir: Path = DEFAULT_WORKSPACE_DIR,
) -> WorkspaceStatusResult:
    """Return a snapshot of the current AEOS workspace state.

    Never modifies the registry. Never writes any file.
    """
    from aeos.project.registry import load_registry

    registry_exists = registry_path.exists()
    project_count = 0

    if registry_exists:
        reg = load_registry(registry_path)
        project_count = len(reg.projects)

    index_path = workspace_dir / "index.html"
    index_exists = index_path.exists()

    if not registry_exists:
        suggested = "aeos project register --name <project> --memory-dir <path>/memory"
    elif project_count == 0:
        suggested = "aeos project register --name <project> --memory-dir <path>/memory"
    elif not index_exists:
        suggested = f"aeos workspace demo --output-dir {workspace_dir}"
    else:
        suggested = f"open {index_path}"

    return WorkspaceStatusResult(
        registry_path=registry_path,
        registry_exists=registry_exists,
        project_count=project_count,
        workspace_dir=workspace_dir,
        index_exists=index_exists,
        suggested_command=suggested,
    )


# ---------------------------------------------------------------------------
# workspace open
# ---------------------------------------------------------------------------


def workspace_open(index_path: Path) -> bool:
    """Open a workspace index.html in the default browser.

    Raises FileNotFoundError if index_path does not exist.
    Returns True if webbrowser.open() reported success.
    Uses webbrowser.open() — no subprocess, no network call.
    """
    if not index_path.exists():
        raise FileNotFoundError(
            f"Workspace file '{index_path}' does not exist.\n"
            "  Run: aeos workspace demo "
            f"--output-dir {index_path.parent}"
        )
    url = index_path.resolve().as_uri()
    return webbrowser.open(url)
