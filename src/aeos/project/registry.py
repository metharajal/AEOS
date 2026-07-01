"""
AEOS Project Registry — persist project registrations to a local JSON file.

Writes only to the AEOS home directory (~/.aeos/registry.json by default).
Never reads .env. Never modifies client project files. No network. No secrets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

AEOS_HOME: Path = Path.home() / ".aeos"
DEFAULT_REGISTRY: Path = AEOS_HOME / "registry.json"


@dataclass
class ProjectRegistration:
    """A single registered project entry."""

    name: str
    project_type: str
    memory_dir: Path
    evidence_dir: Path | None = None
    registered_at: str = ""

    def __post_init__(self) -> None:
        if not self.registered_at:
            self.registered_at = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ProjectRegistry:
    """In-memory representation of the registry file."""

    registry_path: Path
    projects: list[ProjectRegistration] = field(default_factory=list)
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.updated_at:
            self.updated_at = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _registration_to_dict(reg: ProjectRegistration) -> dict[str, object]:
    return {
        "name": reg.name,
        "type": reg.project_type,
        "memory_dir": str(reg.memory_dir),
        "evidence_dir": str(reg.evidence_dir) if reg.evidence_dir is not None else None,
        "registered_at": reg.registered_at,
    }


def _dict_to_registration(d: dict[str, object]) -> ProjectRegistration:
    ev = d.get("evidence_dir")
    return ProjectRegistration(
        name=str(d["name"]),
        project_type=str(d.get("type", "recovered-project")),
        memory_dir=Path(str(d["memory_dir"])),
        evidence_dir=Path(str(ev)) if ev is not None else None,
        registered_at=str(d.get("registered_at", "")),
    )


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def load_registry(registry_path: Path = DEFAULT_REGISTRY) -> ProjectRegistry:
    """Load the registry from disk. Returns an empty registry if absent or corrupt."""
    if not registry_path.exists():
        return ProjectRegistry(registry_path=registry_path)
    try:
        raw = registry_path.read_text(encoding="utf-8")
        data: dict[str, object] = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return ProjectRegistry(registry_path=registry_path)

    projects: list[ProjectRegistration] = []
    raw_projects = data.get("projects", [])
    if isinstance(raw_projects, list):
        for item in raw_projects:
            if isinstance(item, dict):
                try:
                    projects.append(_dict_to_registration(item))
                except (KeyError, TypeError):
                    pass

    return ProjectRegistry(
        registry_path=registry_path,
        projects=projects,
        updated_at=str(data.get("updated_at", "")),
    )


def save_registry(registry: ProjectRegistry) -> None:
    """Persist the registry to disk, creating parent directories as needed."""
    registry.updated_at = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    registry.registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "updated_at": registry.updated_at,
        "projects": [_registration_to_dict(p) for p in registry.projects],
    }
    registry.registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def find_project(registry: ProjectRegistry, name: str) -> ProjectRegistration | None:
    """Return the registration matching name, or None."""
    for p in registry.projects:
        if p.name == name:
            return p
    return None


# ---------------------------------------------------------------------------
# Mutation
# ---------------------------------------------------------------------------


def register_project(
    registration: ProjectRegistration,
    registry_path: Path = DEFAULT_REGISTRY,
    *,
    overwrite: bool = False,
) -> ProjectRegistry:
    """Add or update a project registration, persisting the result.

    Raises ValueError if the name already exists and overwrite is False.
    """
    registry = load_registry(registry_path)
    existing = find_project(registry, registration.name)
    if existing is not None and not overwrite:
        raise ValueError(
            f"Project '{registration.name}' is already registered."
            " Use --overwrite to update."
        )
    if existing is not None:
        registry.projects = [
            registration if p.name == registration.name else p
            for p in registry.projects
        ]
    else:
        registry.projects.append(registration)
    registry.projects.sort(key=lambda p: p.name)
    save_registry(registry)
    return registry
