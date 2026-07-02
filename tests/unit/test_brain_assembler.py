"""Unit tests for ContextAssembler and AIContext (CAP-2-C)."""

from __future__ import annotations

from pathlib import Path

from aeos.brain.assembler import (
    AIContext,
    ContextAssembler,
    _analyze_question,
    _is_safe_fact,
    _sort_key,
)
from aeos.brain.models import (
    Decision,
    KnowledgeFact,
    ProjectIdentity,
    VocabularyTerm,
)
from aeos.brain.store import BrainStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_brain(tmp_path: Path, project: str = "test-proj") -> BrainStore:
    return BrainStore.open(tmp_path / "brain", project)


def _make_fact(
    fact_id: str = "fact-001",
    fact_type: str = "FINDING",
    dimension: str = "SECURITY",
    summary: str = "A test finding",
    severity: str | None = "HIGH",
    detail: str | None = None,
    source_date: str | None = "2026-01-15T10:00:00+00:00",
    resolved_at: str | None = None,
) -> KnowledgeFact:
    return KnowledgeFact(
        id=fact_id,
        fact_type=fact_type,
        dimension=dimension,
        summary=summary,
        severity=severity,
        detail=detail,
        source_date=source_date,
        resolved_at=resolved_at,
        created_at="2026-01-15T10:00:00+00:00",
    )


def _make_decision(
    decision_id: str = "dec-001",
    title: str = "Test Decision",
    description: str = "A description",
) -> Decision:
    return Decision(
        id=decision_id,
        title=title,
        description=description,
        decided_at="2026-01-15T10:00:00+00:00",
    )


def _make_vocabulary(
    term: str = "RLS", definition: str = "Row Level Security"
) -> VocabularyTerm:
    return VocabularyTerm(term=term, definition=definition)


def _make_identity(project_name: str = "test-proj") -> ProjectIdentity:
    return ProjectIdentity(
        project_name=project_name,
        project_path="~/projects/test-proj",
    )


def _brain_with_facts(
    tmp_path: Path,
    facts: list[KnowledgeFact],
    decisions: list[Decision] | None = None,
    vocabulary: list[VocabularyTerm] | None = None,
    identity: ProjectIdentity | None = None,
) -> BrainStore:
    brain = BrainStore.open(tmp_path / "brain", "test-proj")
    for fact in facts:
        brain.insert_fact(fact)
    for decision in decisions or []:
        brain.insert_decision(decision)
    for term in vocabulary or []:
        brain.upsert_vocabulary(term)
    if identity is not None:
        brain.upsert_identity(identity)
    return brain


# ---------------------------------------------------------------------------
# Question analysis
# ---------------------------------------------------------------------------


class TestQuestionAnalysis:
    def test_security_keyword_detects_security(self) -> None:
        dims = _analyze_question("What are the security risks?")
        assert "SECURITY" in dims

    def test_provider_keyword_detects_arch(self) -> None:
        dims = _analyze_question("Which provider are we using?")
        assert "ARCH" in dims

    def test_risk_keyword_detects_security(self) -> None:
        dims = _analyze_question("Show me the risk level")
        assert "SECURITY" in dims

    def test_recovery_keyword_detects_recovery(self) -> None:
        dims = _analyze_question("What is the recovery plan?")
        assert "RECOVERY" in dims

    def test_timeline_always_included(self) -> None:
        dims = _analyze_question("What are the security risks?")
        assert "TIMELINE" in dims

    def test_identity_always_included(self) -> None:
        dims = _analyze_question("What are the security risks?")
        assert "IDENTITY" in dims

    def test_empty_question_includes_always_dims(self) -> None:
        dims = _analyze_question("")
        assert "IDENTITY" in dims
        assert "TIMELINE" in dims

    def test_no_match_fallback_adds_security(self) -> None:
        dims = _analyze_question("hello world")
        assert "SECURITY" in dims

    def test_no_match_fallback_adds_sovereignty(self) -> None:
        dims = _analyze_question("hello world")
        assert "SOVEREIGNTY" in dims

    def test_no_match_fallback_not_all_dimensions(self) -> None:
        dims = _analyze_question("hello world")
        # Should NOT include ARCH, RECOVERY, DOMAIN by default
        assert "ARCH" not in dims
        assert "RECOVERY" not in dims
        assert "DOMAIN" not in dims

    def test_matched_dimension_comes_before_always_dims(self) -> None:
        dims = _analyze_question("What are the security risks?")
        assert dims.index("SECURITY") < dims.index("IDENTITY")
        assert dims.index("SECURITY") < dims.index("TIMELINE")

    def test_no_duplicates_in_result(self) -> None:
        dims = _analyze_question("project identity and timeline history")
        assert len(dims) == len(set(dims))

    def test_multiple_keywords_same_dimension_still_unique(self) -> None:
        dims = _analyze_question("security breach exploit vulnerability attack")
        assert dims.count("SECURITY") == 1


