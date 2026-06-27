"""
Supabase RLS Migration Review Gate — validates a proposed RLS migration
before any human applies it.

Read-only. No network access. No secret reads. No file modification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from aeos.providers.supabase.rls.generator import RLSGenerateResult, run_rls_generate
from aeos.providers.supabase.rls.generator import SQLBlock as GeneratorBlock

# ---------------------------------------------------------------------------
# Dangerous pattern registry
# ---------------------------------------------------------------------------

# Each entry: (human-readable name, compiled regex applied to non-comment SQL)
_BLOCKED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "DROP TABLE",
        re.compile(r"^\s*DROP\s+TABLE\b", re.IGNORECASE | re.MULTILINE),
    ),
    (
        "TRUNCATE",
        re.compile(r"^\s*TRUNCATE\b", re.IGNORECASE | re.MULTILINE),
    ),
    (
        "DELETE FROM (no WHERE)",
        re.compile(r"^\s*DELETE\s+FROM\b", re.IGNORECASE | re.MULTILINE),
    ),
    (
        "UPDATE … SET (no WHERE)",
        re.compile(r"^\s*UPDATE\s+\S+\s+SET\b", re.IGNORECASE | re.MULTILINE),
    ),
    (
        "ALTER TABLE DROP COLUMN",
        re.compile(r"ALTER\s+TABLE\b.+\bDROP\s+COLUMN\b", re.IGNORECASE | re.DOTALL),
    ),
    (
        "ALTER TABLE DROP CONSTRAINT",
        re.compile(
            r"ALTER\s+TABLE\b.+\bDROP\s+CONSTRAINT\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "DROP SCHEMA",
        re.compile(r"^\s*DROP\s+SCHEMA\b", re.IGNORECASE | re.MULTILINE),
    ),
    (
        "DROP DATABASE",
        re.compile(r"^\s*DROP\s+DATABASE\b", re.IGNORECASE | re.MULTILINE),
    ),
    (
        "GRANT ALL",
        re.compile(r"^\s*GRANT\s+ALL\b", re.IGNORECASE | re.MULTILINE),
    ),
    (
        "USING (true) — grants all-row access",
        re.compile(r"\bUSING\s*\(\s*true\s*\)", re.IGNORECASE),
    ),
    (
        "WITH CHECK (true) — allows any write",
        re.compile(r"\bWITH\s+CHECK\s*\(\s*true\s*\)", re.IGNORECASE),
    ),
]

_SECRET_RE = re.compile(
    r"(anon_key|service_role_key|SUPABASE_URL|jwt_secret"
    r"|password\s*=|secret\s*=)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ReviewBlock:
    priority: str  # CRITICAL | HIGH | MEDIUM
    table: str
    policy: str
    risk_type: str
    sql: str
    is_todo: bool
    classification: str  # safe | todo | blocked
    reasons: list[str] = field(default_factory=list)


@dataclass
class ReviewSummary:
    total_blocks: int
    safe_executable_blocks: int
    manual_todo_blocks: int
    blocked_blocks: int
    warnings_count: int
    tables_affected: list[str]
    block_reasons: list[str]


@dataclass
class RLSReviewResult:
    path: Path
    status: str  # OK | WARNING | ERROR  (from generator / inspector)
    verdict: str  # PASS | WARNING | BLOCKED
    migrations_scanned: int
    summary: ReviewSummary
    safe_blocks: list[ReviewBlock] = field(default_factory=list)
    todo_blocks: list[ReviewBlock] = field(default_factory=list)
    blocked_blocks: list[ReviewBlock] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    read_only: bool = True
    applied: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _non_comment_sql(sql: str) -> str:
    """Return SQL with lines starting with '--' removed."""
    return "\n".join(
        line for line in sql.split("\n") if not line.strip().startswith("--")
    )


def _check_dangerous_patterns(sql: str) -> list[str]:
    """
    Return a list of violation descriptions found in non-commented SQL.
    The caller is responsible for stripping comment lines first.
    """
    violations: list[str] = []
    for name, pattern in _BLOCKED_PATTERNS:
        if pattern.search(sql):
            violations.append(f"Dangerous operation detected: {name}")
    return violations


def _classify_block(block: GeneratorBlock) -> ReviewBlock:
    """Classify a generator SQLBlock as safe, todo, or blocked."""
    if block.is_todo:
        return ReviewBlock(
            priority=block.priority,
            table=block.table,
            policy=block.policy,
            risk_type=block.risk_type,
            sql=block.sql,
            is_todo=True,
            classification="todo",
            reasons=[],
        )

    executable_sql = _non_comment_sql(block.sql)
    reasons = _check_dangerous_patterns(executable_sql)
    classification = "blocked" if reasons else "safe"

    return ReviewBlock(
        priority=block.priority,
        table=block.table,
        policy=block.policy,
        risk_type=block.risk_type,
        sql=block.sql,
        is_todo=False,
        classification=classification,
        reasons=reasons,
    )


def _check_invariants(result: RLSGenerateResult) -> list[str]:
    """Return list of invariant violations found in the generate result."""
    violations: list[str] = []
    if not result.read_only:
        violations.append("INVARIANT VIOLATED: read_only is not True")
    if result.applied:
        violations.append("INVARIANT VIOLATED: applied is not False")
    if _SECRET_RE.search(result.generated_sql):
        violations.append("Potential secret detected in generated SQL")
    return violations


def _determine_verdict(
    blocked: list[ReviewBlock],
    todos: list[ReviewBlock],
    invariant_violations: list[str],
) -> str:
    if invariant_violations or blocked:
        return "BLOCKED"
    if todos:
        return "WARNING"
    return "PASS"


def _build_summary(
    safe: list[ReviewBlock],
    todos: list[ReviewBlock],
    blocked: list[ReviewBlock],
    extra_warnings: list[str],
) -> ReviewSummary:
    all_blocks = safe + todos + blocked
    tables_seen: list[str] = []
    for b in all_blocks:
        if b.table not in tables_seen:
            tables_seen.append(b.table)
    block_reasons: list[str] = []
    for b in blocked:
        for r in b.reasons:
            entry = f"[{b.table}] {r}"
            if entry not in block_reasons:
                block_reasons.append(entry)
    return ReviewSummary(
        total_blocks=len(all_blocks),
        safe_executable_blocks=len(safe),
        manual_todo_blocks=len(todos),
        blocked_blocks=len(blocked),
        warnings_count=len(extra_warnings),
        tables_affected=tables_seen,
        block_reasons=block_reasons,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_rls_review(
    path: Path,
    include_medium: bool = False,
) -> RLSReviewResult:
    """
    Review the proposed RLS migration for safety and correctness.
    Read-only — no database connection, no .env read, no file modification.
    `applied` is always False — no migration is applied.
    """
    gen_result = run_rls_generate(path, include_medium=include_medium)

    # Invariant checks on generator output
    invariant_violations = _check_invariants(gen_result)

    if not gen_result.blocks:
        verdict = "BLOCKED" if invariant_violations else "PASS"
        summary = ReviewSummary(
            total_blocks=0,
            safe_executable_blocks=0,
            manual_todo_blocks=0,
            blocked_blocks=0,
            warnings_count=len(invariant_violations),
            tables_affected=[],
            block_reasons=invariant_violations,
        )
        return RLSReviewResult(
            path=gen_result.path,
            status=gen_result.status,
            verdict=verdict,
            migrations_scanned=gen_result.migrations_scanned,
            summary=summary,
            safe_blocks=[],
            todo_blocks=[],
            blocked_blocks=[],
            warnings=invariant_violations,
            read_only=True,
            applied=False,
        )

    # Classify each block
    safe_blocks: list[ReviewBlock] = []
    todo_blocks: list[ReviewBlock] = []
    blocked_blocks: list[ReviewBlock] = []

    for gen_block in gen_result.blocks:
        reviewed = _classify_block(gen_block)
        if reviewed.classification == "safe":
            safe_blocks.append(reviewed)
        elif reviewed.classification == "todo":
            todo_blocks.append(reviewed)
        else:
            blocked_blocks.append(reviewed)

    # Extra warnings: generator warnings + invariant violations
    all_warnings = list(invariant_violations) + list(gen_result.warnings)

    verdict = _determine_verdict(blocked_blocks, todo_blocks, invariant_violations)
    summary = _build_summary(safe_blocks, todo_blocks, blocked_blocks, all_warnings)

    return RLSReviewResult(
        path=gen_result.path,
        status=gen_result.status,
        verdict=verdict,
        migrations_scanned=gen_result.migrations_scanned,
        summary=summary,
        safe_blocks=safe_blocks,
        todo_blocks=todo_blocks,
        blocked_blocks=blocked_blocks,
        warnings=all_warnings,
        read_only=True,
        applied=False,
    )
