"""
Supabase RLS Hardener — orchestrates the full hardening chain:
inspect → plan → generate → review

Produces a single result that summarises every step.
Read-only. No network access. No secret reads. No file modification.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aeos.providers.supabase.rls.generator import RLSGenerateResult, run_rls_generate
from aeos.providers.supabase.rls.inspector import RLSInspectResult, run_rls_inspect
from aeos.providers.supabase.rls.planner import RLSPlanResult, run_rls_plan
from aeos.providers.supabase.rls.reviewer import (
    RLSReviewResult,
    run_rls_review_from_result,
)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class RLSHardenSummary:
    findings_count: int
    findings_by_severity: dict[str, int]  # OK | WARNING | ERROR → count
    plan_actions: int
    plan_by_priority: dict[str, int]  # CRITICAL | HIGH | MEDIUM | LOW → count
    generated_blocks: int
    auto_blocks: int
    todo_blocks: int
    verdict: str  # PASS | WARNING | BLOCKED
    safe_blocks: int
    blocked_blocks: int
    tables_affected: list[str]
    riskiest_tables: list[str]  # top tables by plan priority


@dataclass
class RLSHardenResult:
    path: Path
    status: str  # OK | WARNING | ERROR  (most severe across the chain)
    migrations_scanned: int
    summary: RLSHardenSummary
    inspect: RLSInspectResult
    plan: RLSPlanResult
    generate: RLSGenerateResult
    review: RLSReviewResult
    read_only: bool = True
    applied: bool = False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_rls_harden(
    path: Path,
    include_medium: bool = False,
) -> RLSHardenResult:
    """
    Orchestrate the full RLS hardening chain on a Supabase project.
    Read-only — no database connection, no .env read, no file modification.
    `applied` is always False — no migration is applied.
    """
    inspect_result = run_rls_inspect(path)
    plan_result = run_rls_plan(path)
    gen_result = run_rls_generate(path, include_medium=include_medium)
    review_result = run_rls_review_from_result(gen_result)

    statuses = [inspect_result.status, plan_result.status, gen_result.status]
    if "ERROR" in statuses:
        status = "ERROR"
    elif "WARNING" in statuses:
        status = "WARNING"
    else:
        status = "OK"

    findings_by_severity: dict[str, int] = {}
    for f in inspect_result.findings:
        findings_by_severity[f.severity] = findings_by_severity.get(f.severity, 0) + 1

    summary = RLSHardenSummary(
        findings_count=len(inspect_result.findings),
        findings_by_severity=findings_by_severity,
        plan_actions=plan_result.summary.total_actions,
        plan_by_priority=dict(plan_result.summary.by_priority),
        generated_blocks=gen_result.summary.total_blocks,
        auto_blocks=gen_result.summary.auto_generated,
        todo_blocks=gen_result.summary.manual_todos,
        verdict=review_result.verdict,
        safe_blocks=review_result.summary.safe_executable_blocks,
        blocked_blocks=review_result.summary.blocked_blocks,
        tables_affected=review_result.summary.tables_affected,
        riskiest_tables=plan_result.summary.riskiest_tables[:5],
    )

    return RLSHardenResult(
        path=path,
        status=status,
        migrations_scanned=gen_result.migrations_scanned,
        summary=summary,
        inspect=inspect_result,
        plan=plan_result,
        generate=gen_result,
        review=review_result,
        read_only=True,
        applied=False,
    )