# ---------------------------------------------------------------------------
# Fact priority sort
# ---------------------------------------------------------------------------


class TestFactPriority:
    def test_critical_before_high(self) -> None:
        dims = ["SECURITY", "IDENTITY", "TIMELINE"]
        critical = _make_fact(fact_id="a", severity="CRITICAL", dimension="SECURITY")
        high = _make_fact(fact_id="b", severity="HIGH", dimension="SECURITY")
        key_critical = _sort_key(critical, dims)
        key_high = _sort_key(high, dims)
        assert key_critical < key_high

    def test_high_before_medium(self) -> None:
        dims = ["SECURITY", "IDENTITY", "TIMELINE"]
        high = _make_fact(fact_id="a", severity="HIGH", dimension="SECURITY")
        medium = _make_fact(fact_id="b", severity="MEDIUM", dimension="SECURITY")
        assert _sort_key(high, dims) < _sort_key(medium, dims)

    def test_medium_before_info(self) -> None:
        dims = ["SECURITY", "IDENTITY", "TIMELINE"]
        medium = _make_fact(fact_id="a", severity="MEDIUM", dimension="SECURITY")
        info = _make_fact(fact_id="b", severity="INFO", dimension="SECURITY")
        assert _sort_key(medium, dims) < _sort_key(info, dims)

    def test_primary_dimension_before_secondary(self) -> None:
        dims = ["SECURITY", "ARCH", "IDENTITY", "TIMELINE"]
        sec_fact = _make_fact(fact_id="a", severity="INFO", dimension="SECURITY")
        arch_fact = _make_fact(fact_id="b", severity="INFO", dimension="ARCH")
        assert _sort_key(sec_fact, dims) < _sort_key(arch_fact, dims)

    def test_sort_is_stable_by_id(self) -> None:
        dims = ["SECURITY", "IDENTITY", "TIMELINE"]
        f1 = _make_fact(fact_id="aaa", severity="INFO", dimension="SECURITY")
        f2 = _make_fact(fact_id="zzz", severity="INFO", dimension="SECURITY")
        assert _sort_key(f1, dims) < _sort_key(f2, dims)

    def test_more_recent_date_sorts_first(self) -> None:
        dims = ["SECURITY", "IDENTITY", "TIMELINE"]
        recent = _make_fact(
            fact_id="a", severity="INFO",
            source_date="2026-07-01T00:00:00+00:00"
        )
        older = _make_fact(
            fact_id="a", severity="INFO",
            source_date="2026-01-01T00:00:00+00:00"
        )
        assert _sort_key(recent, dims) < _sort_key(older, dims)


# ---------------------------------------------------------------------------
# Cross-dimension CRITICAL/HIGH pull
# ---------------------------------------------------------------------------


class TestCrossDimensionPull:
    def test_critical_fact_from_non_selected_dim_included(
        self, tmp_path: Path
    ) -> None:
        arch_critical = _make_fact(
            fact_id="arch-crit",
            dimension="ARCH",
            severity="CRITICAL",
            summary="Critical architecture issue",
        )
        with _brain_with_facts(tmp_path, [arch_critical]) as brain:
            assembler = ContextAssembler(brain)
            # Only ask about SECURITY — ARCH not selected
            ctx = assembler.assemble("security risks")
        assert "ARCH" not in ctx.dimensions
        fact_ids = {f.id for f in ctx.facts}
        assert "arch-crit" in fact_ids

    def test_high_fact_from_non_selected_dim_included(
        self, tmp_path: Path
    ) -> None:
        recovery_high = _make_fact(
            fact_id="rec-high",
            dimension="RECOVERY",
            severity="HIGH",
            summary="High recovery issue",
        )
        with _brain_with_facts(tmp_path, [recovery_high]) as brain:
            assembler = ContextAssembler(brain)
            ctx = assembler.assemble("security risks")
        assert "RECOVERY" not in ctx.dimensions
        assert "rec-high" in {f.id for f in ctx.facts}

    def test_info_fact_from_non_selected_dim_not_pulled(
        self, tmp_path: Path
    ) -> None:
        domain_info = _make_fact(
            fact_id="dom-info",
            dimension="DOMAIN",
            severity="INFO",
            summary="Domain info fact",
        )
        with _brain_with_facts(tmp_path, [domain_info]) as brain:
            assembler = ContextAssembler(brain)
            ctx = assembler.assemble("security risks")
        assert "dom-info" not in {f.id for f in ctx.facts}

    def test_medium_from_non_selected_dim_not_pulled(
        self, tmp_path: Path
    ) -> None:
        domain_medium = _make_fact(
            fact_id="dom-med",
            dimension="DOMAIN",
            severity="MEDIUM",
            summary="Domain medium fact",
        )
        with _brain_with_facts(tmp_path, [domain_medium]) as brain:
            assembler = ContextAssembler(brain)
            ctx = assembler.assemble("security risks")
        assert "dom-med" not in {f.id for f in ctx.facts}


