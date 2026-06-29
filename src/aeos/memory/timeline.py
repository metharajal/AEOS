"""
AEOS Memory Timeline — chronological view of MemoryRecords for a single project.

Read-only. No network. No AI. No secrets. No .env.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aeos.memory.compare import _STATUS_RANK, compute_trend
from aeos.memory.models import MemoryRecord
from aeos.memory.store import load_record


@dataclass
class MemoryTimelineEntry:
    """One row in the project timeline — lightweight view of a single MemoryRecord."""

    record_id: str
    created_at: str
    status: str
    control_level: str
    critical: int
    important: int
    manual: int
    generated: int


@dataclass
class MemoryTimelineSynthesis:
    """Global synthesis across all records in the timeline."""

    record_count: int
    first_status: str
    last_status: str
    overall: str  # "improved"|"degraded"|"unchanged"|"mixed"|"insufficient_data"
    critical_trend: str  # "improved"|"degraded"|"unchanged"|"insufficient_data"
    important_trend: str
    manual_trend: str
    generated_trend: str


@dataclass
class MemoryTimelineResult:
    """Full timeline result for a project."""

    project_name: str
    memory_dir: str
    entries: list[MemoryTimelineEntry] = field(default_factory=list)
    synthesis: MemoryTimelineSynthesis | None = None


def load_project_records(memory_dir: Path, project_name: str) -> list[MemoryRecord]:
    """Load all MemoryRecords for project_name, sorted chronologically.

    Returns an empty list if the project directory does not exist or has no records.
    Skips unparseable files (same as list_records).
    Raises FileNotFoundError if memory_dir itself does not exist.
    """
    if not memory_dir.exists():
        raise FileNotFoundError(f"Memory directory not found: {memory_dir}")

    project_dir = memory_dir / project_name
    if not project_dir.exists() or not project_dir.is_dir():
        return []

    records: list[MemoryRecord] = []
    for json_path in sorted(project_dir.glob("*.json")):
        try:
            record = load_record(memory_dir, json_path.stem)
            records.append(record)
        except (FileNotFoundError, ValueError):
            continue

    records.sort(key=lambda r: r.created_at)
    return records


def _numeric_trend(first: int, last: int, higher_is_better: bool) -> str:
    return compute_trend(first, last, higher_is_better)


def compute_timeline_synthesis(records: list[MemoryRecord]) -> MemoryTimelineSynthesis:
    """Compute the global synthesis across all records in the timeline."""
    count = len(records)

    if count < 2:
        first = records[0] if records else None
        return MemoryTimelineSynthesis(
            record_count=count,
            first_status=first.status if first else "",
            last_status=first.status if first else "",
            overall="insufficient_data",
            critical_trend="insufficient_data",
            important_trend="insufficient_data",
            manual_trend="insufficient_data",
            generated_trend="insufficient_data",
        )

    first = records[0]
    last = records[-1]

    # Status trend
    first_sr = _STATUS_RANK.get(first.status, -1)
    last_sr = _STATUS_RANK.get(last.status, -1)
    status_trend = (
        compute_trend(first_sr, last_sr, higher_is_better=True)
        if first_sr >= 0 and last_sr >= 0
        else "unchanged"
    )

    # Findings trends (lower is better for critical/important/manual)
    critical_trend = _numeric_trend(
        first.findings_summary.get("critical", 0),
        last.findings_summary.get("critical", 0),
        higher_is_better=False,
    )
    important_trend = _numeric_trend(
        first.findings_summary.get("important", 0),
        last.findings_summary.get("important", 0),
        higher_is_better=False,
    )
    manual_trend = _numeric_trend(
        first.findings_summary.get("manual", 0),
        last.findings_summary.get("manual", 0),
        higher_is_better=False,
    )
    generated_trend = _numeric_trend(
        first.findings_summary.get("generated", 0),
        last.findings_summary.get("generated", 0),
        higher_is_better=False,
    )

    # Overall = status trend as primary signal
    overall = status_trend

    return MemoryTimelineSynthesis(
        record_count=count,
        first_status=first.status,
        last_status=last.status,
        overall=overall,
        critical_trend=critical_trend,
        important_trend=important_trend,
        manual_trend=manual_trend,
        generated_trend=generated_trend,
    )


def build_timeline(records: list[MemoryRecord]) -> MemoryTimelineResult:
    """Build a MemoryTimelineResult from a list of records (already sorted)."""
    project_name = records[0].project_name if records else ""
    entries = [
        MemoryTimelineEntry(
            record_id=r.record_id,
            created_at=r.created_at,
            status=r.status,
            control_level=r.control_level,
            critical=r.findings_summary.get("critical", 0),
            important=r.findings_summary.get("important", 0),
            manual=r.findings_summary.get("manual", 0),
            generated=r.findings_summary.get("generated", 0),
        )
        for r in records
    ]
    synthesis = compute_timeline_synthesis(records) if records else None
    return MemoryTimelineResult(
        project_name=project_name,
        memory_dir="",
        entries=entries,
        synthesis=synthesis,
    )


def timeline_to_dict(result: MemoryTimelineResult) -> dict[str, object]:
    """Serialize a MemoryTimelineResult to a JSON-compatible dict."""
    syn = result.synthesis
    return {
        "project_name": result.project_name,
        "memory_dir": result.memory_dir,
        "record_count": len(result.entries),
        "entries": [
            {
                "record_id": e.record_id,
                "created_at": e.created_at,
                "status": e.status,
                "control_level": e.control_level,
                "critical": e.critical,
                "important": e.important,
                "manual": e.manual,
                "generated": e.generated,
            }
            for e in result.entries
        ],
        "synthesis": {
            "record_count": syn.record_count,
            "first_status": syn.first_status,
            "last_status": syn.last_status,
            "overall": syn.overall,
            "critical_trend": syn.critical_trend,
            "important_trend": syn.important_trend,
            "manual_trend": syn.manual_trend,
            "generated_trend": syn.generated_trend,
        }
        if syn
        else None,
    }
