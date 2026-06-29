"""
AEOS Memory — MemoryRecord data model.

A MemoryRecord is a safe, serializable snapshot of a single AEOS audit run.
It contains only counts, status labels, and metadata — never secret values.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemoryRecordSummary:
    """Lightweight view of a MemoryRecord for list display."""

    record_id: str
    project_name: str
    created_at: str
    command: str
    status: str
    generator: str | None
    provider_count: int


@dataclass
class MemoryListResult:
    """Result of list_records() — records found plus paths that could not be parsed."""

    records: list[MemoryRecordSummary] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)


@dataclass
class MemoryRecord:
    record_id: str
    created_at: str  # ISO 8601
    project_path: str  # absolute path at time of audit
    project_name: str  # basename of project_path
    rail: str  # "reclaim" | "security" | …
    command: str  # "reclaim harden"
    status: str  # "OK" | "WARNING" | "ERROR"
    generator: str | None  # "lovable" | "bolt" | None
    providers: list[str]  # ["supabase"]
    control_level: str  # "controlled" | "partial" | "weak"
    read_only: bool  # always True — enforced by caller
    applied: bool  # always False — enforced by caller
    findings_summary: dict[str, int]  # {critical, important, manual, generated}
    remediation_summary: dict[str, int] | None  # phases, counts — None if no plan
    strategic_options: list[str]  # exit option labels (truncated to 80 chars)
    human_validated: bool = False
    notes: str | None = None