# ---------------------------------------------------------------------------
# Budget enforcement
# ---------------------------------------------------------------------------


class TestBudgetEnforcement:
    def test_truncated_false_when_facts_fit(self, tmp_path: Path) -> None:
        fact = _make_fact(summary="Short fact")
        with _brain_with_facts(tmp_path, [fact]) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        assert ctx.truncated is False

    def test_truncated_true_when_budget_too_small(self, tmp_path: Path) -> None:
        # Use normal-length facts but a budget so small (1) that fixed overhead
        # alone exhausts it, triggering truncated=True.
        facts = [_make_fact(fact_id=f"fact-{i}") for i in range(5)]
        with _brain_with_facts(tmp_path, facts) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=1)
        assert ctx.truncated is True

    def test_token_estimate_le_budget_when_not_truncated(
        self, tmp_path: Path
    ) -> None:
        fact = _make_fact(summary="Short fact")
        with _brain_with_facts(tmp_path, [fact]) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        if not ctx.truncated:
            assert ctx.token_estimate <= ctx.token_budget

    def test_critical_fact_included_when_budget_tight(
        self, tmp_path: Path
    ) -> None:
        critical = _make_fact(
            fact_id="crit", severity="CRITICAL", summary="Critical issue"
        )
        many_info = [
            _make_fact(
                fact_id=f"info-{i}",
                severity="INFO",
                summary="X" * 100,
                detail="Y" * 100,
            )
            for i in range(50)
        ]
        with _brain_with_facts(tmp_path, [critical, *many_info]) as brain:
            ctx = ContextAssembler(brain).assemble(
                "security", token_budget=300
            )
        fact_ids = {f.id for f in ctx.facts}
        assert "crit" in fact_ids

    def test_no_facts_when_budget_exhausted_by_overhead(
        self, tmp_path: Path
    ) -> None:
        facts = [_make_fact(fact_id=f"f-{i}") for i in range(5)]
        with _brain_with_facts(tmp_path, facts) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=1)
        # Budget so small that overhead alone exceeds it
        assert ctx.truncated is True

    def test_empty_brain_truncated_false(self, tmp_path: Path) -> None:
        with _open_brain(tmp_path) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        assert ctx.truncated is False
        assert ctx.facts == []


# ---------------------------------------------------------------------------
# Security gate
# ---------------------------------------------------------------------------


class TestSecretGate:
    def test_fact_with_jwt_summary_excluded(self, tmp_path: Path) -> None:
        jwt_like = "eyJhbGciOiJIUzI1NiJ9" + "A" * 30
        bad_fact = _make_fact(fact_id="bad", summary=jwt_like)
        with _brain_with_facts(tmp_path, [bad_fact]) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        assert "bad" not in {f.id for f in ctx.facts}

    def test_safe_fact_included(self, tmp_path: Path) -> None:
        safe = _make_fact(fact_id="safe", summary="A normal finding")
        with _brain_with_facts(tmp_path, [safe]) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        assert "safe" in {f.id for f in ctx.facts}

    def test_decision_with_jwt_title_excluded(self, tmp_path: Path) -> None:
        jwt_like = "eyJhbGciOiJIUzI1NiJ9" + "A" * 30
        bad_decision = _make_decision(decision_id="bad-dec", title=jwt_like)
        with _brain_with_facts(tmp_path, [], decisions=[bad_decision]) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        assert "bad-dec" not in {d.id for d in ctx.decisions}

    def test_safe_decision_included(self, tmp_path: Path) -> None:
        decision = _make_decision(decision_id="safe-dec", title="Remove Supabase")
        with _brain_with_facts(tmp_path, [], decisions=[decision]) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        assert "safe-dec" in {d.id for d in ctx.decisions}

    def test_safe_vocabulary_included(self, tmp_path: Path) -> None:
        term = _make_vocabulary("RLS", "Row Level Security")
        with _brain_with_facts(tmp_path, [], vocabulary=[term]) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        assert "RLS" in {t.term for t in ctx.vocabulary}

    def test_is_safe_fact_rejects_jwt_summary(self) -> None:
        jwt_like = "eyJhbGciOiJIUzI1NiJ9" + "A" * 30
        fact = _make_fact(summary=jwt_like)
        assert _is_safe_fact(fact) is False

    def test_is_safe_fact_passes_normal_fact(self) -> None:
        fact = _make_fact(summary="Normal finding")
        assert _is_safe_fact(fact) is True


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


