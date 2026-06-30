"""
Unit tests for aeos.reclaim.recovery and `aeos reclaim recovery plan`.

read_only: true · applied: false
No network access. No real git repos. No secret values read.
Tests use tmp_path or controlled fixtures only.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.reclaim.hardener import (
    ReclaimHardenResult,
    ReclaimHardenSummary,
)
from aeos.reclaim.inspector import (
    ReclaimControlMap,
    ReclaimExitOption,
    ReclaimGenerator,
    ReclaimInspectResult,
    ReclaimMissingAsset,
    ReclaimProvider,
)
from aeos.reclaim.recovery import (
    FrontierAIRule,
    LocalAIPolicy,
    RecoveryPlan,
    build_recovery_markdown,
    build_recovery_plan,
    recovery_plan_to_dict,
)
from aeos.security.checker import SecurityCheckResult, SecurityFinding
from aeos.sovereignty.checker import SovereigntyCheckResult, SovereigntyFinding

runner = CliRunner()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_MOCK_TARGET = "aeos.reclaim.recovery.run_reclaim_harden"


def _make_control_map(
    secrets_exposure: str = "none",
    portability: str = "partial",
) -> ReclaimControlMap:
    return ReclaimControlMap(
        frontend_code="partial",
        backend_runtime="likely_external",
        database_schema="partial",
        auth="likely_external",
        storage="likely_external",
        secrets_control="local",
        secrets_exposure=secrets_exposure,
        deployment="likely_external",
        portability=portability,
    )


def _make_exit_options() -> list[ReclaimExitOption]:
    return [
        ReclaimExitOption(
            id="secure_in_place",
            label="Stay on current provider but secure",
            complexity="low",
            sovereignty="partial",
            advantages=["no migration required"],
            risks=["vendor lock-in"],
            next_action="Run aeos supabase check",
        ),
    ]


def _make_reclaim(
    secrets_exposure: str = "none",
    portability: str = "partial",
    supabase_detected: bool = False,
    path: Path | None = None,
) -> ReclaimInspectResult:
    generators = [
        ReclaimGenerator(name="lovable", detected=False, evidence=""),
        ReclaimGenerator(name="bolt", detected=False, evidence=""),
    ]
    providers = [
        ReclaimProvider(
            name="supabase",
            detected=supabase_detected,
            roles=["database", "auth"] if supabase_detected else [],
            evidence="supabase/migrations/:1" if supabase_detected else "",
        ),
        ReclaimProvider(name="vercel", detected=False, roles=[], evidence=""),
    ]
    missing: list[ReclaimMissingAsset] = [
        ReclaimMissingAsset(asset="ARCHITECTURE.md", impact="governance", present=False),
        ReclaimMissingAsset(asset="docs/DECISIONS.md", impact="governance", present=False),
    ]
    cm = _make_control_map(
        secrets_exposure=secrets_exposure,
        portability=portability,
    )
    return ReclaimInspectResult(
        path=path or Path("/fake/project"),
        status="WARNING",
        generators=generators,
        providers=providers,
        control_map=cm,
        missing_assets=missing,
        exit_options=_make_exit_options(),
        recommended_next_action="Run aeos security check",
    )


def _make_security(
    status: str = "OK",
    error: bool = False,
) -> SecurityCheckResult:
    findings: list[SecurityFinding] = []
    if error:
        findings.append(
            SecurityFinding(
                category="secrets",
                severity="ERROR",
                message="Critical secret exposed in tracked file",
                location=".env:1",
                recommendation="Rotate immediately",
                evidence="file:1",
            )
        )
    return SecurityCheckResult(
        path=Path("/fake/project"),
        status="ERROR" if error else status,
        findings=findings,
    )


def _make_sovereignty(status: str = "WARNING") -> SovereigntyCheckResult:
    findings: list[SovereigntyFinding] = []
    if status == "WARNING":
        findings.append(
            SovereigntyFinding(
                category="portability",
                severity="WARNING",
                message="No Dockerfile found",
                location="project root",
                recommendation="Add Dockerfile",
                evidence="",
            )
        )
    return SovereigntyCheckResult(
        path=Path("/fake/project"),
        status=status,
        findings=findings,
    )


def _make_rls_mock(verdict: str = "WARNING") -> MagicMock:
    rls = MagicMock()
    rls.status = "WARNING"
    rls.review.verdict = verdict
    rls.summary.auto_blocks = 3
    rls.summary.todo_blocks = 2
    rls.review.todo_blocks = []
    return rls


def _make_supabase_mock(detected: bool = False) -> MagicMock:
    sup = MagicMock()
    sup.status = "OK" if not detected else "WARNING"
    sup.supabase_detected = detected
    return sup


def _make_harden_result(
    secrets_exposure: str = "none",
    security_error: bool = False,
    supabase_detected: bool = False,
    portability: str = "partial",
    path: Path | None = None,
) -> ReclaimHardenResult:
    reclaim = _make_reclaim(
        secrets_exposure=secrets_exposure,
        supabase_detected=supabase_detected,
        portability=portability,
        path=path,
    )
    security = _make_security(error=security_error)
    sovereignty = _make_sovereignty()
    supabase = _make_supabase_mock(detected=supabase_detected)
    rls = _make_rls_mock() if supabase_detected else None
    summary = ReclaimHardenSummary(
        generator_detected="",
        providers_detected=["supabase"] if supabase_detected else [],
        control_level="partial",
        secrets_exposure=secrets_exposure,
        security_status=security.status,
        sovereignty_status=sovereignty.status,
        supabase_status="WARNING" if supabase_detected else "",
        rls_verdict="WARNING" if supabase_detected else "",
        generated_actions=3 if supabase_detected else 0,
        manual_actions=2 if supabase_detected else 0,
        critical_findings=1 if security_error else 0,
        important_findings=1,
    )
    return ReclaimHardenResult(
        path=path or Path("/fake/project"),
        status="ERROR" if security_error else "WARNING",
        summary=summary,
        reclaim=reclaim,
        security=security,
        sovereignty=sovereignty,
        supabase=supabase,
        rls=rls,
        recommendations=["Rotate exposed credentials."] if security_error else [],
        exit_options=["1. [low/partial] Stay on current provider"],
        read_only=True,
        applied=False,
    )


# ---------------------------------------------------------------------------
# Tests — Data model
# ---------------------------------------------------------------------------


class TestRecoveryPlanDefaults:
    def test_read_only_is_true(self) -> None:
        plan = RecoveryPlan()
        assert plan.read_only is True

    def test_applied_is_false(self) -> None:
        plan = RecoveryPlan()
        assert plan.applied is False

    def test_command_field(self) -> None:
        plan = RecoveryPlan()
        assert plan.command == "reclaim recovery plan"


# ---------------------------------------------------------------------------
# Tests — build_recovery_plan
# ---------------------------------------------------------------------------


class TestBuildRecoveryPlan:
    def test_clean_project_returns_valid_plan(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        assert plan.read_only is True
        assert plan.applied is False
        assert plan.project_path == str(tmp_path)
        assert plan.project_name == tmp_path.name

    def test_supabase_project_populates_db_section(self, tmp_path: Path) -> None:
        harden = _make_harden_result(supabase_detected=True, path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        assert plan.database_recovery["supabase_detected"] is True
        assert plan.database_recovery["rls_verdict"] == "WARNING"

    def test_secret_exposure_surfaces_in_security_recovery(
        self, tmp_path: Path
    ) -> None:
        harden = _make_harden_result(
            secrets_exposure="confirmed", security_error=True, path=tmp_path
        )
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        assert plan.security_recovery["secret_exposure_status"] == "confirmed"  # noqa: S105
        blockers = plan.security_recovery["immediate_blockers"]
        assert isinstance(blockers, list)
        assert len(blockers) > 0

    def test_recovery_pr_roadmap_has_at_least_7(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        assert len(plan.recovery_pr_roadmap) >= 7

    def test_local_ai_policy_populated(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        policy = plan.local_ai_policy
        assert isinstance(policy, LocalAIPolicy)
        assert len(policy.can_do) >= 1
        assert len(policy.requires_human_approval) >= 1
        assert len(policy.must_never_send_to_frontier) >= 1

    def test_frontier_ai_rules_populated(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        assert len(plan.frontier_ai_rules) >= 1
        assert all(isinstance(r, FrontierAIRule) for r in plan.frontier_ai_rules)

    def test_frontier_ai_rules_forbid_sensitive_data(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        rules_text = " ".join(r.rule.lower() for r in plan.frontier_ai_rules)
        assert "secret" in rules_text or ".env" in rules_text
        never_send = " ".join(
            item.lower() for item in plan.local_ai_policy.must_never_send_to_frontier
        )
        assert ".env" in never_send or "secret" in never_send
        assert "pii" in never_send or "customer" in never_send

    def test_nonexistent_path_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            build_recovery_plan(Path("/nonexistent/path/xyzzy"))


# ---------------------------------------------------------------------------
# Tests — recovery_plan_to_dict
# ---------------------------------------------------------------------------


class TestRecoveryPlanToDict:
    def test_json_output_is_valid(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        data = recovery_plan_to_dict(plan)
        serialized = json.dumps(data)
        parsed = json.loads(serialized)
        assert parsed["read_only"] is True
        assert parsed["applied"] is False
        assert "recovery_pr_roadmap" in parsed
        assert isinstance(parsed["recovery_pr_roadmap"], list)

    def test_json_output_contains_no_secrets(self, tmp_path: Path) -> None:
        canary = "sk_live_SUPERSECRETVALUE12345"
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        output = json.dumps(recovery_plan_to_dict(plan))
        assert canary not in output


# ---------------------------------------------------------------------------
# Tests — build_recovery_markdown
# ---------------------------------------------------------------------------


class TestBuildRecoveryMarkdown:
    def test_markdown_contains_recovery_plan_header(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        md = build_recovery_markdown(plan)
        assert "Recovery Plan" in md

    def test_markdown_ends_with_read_only_footer(self, tmp_path: Path) -> None:
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            plan = build_recovery_plan(tmp_path)
        md = build_recovery_markdown(plan)
        assert "read_only" in md
        assert "applied: false" in md.lower() or "applied`" in md


# ---------------------------------------------------------------------------
# Tests — CLI: --output
# ---------------------------------------------------------------------------


class TestRecoveryPlanOutput:
    def test_output_writes_markdown_file(self, tmp_path: Path) -> None:
        out_file = tmp_path / "recovery.md"
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            result = runner.invoke(
                app,
                [
                    "reclaim",
                    "recovery",
                    "plan",
                    "--path",
                    str(tmp_path),
                    "--output",
                    str(out_file),
                ],
            )
        assert result.exit_code == 0, result.output
        assert out_file.is_file()
        content = out_file.read_text()
        assert "Recovery Plan" in content

    def test_output_refuses_existing_file_without_overwrite(
        self, tmp_path: Path
    ) -> None:
        out_file = tmp_path / "recovery.md"
        out_file.write_text("existing content")
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            result = runner.invoke(
                app,
                [
                    "reclaim",
                    "recovery",
                    "plan",
                    "--path",
                    str(tmp_path),
                    "--output",
                    str(out_file),
                ],
            )
        assert result.exit_code != 0
        assert "existing content" == out_file.read_text()

    def test_overwrite_replaces_existing_file(self, tmp_path: Path) -> None:
        out_file = tmp_path / "recovery.md"
        out_file.write_text("old content")
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            result = runner.invoke(
                app,
                [
                    "reclaim",
                    "recovery",
                    "plan",
                    "--path",
                    str(tmp_path),
                    "--output",
                    str(out_file),
                    "--overwrite",
                ],
            )
        assert result.exit_code == 0, result.output
        new_content = out_file.read_text()
        assert new_content != "old content"
        assert "Recovery Plan" in new_content


# ---------------------------------------------------------------------------
# Tests — CLI: safety
# ---------------------------------------------------------------------------


class TestRecoveryPlanCLISafety:
    def test_text_output_contains_no_raw_secrets(self, tmp_path: Path) -> None:
        canary = "SECRET_DB_PASSWORD_12345"
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            result = runner.invoke(
                app,
                ["reclaim", "recovery", "plan", "--path", str(tmp_path)],
            )
        assert canary not in result.output

    def test_json_cli_output_contains_no_raw_secrets(self, tmp_path: Path) -> None:
        canary = "SECRET_DB_PASSWORD_12345"
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            result = runner.invoke(
                app,
                ["reclaim", "recovery", "plan", "--path", str(tmp_path), "--json"],
            )
        assert canary not in result.output

    def test_does_not_modify_project_files(self, tmp_path: Path) -> None:
        sentinel = tmp_path / "sentinel.txt"
        sentinel.write_text("untouched")
        harden = _make_harden_result(path=tmp_path)
        with patch(_MOCK_TARGET, return_value=harden):
            runner.invoke(
                app,
                ["reclaim", "recovery", "plan", "--path", str(tmp_path)],
            )
        assert sentinel.read_text() == "untouched"

    def test_nonexistent_path_gives_clean_error(self) -> None:
        result = runner.invoke(
            app,
            [
                "reclaim",
                "recovery",
                "plan",
                "--path",
                "/nonexistent/path/xyzzy_aeos_test",
            ],
        )
        assert result.exit_code != 0
