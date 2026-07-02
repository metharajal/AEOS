"""
AEOS Brain Extractor — transforms MemoryRecords into KnowledgeFacts.

Pure extraction pipeline: MemoryRecord → list[KnowledgeFact] → BrainStore.
No AI, no network, no provider, no PromptBuilder.
Idempotent: deterministic IDs + INSERT OR IGNORE → safe to run twice.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aeos.brain.models import KnowledgeFact, ProjectIdentity
from aeos.brain.store import BrainStore
from aeos.memory.models import MemoryRecord
from aeos.memory.store import _looks_like_secret_value, load_record

# Maps record status to fact severity.
_SEVERITY_FROM_STATUS: dict[str, str] = {
    "OK": "INFO",
    "WARNING": "MEDIUM",
    "CRITICAL": "HIGH",
    "ERROR": "HIGH",
    "PARTIAL": "MEDIUM",
}

# Maps lower-case control_level to severity.
_CONTROL_SEVERITY: dict[str, str] = {
    "low": "HIGH",
    "partial": "MEDIUM",
    "controlled": "INFO",
}

# Maps lower-case control_level to human-readable summary.
_CONTROL_SUMMARIES: dict[str, str] = {
    "low": "Control level: low — sovereignty at risk",
    "partial": "Control level: partial",
    "controlled": "Control level: controlled",
}


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


@dataclass
class ExtractionResult:
    records_processed: int
    facts_extracted: int
    facts_inserted: int


class BrainExtractor:
    def __init__(self, brain: BrainStore) -> None:
        self._brain = brain

    def extract_from_record(self, record: MemoryRecord) -> list[KnowledgeFact]:
        """Pure extraction — no I/O. Same record always yields the same fact IDs."""
        facts: list[KnowledgeFact] = []

        # Timeline fact: always produced for every record.
        facts.append(_make_timeline_fact(record))

        # Rail-specific extraction.
        if record.rail == "reclaim":
            facts.extend(_extract_reclaim_facts(record))

        # Post-filter: defence-in-depth credential check on assembled facts.
        return [f for f in facts if _is_safe(f)]

    def build(self, project_name: str, memory_dir: Path) -> ExtractionResult:
        """Scan memory_dir/<project_name>/ and populate the Brain. Idempotent.

        Raises:
            FileNotFoundError: if memory_dir/<project_name>/ does not exist.
        """
        project_memory_dir = memory_dir / project_name
        if not project_memory_dir.exists():
            raise FileNotFoundError(
                f"Memory directory not found for project '{project_name}': "
                f"{project_memory_dir}"
            )

        json_files = sorted(project_memory_dir.glob("*.json"))

        records: list[MemoryRecord] = []
        for json_path in json_files:
            try:
                record = load_record(memory_dir, json_path.stem)
                records.append(record)
            except (FileNotFoundError, ValueError):
                continue

        facts_before = self._brain.get_status().facts_count
        all_facts: list[KnowledgeFact] = []

        for record in records:
            extracted = self.extract_from_record(record)
            all_facts.extend(extracted)
            for fact in extracted:
                self._brain.insert_fact(fact)

        # Upsert ProjectIdentity from the most recently created record.
        if records:
            most_recent = max(records, key=lambda r: r.created_at)
            self._brain.upsert_identity(_make_identity(project_name, most_recent))

        facts_after = self._brain.get_status().facts_count

        return ExtractionResult(
            records_processed=len(records),
            facts_extracted=len(all_facts),
            facts_inserted=facts_after - facts_before,
        )


# ---------------------------------------------------------------------------
# Internal helpers — not part of the public API
# ---------------------------------------------------------------------------


def _make_timeline_fact(record: MemoryRecord) -> KnowledgeFact:
    severity = _SEVERITY_FROM_STATUS.get(record.status.upper(), "INFO")

    if record.applied and record.human_validated:
        summary = f'"{record.command}" — human confirmed'
    else:
        summary = f'"{record.command}" completed — status: {record.status}'

    detail = json.dumps(
        {
            "rail": record.rail,
            "command": record.command,
            "status": record.status,
            "applied": record.applied,
            "human_validated": record.human_validated,
        }
    )
    return KnowledgeFact(
        id=f"{record.record_id}::timeline",
        fact_type="TIMELINE",
        dimension="TIMELINE",
        severity=severity,
        summary=summary,
        detail=detail,
        source_record=record.record_id,
        source_date=record.created_at,
        created_at=_now_iso(),
    )


def _extract_reclaim_facts(record: MemoryRecord) -> list[KnowledgeFact]:
    facts: list[KnowledgeFact] = []
    rid = record.record_id
    s = record.findings_summary
    src_date = record.created_at
    cmd = record.command

    critical = s.get("critical", 0)
    if critical > 0:
        facts.append(
            KnowledgeFact(
                id=f"{rid}::critical",
                fact_type="FINDING",
                dimension="SECURITY",
                severity="CRITICAL",
                summary=f"{critical} critical security findings detected",
                detail=json.dumps({"count": critical, "command": cmd}),
                source_record=rid,
                source_date=src_date,
                created_at=_now_iso(),
            )
        )

    important = s.get("important", 0)
    if important > 0:
        facts.append(
            KnowledgeFact(
                id=f"{rid}::important",
                fact_type="FINDING",
                dimension="SECURITY",
                severity="HIGH",
                summary=f"{important} important security findings detected",
                detail=json.dumps({"count": important, "command": cmd}),
                source_record=rid,
                source_date=src_date,
                created_at=_now_iso(),
            )
        )

    manual = s.get("manual", 0)
    if manual > 0:
        facts.append(
            KnowledgeFact(
                id=f"{rid}::manual",
                fact_type="FINDING",
                dimension="RECOVERY",
                severity="MEDIUM",
                summary=f"{manual} manual remediation actions required",
                detail=json.dumps({"count": manual, "command": cmd}),
                source_record=rid,
                source_date=src_date,
                created_at=_now_iso(),
            )
        )

    rem = record.remediation_summary
    if rem is not None:
        phases = rem.get("phases_count", 0)
        immediate = rem.get("immediate", 0)
        if phases > 0 or immediate > 0:
            rem_summary = (
                f"Remediation plan: {phases} phases,"
                f" {immediate} immediate actions"
            )
            facts.append(
                KnowledgeFact(
                    id=f"{rid}::remediation",
                    fact_type="FINDING",
                    dimension="RECOVERY",
                    severity="INFO",
                    summary=rem_summary,
                    detail=json.dumps(rem),
                    source_record=rid,
                    source_date=src_date,
                    created_at=_now_iso(),
                )
            )

    if record.control_level:
        level = record.control_level.lower()
        ctrl_severity = _CONTROL_SEVERITY.get(level, "INFO")
        ctrl_summary = _CONTROL_SUMMARIES.get(
            level, f"Control level: {record.control_level}"
        )
        facts.append(
            KnowledgeFact(
                id=f"{rid}::control",
                fact_type="SOVEREIGNTY",
                dimension="SOVEREIGNTY",
                severity=ctrl_severity,
                summary=ctrl_summary,
                detail=json.dumps({"control_level": record.control_level}),
                source_record=rid,
                source_date=src_date,
                created_at=_now_iso(),
            )
        )

    for provider in record.providers:
        if _looks_like_secret_value(provider):
            continue
        facts.append(
            KnowledgeFact(
                id=f"{rid}::provider::{provider}",
                fact_type="ARCH",
                dimension="ARCH",
                severity="INFO",
                summary=f"Provider detected: {provider}",
                detail=json.dumps({"provider": provider}),
                source_record=rid,
                source_date=src_date,
                created_at=_now_iso(),
            )
        )

    if record.generator is not None and not _looks_like_secret_value(record.generator):
        facts.append(
            KnowledgeFact(
                id=f"{rid}::generator",
                fact_type="ARCH",
                dimension="ARCH",
                severity="INFO",
                summary=f"Generator detected: {record.generator}",
                detail=json.dumps({"generator": record.generator}),
                source_record=rid,
                source_date=src_date,
                created_at=_now_iso(),
            )
        )

    for idx, option in enumerate(record.strategic_options):
        if _looks_like_secret_value(option):
            continue
        facts.append(
            KnowledgeFact(
                id=f"{rid}::option::{idx}",
                fact_type="SOVEREIGNTY",
                dimension="SOVEREIGNTY",
                severity="INFO",
                summary=f"Exit option: {option}",
                source_record=rid,
                source_date=src_date,
                created_at=_now_iso(),
            )
        )

    return facts


def _normalize_path(project_path: str) -> str:
    """Return path relative to home (~/) when possible, otherwise just the basename."""
    p = Path(project_path)
    try:
        relative = p.relative_to(Path.home())
        return f"~/{relative}"
    except ValueError:
        return p.name


def _make_identity(project_name: str, record: MemoryRecord) -> ProjectIdentity:
    return ProjectIdentity(
        project_name=project_name,
        project_path=_normalize_path(record.project_path),
        updated_at=_now_iso(),
    )


def _is_safe(fact: KnowledgeFact) -> bool:
    """Post-filter: return False if the assembled fact fields contain a credential."""
    if _looks_like_secret_value(fact.summary):
        return False
    if _looks_like_secret_value(fact.detail or ""):
        return False
    return True