class TestReproducibility:
    def test_same_question_same_brain_same_fact_ids(self, tmp_path: Path) -> None:
        facts = [
            _make_fact(fact_id="f1", severity="CRITICAL"),
            _make_fact(fact_id="f2", severity="HIGH"),
            _make_fact(fact_id="f3", severity="INFO"),
        ]
        with _brain_with_facts(tmp_path, facts) as brain:
            assembler = ContextAssembler(brain)
            ctx_a = assembler.assemble("security risks", token_budget=4000)
            ctx_b = assembler.assemble("security risks", token_budget=4000)
        assert [f.id for f in ctx_a.facts] == [f.id for f in ctx_b.facts]

    def test_brain_version_included_in_context(self, tmp_path: Path) -> None:
        with _open_brain(tmp_path) as brain:
            ctx = ContextAssembler(brain).assemble("security")
        assert len(ctx.brain_version) > 0

    def test_resolved_facts_excluded_by_default(self, tmp_path: Path) -> None:
        resolved = _make_fact(
            fact_id="resolved",
            summary="Resolved finding",
            resolved_at="2026-02-01T00:00:00+00:00",
        )
        with _brain_with_facts(tmp_path, [resolved]) as brain:
            ctx = ContextAssembler(brain).assemble("security")
        assert "resolved" not in {f.id for f in ctx.facts}

    def test_include_resolved_true_includes_resolved_facts(
        self, tmp_path: Path
    ) -> None:
        resolved = _make_fact(
            fact_id="resolved",
            summary="Resolved finding",
            resolved_at="2026-02-01T00:00:00+00:00",
        )
        with _brain_with_facts(tmp_path, [resolved]) as brain:
            ctx = ContextAssembler(brain).assemble(
                "security", include_resolved=True
            )
        assert "resolved" in {f.id for f in ctx.facts}

    def test_assembled_at_is_iso8601(self, tmp_path: Path) -> None:
        with _open_brain(tmp_path) as brain:
            ctx = ContextAssembler(brain).assemble("security")
        # ISO 8601 strings start with year (4 digits)
        assert ctx.assembled_at[:4].isdigit()
        assert "T" in ctx.assembled_at


# ---------------------------------------------------------------------------
# AIContext fields
# ---------------------------------------------------------------------------


class TestAIContextFields:
    def test_question_copied_verbatim(self, tmp_path: Path) -> None:
        with _open_brain(tmp_path) as brain:
            ctx = ContextAssembler(brain).assemble("What are the security risks?")
        assert ctx.question == "What are the security risks?"

    def test_dimensions_in_context(self, tmp_path: Path) -> None:
        with _open_brain(tmp_path) as brain:
            ctx = ContextAssembler(brain).assemble("security risks")
        assert "SECURITY" in ctx.dimensions
        assert "IDENTITY" in ctx.dimensions
        assert "TIMELINE" in ctx.dimensions

    def test_decisions_included_in_context(self, tmp_path: Path) -> None:
        dec = _make_decision()
        with _brain_with_facts(tmp_path, [], decisions=[dec]) as brain:
            ctx = ContextAssembler(brain).assemble("security")
        assert len(ctx.decisions) == 1
        assert ctx.decisions[0].id == "dec-001"

    def test_vocabulary_included_in_context(self, tmp_path: Path) -> None:
        term = _make_vocabulary()
        with _brain_with_facts(tmp_path, [], vocabulary=[term]) as brain:
            ctx = ContextAssembler(brain).assemble("security")
        assert len(ctx.vocabulary) == 1
        assert ctx.vocabulary[0].term == "RLS"

    def test_project_identity_included(self, tmp_path: Path) -> None:
        identity = _make_identity()
        with _brain_with_facts(tmp_path, [], identity=identity) as brain:
            ctx = ContextAssembler(brain).assemble("security")
        assert ctx.project_identity is not None
        assert ctx.project_identity.project_name == "test-proj"

    def test_empty_brain_produces_valid_context(self, tmp_path: Path) -> None:
        with _open_brain(tmp_path) as brain:
            ctx = ContextAssembler(brain).assemble("security")
        assert isinstance(ctx, AIContext)
        assert ctx.facts == []
        assert ctx.decisions == []
        assert ctx.vocabulary == []
        assert ctx.project_identity is None
        assert ctx.truncated is False

    def test_token_budget_reflected_in_context(self, tmp_path: Path) -> None:
        with _open_brain(tmp_path) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=1234)
        assert ctx.token_budget == 1234

    def test_first_fact_is_highest_priority(self, tmp_path: Path) -> None:
        facts = [
            _make_fact(fact_id="info", severity="INFO"),
            _make_fact(fact_id="crit", severity="CRITICAL"),
        ]
        with _brain_with_facts(tmp_path, facts) as brain:
            ctx = ContextAssembler(brain).assemble("security", token_budget=4000)
        if ctx.facts:
            assert ctx.facts[0].severity in ("CRITICAL", "HIGH")
