"""
AEOS Brain Prompt Renderer — serializes AIContext to structured text.

Pure function: no I/O, no AI calls, no Brain reads or writes.
Deterministic: same AIContext -> same prompt string.
project_path is never rendered (sovereignty constraint).
Anti-hallucination clause is always appended.
"""

from __future__ import annotations

from aeos.brain.assembler import AIContext

_HEADER = "[AEOS BRAIN CONTEXT — sovereign | no hallucination license]"

_ANTI_HALLUCINATION = (
    "Answer the question using ONLY the facts listed above.\n"
    "Do NOT invent or add information not present in this context.\n"
    "If the information is insufficient to answer, say so explicitly."
)

_TRUNCATION_WARNING = (
    "[WARNING: context truncated — some facts omitted due to token budget]"
)


def format_context_as_prompt(ctx: AIContext) -> str:
    """Render AIContext as structured text for local AI consumption.

    project_path is never included.
    Anti-hallucination clause is always the final section.
    Deterministic: same AIContext -> same output string.
    """
    parts: list[str] = []

    parts.append(_HEADER)
    parts.append(
        f"Brain: {ctx.brain_version} | "
        f"Dims: {', '.join(ctx.dimensions)} | "
        f"Budget: {ctx.token_budget} | "
        f"Est: {ctx.token_estimate} | "
        f"Truncated: {'yes' if ctx.truncated else 'no'}"
    )
    parts.append("")

    # project_path is deliberately omitted — sovereignty constraint
    if ctx.project_identity is not None:
        parts.append("=== PROJECT IDENTITY ===")
        parts.append(f"Project: {ctx.project_identity.project_name}")
        if ctx.project_identity.description:
            parts.append(ctx.project_identity.description)
        parts.append("")

    parts.append(f"=== FACTS ({len(ctx.facts)} selected) ===")
    if ctx.facts:
        for fact in ctx.facts:
            sev = fact.severity or "INFO"
            parts.append(f"[{sev}][{fact.dimension}] {fact.summary}")
            if fact.detail:
                parts.append(f"  Detail: {fact.detail}")
    else:
        parts.append("(no facts selected for this question)")
    parts.append("")

    if ctx.decisions:
        parts.append(f"=== DECISIONS ({len(ctx.decisions)}) ===")
        for decision in ctx.decisions:
            parts.append(f"- {decision.title}: {decision.description}")
        parts.append("")

    if ctx.vocabulary:
        parts.append(f"=== VOCABULARY ({len(ctx.vocabulary)}) ===")
        for term in ctx.vocabulary:
            parts.append(f"- {term.term}: {term.definition}")
        parts.append("")

    if ctx.truncated:
        parts.append(_TRUNCATION_WARNING)
        parts.append("")

    parts.append("=== INSTRUCTION ===")
    parts.append(_ANTI_HALLUCINATION)
    parts.append(f"Question: {ctx.question}")

    return "\n".join(parts)
