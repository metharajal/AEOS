"""
AEOS Memory Compare — compare two MemoryRecord snapshots.

Read-only. No network. No AI. No secrets. No .env.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aeos.memory.models import MemoryRecord
from aeos.memory.store import load_record

_STATUS_RANK: dict[str, int] = {"ERROR": 0, "WARNING": 1, "OK": 2}
_CONTROL_RANK: dict[str, int] = {"weak": 0, "partial": 1, "controlled": 2}


@dataclass
class MemoryCompareDelta:
    """Delta for a single compared field between two MemoryRecords."""

    field: str
    left_value: str
    right_value: str
    trend: str  # "improved" | "degraded" | "unchanged" | "incompatible"


@dataclass
class MemoryCompareResult:
    """Result of comparing two MemoryRecord snapshots."""

    left_id: str
    right_id: str
    project_name: str
    compatible: bool
    synthesis: str  # "improved" | "degraded" | "unchanged" | "mixed" | "incompatible"
    improved: list[MemoryCompareDelta] = field(default_factory=list)
    degraded: list[MemoryCompareDelta] = field(default_factory=list)
    unchanged: list[MemoryCompareDelta] = field(default_factory=list)
    incompatible_fields: list[MemoryCompareDelta] = field(default_factory=list)


def compute_trend(left: int, right: int, higher_is_better: bool) -> str:
    """Return "improved", "degraded", or "unchanged" for a numeric field comparison."""
    if left == right:
        return "unchanged"
    if higher_is_better:
        return "improved" if right > left else "degraded"
    return "improved" if right < left else "degraded"


def _load_from_path(path: Path) -> MemoryRecord:
    """Load a MemoryRecord directly from a JSON file path (no directory scan)."""
    try:
        raw = path.read_text(encoding="utf-8")
        p: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON at '{path}': {exc}") from exc

    try:
        return MemoryRecord(
            record_id=str(p["record_id"]),
            created_at=str(p["created_at"]),
            project_path=str(p["project_path"]),
            project_name=str(p["project_name"]),
            rail=str(p["rail"]),
            command=str(p["command"]),
            status=str(p["status"]),
            generator=p.get("generator"),
            providers=list(p.get("providers", [])),
            control_level=str(p["control_level"]),
            read_only=bool(p.get("read_only", True)),
            applied=bool(p.get("applied", False)),
            findings_summary=dict(p.get("findings_summary", {})),
            remediation_summary=(
                dict(p["remediation_summary"])
                if p.get("remediation_summary") is not None
                else None
            ),
            strategic_options=list(p.get("strategic_options", [])),
            human_validated=bool(p.get("human_validated", False)),
            notes=p.get("notes"),
        )
    except KeyError as exc:
        raise ValueError(
            f"Malformed MemoryRecord at '{path}': missing field {exc}"
        ) from exc


def load_record_reference(memory_dir: Path, ref: str) -> MemoryRecord:
    """Load a MemoryRecord from a record_id string or a direct JSON file path.

    If ref resolves to an existing file, it is loaded directly.
    Otherwise ref is treated as a record_id and looked up under memory_dir.

    Raises FileNotFoundError or ValueError on failure.
    """
    candidate = Path(ref)
    if candidate.exists() and candidate.is_file():
        return _load_from_path(candidate)
    return load_record(memory_dir, ref)


def compare_records(left: MemoryRecord, right: MemoryRecord) -> MemoryCompareResult:
    """Compare two MemoryRecord snapshots and return a MemoryCompareResult.

    Fields compared:
    - status (ERROR < WARNING < OK — higher is better)
    - control_level (weak < partial < controlled — higher is better)
    - findings_summary: critical, important, manual (lower is better)
    - findings_summary: generated (informational — no trend judgment)
    - remediation_summary: phases_count if present in both (lower is better)
    """
    improved: list[MemoryCompareDelta] = []
    degraded: list[MemoryCompareDelta] = []
    unchanged: list[MemoryCompareDelta] = []
    incompatible_fields: list[MemoryCompareDelta] = []

    if left.project_name != right.project_name:
        return MemoryCompareResult(
            left_id=left.record_id,
            right_id=right.record_id,
            project_name=f"{left.project_name} vs {right.project_name}",
            compatible=False,
            synthesis="incompatible",
            incompatible_fields=[
                MemoryCompareDelta(
                    field="project_name",
                    left_value=left.project_name,
                    right_value=right.project_name,
                    trend="incompatible",
                )
            ],
        )

    def _categorize(delta: MemoryCompareDelta) -> None:
        if delta.trend == "improved":
            improved.append(delta)
        elif delta.trend == "degraded":
            degraded.append(delta)
        else:
            unchanged.append(delta)

    # status
    left_sr = _STATUS_RANK.get(left.status, -1)
    right_sr = _STATUS_RANK.get(right.status, -1)
    if left_sr < 0 or right_sr < 0:
        incompatible_fields.append(
            MemoryCompareDelta(
                field="status",
                left_value=left.status,
                right_value=right.status,
                trend="incompatible",
            )
        )
    else:
        _categorize(
            MemoryCompareDelta(
                field="status",
                left_value=left.status,
                right_value=right.status,
                trend=compute_trend(left_sr, right_sr, higher_is_better=True),
            )
        )

    # control_level
    left_cr = _CONTROL_RANK.get(left.control_level, -1)
    right_cr = _CONTROL_RANK.get(right.control_level, -1)
    if left_cr < 0 or right_cr < 0:
        incompatible_fields.append(
            MemoryCompareDelta(
                field="control_level",
                left_value=left.control_level,
                right_value=right.control_level,
                trend="incompatible",
            )
        )
    else:
        _categorize(
            MemoryCompareDelta(
                field="control_level",
                left_value=left.control_level,
                right_value=right.control_level,
                trend=compute_trend(left_cr, right_cr, higher_is_better=True),
            )
        )

    # findings: critical, important, manual (lower is better)
    for key in ("critical", "important", "manual"):
        lv = left.findings_summary.get(key, 0)
        rv = right.findings_summary.get(key, 0)
        _categorize(
            MemoryCompareDelta(
                field=key,
                left_value=str(lv),
                right_value=str(rv),
                trend=compute_trend(lv, rv, higher_is_better=False),
            )
        )

    # generated — informational only (no trend judgment)
    lg = left.findings_summary.get("generated", 0)
    rg = right.findings_summary.get("generated", 0)
    unchanged.append(
        MemoryCompareDelta(
            field="generated",
            left_value=str(lg),
            right_value=str(rg),
            trend="unchanged",
        )
    )

    # remediation phases_count (lower is better)
    left_phases = (
        left.remediation_summary.get("phases_count")
        if left.remediation_summary
        else None
    )
    right_phases = (
        right.remediation_summary.get("phases_count")
        if right.remediation_summary
        else None
    )
    if left_phases is not None and right_phases is not None:
        _categorize(
            MemoryCompareDelta(
                field="phases_count",
                left_value=str(left_phases),
                right_value=str(right_phases),
                trend=compute_trend(left_phases, right_phases, higher_is_better=False),
            )
        )

    if improved and degraded:
        synthesis = "mixed"
    elif improved:
        synthesis = "improved"
    elif degraded:
        synthesis = "degraded"
    else:
        synthesis = "unchanged"

    return MemoryCompareResult(
        left_id=left.record_id,
        right_id=right.record_id,
        project_name=left.project_name,
        compatible=True,
        synthesis=synthesis,
        improved=improved,
        degraded=degraded,
        unchanged=unchanged,
        incompatible_fields=incompatible_fields,
    )
