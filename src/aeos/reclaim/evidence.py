"""
AEOS Recovery Evidence Engine — associates expected, confirmed and missing evidence
to each recovery stage.

Read-only. No filesystem scan. No network. No secret reads. No MemoryRecord writes.
Evidence status is computed from caller-declared confirmed indices — never
auto-detected.
read_only: true · applied: false
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aeos.reclaim.stages import get_recovery_stages, get_stage_by_id


@dataclass
class EvidenceItem:
    """One expected evidence item for a recovery stage."""

    index: int
    label: str
    status: str  # "confirmed" | "pending"


@dataclass
class EvidenceReport:
    """Evidence status for one recovery stage. Read-only."""

    stage_id: str
    stage_name: str
    read_only: bool
    applied: bool
    total_expected: int
    total_confirmed: int
    total_pending: int
    evidence_status: str  # "verified" | "partial" | "unverified"
    validation_blocked_reason: str | None
    items: list[EvidenceItem] = field(default_factory=list)


def validate_confirmed_indices(stage_id: str, indices: list[int]) -> list[int]:
    """Return indices that are out of bounds for the stage's expected_evidence list.

    Returns an empty list when stage_id is unknown (caller handles that separately).
    Negative indices are always out of bounds.
    """
    stage = get_stage_by_id(stage_id)
    if stage is None:
        return []
    n = len(stage.expected_evidence)
    return [i for i in indices if i < 0 or i >= n]


def build_evidence_report(
    stage_id: str,
    confirmed_indices: list[int] | None = None,
) -> EvidenceReport | None:
    """Build the evidence report for one stage.

    Returns None if stage_id is not found in the registry.
    confirmed_indices is the caller-declared subset of expected_evidence indices.
    Read-only. No filesystem. No network. No MemoryRecord writes.
    """
    stage = get_stage_by_id(stage_id)
    if stage is None:
        return None

    resolved = confirmed_indices if confirmed_indices is not None else []
    confirmed_set = set(resolved)

    items = [
        EvidenceItem(
            index=i,
            label=label,
            status="confirmed" if i in confirmed_set else "pending",
        )
        for i, label in enumerate(stage.expected_evidence)
    ]

    total_expected = len(items)
    total_confirmed = sum(1 for item in items if item.status == "confirmed")
    total_pending = total_expected - total_confirmed

    if total_confirmed == total_expected:
        evidence_status = "verified"
        validation_blocked_reason: str | None = None
    elif total_confirmed > 0:
        evidence_status = "partial"
        missing = [item.label for item in items if item.status == "pending"]
        n = len(missing)
        noun = "item" if n == 1 else "items"
        validation_blocked_reason = f"{n} evidence {noun} missing: {'; '.join(missing)}"
    else:
        evidence_status = "unverified"
        validation_blocked_reason = "No evidence confirmed for this stage."

    return EvidenceReport(
        stage_id=stage.id,
        stage_name=stage.name,
        read_only=True,
        applied=False,
        total_expected=total_expected,
        total_confirmed=total_confirmed,
        total_pending=total_pending,
        evidence_status=evidence_status,
        validation_blocked_reason=validation_blocked_reason,
        items=items,
    )


def build_evidence_summary(
    confirmed_by_stage: dict[str, list[int]] | None = None,
) -> list[EvidenceReport]:
    """Build evidence reports for all 10 stages. Read-only."""
    confirmed = confirmed_by_stage or {}
    reports = []
    for stage in get_recovery_stages():
        stage_confirmed = confirmed.get(stage.id, [])
        report = build_evidence_report(stage.id, stage_confirmed)
        if report is not None:
            reports.append(report)
    return reports


def evidence_report_to_dict(report: EvidenceReport) -> dict[str, object]:
    """Serialize an EvidenceReport to a JSON-compatible dict."""
    return {
        "stage_id": report.stage_id,
        "stage_name": report.stage_name,
        "read_only": report.read_only,
        "applied": report.applied,
        "total_expected": report.total_expected,
        "total_confirmed": report.total_confirmed,
        "total_pending": report.total_pending,
        "evidence_status": report.evidence_status,
        "validation_blocked_reason": report.validation_blocked_reason,
        "items": [
            {
                "index": item.index,
                "label": item.label,
                "status": item.status,
            }
            for item in report.items
        ],
    }
