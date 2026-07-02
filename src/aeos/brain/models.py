"""
AEOS Brain — data models for the Project Brain.

All objects are plain dataclasses — no external dependencies, no AI coupling.
The Brain survives model replacement, runtime replacement, and framework change.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectIdentity:
    """Stable identity of a project tracked by AEOS."""

    project_name: str
    project_path: str
    project_type: str | None = None
    stack: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    description: str | None = None
    updated_at: str = ""


@dataclass
class KnowledgeFact:
    """A structured, sourced fact about a project.

    fact_type: FINDING | SOVEREIGNTY | ARCHITECTURE | RISK | RECOVERY | TIMELINE
    dimension: SECURITY | ARCH | SOVEREIGNTY | RECOVERY | DOMAIN | IDENTITY
    severity:  CRITICAL | HIGH | MEDIUM | LOW | INFO  (nullable)
    """

    id: str
    fact_type: str
    dimension: str
    summary: str
    severity: str | None = None
    detail: str | None = None
    source_record: str | None = None
    source_date: str | None = None
    resolved_at: str | None = None
    created_at: str = ""


@dataclass
class Decision:
    """An architecture or engineering decision recorded in the Brain."""

    id: str
    title: str
    description: str
    rationale: str | None = None
    alternatives: list[str] = field(default_factory=list)
    impact: str | None = None
    decided_at: str = ""
    decided_by: str = "human"


@dataclass
class VocabularyTerm:
    """A domain vocabulary entry."""

    term: str
    definition: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class InteractionRecord:
    """An immutable log entry for one AI interaction against the Brain."""

    id: str
    question: str
    brain_version: str
    dimensions: list[str]
    token_budget: int | None = None
    provider: str | None = None
    model: str | None = None
    response_summary: str | None = None
    asked_at: str = ""


@dataclass
class BrainStatus:
    """Snapshot of a Brain's current state — returned by BrainStore.get_status()."""

    project_name: str
    db_path: str
    schema_version: int
    facts_count: int
    decisions_count: int
    vocabulary_count: int
    interactions_count: int
    last_fact_at: str | None
    dimension_counts: dict[str, int]
    brain_version: str
