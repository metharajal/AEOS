"""
AEOS Recovery Stage Model — ordered registry of the 10 sovereign recovery stages.

Read-only. No network. No secret reads. No file modification.
read_only: true · applied: false
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RecoveryStage:
    """One stage in the Total Sovereign Recovery arc."""

    id: str
    name: str
    objective: str
    prerequisites: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    expected_evidence: list[str] = field(default_factory=list)
    human_gate: str = ""
    rollback_path: str | None = None
    memory_record_type: str = ""
    allowed_agents: list[str] = field(default_factory=list)


def get_recovery_stages() -> list[RecoveryStage]:
    """Return the ordered registry of all 10 recovery stages."""
    return [
        RecoveryStage(
            id="stage_0_baseline",
            name="Baseline Assessment",
            objective=(
                "Understand the current state of the project: stack, providers, "
                "generators, risks, and control level."
            ),
            prerequisites=[],
            actions=[
                "aeos reclaim inspect --path <project>",
                "aeos reclaim harden --path <project> --memory-dir <dir>",
                "aeos reclaim recovery plan --path <project> --output <file>",
            ],
            risks=[
                "Misidentified generators or providers",
                "Unknown zones not detected by the inspector",
            ],
            expected_evidence=[
                "Harden report (Markdown) present in output",
                "Recovery plan (Markdown + JSON) generated",
                "MemoryRecord created in --memory-dir",
            ],
            human_gate=(
                "Human reviews the baseline report before proceeding to "
                "stage_1_governance."
            ),
            rollback_path=None,
            memory_record_type="reclaim_harden",
            allowed_agents=["Intake Agent", "Reclaim Agent", "Security Agent"],
        ),
        RecoveryStage(
            id="stage_1_governance",
            name="Governance Documentation",
            objective=(
                "Create the governance documentation baseline: architecture, "
                "decisions, security policy, AI policy, sovereignty, and "
                "recovery roadmap."
            ),
            prerequisites=["stage_0_baseline"],
            actions=[
                "Create ARCHITECTURE.md",
                "Create aeos.toml",
                "Create docs/RECOVERY.md",
                "Create docs/SECURITY.md",
                "Create docs/SOVEREIGNTY.md",
                "Create docs/DECISIONS.md",
                "Create docs/AI-DEVELOPMENT-POLICY.md",
                "Open PR for human review",
            ],
            risks=[
                "Documentation written without reading actual project files",
                "Inaccurate architecture map if project structure is unclear",
            ],
            expected_evidence=[
                "7 governance files created and reviewed",
                "PR opened and reviewed by human",
                "PR merged into main",
            ],
            human_gate="Human reviews all governance files before PR merge.",
            rollback_path=(
                "Delete governance files — documentation only, "
                "no application code changed."
            ),
            memory_record_type="governance_baseline",
            allowed_agents=["Recovery Agent", "PR Agent"],
        ),
        RecoveryStage(
            id="stage_2_secrets_env",
            name="Secrets and Environment Policy",
            objective=(
                "Stabilize the secrets and environment policy: verify "
                ".gitignore, rotate exposed credentials, confirm .env.example "
                "is complete."
            ),
            prerequisites=["stage_1_governance"],
            actions=[
                "Verify git log --all --full-history -- .env",
                "Confirm .gitignore includes .env, .env.*, !.env.example",
                "Verify .env.example is complete with all variable names",
                "Rotate credentials exposed in Git history",
                "Verify external generator integration is disabled",
                "Document secret management procedure in docs/SECURITY.md",
            ],
            risks=[
                "Credentials still valid in Git history after rotation",
                ".env.example incomplete — some variables undocumented",
                "External generator integration still active after decoupling",
            ],
            expected_evidence=[
                ".env absent from HEAD",
                ".gitignore verified and correct",
                "Credentials rotated",
                "PR merged",
            ],
            human_gate=(
                "Human confirms credential rotation. Human approves any "
                "git filter-repo history rewrite."
            ),
            rollback_path=(
                "Credential rotation is irreversible — plan and verify "
                "before executing."
            ),
            memory_record_type="secrets_env_stabilized",
            allowed_agents=["Security Agent", "PR Agent"],
        ),
        RecoveryStage(
            id="stage_3_database_rls",
            name="Database and RLS Hardening",
            objective=(
                "Harden database access: review RLS proposals, apply with "
                "human validation, document decisions."
            ),
            prerequisites=["stage_2_secrets_env"],
            actions=[
                "aeos supabase rls harden --path <project>",
                "Human reviews each SQL block before apply",
                "Apply RLS policies with explicit human gate",
                "Test with non-admin user after apply",
                "Document RLS decisions in docs/DECISIONS.md",
            ],
            risks=[
                "RLS too restrictive — application features break",
                "RLS too permissive — data remains exposed",
                "Apply executed without post-apply testing",
            ],
            expected_evidence=[
                "All RLS policies reviewed by human",
                "SQL applied with explicit human gate",
                "Post-apply test result documented",
                "PR merged",
            ],
            human_gate=(
                "Human reviews every SQL block before apply. "
                "Human confirms test result after apply."
            ),
            rollback_path=(
                "Rollback SQL prepared before any apply. Service role "
                "verified before switching to anon role."
            ),
            memory_record_type="rls_hardened",
            allowed_agents=["Database/RLS Agent", "Security Agent", "PR Agent"],
        ),
        RecoveryStage(
            id="stage_4_tests_ci",
            name="Tests and CI Gate",
            objective=(
                "Establish a test baseline and CI quality gate to prevent regressions."
            ),
            prerequisites=["stage_1_governance"],
            actions=[
                "Audit existing test setup",
                "Add smoke tests for critical flows",
                "Create .github/workflows/ci.yml",
                "Enable branch protection on main",
            ],
            risks=[
                "Tests pass on CI but fail locally",
                "Low test coverage gives false confidence",
            ],
            expected_evidence=[
                "CI green on PR",
                "Smoke tests passing",
                "Branch protection active",
                "PR merged",
            ],
            human_gate=("Human reviews test coverage before declaring stage complete."),
            rollback_path=(
                "Disable branch protection if CI blocks legitimate work. "
                "Add failing test as known failure."
            ),
            memory_record_type="ci_gate_active",
            allowed_agents=["Recovery Agent", "PR Agent"],
        ),
        RecoveryStage(
            id="stage_5_local_run",
            name="Local Run",
            objective=("Make the project runnable locally without cloud dependency."),
            prerequisites=["stage_1_governance"],
            actions=[
                "Document local run procedure in README",
                "Configure local database (e.g. Supabase CLI)",
                "Verify local run command works end-to-end",
            ],
            risks=[
                "Local database schema diverges from cloud schema",
                "Environment variables not fully documented in .env.example",
            ],
            expected_evidence=[
                "Project starts locally with documented run command",
                "README documents the local run procedure",
                "PR merged",
            ],
            human_gate=(
                "Human confirms local run works end-to-end before "
                "declaring stage complete."
            ),
            rollback_path="Revert README changes. No application code changed.",
            memory_record_type="local_run_possible",
            allowed_agents=["Recovery Agent", "PR Agent"],
        ),
        RecoveryStage(
            id="stage_6_portability",
            name="Portability",
            objective=(
                "Achieve full portability: Dockerfile, versioned migrations, "
                "reversible deployment."
            ),
            prerequisites=["stage_5_local_run"],
            actions=[
                "Add Dockerfile",
                "Add docker-compose.yml",
                "Export database schema as local migration files",
                "Document deployment target",
            ],
            risks=[
                "Docker image too large for target environment",
                "Migration files out of sync with cloud schema",
            ],
            expected_evidence=[
                "docker build succeeds",
                "docker-compose up starts the stack",
                "Migrations are reproducible on a fresh instance",
                "PR merged",
            ],
            human_gate=(
                "Human confirms Docker build and migration replay on a fresh instance."
            ),
            rollback_path=(
                "Remove Dockerfile and docker-compose. No production impact."
            ),
            memory_record_type="portability_achieved",
            allowed_agents=["Sovereignty Agent", "PR Agent"],
        ),
        RecoveryStage(
            id="stage_7_migration_readiness",
            name="Migration Readiness",
            objective=(
                "Assess and prepare migration to a more sovereign architecture, "
                "if the human has decided to migrate."
            ),
            prerequisites=["stage_6_portability"],
            actions=[
                "aeos migrate plan --path <project>",
                "Verify backup exists and is complete",
                "Dry-run migration",
                "Prepare rollback SQL",
                "Human approval before apply",
                "Apply migration",
                "Run post-migration tests",
                "Document decision in docs/DECISIONS.md",
            ],
            risks=[
                "Data loss without verified backup",
                "Schema mismatch post-migration",
                "Application broken after connection string switch",
            ],
            expected_evidence=[
                "Backup verified",
                "Dry-run passed",
                "Rollback path documented",
                "Post-migration tests green",
                "MemoryRecord created",
            ],
            human_gate=(
                "Human approves migration plan. Human confirms backup. "
                "Human confirms post-migration test result."
            ),
            rollback_path=(
                "Restore from backup. Revert connection strings. "
                "Test original stack before switching traffic."
            ),
            memory_record_type="migration_event",
            allowed_agents=[
                "Migration Agent",
                "Database/RLS Agent",
                "Security Agent",
                "PR Agent",
            ],
        ),
        RecoveryStage(
            id="stage_8_local_ai_continuation",
            name="Local AI Continuation",
            objective=(
                "Enable local-AI-first development continuation: configure "
                "local model, establish workflow, define context filtering rules."
            ),
            prerequisites=["stage_4_tests_ci"],
            actions=[
                "Configure local model in aeos.toml",
                "Document AI workflow in docs/AI-DEVELOPMENT-POLICY.md",
                "Establish branch + PR discipline",
                "Define context filtering rules",
            ],
            risks=[
                "Local model insufficient for complex tasks",
                "Context filtering too strict or too loose",
            ],
            expected_evidence=[
                "Local model operational",
                "AI workflow documented",
                "First feature developed via local AI with PR evidence",
            ],
            human_gate=(
                "Human reviews AI-generated code before merge. "
                "Human approves any frontier AI escalation."
            ),
            rollback_path=("Revert aeos.toml changes. No application code changed."),
            memory_record_type="local_ai_active",
            allowed_agents=[
                "Local AI Agent",
                "Frontier AI Escalation Agent",
                "PR Agent",
            ],
        ),
        RecoveryStage(
            id="stage_9_sovereign_operating_mode",
            name="Sovereign Operating Mode",
            objective=(
                "Maintain sovereignty over time: continuous audit, drift "
                "detection, periodic AEOS reports."
            ),
            prerequisites=[
                "stage_0_baseline",
                "stage_1_governance",
                "stage_2_secrets_env",
                "stage_4_tests_ci",
            ],
            actions=[
                "Schedule periodic aeos reclaim harden runs",
                "aeos memory timeline --project <name>",
                "Review periodic reports",
                "Update governance docs",
                "Track new external dependencies",
            ],
            risks=[
                "Sovereignty drift as new features add undocumented dependencies",
                "AI policy not enforced for new team members",
            ],
            expected_evidence=[
                "Timeline shows stable or improving trend",
                "New dependencies have ADRs",
                "AI policy reviewed periodically",
            ],
            human_gate=(
                "Human reviews each periodic report. Human approves any "
                "new external dependency."
            ),
            rollback_path=(
                "Remove undocumented dependency. Rotate newly exposed credentials."
            ),
            memory_record_type="periodic_audit",
            allowed_agents=["Operate Agent", "Memory Agent", "Security Agent"],
        ),
    ]


def get_stage_by_id(stage_id: str) -> RecoveryStage | None:
    """Return the stage matching stage_id, or None if not found."""
    for stage in get_recovery_stages():
        if stage.id == stage_id:
            return stage
    return None


def recovery_stage_to_dict(stage: RecoveryStage) -> dict[str, object]:
    """Serialize a RecoveryStage to a JSON-compatible dict."""
    return {
        "id": stage.id,
        "name": stage.name,
        "objective": stage.objective,
        "prerequisites": stage.prerequisites,
        "actions": stage.actions,
        "risks": stage.risks,
        "expected_evidence": stage.expected_evidence,
        "human_gate": stage.human_gate,
        "rollback_path": stage.rollback_path,
        "memory_record_type": stage.memory_record_type,
        "allowed_agents": stage.allowed_agents,
    }
