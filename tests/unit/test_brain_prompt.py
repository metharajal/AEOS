"""Unit tests for the Brain Prompt Renderer (CAP-2-D)."""

from __future__ import annotations

from aeos.brain.assembler import AIContext
from aeos.brain.models import Decision, KnowledgeFact, ProjectIdentity, VocabularyTerm
from aeos.brain.prompt import format_context_as_prompt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx(
    question: str = "security risks",
    brain_version: str = "abc123def456",
    dimensions: list[str] | None = None,
    token_budget: int = 4000,
    facts: list[KnowledgeFact] | None = None,
    decisions: list[Decision] | None = None,
    vocabulary: list[VocabularyTerm] | None = None,
    project_identity: ProjectIdentity | None = None,
    token_estimate: int = 100,
    truncated: bool = False,
) -> AIContext:
    return AIContext(
        question=question,
        brain_version=brain_version,
        dimensions=dimensions or ["SECURITY", "IDENTITY", "TIMELINE"],
        token_budget=token_budget,
        facts=facts or [],
        decisions=decisions or [],
        vocabulary=vocabulary or [],
        project_identity=project_identity,
        assembled_at="2026-07-02T00:00:00+00:00",
        token_estimate=token_estimate,
        truncated=truncated,
    )


def _make_fact(
    fact_id: str = "fact-001",
    summary: str = "A test finding",
    detail: str | None = None,
    severity: str = "HIGH",
    dimension: str = "SECURITY",
) -> KnowledgeFact:
    return KnowledgeFact(
        id=fact_id,
        fact_type="FINDING",
        dimension=dimension,
        summary=summary,
        severity=severity,
        detail=detail,
        created_at="2026-01-01T00:00:00+00:00",
    )


def _make_decision(
    title: str = "Use local AI only",
    description: str = "Avoid frontier providers for security.",
) -> Decision:
    return Decision(
        id="dec-001",
        title=title,
        description=description,
        decided_at="2026-01-01T00:00:00+00:00",
    )


def _make_term(
    term: str = "RLS", definition: str = "Row Level Security"
) -> VocabularyTerm:
    return VocabularyTerm(term=term, definition=definition)


