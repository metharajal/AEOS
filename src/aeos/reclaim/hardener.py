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
class RemediationPhase:
    id: str  # "phase_0" … "phase_4"
    label: str
    priority: str  # "critical" | "high" | "medium" | "low"
    goal: str
    why_it_matters: str
    actions: list[str]
    automation_level: str  # "manual" | "assisted" | "generatable"
    expected_outcome: str
    risk_if_skipped: str


@dataclass
class RemediationPlan:
    phases: list[RemediationPhase]
    phases_count: int
    immediate_actions_count: int  # Phase 0 action count
    manual_actions_count: int  # actions in manual phases
    generatable_actions_count: int  # RLS auto-generated blocks
    strategic_options_count: int  # always 5


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
    remediation_plan: RemediationPlan | None = None
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


def _build_remediation_plan(
    summary: ReclaimHardenSummary,
    reclaim: ReclaimInspectResult,
    security: SecurityCheckResult,
    rls: RLSHardenResult | None,
    path: Path,
) -> RemediationPlan:
    """Build a 5-phase remediation plan from audit sub-results. Read-only."""
    path_str = str(path)
    cm = reclaim.control_map

    # ── Phase 0 — Immediate security stabilization ───────────────────────────
    p0_priority = (
        "critical"
        if cm.secrets_exposure in ("confirmed", "risk") or summary.critical_findings > 0
        else "medium"
    )
    p0_actions: list[str] = []
    if cm.secrets_exposure == "confirmed":
        p0_actions.append("Rotate all exposed credentials — they are in Git history.")
        p0_actions.append("Remove .env from Git tracking: git rm --cached .env")
        p0_actions.append("Add .env to .gitignore and push a clean commit.")
    elif cm.secrets_exposure == "risk":
        p0_actions.append("Remove .env from Git tracking before the next push.")
        p0_actions.append("Rotate keys as a precaution even if not yet confirmed.")
    for sf in security.findings:
        if sf.severity == "ERROR":
            p0_actions.append(f"Fix: {sf.message} ({sf.location})")
    if not p0_actions:
        p0_actions.append("No immediate security blocker — proceed to Phase 1.")

    phase_0 = RemediationPhase(
        id="phase_0",
        label="Immediate security stabilization",
        priority=p0_priority,
        goal="Neutralize all active security risks before any other action.",
        why_it_matters=(
            "Exposed credentials remain active until rotated. Any push or deployment "
            "before rotation extends the breach window."
        ),
        actions=p0_actions,
        automation_level="manual",
        expected_outcome=(
            "No exposed credentials in Git history. No active security blockers. "
            "Baseline is safe to continue."
        ),
        risk_if_skipped=(
            "Credentials remain compromised. Any deployment amplifies the breach. "
            "Security findings block safe migration."
        ),
    )

    # ── Phase 1 — Database and RLS hardening ─────────────────────────────────
    if rls is not None:
        if rls.review.verdict == "BLOCKED":
            p1_priority = "critical"
        elif rls.review.verdict == "WARNING":
            p1_priority = "high"
        else:
            p1_priority = "medium"
    elif summary.supabase_status is not None:
        p1_priority = "high"
    else:
        p1_priority = "low"

    p1_actions: list[str] = []
    if rls is not None:
        if rls.summary.auto_blocks:
            p1_actions.append(
                f"Export {rls.summary.auto_blocks} auto-generated RLS block(s): "
                f"`aeos supabase rls harden --path {path_str} "
                "--output /tmp/rls-proposal.sql --force-warning`"
            )
        if rls.summary.todo_blocks:
            p1_actions.append(
                f"Review {rls.summary.todo_blocks} manual RLS TODO block(s) "
                "before applying any migration."
            )
        if rls.review.verdict == "BLOCKED":
            p1_actions.append(
                "Resolve blocked migration patterns before exporting any SQL."
            )
    if summary.supabase_status in ("ERROR", "CRITICAL"):
        p1_actions.append(
            "Run `aeos supabase check` and complete all critical remediation steps."
        )
    if not p1_actions:
        p1_actions.append(
            "No Supabase or RLS detected — database hardening not applicable."
        )

    p1_automation = (
        "generatable" if rls is not None and rls.summary.auto_blocks > 0 else "manual"
    )

    phase_1 = RemediationPhase(
        id="phase_1",
        label="Database and RLS hardening",
        priority=p1_priority,
        goal="Secure data access at the database layer before any migration.",
        why_it_matters=(
            "Permissive RLS policies expose rows to unauthorized users. "
            "SQL blocks can be auto-generated — but must be human-reviewed "
            "before apply."
        ),
        actions=p1_actions,
        automation_level=p1_automation,
        expected_outcome=(
            "RLS policies reviewed. Auto-generated SQL exported and inspected. "
            "No permissive SELECT or missing WITH CHECK clauses."
        ),
        risk_if_skipped=(
            "Data remains accessible to unauthenticated or over-privileged users "
            "even after migration."
        ),
    )

    # ── Phase 2 — Application control recovery ───────────────────────────────
    any_generator = any(g.detected for g in reclaim.generators)
    p2_priority = "high" if any_generator else "medium"

    p2_actions: list[str] = []
    if any_generator:
        gen_name = summary.generator_detected or "the generator"
        p2_actions.append(
            f"Audit all {gen_name}-specific patterns in the codebase "
            "(`.lovable/`, `src/integrations/supabase/`, etc.)."
        )
        p2_actions.append(
            "Replace generator-managed Supabase client with a project-owned client."
        )
        p2_actions.append(
            "Document all architecture decisions made implicitly by the generator."
        )
    if cm.backend_runtime in ("likely_external", "external"):
        p2_actions.append(
            "Identify if a local backend exists or must be created "
            "(`server/`, `api/`, `backend/`)."
        )
    if not p2_actions:
        p2_actions.append(
            "Application layer appears controlled — document ownership explicitly."
        )

    phase_2 = RemediationPhase(
        id="phase_2",
        label="Application control recovery",
        priority=p2_priority,
        goal="Recover technical ownership of the application layer.",
        why_it_matters=(
            "Generator-managed code contains implicit decisions about stack, auth, "
            "and API patterns. Until documented and owned, evolution depends on "
            "the generator platform."
        ),
        actions=p2_actions,
        automation_level="assisted",
        expected_outcome=(
            "Every architectural decision is documented and consciously owned. "
            "No hidden generator dependencies block future evolution."
        ),
        risk_if_skipped=(
            "Application evolution remains tied to the generator. "
            "Technical debt accumulates invisibly."
        ),
    )

    # ── Phase 3 — Portability preparation ────────────────────────────────────
    p3_priority = "medium" if cm.portability in ("weak", "partial") else "low"

    p3_actions: list[str] = []
    if cm.deployment in ("likely_external", "external"):
        p3_actions.append(
            "Add a Dockerfile and docker-compose.yml to enable local execution."
        )
    if cm.database_schema in ("missing", "partial"):
        p3_actions.append(
            "Export the current database schema to local migration files."
        )
    if cm.backend_runtime in ("likely_external", "external"):
        p3_actions.append(
            "Create a local backend directory (`server/` or `api/`) with a stub."
        )
    p3_actions.append(
        "Run `aeos reclaim inspect` after each improvement "
        "to track portability score progress."
    )
    if not p3_actions or len(p3_actions) == 1:
        p3_actions.insert(0, "Portability is already partial — focus on Dockerfile.")

    phase_3 = RemediationPhase(
        id="phase_3",
        label="Portability preparation",
        priority=p3_priority,
        goal="Prepare the project for a possible provider exit.",
        why_it_matters=(
            "Without Dockerfile, local schema, and local backend, "
            "migration to any alternative stack costs significantly more. "
            "Portability should be built incrementally, not urgently."
        ),
        actions=p3_actions,
        automation_level="assisted",
        expected_outcome=(
            "Project can be cloned, started locally, and deployed to a different "
            "provider without requiring the original generator platform."
        ),
        risk_if_skipped=(
            "When migration becomes necessary (cost, compliance, platform change), "
            "it will be significantly more expensive and disruptive."
        ),
    )

    # ── Phase 4 — Strategic exit path ────────────────────────────────────────
    exit_labels = (
        [opt.label for opt in reclaim.exit_options[:3]]
        if reclaim.exit_options
        else ["Stay and secure", "Migrate to own account", "Self-host"]
    )
    first_exit = exit_labels[0] if exit_labels else "Stay and secure"

    p4_actions: list[str] = [
        "Review the 5 strategic exit options and select a target trajectory.",
        f"Likely near-term path: {first_exit}.",
        "Document the chosen target architecture in `docs/governance/`.",
        "Define a migration timeline with milestones.",
        "Run `aeos reclaim harden --output` monthly to track progress.",
    ]

    phase_4 = RemediationPhase(
        id="phase_4",
        label="Strategic exit path",
        priority="low",
        goal="Choose and plan the long-term target architecture.",
        why_it_matters=(
            "Without a defined trajectory, teams stay on the current provider "
            "by inertia. A documented plan makes migration a decision, not a crisis."
        ),
        actions=p4_actions,
        automation_level="manual",
        expected_outcome=(
            "Team has a defined, documented migration target. "
            "The next `aeos reclaim harden` run will show measurable progress."
        ),
        risk_if_skipped=(
            "Vendor lock-in accumulates. When migration becomes mandatory "
            "(compliance, cost, platform EOL), the team has no plan."
        ),
    )

    phases = [phase_0, phase_1, phase_2, phase_3, phase_4]

    manual_count = sum(
        len(ph.actions) for ph in phases if ph.automation_level == "manual"
    )

    return RemediationPlan(
        phases=phases,
        phases_count=len(phases),
        immediate_actions_count=len(phase_0.actions),
        manual_actions_count=manual_count,
        generatable_actions_count=summary.generated_actions,
        strategic_options_count=len(reclaim.exit_options),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_harden_report(result: ReclaimHardenResult) -> str:
    """Build the Markdown content of an exported reclaim harden report.

    Safe to call any time after run_reclaim_harden returns. Reads nothing
    from the filesystem and contains no secret values.
    """
    import datetime

    date_str = datetime.date.today().isoformat()
    s = result.summary

    _SEP = "---"

    def _status_icon(v: str) -> str:
        return {"OK": "OK ✓", "WARNING": "WARNING ⚠", "ERROR": "ERROR ✗"}.get(v, v)

    lines: list[str] = [
        "# AEOS Reclaim Harden Report",
        "",
        "Generated by:  `aeos reclaim harden --output`",
        f"Date:          {date_str}",
        f"Project:       {result.path}",
        "read_only:     true",
        "applied:       false",
        "",
        _SEP,
        "",
        f"## Status: {_status_icon(result.status)}",
        "",
        _SEP,
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Generator detected | {s.generator_detected or 'none'} |",
        f"| Providers detected | {', '.join(s.providers_detected) if s.providers_detected else 'none'} |",  # noqa: E501
        f"| Control level | {s.control_level} |",
        f"| Secrets exposure | {s.secrets_exposure} |",
        f"| Security | {_status_icon(s.security_status)} |",
        f"| Sovereignty | {_status_icon(s.sovereignty_status)} |",
    ]

    if s.supabase_status is not None:
        lines.append(f"| Supabase | {_status_icon(s.supabase_status)} |")
    if s.rls_verdict is not None:
        _rls_icons = {"PASS": "PASS ✓", "WARNING": "WARNING ⚠", "BLOCKED": "BLOCKED ✗"}
        rls_icon = _rls_icons.get(s.rls_verdict, s.rls_verdict)
        lines.append(f"| RLS verdict | {rls_icon} |")

    lines += [
        f"| Critical findings | {s.critical_findings} |",
        f"| Important findings | {s.important_findings} |",
        f"| Auto-generatable SQL blocks | {s.generated_actions} |",
        f"| Manual actions required | {s.manual_actions} |",
        "",
        _SEP,
    ]

    if s.critical_findings:
        lines += ["", "## Critical Risks", ""]
        for sf in result.security.findings:
            if sf.severity == "ERROR":
                lines.append(f"- **[security]** {sf.message}")
        for svf in result.sovereignty.findings:
            if svf.severity == "ERROR":
                lines.append(f"- **[sovereignty]** {svf.message}")
        if result.rls is not None:
            for rf in result.rls.inspect.findings:
                if rf.severity == "ERROR":
                    lines.append(f"- **[rls]** `{rf.table}` — {rf.rule}: {rf.message}")
        lines += ["", _SEP]

    if s.important_findings:
        lines += ["", "## Important Risks", ""]
        shown = 0
        for sf in result.security.findings:
            if sf.severity == "WARNING" and shown < 5:
                lines.append(f"- [security] {sf.message}")
                shown += 1
        for svf in result.sovereignty.findings:
            if svf.severity == "WARNING" and shown < 8:
                lines.append(f"- [sovereignty] {svf.message}")
                shown += 1
        if result.rls is not None:
            for rf in result.rls.inspect.findings:
                if rf.severity == "WARNING" and shown < 10:
                    lines.append(f"- [rls] `{rf.table}` — {rf.rule}: {rf.message}")
                    shown += 1
        lines += ["", _SEP]

    if s.generated_actions:
        lines += [
            "",
            "## Generatable Fixes",
            "",
            f"{s.generated_actions} auto-generated RLS block(s) ready.",
            "",
            "Export with:",
            "",
            "```",
            f"aeos supabase rls harden --path {result.path}"
            " --output /tmp/rls-proposal.sql --force-warning",
            "```",
            "",
            _SEP,
        ]

    if s.manual_actions:
        lines += ["", "## Manual Actions Required", ""]
        if result.rls is not None and result.rls.summary.todo_blocks:
            lines.append(
                f"- Review {result.rls.summary.todo_blocks} RLS TODO block(s) "
                "before applying any migration."
            )
        if result.supabase is not None:
            manual_steps = [
                step
                for step in result.supabase.remediation_steps
                if step.status == "manual"
            ]
            for step in manual_steps[:5]:
                lines.append(f"- [supabase] {step.action}")
        lines += ["", _SEP]

    lines += ["", "## Recommendations", ""]
    for i, rec in enumerate(result.recommendations, start=1):
        lines.append(f"{i}. {rec}")

    lines += ["", _SEP, "", "## Exit Options", ""]
    for opt in result.exit_options:
        lines.append(f"- {opt}")

    # ── Remediation Plan section ─────────────────────────────────────────────
    if result.remediation_plan is not None:
        plan = result.remediation_plan
        lines += [
            "",
            _SEP,
            "",
            "## Remediation Plan",
            "",
            f"{plan.phases_count} phases · "
            f"{plan.immediate_actions_count} immediate actions · "
            f"{plan.manual_actions_count} manual · "
            f"{plan.generatable_actions_count} generatable · "
            f"{plan.strategic_options_count} strategic paths",
        ]
        _PRIORITY_ICON = {
            "critical": "🔴 critical",
            "high": "🟠 high",
            "medium": "🟡 medium",
            "low": "🟢 low",
        }
        for phase in plan.phases:
            pid = phase.id.replace("_", " ").title()
            prio_label = _PRIORITY_ICON.get(phase.priority, phase.priority)
            lines += [
                "",
                f"### {pid} — {phase.label} [{prio_label}]",
                "",
                f"**Goal:** {phase.goal}",
                "",
                f"**Why it matters:** {phase.why_it_matters}",
                "",
                "**Actions:**",
            ]
            for action in phase.actions:
                lines.append(f"- {action}")
            lines += [
                "",
                f"**Automation level:** {phase.automation_level}",
                "",
                f"**Expected outcome:** {phase.expected_outcome}",
                "",
                f"**Risk if skipped:** {phase.risk_if_skipped}",
            ]

    lines += [
        "",
        _SEP,
        "",
        "> **No correction has been applied.** This report is read-only.",
        "> `read_only: true` · `applied: false`",
        "> No file in the audited project was modified.",
        "> No database connection was opened.",
        "> No secret was read or displayed.",
    ]

    return "\n".join(lines) + "\n"


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
    remediation_plan = _build_remediation_plan(
        summary, reclaim, security, rls, resolved
    )

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
        remediation_plan=remediation_plan,
        read_only=True,
        applied=False,
    )
