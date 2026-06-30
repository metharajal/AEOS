"""
AEOS Reclaim Recovery Plan — comprehensive recovery roadmap for an existing project.

Read-only. No network. No secret reads. No file modification of the audited project.
read_only: true · applied: false
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path

from aeos.reclaim.hardener import ReclaimHardenResult, run_reclaim_harden

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

_GITIGNORE_ENV_TOKENS: frozenset[str] = frozenset({".env", ".env.*", "*.env", "/.env"})


@dataclass
class LocalAIPolicy:
    can_do: list[str] = field(default_factory=list)
    requires_human_approval: list[str] = field(default_factory=list)
    may_require_frontier: list[str] = field(default_factory=list)
    must_never_send_to_frontier: list[str] = field(default_factory=list)


@dataclass
class FrontierAIRule:
    rule: str
    reason: str


@dataclass
class RecoveryPRRoadmapItem:
    pr_number: int
    title: str
    goal: str
    tasks: list[str] = field(default_factory=list)
    priority: str = "medium"
    prerequisite: str | None = None


@dataclass
class RecoveryBacklogCategory:
    name: str
    items: list[str] = field(default_factory=list)


@dataclass
class RecoveryPlan:
    command: str = "reclaim recovery plan"
    read_only: bool = True
    applied: bool = False
    project_path: str = ""
    project_name: str = ""
    status: str = "OK"
    current_architecture: dict[str, object] = field(default_factory=dict)
    control_status: dict[str, str] = field(default_factory=dict)
    security_recovery: dict[str, object] = field(default_factory=dict)
    sovereignty_recovery: dict[str, object] = field(default_factory=dict)
    database_recovery: dict[str, object] = field(default_factory=dict)
    governance_recovery: dict[str, object] = field(default_factory=dict)
    testing_ci_recovery: dict[str, object] = field(default_factory=dict)
    local_ai_policy: LocalAIPolicy = field(default_factory=LocalAIPolicy)
    frontier_ai_rules: list[FrontierAIRule] = field(default_factory=list)
    recovery_pr_roadmap: list[RecoveryPRRoadmapItem] = field(default_factory=list)
    development_continuation_backlog: list[RecoveryBacklogCategory] = field(
        default_factory=list
    )
    recommended_next_action: str = ""


# ---------------------------------------------------------------------------
# Static policies (no dynamic data)
# ---------------------------------------------------------------------------


def _build_local_ai_policy() -> LocalAIPolicy:
    return LocalAIPolicy(
        can_do=[
            "Read project files and identify architecture patterns",
            "Propose governance documents (README, ARCHITECTURE, DECISIONS)",
            "Generate RLS policy recommendations (human reviews before apply)",
            "Suggest refactoring steps and code improvements",
            "Draft commit messages and PR descriptions",
            "Analyze test coverage gaps and propose test cases",
            "Generate boilerplate code under explicit human review",
            "Run AEOS audit commands (reclaim harden, security check,"
            " sovereignty check)",
        ],
        requires_human_approval=[
            "Any change applied to the production database",
            "Any secret rotation or credential management",
            "Any deployment configuration change",
            "Any change to authentication or authorization logic",
            "Any migration applied to the live schema",
            "Any pull request merged to the main branch",
            "Any external service account modification",
        ],
        may_require_frontier=[
            "Complex refactoring requiring deep semantic understanding",
            "Architecture design decisions with long-term implications",
            "Security vulnerability analysis beyond pattern matching",
            "Interpreting ambiguous product requirements",
        ],
        must_never_send_to_frontier=[
            ".env files or any file containing secrets",
            "Database connection strings or credentials",
            "Customer data or personally identifiable information (PII)",
            "Production database dumps or exports",
            "API keys, tokens, or service role keys",
            "Any content from .env.local, .env.production, .env.staging",
            "Authentication credentials or session tokens",
        ],
    )


def _build_frontier_ai_rules() -> list[FrontierAIRule]:
    return [
        FrontierAIRule(
            rule="Never send secrets or credentials to frontier AI",
            reason="Secrets sent to frontier AI may be logged, cached, or exposed "
            "in training data.",
        ),
        FrontierAIRule(
            rule="Never send .env or environment files",
            reason=".env files contain keys that must remain local and never traverse "
            "external networks.",
        ),
        FrontierAIRule(
            rule="Never send customer data or PII",
            reason="Customer data must not leave the controlled environment without "
            "explicit consent and legal basis.",
        ),
        FrontierAIRule(
            rule="Never send database dumps or production data",
            reason="Production data must remain in the controlled environment. "
            "Use anonymized fixtures for AI assistance.",
        ),
        FrontierAIRule(
            rule="Explicit human approval required before any frontier AI escalation",
            reason="Frontier AI calls may incur cost and expose context outside the "
            "local environment.",
        ),
        FrontierAIRule(
            rule="Filter all context before sending — strip sensitive patterns",
            reason="Even innocuous-seeming files may reference credentials or PII "
            "indirectly. Filter before sending.",
        ),
    ]


# ---------------------------------------------------------------------------
# Dynamic PR roadmap
# ---------------------------------------------------------------------------


def _pr3_tasks(harden: ReclaimHardenResult) -> list[str]:
    if not harden.summary.supabase_status:
        return [
            "Document current database provider in ARCHITECTURE.md",
            "Create local migration files if not present",
            "Define database portability strategy",
        ]
    tasks: list[str] = []
    if harden.rls is not None:
        if harden.rls.summary.auto_blocks:
            tasks.append(
                f"Export {harden.rls.summary.auto_blocks} auto-generated RLS block(s): "
                "aeos supabase rls harden --path . --output /tmp/rls-proposal.sql"
            )
        if harden.rls.summary.todo_blocks:
            tasks.append(
                f"Manually review {harden.rls.summary.todo_blocks} RLS TODO block(s) "
                "before applying any migration"
            )
    tasks.extend(
        [
            "Enable RLS on all Supabase tables that lack it",
            "Add WITH CHECK clauses to all INSERT/UPDATE policies",
            "Test with a non-admin user to confirm RLS is enforced",
        ]
    )
    return tasks


def _build_recovery_pr_roadmap(
    harden: ReclaimHardenResult,
) -> list[RecoveryPRRoadmapItem]:
    cm = harden.reclaim.control_map

    pr1_tasks = [
        "Ensure .gitignore contains .env, .env.*, !.env.example",
        "Create .env.example with all required variable names (no values)",
        "Remove .env from Git tracking if currently tracked: git rm --cached .env",
    ]
    if cm.secrets_exposure == "confirmed":
        pr1_tasks.insert(
            0, "URGENT: Rotate all exposed credentials before anything else"
        )
    elif cm.secrets_exposure == "risk":
        pr1_tasks.insert(0, "Remove .env from tracking before the next push")

    return [
        RecoveryPRRoadmapItem(
            pr_number=1,
            title="Stabilize secrets and environment policy",
            goal="Ensure no secret is exposed in Git and .env is properly gitignored.",
            tasks=pr1_tasks,
            priority=(
                "critical" if cm.secrets_exposure in ("confirmed", "risk") else "high"
            ),
        ),
        RecoveryPRRoadmapItem(
            pr_number=2,
            title="Add governance documentation",
            goal="Create ARCHITECTURE.md, DECISIONS.md, SECURITY.md, SOVEREIGNTY.md.",
            tasks=[
                "Create ARCHITECTURE.md with project overview and component diagram",
                "Create docs/DECISIONS.md with first architecture decisions",
                "Create docs/SECURITY.md with security baseline",
                "Create docs/SOVEREIGNTY.md with provider list and exit strategy",
                "Optional: run aeos build scaffold to generate governance template",
            ],
            priority="high",
            prerequisite="PR 1",
        ),
        RecoveryPRRoadmapItem(
            pr_number=3,
            title=(
                "Harden database and RLS"
                if harden.summary.supabase_status
                else "Document database architecture"
            ),
            goal="Secure data access at the database layer.",
            tasks=_pr3_tasks(harden),
            priority="high" if harden.summary.supabase_status else "medium",
            prerequisite="PR 1",
        ),
        RecoveryPRRoadmapItem(
            pr_number=4,
            title="Add smoke tests",
            goal="Establish a minimal test baseline to detect regressions.",
            tasks=[
                "Create tests/ directory if not present",
                "Add smoke tests for critical user paths",
                "Add unit tests for authentication and data access logic",
                "Ensure all tests pass before continuing to PR 5",
            ],
            priority="medium",
            prerequisite="PR 2",
        ),
        RecoveryPRRoadmapItem(
            pr_number=5,
            title="Add CI quality gate",
            goal="Block merges without passing tests and quality checks.",
            tasks=[
                "Create .github/workflows/ci.yml",
                "Gate: lint + format + type check + test suite",
                "Gate: security scan (aeos security check or equivalent)",
                "Enable branch protection requiring CI to pass before merge",
            ],
            priority="medium",
            prerequisite="PR 4",
        ),
        RecoveryPRRoadmapItem(
            pr_number=6,
            title="Improve portability",
            goal="Reduce provider lock-in and prepare for migration if needed.",
            tasks=[
                "Add Dockerfile for reproducible local and production builds",
                "Add docker-compose.yml for local development stack",
                "Export database schema to local migration files",
                "Document local run commands in README.md",
                "Run aeos reclaim harden to verify portability score improved",
            ],
            priority="low" if cm.portability == "strong" else "medium",
            prerequisite="PR 2",
        ),
        RecoveryPRRoadmapItem(
            pr_number=7,
            title="Prepare AI-assisted development workflow",
            goal="Document and enforce the local-first AI development policy.",
            tasks=[
                "Create docs/AI-DEVELOPMENT-POLICY.md",
                "Define which tasks go to local AI vs. frontier AI",
                "Document frontier AI escalation rules (no .env, no secrets, no PII)",
                "Run aeos reclaim recovery plan to review and update the plan",
                "Schedule monthly aeos memory timeline review",
            ],
            priority="low",
            prerequisite="PR 2",
        ),
    ]


# ---------------------------------------------------------------------------
# Dynamic backlog
# ---------------------------------------------------------------------------


def _build_backlog(harden: ReclaimHardenResult) -> list[RecoveryBacklogCategory]:
    cm = harden.reclaim.control_map
    s = harden.summary

    stabilization: list[str] = [
        "Complete all PR 1-5 items before adding new features",
        "Run aeos reclaim harden after each PR to track progress",
        "Do not deploy to production until PR 1 (secrets) is complete",
    ]
    if cm.secrets_exposure != "none":
        stabilization.insert(0, "URGENT: Resolve secret exposure before any other work")

    security_items: list[str] = [
        "Implement Content Security Policy (CSP) headers",
        "Add rate limiting to all API endpoints",
        "Enable audit logging for sensitive operations",
        "Review all authentication flows for bypass risks",
        "Enforce HTTPS in all environments",
    ]
    if cm.secrets_exposure != "none":
        security_items.insert(0, "URGENT: Rotate all exposed credentials immediately")

    architecture_items: list[str] = [
        "Complete ARCHITECTURE.md with component diagram",
        "Document all external provider dependencies and exit paths",
        "Define API contract (OpenAPI or equivalent) before adding endpoints",
        "Document local development setup completely",
    ]
    if any(g.detected for g in harden.reclaim.generators):
        architecture_items.insert(
            0,
            f"Audit {s.generator_detected}-generated patterns and document ownership",
        )

    testing_items: list[str] = [
        "Add unit tests for all business logic",
        "Add integration tests for API routes and database access",
        "Add end-to-end tests for critical user flows before production",
        "Maintain >80% coverage on core business logic",
        "Add contract tests for any external provider integrations",
    ]

    dx_items: list[str] = [
        "Add pre-commit hooks: lint, format, type check",
        "Document local development setup in README.md",
        "Add docker-compose.yml for one-command local start",
        "Add Makefile or scripts/ for common developer tasks",
        "Document the AEOS command chain for this project",
    ]

    product_items: list[str] = [
        "Define feature roadmap with technical prerequisites",
        "Run aeos build plan before starting each new major feature",
        "Require aeos reclaim harden before each production release",
        "Schedule monthly sovereignty review using aeos memory timeline",
        "Document any intentional technical debt with exit conditions",
    ]

    return [
        RecoveryBacklogCategory(name="stabilization", items=stabilization),
        RecoveryBacklogCategory(name="security", items=security_items),
        RecoveryBacklogCategory(name="architecture", items=architecture_items),
        RecoveryBacklogCategory(name="testing", items=testing_items),
        RecoveryBacklogCategory(name="developer_experience", items=dx_items),
        RecoveryBacklogCategory(name="product_continuation", items=product_items),
    ]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _gitignore_protects_env(path: Path) -> bool:
    gitignore = path / ".gitignore"
    if not gitignore.is_file():
        return False
    try:
        text = gitignore.read_text(encoding="utf-8", errors="replace")
        lines = {line.strip() for line in text.splitlines()}
        return bool(lines & _GITIGNORE_ENV_TOKENS)
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def build_recovery_plan(path: Path) -> RecoveryPlan:
    """Build a full recovery plan for an existing project. Read-only."""
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"Path does not exist or is not a directory: {resolved}")

    harden = run_reclaim_harden(resolved)
    cm = harden.reclaim.control_map

    # ── Section 3 — Current Architecture ────────────────────────────────────
    current_arch: dict[str, object] = {
        "frontend": cm.frontend_code,
        "backend": cm.backend_runtime,
        "database": cm.database_schema,
        "auth": cm.auth,
        "deployment": cm.deployment,
        "portability": cm.portability,
        "detected_generators": [
            g.name for g in harden.reclaim.generators if g.detected
        ],
        "detected_providers": [p.name for p in harden.reclaim.providers if p.detected],
        "missing_docs": [
            a.asset for a in harden.reclaim.missing_assets if not a.present
        ],
    }

    # ── Section 4 — Control Status ────────────────────────────────────────
    git_present = (resolved / ".git").is_dir()
    ctrl: dict[str, str] = {
        "secrets": cm.secrets_control,
        "secrets_exposure": cm.secrets_exposure,
        "source_control": "git_present" if git_present else "no_git",
        "database": cm.database_schema,
        "deployment": cm.deployment,
        "portability": cm.portability,
    }

    # ── Section 5 — Security Recovery ─────────────────────────────────────
    immediate_blockers = [
        f.message for f in harden.security.findings if f.severity == "ERROR"
    ]
    sec_rec: dict[str, object] = {
        "status": harden.security.status,
        "immediate_blockers": immediate_blockers,
        "secret_exposure_status": cm.secrets_exposure,
        "gitignore_protects_env": _gitignore_protects_env(resolved),
        "env_example_exists": (resolved / ".env.example").is_file(),
        "env_currently_tracked": cm.secrets_control == "external",
        "critical_findings_count": len(immediate_blockers),
    }

    # ── Section 6 — Sovereignty Recovery ──────────────────────────────────
    ext_deps = [
        f"{p.name} ({', '.join(p.roles)})"
        for p in harden.reclaim.providers
        if p.detected and p.roles
    ]
    portability_risks = [
        f.message
        for f in harden.sovereignty.findings
        if f.severity in ("WARNING", "ERROR")
    ]
    exit_opts = [opt.label for opt in harden.reclaim.exit_options[:3]]
    sov_rec: dict[str, object] = {
        "status": harden.sovereignty.status,
        "external_dependencies": ext_deps,
        "portability_risks": portability_risks,
        "exit_strategy_options": exit_opts,
    }

    # ── Section 7 — Database Recovery ─────────────────────────────────────
    supabase_detected = (
        harden.supabase is not None and harden.supabase.supabase_detected
    )
    rls_todo_items: list[str] = []
    if harden.rls is not None:
        rls_todo_items = [
            f"RLS TODO: {b.table} — {b.risk_type}"
            for b in harden.rls.review.todo_blocks[:5]
        ]
    db_rec: dict[str, object] = {
        "supabase_detected": supabase_detected,
        "supabase_status": harden.supabase.status if harden.supabase else None,
        "rls_verdict": harden.rls.review.verdict if harden.rls else None,
        "generated_fixes_count": (harden.rls.summary.auto_blocks if harden.rls else 0),
        "manual_review_required": (harden.rls.summary.todo_blocks if harden.rls else 0),
        "manual_review_items": rls_todo_items,
    }

    # ── Section 8 — Governance Recovery ───────────────────────────────────
    gov_rec: dict[str, object] = {
        "missing_docs": [
            a.asset for a in harden.reclaim.missing_assets if not a.present
        ],
        "aeos_toml_present": (resolved / "aeos.toml").is_file(),
        "decisions_doc_present": (resolved / "docs" / "DECISIONS.md").is_file(),
        "security_doc_present": (resolved / "docs" / "SECURITY.md").is_file(),
        "sovereignty_doc_present": (resolved / "docs" / "SOVEREIGNTY.md").is_file(),
    }

    # ── Section 9 — Testing/CI Recovery ───────────────────────────────────
    tests_present = (
        (resolved / "tests").is_dir()
        or (resolved / "__tests__").is_dir()
        or (resolved / "test").is_dir()
    )
    ci_present = (resolved / ".github" / "workflows").is_dir()
    testing_ci: dict[str, object] = {
        "tests_directory_present": tests_present,
        "ci_workflow_present": ci_present,
        "tests_status": "present" if tests_present else "missing",
        "ci_status": "present" if ci_present else "missing",
        "recommended_baseline": [
            "Unit tests for all business logic",
            "Integration tests for API routes and database access",
            "End-to-end tests for critical user flows before production",
            "CI quality gate: lint + format + type check + tests must pass"
            " before merge",
        ],
    }

    return RecoveryPlan(
        command="reclaim recovery plan",
        read_only=True,
        applied=False,
        project_path=str(resolved),
        project_name=resolved.name,
        status=harden.status,
        current_architecture=current_arch,
        control_status=ctrl,
        security_recovery=sec_rec,
        sovereignty_recovery=sov_rec,
        database_recovery=db_rec,
        governance_recovery=gov_rec,
        testing_ci_recovery=testing_ci,
        local_ai_policy=_build_local_ai_policy(),
        frontier_ai_rules=_build_frontier_ai_rules(),
        recovery_pr_roadmap=_build_recovery_pr_roadmap(harden),
        development_continuation_backlog=_build_backlog(harden),
        recommended_next_action=harden.reclaim.recommended_next_action,
    )


def recovery_plan_to_dict(plan: RecoveryPlan) -> dict[str, object]:
    return {
        "command": plan.command,
        "read_only": plan.read_only,
        "applied": plan.applied,
        "project_path": plan.project_path,
        "project_name": plan.project_name,
        "status": plan.status,
        "current_architecture": plan.current_architecture,
        "control_status": dict(plan.control_status),
        "security_recovery": plan.security_recovery,
        "sovereignty_recovery": plan.sovereignty_recovery,
        "database_recovery": plan.database_recovery,
        "governance_recovery": plan.governance_recovery,
        "testing_ci_recovery": plan.testing_ci_recovery,
        "local_ai_policy": {
            "can_do": plan.local_ai_policy.can_do,
            "requires_human_approval": plan.local_ai_policy.requires_human_approval,
            "may_require_frontier": plan.local_ai_policy.may_require_frontier,
            "must_never_send_to_frontier": (
                plan.local_ai_policy.must_never_send_to_frontier
            ),
        },
        "frontier_ai_rules": [
            {"rule": r.rule, "reason": r.reason} for r in plan.frontier_ai_rules
        ],
        "recovery_pr_roadmap": [
            {
                "pr_number": item.pr_number,
                "title": item.title,
                "goal": item.goal,
                "tasks": item.tasks,
                "priority": item.priority,
                "prerequisite": item.prerequisite,
            }
            for item in plan.recovery_pr_roadmap
        ],
        "development_continuation_backlog": [
            {"name": cat.name, "items": cat.items}
            for cat in plan.development_continuation_backlog
        ],
        "recommended_next_action": plan.recommended_next_action,
    }


def _join_str_list(val: object, fallback: str = "none") -> str:
    if not isinstance(val, list):
        return fallback
    joined = ", ".join(str(item) for item in val if isinstance(item, str))
    return joined or fallback


def build_recovery_markdown(plan: RecoveryPlan) -> str:
    """Build Markdown for an exported recovery plan. No network, no secrets."""
    date_str = datetime.date.today().isoformat()
    _SEP = "---"

    def _h(s: str) -> str:
        return f"## {s}"

    def _items(lst: list[str]) -> str:
        return "\n".join(f"- {item}" for item in lst) if lst else "- (none)"

    lines: list[str] = [
        "# AEOS Recovery Plan",
        "",
        "Generated by:  `aeos reclaim recovery plan`",
        f"Date:          {date_str}",
        f"Project:       {plan.project_path}",
        "read_only:     true",
        "applied:       false",
        "",
        _SEP,
        "",
        f"## Status: {plan.status}",
        "",
        _SEP,
        "",
        _h("1. Project Identity"),
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Path | `{plan.project_path}` |",
        f"| Name | {plan.project_name} |",
        "| Detected generators | "
        + _join_str_list(plan.current_architecture.get("detected_generators"))
        + " |",
        "| Detected providers | "
        + _join_str_list(plan.current_architecture.get("detected_providers"))
        + " |",
        "",
        _SEP,
        "",
        _h("2. Current Architecture"),
        "",
        "| Dimension | Status |",
        "|---|---|",
        f"| Frontend | {plan.current_architecture.get('frontend', 'unknown')} |",
        f"| Backend | {plan.current_architecture.get('backend', 'unknown')} |",
        f"| Database schema | {plan.current_architecture.get('database', 'unknown')} |",
        f"| Auth | {plan.current_architecture.get('auth', 'unknown')} |",
        f"| Deployment | {plan.current_architecture.get('deployment', 'unknown')} |",
        f"| Portability | {plan.current_architecture.get('portability', 'unknown')} |",
        "",
        _SEP,
        "",
        _h("3. Control Status"),
        "",
        "| Control | Status |",
        "|---|---|",
        f"| Secrets | {plan.control_status.get('secrets', 'unknown')} |",
        "| Secrets exposure | "
        f"{plan.control_status.get('secrets_exposure', 'unknown')} |",
        f"| Source control | {plan.control_status.get('source_control', 'unknown')} |",
        f"| Database | {plan.control_status.get('database', 'unknown')} |",
        f"| Deployment | {plan.control_status.get('deployment', 'unknown')} |",
        f"| Portability | {plan.control_status.get('portability', 'unknown')} |",
        "",
        _SEP,
        "",
        _h("4. Security Recovery"),
        "",
        f"**Status:** {plan.security_recovery.get('status', 'OK')}",
        "**Secret exposure:** "
        f"{plan.security_recovery.get('secret_exposure_status', 'unknown')}",
        "",
        "**Immediate blockers:**",
    ]

    blockers = plan.security_recovery.get("immediate_blockers", [])
    if isinstance(blockers, list):
        lines.extend(f"- {b}" for b in blockers) if blockers else lines.append(
            "- No immediate security blockers."
        )
    else:
        lines.append("- No immediate security blockers.")

    gitignore_ok = plan.security_recovery.get("gitignore_protects_env", False)
    env_example = plan.security_recovery.get("env_example_exists", False)
    lines += [
        "",
        "| Check | Status |",
        "|---|---|",
        f"| .gitignore protects .env | {'yes' if gitignore_ok else 'no'} |",
        f"| .env.example exists | {'yes' if env_example else 'no'} |",
        "",
        _SEP,
        "",
        _h("5. Sovereignty Recovery"),
        "",
        f"**Status:** {plan.sovereignty_recovery.get('status', 'OK')}",
        "",
        "**External dependencies:**",
    ]

    ext = plan.sovereignty_recovery.get("external_dependencies", [])
    if isinstance(ext, list):
        lines.extend(f"- {d}" for d in ext) if ext else lines.append(
            "- No external dependencies detected."
        )
    else:
        lines.append("- No external dependencies detected.")

    lines += ["", "**Exit strategy options (top 3):**"]
    exits = plan.sovereignty_recovery.get("exit_strategy_options", [])
    if isinstance(exits, list):
        lines.extend(
            f"{i + 1}. {opt}" for i, opt in enumerate(exits)
        ) if exits else lines.append("- No exit options defined.")

    supabase_status = plan.database_recovery.get("supabase_status")
    rls_verdict = plan.database_recovery.get("rls_verdict")
    generated_fixes = plan.database_recovery.get("generated_fixes_count", 0)
    manual_review = plan.database_recovery.get("manual_review_required", 0)

    lines += [
        "",
        _SEP,
        "",
        _h("6. Database and RLS Recovery"),
        "",
        "| Field | Value |",
        "|---|---|",
        "| Supabase detected | "
        f"{'yes' if plan.database_recovery.get('supabase_detected') else 'no'} |",
        f"| Supabase status | {supabase_status or 'N/A'} |",
        f"| RLS verdict | {rls_verdict or 'N/A'} |",
        f"| Auto-generated fixes | {generated_fixes} |",
        f"| Manual review required | {manual_review} |",
        "",
        _SEP,
        "",
        _h("7. Governance Recovery"),
        "",
        "| Document | Status |",
        "|---|---|",
    ]

    def _gov(key: str) -> str:
        return "present" if plan.governance_recovery.get(key) else "missing"

    lines += [
        f"| aeos.toml | {_gov('aeos_toml_present')} |",
        f"| docs/DECISIONS.md | {_gov('decisions_doc_present')} |",
        f"| docs/SECURITY.md | {_gov('security_doc_present')} |",
        f"| docs/SOVEREIGNTY.md | {_gov('sovereignty_doc_present')} |",
        "",
        _SEP,
        "",
        _h("8. Testing and CI Recovery"),
        "",
        "| Check | Status |",
        "|---|---|",
        "| Tests directory | "
        f"{plan.testing_ci_recovery.get('tests_status', 'unknown')} |",
        f"| CI quality gate | {plan.testing_ci_recovery.get('ci_status', 'unknown')} |",
        "",
        _SEP,
        "",
        _h("9. Local AI Development Policy"),
        "",
        "**Local AI can do by default:**",
    ]
    lines.append(_items(plan.local_ai_policy.can_do))
    lines += ["", "**Requires human approval:**"]
    lines.append(_items(plan.local_ai_policy.requires_human_approval))
    lines += ["", "**May require frontier AI:**"]
    lines.append(_items(plan.local_ai_policy.may_require_frontier))
    lines += ["", "**Must NEVER send to frontier AI:**"]
    lines.append(_items(plan.local_ai_policy.must_never_send_to_frontier))

    lines += [
        "",
        _SEP,
        "",
        _h("10. Frontier AI Escalation Rules"),
        "",
    ]
    for rule in plan.frontier_ai_rules:
        lines.append(f"**Rule:** {rule.rule}")
        lines.append(f"**Reason:** {rule.reason}")
        lines.append("")

    lines += [
        _SEP,
        "",
        _h("11. Recovery PR Roadmap"),
        "",
    ]
    for item in plan.recovery_pr_roadmap:
        prereq = f" (requires: {item.prerequisite})" if item.prerequisite else ""
        lines += [
            f"### PR {item.pr_number} — {item.title} [{item.priority}]{prereq}",
            "",
            f"**Goal:** {item.goal}",
            "",
            "**Tasks:**",
        ]
        lines.extend(f"- [ ] {task}" for task in item.tasks)
        lines.append("")

    lines += [
        _SEP,
        "",
        _h("12. Development Continuation Backlog"),
        "",
    ]
    for cat in plan.development_continuation_backlog:
        lines.append(f"### {cat.name.replace('_', ' ').title()}")
        lines.append("")
        lines.extend(f"- {item}" for item in cat.items)
        lines.append("")

    lines += [
        _SEP,
        "",
        _h("13. Recommended Next Action"),
        "",
        plan.recommended_next_action,
        "",
        _SEP,
        "",
        "> **No correction has been applied.** This plan is read-only.",
        "> `read_only: true` · `applied: false`",
        "> No file in the audited project was modified.",
        "> No database connection was opened.",
        "> No secret was read or displayed.",
    ]

    return "\n".join(lines) + "\n"