def _make_identity(
    project_name: str = "my-project",
    project_path: str = "/home/user/projects/my-project",
    description: str | None = "A test project.",
) -> ProjectIdentity:
    return ProjectIdentity(
        project_name=project_name,
        project_path=project_path,
        description=description,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPromptFormat:
    def test_contains_question(self) -> None:
        ctx = _make_ctx(question="What are the security risks?")
        prompt = format_context_as_prompt(ctx)
        assert "What are the security risks?" in prompt

    def test_contains_brain_version(self) -> None:
        ctx = _make_ctx(brain_version="deadbeef0123")
        prompt = format_context_as_prompt(ctx)
        assert "deadbeef0123" in prompt

    def test_contains_dimensions(self) -> None:
        ctx = _make_ctx(dimensions=["SECURITY", "ARCH", "IDENTITY"])
        prompt = format_context_as_prompt(ctx)
        assert "SECURITY" in prompt
        assert "ARCH" in prompt
        assert "IDENTITY" in prompt

    def test_fact_summary_in_prompt(self) -> None:
        fact = _make_fact(summary="Exposed API key in source")
        ctx = _make_ctx(facts=[fact])
        prompt = format_context_as_prompt(ctx)
        assert "Exposed API key in source" in prompt

    def test_fact_detail_in_prompt(self) -> None:
        fact = _make_fact(
            summary="Secret leak", detail="Found in src/config.py line 42"
        )
        ctx = _make_ctx(facts=[fact])
        prompt = format_context_as_prompt(ctx)
        assert "Found in src/config.py line 42" in prompt

    def test_fact_severity_in_prompt(self) -> None:
        fact = _make_fact(severity="CRITICAL", summary="Critical issue")
        ctx = _make_ctx(facts=[fact])
        prompt = format_context_as_prompt(ctx)
        assert "[CRITICAL]" in prompt

    def test_facts_count_in_prompt(self) -> None:
        facts = [_make_fact(fact_id=f"f{i}", summary=f"Finding {i}") for i in range(3)]
        ctx = _make_ctx(facts=facts)
        prompt = format_context_as_prompt(ctx)
        assert "FACTS (3 selected)" in prompt

    def test_no_project_path_in_prompt(self) -> None:
        identity = _make_identity(project_path="/secret/internal/path/project")
        ctx = _make_ctx(project_identity=identity)
        prompt = format_context_as_prompt(ctx)
        assert "/secret/internal/path/project" not in prompt

    def test_anti_hallucination_clause_present(self) -> None:
        ctx = _make_ctx()
        prompt = format_context_as_prompt(ctx)
        assert "ONLY" in prompt
        assert "Do NOT" in prompt

    def test_anti_hallucination_at_end(self) -> None:
        ctx = _make_ctx(question="my question")
        prompt = format_context_as_prompt(ctx)
        instruction_pos = prompt.index("=== INSTRUCTION ===")
        question_pos = prompt.index("Question: my question")
        assert instruction_pos < question_pos
        # INSTRUCTION is the final section
        assert prompt.endswith("Question: my question")

    def test_truncated_warning_present_when_truncated(self) -> None:
        ctx = _make_ctx(truncated=True)
        prompt = format_context_as_prompt(ctx)
        assert "truncated" in prompt.lower()
        assert "WARNING" in prompt

    def test_no_truncated_warning_when_not_truncated(self) -> None:
        ctx = _make_ctx(truncated=False)
        prompt = format_context_as_prompt(ctx)
        assert "WARNING" not in prompt

    def test_empty_facts_renders_valid_prompt(self) -> None:
        ctx = _make_ctx(facts=[])
        prompt = format_context_as_prompt(ctx)
        assert "no facts selected" in prompt
        assert "=== INSTRUCTION ===" in prompt

    def test_decision_in_prompt(self) -> None:
        decision = _make_decision(
            title="Local AI only", description="No frontier providers."
        )
        ctx = _make_ctx(decisions=[decision])
        prompt = format_context_as_prompt(ctx)
        assert "Local AI only" in prompt
        assert "No frontier providers." in prompt

    def test_vocabulary_in_prompt(self) -> None:
        term = _make_term(term="RLS", definition="Row Level Security in Supabase")
        ctx = _make_ctx(vocabulary=[term])
        prompt = format_context_as_prompt(ctx)
        assert "RLS" in prompt
        assert "Row Level Security in Supabase" in prompt

    def test_identity_name_in_prompt(self) -> None:
        identity = _make_identity(project_name="sovereign-project")
        ctx = _make_ctx(project_identity=identity)
        prompt = format_context_as_prompt(ctx)
        assert "sovereign-project" in prompt

    def test_identity_path_not_in_prompt(self) -> None:
        identity = _make_identity(project_path="/users/secret/projects/x")
        ctx = _make_ctx(project_identity=identity)
        prompt = format_context_as_prompt(ctx)
        assert "/users/secret/projects/x" not in prompt

    def test_identity_description_in_prompt(self) -> None:
        identity = _make_identity(description="A sovereign platform for continuity.")
        ctx = _make_ctx(project_identity=identity)
        prompt = format_context_as_prompt(ctx)
        assert "A sovereign platform for continuity." in prompt

    def test_no_identity_section_when_none(self) -> None:
        ctx = _make_ctx(project_identity=None)
        prompt = format_context_as_prompt(ctx)
        assert "PROJECT IDENTITY" not in prompt

    def test_no_decisions_section_when_empty(self) -> None:
        ctx = _make_ctx(decisions=[])
        prompt = format_context_as_prompt(ctx)
        assert "=== DECISIONS" not in prompt

    def test_no_vocabulary_section_when_empty(self) -> None:
        ctx = _make_ctx(vocabulary=[])
        prompt = format_context_as_prompt(ctx)
        assert "=== VOCABULARY" not in prompt

    def test_prompt_is_deterministic(self) -> None:
        ctx = _make_ctx(
            facts=[_make_fact()],
            decisions=[_make_decision()],
            vocabulary=[_make_term()],
        )
        p1 = format_context_as_prompt(ctx)
        p2 = format_context_as_prompt(ctx)
        assert p1 == p2

    def test_sovereign_header_present(self) -> None:
        ctx = _make_ctx()
        prompt = format_context_as_prompt(ctx)
        assert "sovereign" in prompt.lower()

    def test_returns_str(self) -> None:
        ctx = _make_ctx()
        result = format_context_as_prompt(ctx)
        assert isinstance(result, str)
        assert len(result) > 0
