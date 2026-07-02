"""
AEOS Context Assembler — builds AIContext from Project Brain.

Pure assembly: reads Brain → constructs bounded AIContext.
No AI, no network, no writing to Brain, no provider, no PromptBuilder.
Reproducible: same Brain state + same question + same budget → same AIContext.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aeos.brain.models import Decision, KnowledgeFact, ProjectIdentity, VocabularyTerm
from aeos.brain.store import BrainStore
from aeos.memory.store import _looks_like_secret_value

# _looks_like_secret_value is a narrow heuristic (JWT, long base64, Stripe keys).
# Defence-in-depth only — the primary protection is that MemoryRecords are
# produced by controlled AEOS commands, not from arbitrary user-supplied text.

# ---------------------------------------------------------------------------
# Dimension keyword mapping
# ---------------------------------------------------------------------------

_DIMENSION_KEYWORDS: dict[str, list[str]] = {
    "SECURITY": [
        "security",
        "vulnerability",
        "risk",
        "attack",
        "credential",
        "auth",
        "permission",
        "leak",
        "exposure",
        "breach",
        "exploit",
        "injection",
        "xss",
        "sensitive",
    ],
    "SOVEREIGNTY": [
        "sovereignty",
        "control",
        "dependency",
        "vendor",
        "lock",
        "migration",
        "exit",
        "replace",
        "alternative",
        "independent",
    ],
    "ARCH": [
        "architecture",
        "provider",
        "service",
        "stack",
        "integration",
        "api",
        "database",
        "generator",
        "infrastructure",
        "technology",
    ],
    "RECOVERY": [
        "recovery",
        "remediation",
        "fix",
        "repair",
        "restore",
        "action",
        "plan",
        "phase",
        "remediate",
        "resolve",
    ],
    "DOMAIN": [
        "domain",
        "business",
        "feature",
        "product",
        "user",
        "requirement",
        "functionality",
    ],
    "IDENTITY": [
        "identity",
        "project",
        "team",
        "owner",
        "contact",
        "who",
    ],
    "TIMELINE": [
        "timeline",
        "history",
        "when",
        "date",
        "audit",
        "previous",
        "last",
        "recent",
        "latest",
    ],
}

# Always included regardless of question content.
_ALWAYS_DIMENSIONS: tuple[str, ...] = ("IDENTITY", "TIMELINE")

# Default additions when no keyword matches (besides _ALWAYS_DIMENSIONS).
_DEFAULT_FALLBACK_DIMENSIONS: tuple[str, ...] = ("SECURITY", "SOVEREIGNTY")

# Severity ordering for priority sort (lower rank = higher priority).
_SEVERITY_RANK: dict[str | None, int] = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFO": 4,
    None: 5,
}

# Severities always included regardless of dimension selection.
_ALWAYS_PULL_SEVERITIES: frozenset[str] = frozenset({"CRITICAL", "HIGH"})

# Approximate characters per token (conservative underestimate).
_CHARS_PER_TOKEN: int = 4

# Fixed structural overhead reserved from budget (labels, separators, formatting).
_STRUCTURAL_OVERHEAD_TOKENS: int = 50


# ---------------------------------------------------------------------------
# AIContext — the output of ContextAssembler
# ---------------------------------------------------------------------------


@dataclass
class AIContext:
    """Bounded, neutral context for AI consumption. No provider coupling."""

    question: str
    brain_version: str
    dimensions: list[str]
    token_budget: int
    facts: list[KnowledgeFact]
    decisions: list[Decision]
    vocabulary: list[VocabularyTerm]
    project_identity: ProjectIdentity | None
    assembled_at: str
    token_estimate: int
    truncated: bool


# ---------------------------------------------------------------------------
# ContextAssembler
# ---------------------------------------------------------------------------


class ContextAssembler:
    def __init__(self, brain: BrainStore) -> None:
        self._brain = brain

    def assemble(
        self,
        question: str,
        token_budget: int = 4000,
        include_resolved: bool = False,
    ) -> AIContext:
        """Build a bounded AIContext from the Brain. Never writes to the Brain.

        Reproducible: same Brain state + same question + same budget → same result.
        """
        dimensions = _analyze_question(question)
        brain_version = self._brain.get_brain_version()

        # Collect and filter candidate facts
        dimension_set = set(dimensions)
        all_facts = self._brain.get_facts(include_resolved=include_resolved)
        candidate_facts = [
            f
            for f in all_facts
            if f.dimension in dimension_set
            or f.severity in _ALWAYS_PULL_SEVERITIES
        ]
        safe_facts = [f for f in candidate_facts if _is_safe_fact(f)]

        # Sort by (severity, dimension relevance, date desc, id)
        sorted_facts = sorted(
            safe_facts,
            key=lambda f: _sort_key(f, dimensions),
        )

        # Decisions and vocabulary — included in full, security-gated
        decisions = [
            d for d in self._brain.get_decisions() if _is_safe_decision(d)
        ]
        vocabulary = [
            v for v in self._brain.get_vocabulary() if _is_safe_vocabulary(v)
        ]
        identity = self._brain.get_identity()

        # Fixed overhead: question + dimensions + brain_version + identity +
        # decisions + vocabulary + structural labels
        fixed_tokens = (
            _estimate_tokens(question)
            + _estimate_tokens(" ".join(dimensions))
            + _estimate_tokens(brain_version)
            + _identity_token_cost(identity)
            + sum(_decision_token_cost(d) for d in decisions)
            + sum(_vocabulary_token_cost(v) for v in vocabulary)
            + _STRUCTURAL_OVERHEAD_TOKENS
        )

        remaining_budget = token_budget - fixed_tokens

        # Apply fact budget (greedy, priority order)
        selected_facts: list[KnowledgeFact] = []
        fact_tokens_used = 0
        truncated = remaining_budget <= 0 and len(sorted_facts) > 0

        if remaining_budget > 0:
            for fact in sorted_facts:
                cost = _fact_token_cost(fact)
                if fact_tokens_used + cost <= remaining_budget:
                    selected_facts.append(fact)
                    fact_tokens_used += cost
                else:
                    truncated = True

        token_estimate = fixed_tokens + fact_tokens_used

        return AIContext(
            question=question,
            brain_version=brain_version,
            dimensions=dimensions,
            token_budget=token_budget,
            facts=selected_facts,
            decisions=decisions,
            vocabulary=vocabulary,
            project_identity=identity,
            assembled_at=datetime.now(tz=UTC).isoformat(),
            token_estimate=token_estimate,
            truncated=truncated,
        )


# ---------------------------------------------------------------------------
# Question analysis
# ---------------------------------------------------------------------------


def _analyze_question(question: str) -> list[str]:
    """Map question keywords to Brain dimensions.

    Always appends IDENTITY and TIMELINE.
    Falls back to SECURITY + SOVEREIGNTY when no keyword matches.
    Never returns all dimensions by default.
    """
    q = question.lower()
    scores: dict[str, int] = {}

    for dim, keywords in _DIMENSION_KEYWORDS.items():
        if dim in _ALWAYS_DIMENSIONS:
            continue  # handled as always-includes below
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[dim] = score

    if scores:
        matched: list[str] = sorted(scores, key=lambda d: (-scores[d], d))
    else:
        matched = list(_DEFAULT_FALLBACK_DIMENSIONS)

    result: list[str] = list(matched)
    for dim in _ALWAYS_DIMENSIONS:
        if dim not in result:
            result.append(dim)

    return result


# ---------------------------------------------------------------------------
# Sort key for facts
# ---------------------------------------------------------------------------


def _dim_rank(dimension: str, dimensions: list[str]) -> int:
    """Return index of dimension in selected list, or 50 for cross-dim pull."""
    try:
        return dimensions.index(dimension)
    except ValueError:
        return 50


def _parse_date_epoch(date_str: str | None) -> float:
    """Parse ISO 8601 date to float epoch. Returns 0.0 on failure."""
    if not date_str:
        return 0.0
    try:
        return datetime.fromisoformat(date_str).timestamp()
    except ValueError:
        return 0.0


def _sort_key(
    fact: KnowledgeFact, dimensions: list[str]
) -> tuple[int, int, float, str]:
    """Priority key: (severity ASC, dim_rank ASC, date DESC, id ASC)."""
    sev = _SEVERITY_RANK.get(fact.severity, 5)
    dim = _dim_rank(fact.dimension, dimensions)
    neg_date = -_parse_date_epoch(fact.source_date)
    return (sev, dim, neg_date, fact.id)


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _fact_token_cost(fact: KnowledgeFact) -> int:
    text = " ".join(
        [
            fact.id,
            fact.fact_type,
            fact.dimension,
            fact.severity or "",
            fact.summary,
            fact.detail or "",
        ]
    )
    return _estimate_tokens(text)


def _decision_token_cost(decision: Decision) -> int:
    return _estimate_tokens(f"{decision.title} {decision.description}")


def _vocabulary_token_cost(term: VocabularyTerm) -> int:
    return _estimate_tokens(f"{term.term} {term.definition}")


def _identity_token_cost(identity: ProjectIdentity | None) -> int:
    if identity is None:
        return 0
    parts = [identity.project_name, identity.project_path]
    if identity.description is not None:
        parts.append(identity.description)
    return _estimate_tokens(" ".join(parts))


# ---------------------------------------------------------------------------
# Security gates
# ---------------------------------------------------------------------------


def _is_safe_fact(fact: KnowledgeFact) -> bool:
    if _looks_like_secret_value(fact.summary):
        return False
    if _looks_like_secret_value(fact.detail or ""):
        return False
    return True


def _is_safe_decision(decision: Decision) -> bool:
    if _looks_like_secret_value(decision.title):
        return False
    if _looks_like_secret_value(decision.description):
        return False
    if _looks_like_secret_value(decision.rationale or ""):
        return False
    return True


def _is_safe_vocabulary(term: VocabularyTerm) -> bool:
    if _looks_like_secret_value(term.term):
        return False
    if _looks_like_secret_value(term.definition):
        return False
    return True
