"""
AEOS Memory Store — build and persist MemoryRecord instances locally.

Writes JSON files to a configurable local directory.
Never reads .env. Never stores secret values. Never connects to any network.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from aeos.memory.models import MemoryRecord

if TYPE_CHECKING:
    from aeos.reclaim.hardener import ReclaimHardenResult

# Patterns that look like raw credential values (defense-in-depth guard).
# We check these against every string value before writing to disk.
_CREDENTIAL_PATTERNS = [
    re.compile(r"^eyJ[A-Za-z0-9_\-]{20,}"),  # JWT
    re.compile(r"^[A-Za-z0-9+/]{60,}={0,2}$"),  # long base64 blob
    re.compile(r"^(sk|pk)_live_[A-Za-z0-9]{20,}"),  # Stripe-style live key
]


def _looks_like_secret_value(s: str) -> bool:
    for pattern in _CREDENTIAL_PATTERNS:
        if pattern.search(s):
            return True
    return False


def _iter_string_leaves(obj: object) -> list[str]:
    """Recursively collect all string values in a JSON-compatible object."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        results: list[str] = []
        for v in obj.values():
            results.extend(_iter_string_leaves(v))
        return results
    if isinstance(obj, list):
        results = []
        for item in obj:
            results.extend(_iter_string_leaves(item))
        return results
    return []


def build_memory_record_from_reclaim_harden(
    result: ReclaimHardenResult,
    project_path: Path,
) -> MemoryRecord:
    """Build a safe MemoryRecord from a ReclaimHardenResult."""
    s = result.summary
    now = datetime.now(tz=UTC)
    ts = now.strftime("%Y%m%dT%H%M%S")
    short_id = uuid.uuid4().hex[:8]
    project_name = project_path.name or "unknown"
    record_id = f"{project_name}-{ts}-{short_id}"

    findings_summary: dict[str, int] = {
        "critical": s.critical_findings,
        "important": s.important_findings,
        "manual": s.manual_actions,
        "generated": s.generated_actions,
    }

    remediation_summary: dict[str, int] | None = None
    if result.remediation_plan is not None:
        p = result.remediation_plan
        remediation_summary = {
            "phases_count": p.phases_count,
            "immediate": p.immediate_actions_count,
            "manual": p.manual_actions_count,
            "generatable": p.generatable_actions_count,
            "strategic": p.strategic_options_count,
        }

    # Truncate exit option labels to 80 chars — no values, no secrets
    strategic_options = [opt[:80] for opt in result.exit_options]

    return MemoryRecord(
        record_id=record_id,
        created_at=now.isoformat(),
        project_path=str(project_path.resolve()),
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status=result.status,
        generator=s.generator_detected,
        providers=list(s.providers_detected),
        control_level=s.control_level,
        read_only=result.read_only,
        applied=result.applied,
        findings_summary=findings_summary,
        remediation_summary=remediation_summary,
        strategic_options=strategic_options,
        human_validated=False,
        notes=None,
    )


def save_record(record: MemoryRecord, memory_dir: Path) -> Path:
    """Write record JSON to memory_dir/<project_name>/<record_id>.json.

    Raises ValueError if any string value matches a known credential pattern.
    """
    payload: dict[str, object] = {
        "record_id": record.record_id,
        "created_at": record.created_at,
        "project_path": record.project_path,
        "project_name": record.project_name,
        "rail": record.rail,
        "command": record.command,
        "status": record.status,
        "generator": record.generator,
        "providers": record.providers,
        "control_level": record.control_level,
        "read_only": record.read_only,
        "applied": record.applied,
        "findings_summary": record.findings_summary,
        "remediation_summary": record.remediation_summary,
        "strategic_options": record.strategic_options,
        "human_validated": record.human_validated,
        "notes": record.notes,
    }

    for value in _iter_string_leaves(payload):
        if _looks_like_secret_value(value):
            raise ValueError(
                "MemoryRecord refused: a string value matched a credential pattern. "
                "No data was written."
            )

    project_dir = memory_dir / record.project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    record_path = project_dir / f"{record.record_id}.json"
    record_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return record_path
