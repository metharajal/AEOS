"""
AEOS Project Registry — persist watched-project metadata to a local JSON file.

Writes only to the AEOS home directory (~/.aeos/projects.json by default).
Never reads .env. Never modifies client project files. No network. No secrets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

AEOS_HOME: Path = Path.home() / ".aeos"
DEFAULT_REGISTRY: Path = AEOS_HOME / "projects.json"

_TS_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _now() -> str:
    return datetime.now(tz=UTC).strftime(_TS_FMT)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ProjectRegistration:
    """Metadata for one registered project."""

    name: str
    project_type: str
    memory_dir: Path
    evidence_dir: Path | None = None
    registered_at: str = ""
    last_seen_at: str = ""
    local_only: bool = True
    read_only: bool = True

    def __post_init__(self) -> None:
        now = _now()
        if not self.registered_at:
            self.registered_at = now
        if not self.last_seen_at:
            self.last_seen_at = now


@dataclass
class ProjectRegistry:
    """In-memory representation of the registry file."""

    registry_path: Path
    projects: list[ProjectRegistration] = field(default_factory=list)
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.updated_at:
            self.updated_at = _now()


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _to_dict(reg: ProjectRegistration) -> dict[str, object]:
    return {
        "name": reg.name,
        "type": reg.project_type,
        "memory_dir": str(reg.memory_dir),
        "evidence_dir": str(reg.evidence_dir) if reg.evidence_dir is not None else None,
        "registered_at": reg.registered_at,
        "last_seen_at": reg.last_seen_at,
        "local_only": reg.local_only,
        "read_only": reg.read_only,
    }


def _from_dict(d: dict[str, object]) -> ProjectRegistration:
    ev = d.get("evidence_dir")
    return ProjectRegistration(
        name=str(d["name"]),
        project_type=str(d.get("type", "recovered-project")),
        memory_dir=Path(str(d["memory_dir"])),
        evidence_dir=Path(str(ev)) if ev is not None else None,
        registered_at=str(d.get("registered_at", "")),
        last_seen_at=str(d.get("last_seen_at", "")),
        local_only=bool(d.get("local_only", True)),
        read_only=bool(d.get("read_only", True)),
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
                    projects.append(_from_dict(item))
                except (KeyError, TypeError):
                    pass

    return ProjectRegistry(
        registry_path=registry_path,
        projects=projects,
        updated_at=str(data.get("updated_at", "")),
    )


def save_registry(registry: ProjectRegistry) -> None:
    """Persist the registry to disk, creating parent directories as needed."""
    registry.updated_at = _now()
    registry.registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "updated_at": registry.updated_at,
        "local_only": True,
        "read_only": True,
        "projects": [_to_dict(p) for p in registry.projects],
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
# Mutation — upsert
# ---------------------------------------------------------------------------


def register_project(
    registration: ProjectRegistration,
    registry_path: Path = DEFAULT_REGISTRY,
) -> tuple[ProjectRegistry, bool]:
    """Upsert a project into the registry, persisting the result.

    Returns (registry, created) where created=True means a new entry was added,
    False means an existing entry was updated.
    """
    registry = load_registry(registry_path)
    existing = find_project(registry, registration.name)

    if existing is not None:
        # Update all fields, preserve original registered_at
        registration.registered_at = existing.registered_at
        registration.last_seen_at = _now()
        registry.projects = [
            registration if p.name == registration.name else p
            for p in registry.projects
        ]
        created = False
    else:
        registry.projects.append(registration)
        created = True

    registry.projects.sort(key=lambda p: p.name)
    save_registry(registry)
    return registry, created
