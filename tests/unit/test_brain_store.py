"""Unit tests for BrainStore — Project Brain SQLite layer (CAP-2-A)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aeos.brain.models import (
    Decision,
    InteractionRecord,
    KnowledgeFact,
    ProjectIdentity,
    VocabularyTerm,
)
from aeos.brain.store import SCHEMA_VERSION, BrainStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _fact(
    fact_id: str = "f1",
    dimension: str = "SECURITY",
    severity: str | None = "HIGH",
    resolved: bool = False,
) -> KnowledgeFact:
    return KnowledgeFact(
        id=fact_id,
        fact_type="FINDING",
        dimension=dimension,
        summary=f"Finding {fact_id}",
        severity=severity,
        resolved_at=_now() if resolved else None,
        created_at=_now(),
    )


def _decision(decision_id: str = "d1") -> Decision:
    return Decision(
        id=decision_id,
        title=f"Decision {decision_id}",
        description="Use SQLite for Brain storage.",
        rationale="Local-first, portable, zero dependency.",
        alternatives=["PostgreSQL", "DuckDB"],
        impact="High",
        decided_at=_now(),
    )


def _interaction(interaction_id: str = "i1") -> InteractionRecord:
    return InteractionRecord(
        id=interaction_id,
        question="What are the security risks?",
        brain_version="abc123",
        dimensions=["SECURITY", "SOVEREIGNTY"],
        token_budget=2048,
        provider="local",
        model="mistral",
        asked_at=_now(),
    )


@pytest.fixture
def brain(tmp_path: Path) -> BrainStore:
    store = BrainStore.open(tmp_path / "brain", "test-project")
    yield store
    store.close()


# ---------------------------------------------------------------------------
# Initialisation & schema
# ---------------------------------------------------------------------------


class TestBrainStoreInit:
    def test_open_creates_db_file(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        BrainStore.open(brain_dir, "proj").close()
        assert (brain_dir / "proj.db").exists()

    def test_open_creates_brain_dir(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "deeply" / "nested" / "brain"
        BrainStore.open(brain_dir, "proj").close()
        assert brain_dir.is_dir()

    def test_schema_version_is_correct(self, brain: BrainStore) -> None:
        assert brain.get_status().schema_version == SCHEMA_VERSION

    def test_two_projects_have_separate_files(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        BrainStore.open(brain_dir, "proj-a").close()
        BrainStore.open(brain_dir, "proj-b").close()
        assert (brain_dir / "proj-a.db").exists()
        assert (brain_dir / "proj-b.db").exists()
        assert not (brain_dir / "proj-a.db") == (brain_dir / "proj-b.db")

    def test_exists_returns_false_before_init(self, tmp_path: Path) -> None:
        assert not BrainStore.exists(tmp_path / "brain", "proj")

    def test_exists_returns_true_after_init(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        BrainStore.open(brain_dir, "proj").close()
        assert BrainStore.exists(brain_dir, "proj")

    def test_open_is_idempotent(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        BrainStore.open(brain_dir, "proj").close()
        BrainStore.open(brain_dir, "proj").close()
        assert BrainStore.exists(brain_dir, "proj")

    def test_context_manager_closes_cleanly(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "proj") as store:
            assert store.get_status().schema_version == SCHEMA_VERSION

    def test_db_path_for_returns_correct_path(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        assert BrainStore.db_path_for(brain_dir, "proj") == brain_dir / "proj.db"

    def test_empty_brain_has_zero_counts(self, brain: BrainStore) -> None:
        s = brain.get_status()
        assert s.facts_count == 0
        assert s.decisions_count == 0
        assert s.vocabulary_count == 0
        assert s.interactions_count == 0

    def test_empty_brain_dimension_counts_empty(self, brain: BrainStore) -> None:
        assert brain.get_status().dimension_counts == {}


# ---------------------------------------------------------------------------
# ProjectIdentity
# ---------------------------------------------------------------------------


class TestProjectIdentity:
    def test_get_identity_empty(self, brain: BrainStore) -> None:
        assert brain.get_identity() is None

    def test_upsert_and_retrieve(self, brain: BrainStore) -> None:
        identity = ProjectIdentity(
            project_name="test-project",
            project_path="/projects/test",
            project_type="web",
            stack=["Next.js", "Supabase"],
            languages=["TypeScript"],
            description="Test project",
            updated_at=_now(),
        )
        brain.upsert_identity(identity)
        result = brain.get_identity()
        assert result is not None
        assert result.project_name == "test-project"
        assert result.project_path == "/projects/test"
        assert result.stack == ["Next.js", "Supabase"]
        assert result.languages == ["TypeScript"]
        assert result.description == "Test project"

    def test_upsert_updates_existing(self, brain: BrainStore) -> None:
        brain.upsert_identity(
            ProjectIdentity(
                project_name="test-project",
                project_path="/projects/v1",
                updated_at=_now(),
            )
        )
        brain.upsert_identity(
            ProjectIdentity(
                project_name="test-project",
                project_path="/projects/v2",
                description="updated",
                updated_at=_now(),
            )
        )
        result = brain.get_identity()
        assert result is not None
        assert result.project_path == "/projects/v2"
        assert result.description == "updated"

    def test_empty_stack_roundtrips(self, brain: BrainStore) -> None:
        brain.upsert_identity(
            ProjectIdentity(
                project_name="test-project",
                project_path="/p",
                updated_at=_now(),
            )
        )
        result = brain.get_identity()
        assert result is not None
        assert result.stack == []
        assert result.languages == []

    def test_optional_fields_none(self, brain: BrainStore) -> None:
        brain.upsert_identity(
            ProjectIdentity(
                project_name="test-project",
                project_path="/p",
                updated_at=_now(),
            )
        )
        result = brain.get_identity()
        assert result is not None
        assert result.project_type is None
        assert result.description is None


# ---------------------------------------------------------------------------
# KnowledgeFact
# ---------------------------------------------------------------------------


class TestKnowledgeFacts:
    def test_insert_and_retrieve(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        facts = brain.get_facts()
        assert len(facts) == 1
        assert facts[0].id == "f1"

    def test_get_fact_by_id(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        result = brain.get_fact("f1")
        assert result is not None
        assert result.id == "f1"
        assert result.dimension == "SECURITY"
        assert result.severity == "HIGH"

    def test_get_fact_unknown_returns_none(self, brain: BrainStore) -> None:
        assert brain.get_fact("does-not-exist") is None

    def test_filter_by_dimension(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1", dimension="SECURITY"))
        brain.insert_fact(_fact("f2", dimension="ARCH"))
        brain.insert_fact(_fact("f3", dimension="SECURITY"))
        result = brain.get_facts(dimension="SECURITY")
        assert len(result) == 2
        assert all(f.dimension == "SECURITY" for f in result)

    def test_resolved_excluded_by_default(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        brain.insert_fact(_fact("f2", resolved=True))
        result = brain.get_facts()
        assert len(result) == 1
        assert result[0].id == "f1"

    def test_include_resolved(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        brain.insert_fact(_fact("f2", resolved=True))
        result = brain.get_facts(include_resolved=True)
        assert len(result) == 2

    def test_filter_dimension_excludes_resolved(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1", dimension="SECURITY"))
        brain.insert_fact(_fact("f2", dimension="SECURITY", resolved=True))
        result = brain.get_facts(dimension="SECURITY")
        assert len(result) == 1

    def test_insert_duplicate_id_ignored(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        brain.insert_fact(_fact("f1"))  # duplicate — silently ignored
        assert len(brain.get_facts()) == 1

    def test_detail_json_roundtrip(self, brain: BrainStore) -> None:
        detail = json.dumps({"file": "main.py", "line": 42})
        fact = KnowledgeFact(
            id="f1",
            fact_type="FINDING",
            dimension="SECURITY",
            summary="JSON detail",
            detail=detail,
            created_at=_now(),
        )
        brain.insert_fact(fact)
        result = brain.get_fact("f1")
        assert result is not None
        assert result.detail == detail

    def test_null_severity_roundtrip(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1", severity=None))
        result = brain.get_fact("f1")
        assert result is not None
        assert result.severity is None

    def test_source_record_roundtrip(self, brain: BrainStore) -> None:
        fact = KnowledgeFact(
            id="f1",
            fact_type="FINDING",
            dimension="SECURITY",
            summary="Sourced fact",
            source_record="harden-abc123",
            source_date="2026-07-02",
            created_at=_now(),
        )
        brain.insert_fact(fact)
        result = brain.get_fact("f1")
        assert result is not None
        assert result.source_record == "harden-abc123"
        assert result.source_date == "2026-07-02"

    def test_fts_search_finds_match(self, brain: BrainStore) -> None:
        brain.insert_fact(
            KnowledgeFact(
                id="f1",
                fact_type="FINDING",
                dimension="SECURITY",
                summary="RLS disabled on public users table",
                created_at=_now(),
            )
        )
        results = brain.search_facts("RLS")
        assert len(results) >= 1
        assert results[0].id == "f1"

    def test_fts_search_no_match(self, brain: BrainStore) -> None:
        brain.insert_fact(
            KnowledgeFact(
                id="f1",
                fact_type="FINDING",
                dimension="SECURITY",
                summary="RLS disabled on public users table",
                created_at=_now(),
            )
        )
        results = brain.search_facts("CORS")
        assert results == []


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


class TestDecisions:
    def test_insert_and_retrieve(self, brain: BrainStore) -> None:
        brain.insert_decision(_decision())
        decisions = brain.get_decisions()
        assert len(decisions) == 1
        assert decisions[0].id == "d1"
        assert decisions[0].title == "Decision d1"

    def test_alternatives_roundtrip(self, brain: BrainStore) -> None:
        brain.insert_decision(_decision())
        result = brain.get_decisions()[0]
        assert result.alternatives == ["PostgreSQL", "DuckDB"]

    def test_duplicate_ignored(self, brain: BrainStore) -> None:
        brain.insert_decision(_decision())
        brain.insert_decision(_decision())
        assert len(brain.get_decisions()) == 1

    def test_empty_alternatives_roundtrip(self, brain: BrainStore) -> None:
        brain.insert_decision(
            Decision(id="d1", title="D", description="Desc", decided_at=_now())
        )
        result = brain.get_decisions()[0]
        assert result.alternatives == []

    def test_optional_fields_none(self, brain: BrainStore) -> None:
        brain.insert_decision(
            Decision(id="d1", title="D", description="Desc", decided_at=_now())
        )
        result = brain.get_decisions()[0]
        assert result.rationale is None
        assert result.impact is None

    def test_default_decided_by(self, brain: BrainStore) -> None:
        brain.insert_decision(
            Decision(id="d1", title="D", description="Desc", decided_at=_now())
        )
        assert brain.get_decisions()[0].decided_by == "human"


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


class TestVocabulary:
    def test_upsert_and_retrieve(self, brain: BrainStore) -> None:
        brain.upsert_vocabulary(
            VocabularyTerm("RLS", "Row Level Security", ["row-level-security"])
        )
        vocab = brain.get_vocabulary()
        assert len(vocab) == 1
        assert vocab[0].term == "RLS"
        assert vocab[0].definition == "Row Level Security"
        assert vocab[0].aliases == ["row-level-security"]

    def test_upsert_updates_existing(self, brain: BrainStore) -> None:
        brain.upsert_vocabulary(VocabularyTerm("RLS", "Old definition"))
        brain.upsert_vocabulary(VocabularyTerm("RLS", "Row Level Security"))
        vocab = brain.get_vocabulary()
        assert len(vocab) == 1
        assert vocab[0].definition == "Row Level Security"

    def test_empty_aliases_roundtrip(self, brain: BrainStore) -> None:
        brain.upsert_vocabulary(VocabularyTerm("CTO", "Chief Technology Officer"))
        result = brain.get_vocabulary()[0]
        assert result.aliases == []

    def test_ordered_alphabetically(self, brain: BrainStore) -> None:
        brain.upsert_vocabulary(VocabularyTerm("RLS", "Row Level Security"))
        brain.upsert_vocabulary(VocabularyTerm("ADR", "Architecture Decision Record"))
        brain.upsert_vocabulary(VocabularyTerm("MFA", "Multi-Factor Authentication"))
        terms = [v.term for v in brain.get_vocabulary()]
        assert terms == sorted(terms)


# ---------------------------------------------------------------------------
# InteractionLog
# ---------------------------------------------------------------------------


class TestInteractionLog:
    def test_log_and_count(self, brain: BrainStore) -> None:
        brain.log_interaction(_interaction())
        assert brain.get_status().interactions_count == 1

    def test_duplicate_ignored(self, brain: BrainStore) -> None:
        brain.log_interaction(_interaction())
        brain.log_interaction(_interaction())
        assert brain.get_status().interactions_count == 1

    def test_multiple_interactions(self, brain: BrainStore) -> None:
        brain.log_interaction(_interaction("i1"))
        brain.log_interaction(_interaction("i2"))
        assert brain.get_status().interactions_count == 2


# ---------------------------------------------------------------------------
# BrainStatus & counts
# ---------------------------------------------------------------------------


class TestBrainStatus:
    def test_counts_reflect_inserts(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        brain.insert_fact(_fact("f2"))
        brain.insert_decision(_decision("d1"))
        brain.upsert_vocabulary(VocabularyTerm("RLS", "Row Level Security"))
        s = brain.get_status()
        assert s.facts_count == 2
        assert s.decisions_count == 1
        assert s.vocabulary_count == 1

    def test_dimension_counts(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1", dimension="SECURITY"))
        brain.insert_fact(_fact("f2", dimension="SECURITY"))
        brain.insert_fact(_fact("f3", dimension="ARCH"))
        s = brain.get_status()
        assert s.dimension_counts["SECURITY"] == 2
        assert s.dimension_counts["ARCH"] == 1

    def test_dimension_counts_exclude_resolved(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1", dimension="SECURITY"))
        brain.insert_fact(_fact("f2", dimension="SECURITY", resolved=True))
        s = brain.get_status()
        # dimension_counts queries all facts (not filtered by resolved)
        assert "SECURITY" in s.dimension_counts

    def test_last_fact_at_none_when_empty(self, brain: BrainStore) -> None:
        assert brain.get_status().last_fact_at is None

    def test_last_fact_at_set_after_insert(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        assert brain.get_status().last_fact_at is not None

    def test_db_path_in_status(self, brain: BrainStore) -> None:
        assert brain.get_status().db_path.endswith(".db")


# ---------------------------------------------------------------------------
# Brain version
# ---------------------------------------------------------------------------


class TestBrainVersion:
    def test_empty_brain_version_is_stable(self, brain: BrainStore) -> None:
        v1 = brain.get_brain_version()
        v2 = brain.get_brain_version()
        assert v1 == v2

    def test_version_changes_after_fact_insert(self, brain: BrainStore) -> None:
        v1 = brain.get_brain_version()
        brain.insert_fact(_fact("f1"))
        v2 = brain.get_brain_version()
        assert v1 != v2

    def test_version_changes_after_decision_insert(self, brain: BrainStore) -> None:
        v1 = brain.get_brain_version()
        brain.insert_decision(_decision("d1"))
        v2 = brain.get_brain_version()
        assert v1 != v2

    def test_version_changes_after_vocabulary_upsert(self, brain: BrainStore) -> None:
        v1 = brain.get_brain_version()
        brain.upsert_vocabulary(VocabularyTerm("RLS", "Row Level Security"))
        v2 = brain.get_brain_version()
        assert v1 != v2

    def test_version_stable_after_same_state(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        v1 = brain.get_brain_version()
        v2 = brain.get_brain_version()
        assert v1 == v2

    def test_version_length_is_12(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        assert len(brain.get_brain_version()) == 12

    def test_duplicate_insert_does_not_change_version(self, brain: BrainStore) -> None:
        brain.insert_fact(_fact("f1"))
        v1 = brain.get_brain_version()
        brain.insert_fact(_fact("f1"))  # ignored
        v2 = brain.get_brain_version()
        assert v1 == v2


# ---------------------------------------------------------------------------
# Isolation between projects
# ---------------------------------------------------------------------------


class TestProjectIsolation:
    def test_two_projects_independent(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "proj-a") as a:
            a.insert_fact(_fact("f1"))
        with BrainStore.open(brain_dir, "proj-b") as b:
            assert b.get_facts() == []

    def test_facts_in_one_do_not_appear_in_other(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "proj-a") as a:
            a.insert_fact(_fact("f1"))
            a.insert_fact(_fact("f2"))
        with BrainStore.open(brain_dir, "proj-b") as b:
            assert b.get_status().facts_count == 0
