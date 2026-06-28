"""
AEOS Reclaim Hardener — orchestrates the full project reclaim chain.

Runs: reclaim inspect → security check → sovereignty check
      → supabase check (if detected) → rls harden (if Supabase + migrations)

Read-only. No network access. No secret reads. No file modification.
`applied` is always False — no migration is applied.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aeos.providers.supabase import SupabaseCheckResult, run_supabase_check
from aeos.providers.supabase.rls import RLSHardenResult, run_rls_harden
from aeos.reclaim.inspector import ReclaimInspectResult, run_reclaim_inspect
from aeos.security.checker import SecurityCheckResult, run_security_check
from aeos.sovereignty.checker import SovereigntyCheckResult, run_sovereignty_check

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ReclaimHardenSummary:
    generator_detected: str | None  # "lovable" | "bolt" | "replit" | None
    providers_detected: list[str]  # names of detected providers
    control_level: str  # "controlled" | "partial" | "weak" | "unknown"
    secrets_exposure: str  # "none" | "risk" | "confirmed"
    security_status: str  # OK | WARNING | ERROR
    sovereignty_status: str  # OK | WARNING | ERROR
    supabase_status: str | None  # OK | WARNING | ERROR | CRITICAL | None
    rls_verdict: str | None  # PASS | WARNING | BLOCKED | None
    generated_actions: int  # auto SQL blocks ready
    manual_actions: int  # TODO blocks + manual remediation steps
    critical_findings: int
    important_findings: int


@dataclass
class ReclaimHardenResult:
    path: Path
    status: str  # OK | WARNING | ERROR
    summary: ReclaimHardenSummary
    reclaim: ReclaimInspectResult
    security: SecurityCheckResult
    sovereignty: SovereigntyCheckResult
    supabase: SupabaseCheckResult | None
    rls: RLSHardenResult | None
    recommendations: list[str] = field(default_factory=list)
    exit_options: list[str] = field(default_factory=list)
    read_only: bool = True
    applied: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _control_level(reclaim: ReclaimInspectResult) -> str:
    portability = reclaim.control_map.portability
    if portability == "strong":
        return "controlled"
    if portability == "partial":
        return "partial"
    if portability == "weak":
        return "weak"
    return "unknown"


def _count_findings(
    security: SecurityCheckResult,
    sovereignty: SovereigntyCheckResult,
    rls: RLSHardenResult | None,
) -> tuple[int, int]:
    """Return (critical_count, important_count) across all sub-results."""
    critical = 0
    important = 0

    for sf in security.findings:
        if sf.severity == "ERROR":
            critical += 1
        elif sf.severity == "WARNING":
            important += 1

    for svf in sovereignty.findings:
        if svf.severity == "ERROR":
            critical += 1
        elif svf.severity == "WARNING":
            important += 1

    if rls is not None:
        for rf in rls.inspect.findings:
            if rf.severity == "ERROR":
                critical += 1
            elif rf.severity == "WARNING":
                important += 1

    return critical, important


def _compute_status(
    reclaim: ReclaimInspectResult,
    security: SecurityCheckResult,
    supabase: SupabaseCheckResult | None,
    rls: RLSHardenResult | None,
) -> str:
    secrets_exposure = reclaim.control_map.secrets_exposure

    # ERROR conditions — hard blockers
    if secrets_exposure in ("confirmed", "risk"):
        return "ERROR"
    if any(f.severity == "ERROR" for f in security.findings):
        return "ERROR"
    if supabase is not None and supabase.status in ("CRITICAL", "ERROR"):
        return "ERROR"
    if rls is not None and rls.review.verdict == "BLOCKED":
        return "ERROR"

    # WARNING conditions
    any_generator = any(g.detected for g in reclaim.generators)
    if any_generator:
        return "WARNING"
    if reclaim.control_map.portability in ("weak", "partial"):
        return "WARNING"
    if security.status == "WARNING":
        return "WARNING"
    if supabase is not None and supabase.status == "WARNING":
        return "WARNING"
    if rls is not None and rls.review.verdict == "WARNING":
        return "WARNING"

    return "OK"


def _build_recommendations(
    reclaim: ReclaimInspectResult,
    security: SecurityCheckResult,
    supabase: SupabaseCheckResult | None,
    rls: RLSHardenResult | None,
    path: Path,
) -> list[str]:
    recs: list[str] = []
    path_str = str(path)
    cm = reclaim.control_map

    if cm.secrets_exposure == "confirmed":
        recs.append("Rotate all exposed keys immediately — they are in Git history.")
    if cm.secrets_exposure == "risk":
        recs.append("Remove .env from Git tracking and rotate keys before next push.")
    if any(f.severity == "ERROR" for f in security.findings):
        recs.append("Fix critical security findings before any deployment.")
    if rls is not None and rls.review.verdict in ("WARNING", "BLOCKED"):
        if rls.summary.todo_blocks:
            recs.append(
                f"Review {rls.summary.todo_blocks} RLS TODO block(s) manually "
                "before applying any migration."
            )
    if rls is not None and rls.summary.auto_blocks:
        recs.append(
            f"Export {rls.summary.auto_blocks} auto-generated RLS block(s) with: "
            f"`aeos supabase rls harden --path {path_str} "
            f"--output /tmp/rls-proposal.sql --force-warning`"
        )
    if supabase is not None and supabase.supabase_detected:
        manual_steps = [s for s in supabase.remediation_steps if s.status == "manual"]
        if manual_steps:
            recs.append(
                f"Complete {len(manual_steps)} manual Supabase remediation step(s) "
                "from `aeos supabase check`."
            )
    if cm.portability == "weak":
        recs.append(
            "Consider adding Dockerfile and local backend to improve portability."
        )

    if not recs:
        recs.append(
            "Project looks clean — run `aeos supabase rls harden` periodically."
        )

    return recs


def _build_exit_options(reclaim: ReclaimInspectResult) -> list[str]:
    return [
        f"{i + 1}. [{opt.complexity}/{opt.sovereignty}] {opt.label}"
        for i, opt in enumerate(reclaim.exit_options)
    ]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_reclaim_harden(path: Path) -> ReclaimHardenResult:
    """
    Orchestrate the full project reclaim analysis. Read-only — no database
    connection, no .env read, no file modification. `applied` is always False.
    """
    resolved = path.resolve()

    reclaim = run_reclaim_inspect(resolved)
    security = run_security_check(resolved)
    sovereignty = run_sovereignty_check(resolved)

    # Supabase check only if Supabase is detected by reclaim inspector
    supabase_detected = any(
        p.name == "supabase" and p.detected for p in reclaim.providers
    )
    supabase: SupabaseCheckResult | None = None
    rls: RLSHardenResult | None = None

    if supabase_detected:
        supabase = run_supabase_check(resolved)
        # RLS harden only if migrations directory exists
        migrations_dir = resolved / "supabase" / "migrations"
        if migrations_dir.is_dir():
            rls = run_rls_harden(resolved)

    generator_detected = next((g.name for g in reclaim.generators if g.detected), None)
    providers_detected = [p.name for p in reclaim.providers if p.detected]

    generated_actions = rls.summary.auto_blocks if rls is not None else 0
    manual_supabase = (
        sum(1 for s in supabase.remediation_steps if s.status == "manual")
        if supabase is not None
        else 0
    )
    manual_rls = rls.summary.todo_blocks if rls is not None else 0
    manual_actions = manual_supabase + manual_rls

    critical, important = _count_findings(security, sovereignty, rls)

    summary = ReclaimHardenSummary(
        generator_detected=generator_detected,
        providers_detected=providers_detected,
        control_level=_control_level(reclaim),
        secrets_exposure=reclaim.control_map.secrets_exposure,
        security_status=security.status,
        sovereignty_status=sovereignty.status,
        supabase_status=supabase.status if supabase is not None else None,
        rls_verdict=rls.review.verdict if rls is not None else None,
        generated_actions=generated_actions,
        manual_actions=manual_actions,
        critical_findings=critical,
        important_findings=important,
    )

    status = _compute_status(reclaim, security, supabase, rls)
    recommendations = _build_recommendations(reclaim, security, supabase, rls, resolved)
    exit_options = _build_exit_options(reclaim)

    return ReclaimHardenResult(
        path=resolved,
        status=status,
        summary=summary,
        reclaim=reclaim,
        security=security,
        sovereignty=sovereignty,
        supabase=supabase,
        rls=rls,
        recommendations=recommendations,
        exit_options=exit_options,
        read_only=True,
        applied=False,
    )
