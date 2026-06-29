"""
Unit tests for aeos.reclaim.hardener and the `reclaim harden` CLI command.
No network access. No real git repos. No secret values read.
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
    RemediationPhase,
    RemediationPlan,
    _build_exit_options,
    _build_recommendations,
    _build_remediation_plan,
    _compute_status,
    _control_level,
    _count_findings,
    build_harden_report,
    run_reclaim_harden,
)
from aeos.reclaim.inspector import (
    ReclaimControlMap,
    ReclaimExitOption,
    ReclaimGenerator,
    ReclaimInspectResult,
    ReclaimProvider,
)
from aeos.security.checker import SecurityCheckResult, SecurityFinding
from aeos.sovereignty.checker import SovereigntyCheckResult, SovereigntyFinding

runner = CliRunner()

# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _make_control_map(
    portability: str = "partial",
    secrets_exposure: str = "none",
    backend_runtime: str = "likely_external",
) -> ReclaimControlMap:
    return ReclaimControlMap(
        frontend_code="partial",
        backend_runtime=backend_runtime,
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
        ReclaimExitOption(
            id="own_supabase_cloud",
            label="Migrate to own Supabase Cloud project",
            complexity="medium",
            sovereignty="medium",
            advantages=["you own the project"],
            risks=["still cloud-dependent"],
            next_action="Export schema",
        ),
    ]


def _make_reclaim(
    status: str = "WARNING",
    secrets_exposure: str = "none",
    portability: str = "partial",
    generator: str | None = "lovable",
    supabase_detected: bool = True,
) -> ReclaimInspectResult:
    generators = [
        ReclaimGenerator(
            name="lovable",
            detected=(generator == "lovable"),
            evidence=".lovable/:1" if generator == "lovable" else "",
        ),
        ReclaimGenerator(name="bolt", detected=False, evidence=""),
        ReclaimGenerator(name="replit", detected=False, evidence=""),
    ]
    providers = [
        ReclaimProvider(
            name="supabase",
            detected=supabase_detected,
            roles=["database", "auth"],
            evidence="supabase/migrations/:1",
        ),
        ReclaimProvider(name="vercel", detected=False, roles=[], evidence=""),
    ]
    cm = _make_control_map(
        portability=portability,
        secrets_exposure=secrets_exposure,
    )
    return ReclaimInspectResult(
        path=Path("/fake/project"),
        status=status,
        generators=generators,
        providers=providers,
        control_map=cm,
        exit_options=_make_exit_options(),
        recommended_next_action="Run aeos supabase check",
    )


def _make_security(status: str = "WARNING", error: bool = False) -> SecurityCheckResult:
    findings = []
    if error:
        findings.append(
            SecurityFinding(
                category="secrets",
                severity="ERROR",
                message="Critical secret exposed",
                location=".env:1",
                recommendation="Rotate immediately",
                evidence="file:1",
            )
        )
    elif status == "WARNING":
        findings.append(
            SecurityFinding(
                category="secrets",
                severity="WARNING",
                message="Sensitive key name found in tracked file",
                location=".env.example:1",
                recommendation="Use .env.example without values",
                evidence="file:1",
            )
        )
    return SecurityCheckResult(
        path=Path("/fake/project"),
        status=status,
        findings=findings,
    )


def _make_sovereignty(status: str = "WARNING") -> SovereigntyCheckResult:
    findings = []
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
    rls.status = "WARNING" if verdict == "WARNING" else "OK"
    rls.migrations_scanned = 8
    rls.review.verdict = verdict
    rls.summary.auto_blocks = 25
    rls.summary.todo_blocks = 13
    rls.summary.blocked_blocks = 0
    rls.inspect.findings = []
    return rls


def _make_supabase_mock(status: str = "WARNING") -> MagicMock:
    sup = MagicMock()
    sup.status = status
    sup.supabase_detected = True
    sup.requires_manual_action = True
    step = MagicMock()
    step.status = "manual"
    step.action = "Rotate SUPABASE_SERVICE_ROLE_KEY"
    sup.remediation_steps = [step]
    return sup


def _make_harden_result(
    status: str = "WARNING",
    secrets_exposure: str = "none",
    rls_verdict: str = "WARNING",
    security_error: bool = False,
    supabase_status: str = "WARNING",
) -> ReclaimHardenResult:
    reclaim = _make_reclaim(secrets_exposure=secrets_exposure)
    security = _make_security(error=security_error)
    sovereignty = _make_sovereignty()
    supabase = _make_supabase_mock(supabase_status)
    rls = _make_rls_mock(rls_verdict)
    summary = ReclaimHardenSummary(
        generator_detected="lovable",
        providers_detected=["supabase"],
        control_level="partial",
        secrets_exposure=secrets_exposure,
        security_status=security.status,
        sovereignty_status=sovereignty.status,
        supabase_status=supabase_status,
        rls_verdict=rls_verdict,
        generated_actions=25,
        manual_actions=13,
        critical_findings=1 if security_error else 0,
        important_findings=2,
    )
    return ReclaimHardenResult(
        path=Path("/fake/project"),
        status=status,
        summary=summary,
        reclaim=reclaim,
        security=security,
        sovereignty=sovereignty,
        supabase=supabase,
        rls=rls,
        recommendations=["Review 13 RLS TODO blocks."],
        exit_options=["1. [low/partial] Stay on current provider"],
        read_only=True,
        applied=False,
    )


# ---------------------------------------------------------------------------
# TestDataModel
# ---------------------------------------------------------------------------


class TestDataModel:
    def test_summary_fields(self) -> None:
        s = ReclaimHardenSummary(
            generator_detected="lovable",
            providers_detected=["supabase"],
            control_level="partial",
            secrets_exposure="none",
            security_status="WARNING",
            sovereignty_status="WARNING",
            supabase_status="WARNING",
            rls_verdict="WARNING",
            generated_actions=25,
            manual_actions=13,
            critical_findings=0,
            important_findings=2,
        )
        assert s.generator_detected == "lovable"
        assert s.generated_actions == 25

    def test_result_read_only_applied(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        assert result.read_only is True
        assert result.applied is False

    def test_result_defaults(self) -> None:
        result = _make_harden_result()
        assert result.path == Path("/fake/project")
        assert result.rls is not None
        assert result.supabase is not None


# ---------------------------------------------------------------------------
# TestControlLevel
# ---------------------------------------------------------------------------


class TestControlLevel:
    def test_strong_portability(self) -> None:
        r = _make_reclaim(portability="strong")
        assert _control_level(r) == "controlled"

    def test_partial_portability(self) -> None:
        r = _make_reclaim(portability="partial")
        assert _control_level(r) == "partial"

    def test_weak_portability(self) -> None:
        r = _make_reclaim(portability="weak")
        assert _control_level(r) == "weak"


# ---------------------------------------------------------------------------
# TestCountFindings
# ---------------------------------------------------------------------------


class TestCountFindings:
    def test_counts_security_error(self) -> None:
        security = _make_security(error=True)
        sovereignty = _make_sovereignty(status="OK")
        crit, important = _count_findings(security, sovereignty, None)
        assert crit == 1
        assert important == 0

    def test_counts_sovereignty_warning(self) -> None:
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="WARNING")
        crit, important = _count_findings(security, sovereignty, None)
        assert crit == 0
        assert important == 1

    def test_counts_rls_findings(self) -> None:
        from aeos.providers.supabase.rls.inspector import RLSFinding

        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        rls = _make_rls_mock()
        rls_finding = MagicMock(spec=RLSFinding)
        rls_finding.severity = "ERROR"
        rls_finding.table = "budget_entries"
        rls_finding.policy_name = "budget_entries_select"
        rls_finding.issue = "SELECT_TOO_PERMISSIVE"
        rls.inspect.findings = [rls_finding]
        crit, _important = _count_findings(security, sovereignty, rls)
        assert crit == 1

    def test_no_findings_zero(self) -> None:
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        crit, important = _count_findings(security, sovereignty, None)
        assert crit == 0
        assert important == 0


# ---------------------------------------------------------------------------
# TestComputeStatus
# ---------------------------------------------------------------------------


class TestComputeStatus:
    def test_error_on_confirmed_secrets(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="confirmed")
        security = _make_security(status="OK")
        assert _compute_status(reclaim, security, None, None) == "ERROR"

    def test_error_on_risk_secrets(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="risk")
        security = _make_security(status="OK")
        assert _compute_status(reclaim, security, None, None) == "ERROR"

    def test_error_on_security_error_finding(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="none", generator=None)
        security = _make_security(error=True)
        assert _compute_status(reclaim, security, None, None) == "ERROR"

    def test_error_on_supabase_critical(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="strong"
        )
        security = _make_security(status="OK")
        supabase = _make_supabase_mock(status="CRITICAL")
        assert _compute_status(reclaim, security, supabase, None) == "ERROR"

    def test_error_on_supabase_error(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="strong"
        )
        security = _make_security(status="OK")
        supabase = _make_supabase_mock(status="ERROR")
        assert _compute_status(reclaim, security, supabase, None) == "ERROR"

    def test_error_on_rls_blocked(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="strong"
        )
        security = _make_security(status="OK")
        rls = _make_rls_mock(verdict="BLOCKED")
        assert _compute_status(reclaim, security, None, rls) == "ERROR"

    def test_warning_on_generator_detected(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="none", generator="lovable")
        security = _make_security(status="OK")
        assert _compute_status(reclaim, security, None, None) == "WARNING"

    def test_warning_on_weak_portability(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="weak"
        )
        security = _make_security(status="OK")
        assert _compute_status(reclaim, security, None, None) == "WARNING"

    def test_warning_on_partial_portability(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="partial"
        )
        security = _make_security(status="OK")
        assert _compute_status(reclaim, security, None, None) == "WARNING"

    def test_warning_on_security_warning(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="strong"
        )
        security = _make_security(status="WARNING")
        assert _compute_status(reclaim, security, None, None) == "WARNING"

    def test_warning_on_rls_warning(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="strong"
        )
        security = _make_security(status="OK")
        rls = _make_rls_mock(verdict="WARNING")
        assert _compute_status(reclaim, security, None, rls) == "WARNING"

    def test_ok_on_clean_project(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none",
            generator=None,
            portability="strong",
            supabase_detected=False,
        )
        security = _make_security(status="OK")
        assert _compute_status(reclaim, security, None, None) == "OK"


# ---------------------------------------------------------------------------
# TestBuildRecommendations
# ---------------------------------------------------------------------------


class TestBuildRecommendations:
    def test_recommends_rotate_on_confirmed_secrets(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="confirmed")
        security = _make_security(status="OK")
        recs = _build_recommendations(reclaim, security, None, None, Path("/fake"))
        assert any("Rotate" in r for r in recs)

    def test_recommends_remove_env_on_risk(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="risk")
        security = _make_security(status="OK")
        recs = _build_recommendations(reclaim, security, None, None, Path("/fake"))
        assert any("Remove .env" in r for r in recs)

    def test_recommends_export_on_auto_blocks(self) -> None:
        reclaim = _make_reclaim()
        security = _make_security(status="OK")
        rls = _make_rls_mock(verdict="WARNING")
        recs = _build_recommendations(reclaim, security, None, rls, Path("/fake"))
        assert any("aeos supabase rls harden" in r for r in recs)

    def test_fallback_on_clean_project(self) -> None:
        reclaim = _make_reclaim(
            secrets_exposure="none", generator=None, portability="strong"
        )
        security = _make_security(status="OK")
        recs = _build_recommendations(reclaim, security, None, None, Path("/fake"))
        assert len(recs) >= 1

    def test_manual_steps_included(self) -> None:
        reclaim = _make_reclaim()
        security = _make_security(status="OK")
        supabase = _make_supabase_mock()
        recs = _build_recommendations(reclaim, security, supabase, None, Path("/fake"))
        assert any("manual Supabase" in r for r in recs)


# ---------------------------------------------------------------------------
# TestBuildExitOptions
# ---------------------------------------------------------------------------


class TestBuildExitOptions:
    def test_exit_options_count(self) -> None:
        reclaim = _make_reclaim()
        opts = _build_exit_options(reclaim)
        assert len(opts) == len(reclaim.exit_options)

    def test_exit_options_format(self) -> None:
        reclaim = _make_reclaim()
        opts = _build_exit_options(reclaim)
        for opt in opts:
            assert "/" in opt
            assert opt.startswith(tuple("12345"))


# ---------------------------------------------------------------------------
# TestRunReclaimHarden (integration-style with mocks)
# ---------------------------------------------------------------------------


class TestRunReclaimHarden:
    def _patch_all(
        self,
        reclaim: object,
        security: object,
        sovereignty: object,
        supabase: object | None = None,
        rls: object | None = None,
        has_migrations: bool = True,
    ) -> list[object]:
        return [
            patch("aeos.reclaim.hardener.run_reclaim_inspect", return_value=reclaim),
            patch("aeos.reclaim.hardener.run_security_check", return_value=security),
            patch(
                "aeos.reclaim.hardener.run_sovereignty_check",
                return_value=sovereignty,
            ),
            patch(
                "aeos.reclaim.hardener.run_supabase_check",
                return_value=supabase or _make_supabase_mock(),
            ),
            patch(
                "aeos.reclaim.hardener.run_rls_harden",
                return_value=rls or _make_rls_mock(),
            ),
            patch(
                "aeos.reclaim.hardener.Path.is_dir",
                return_value=has_migrations,
            ),
        ]

    def test_result_read_only_true(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _patch = "aeos.reclaim.hardener"
        with (
            patch(f"{_patch}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_patch}.run_security_check", return_value=security),
            patch(f"{_patch}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.read_only is True

    def test_result_applied_false(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _patch = "aeos.reclaim.hardener"
        with (
            patch(f"{_patch}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_patch}.run_security_check", return_value=security),
            patch(f"{_patch}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.applied is False

    def test_no_supabase_skips_rls(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _patch = "aeos.reclaim.hardener"
        with (
            patch(f"{_patch}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_patch}.run_security_check", return_value=security),
            patch(f"{_patch}.run_sovereignty_check", return_value=sovereignty),
            patch(f"{_patch}.run_rls_harden") as mock_rls,
        ):
            result = run_reclaim_harden(tmp_path)
        mock_rls.assert_not_called()
        assert result.rls is None
        assert result.supabase is None

    def test_supabase_detected_runs_supabase_check(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=True)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        supabase_mock = _make_supabase_mock()
        migrations_dir = tmp_path / "supabase" / "migrations"
        migrations_dir.mkdir(parents=True)
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
            patch(f"{_p}.run_supabase_check", return_value=supabase_mock) as mock_sup,
            patch(f"{_p}.run_rls_harden", return_value=_make_rls_mock()),
        ):
            run_reclaim_harden(tmp_path)
        mock_sup.assert_called_once()

    def test_rls_not_run_without_migrations(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=True)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        supabase_mock = _make_supabase_mock()
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
            patch(f"{_p}.run_supabase_check", return_value=supabase_mock),
            patch(f"{_p}.run_rls_harden") as mock_rls,
        ):
            result = run_reclaim_harden(tmp_path)
        mock_rls.assert_not_called()
        assert result.rls is None

    def test_status_error_on_confirmed_secrets(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(secrets_exposure="confirmed", supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.status == "ERROR"

    def test_status_warning_on_generator(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(generator="lovable", supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.status == "WARNING"

    def test_status_ok_on_clean_project(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(
            generator=None,
            portability="strong",
            secrets_exposure="none",
            supabase_detected=False,
        )
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.status == "OK"

    def test_summary_generator_detected(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(generator="lovable", supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.summary.generator_detected == "lovable"

    def test_summary_no_generator(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(generator=None, supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.summary.generator_detected is None

    def test_summary_generated_actions_from_rls(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=True)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        rls_mock = _make_rls_mock(verdict="WARNING")
        migrations_dir = tmp_path / "supabase" / "migrations"
        migrations_dir.mkdir(parents=True)
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
            patch(f"{_p}.run_supabase_check", return_value=_make_supabase_mock()),
            patch(f"{_p}.run_rls_harden", return_value=rls_mock),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.summary.generated_actions == 25
        assert result.summary.manual_actions >= 13


# ---------------------------------------------------------------------------
# TestRemediationPlan
# ---------------------------------------------------------------------------


def _make_plan() -> RemediationPlan:
    phase = RemediationPhase(
        id="phase_0",
        label="Immediate security stabilization",
        priority="critical",
        goal="Neutralize all active security risks.",
        why_it_matters="Exposed credentials remain active until rotated.",
        actions=["Rotate exposed keys.", "Remove .env from Git."],
        automation_level="manual",
        expected_outcome="No exposed credentials.",
        risk_if_skipped="Breach window remains open.",
    )
    return RemediationPlan(
        phases=[phase],
        phases_count=1,
        immediate_actions_count=2,
        manual_actions_count=2,
        generatable_actions_count=25,
        strategic_options_count=5,
    )


class TestRemediationPlan:
    def test_dataclass_fields(self) -> None:
        plan = _make_plan()
        assert plan.phases_count == 1
        assert plan.immediate_actions_count == 2
        assert plan.generatable_actions_count == 25
        assert plan.strategic_options_count == 5

    def test_phase_fields(self) -> None:
        plan = _make_plan()
        phase = plan.phases[0]
        assert phase.id == "phase_0"
        assert phase.priority == "critical"
        assert phase.automation_level == "manual"
        assert len(phase.actions) == 2

    def test_build_remediation_plan_returns_five_phases(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="confirmed")
        security = _make_security(error=True)
        summary = ReclaimHardenSummary(
            generator_detected="lovable",
            providers_detected=["supabase"],
            control_level="weak",
            secrets_exposure="confirmed",
            security_status="ERROR",
            sovereignty_status="WARNING",
            supabase_status="ERROR",
            rls_verdict="WARNING",
            generated_actions=25,
            manual_actions=13,
            critical_findings=1,
            important_findings=2,
        )
        plan = _build_remediation_plan(
            summary, reclaim, security, _make_rls_mock(), Path("/fake")
        )
        assert plan.phases_count == 5
        assert len(plan.phases) == 5

    def test_phase_ids_sequential(self) -> None:
        reclaim = _make_reclaim()
        security = _make_security(status="OK")
        summary = ReclaimHardenSummary(
            generator_detected="lovable",
            providers_detected=["supabase"],
            control_level="partial",
            secrets_exposure="none",
            security_status="OK",
            sovereignty_status="WARNING",
            supabase_status="WARNING",
            rls_verdict="WARNING",
            generated_actions=0,
            manual_actions=0,
            critical_findings=0,
            important_findings=1,
        )
        plan = _build_remediation_plan(summary, reclaim, security, None, Path("/fake"))
        ids = [ph.id for ph in plan.phases]
        assert ids == ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"]

    def test_phase_0_critical_on_secrets_exposed(self) -> None:
        reclaim = _make_reclaim(secrets_exposure="confirmed")
        security = _make_security(status="OK")
        summary = ReclaimHardenSummary(
            generator_detected=None,
            providers_detected=[],
            control_level="weak",
            secrets_exposure="confirmed",
            security_status="OK",
            sovereignty_status="OK",
            supabase_status=None,
            rls_verdict=None,
            generated_actions=0,
            manual_actions=0,
            critical_findings=0,
            important_findings=0,
        )
        plan = _build_remediation_plan(summary, reclaim, security, None, Path("/fake"))
        assert plan.phases[0].priority == "critical"
        assert any("Rotate" in a for a in plan.phases[0].actions)

    def test_phase_1_generatable_when_rls_auto_blocks(self) -> None:
        reclaim = _make_reclaim()
        security = _make_security(status="OK")
        rls = _make_rls_mock(verdict="WARNING")
        summary = ReclaimHardenSummary(
            generator_detected="lovable",
            providers_detected=["supabase"],
            control_level="partial",
            secrets_exposure="none",
            security_status="OK",
            sovereignty_status="WARNING",
            supabase_status="WARNING",
            rls_verdict="WARNING",
            generated_actions=25,
            manual_actions=13,
            critical_findings=0,
            important_findings=2,
        )
        plan = _build_remediation_plan(summary, reclaim, security, rls, Path("/fake"))
        assert plan.phases[1].automation_level == "generatable"
        assert plan.generatable_actions_count == 25

    def test_phase_2_high_on_generator_detected(self) -> None:
        reclaim = _make_reclaim(generator="lovable")
        security = _make_security(status="OK")
        summary = ReclaimHardenSummary(
            generator_detected="lovable",
            providers_detected=["supabase"],
            control_level="partial",
            secrets_exposure="none",
            security_status="OK",
            sovereignty_status="WARNING",
            supabase_status=None,
            rls_verdict=None,
            generated_actions=0,
            manual_actions=0,
            critical_findings=0,
            important_findings=0,
        )
        plan = _build_remediation_plan(summary, reclaim, security, None, Path("/fake"))
        assert plan.phases[2].priority == "high"

    def test_phase_4_always_low(self) -> None:
        reclaim = _make_reclaim()
        security = _make_security(status="OK")
        summary = ReclaimHardenSummary(
            generator_detected=None,
            providers_detected=[],
            control_level="strong",
            secrets_exposure="none",
            security_status="OK",
            sovereignty_status="OK",
            supabase_status=None,
            rls_verdict=None,
            generated_actions=0,
            manual_actions=0,
            critical_findings=0,
            important_findings=0,
        )
        plan = _build_remediation_plan(summary, reclaim, security, None, Path("/fake"))
        assert plan.phases[4].priority == "low"
        assert plan.phases[4].id == "phase_4"

    def test_strategic_options_count(self) -> None:
        reclaim = _make_reclaim()
        security = _make_security(status="OK")
        summary = ReclaimHardenSummary(
            generator_detected="lovable",
            providers_detected=["supabase"],
            control_level="partial",
            secrets_exposure="none",
            security_status="OK",
            sovereignty_status="WARNING",
            supabase_status=None,
            rls_verdict=None,
            generated_actions=0,
            manual_actions=0,
            critical_findings=0,
            important_findings=0,
        )
        plan = _build_remediation_plan(summary, reclaim, security, None, Path("/fake"))
        assert plan.strategic_options_count == len(reclaim.exit_options)

    def test_result_has_remediation_plan_after_run(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        assert result.remediation_plan is not None
        assert result.remediation_plan.phases_count == 5

    def test_remediation_plan_in_markdown_report(self) -> None:
        result = _make_harden_result()
        result.remediation_plan = _make_plan()
        report = build_harden_report(result)
        assert "## Remediation Plan" in report
        assert "Phase 0" in report
        assert "Immediate security stabilization" in report

    def test_markdown_report_has_all_five_phases(self, tmp_path: Path) -> None:
        reclaim = _make_reclaim(supabase_detected=False)
        security = _make_security(status="OK")
        sovereignty = _make_sovereignty(status="OK")
        _p = "aeos.reclaim.hardener"
        with (
            patch(f"{_p}.run_reclaim_inspect", return_value=reclaim),
            patch(f"{_p}.run_security_check", return_value=security),
            patch(f"{_p}.run_sovereignty_check", return_value=sovereignty),
        ):
            result = run_reclaim_harden(tmp_path)
        report = build_harden_report(result)
        for i in range(5):
            label = f"Phase {i}"
            slug = f"phase_{i}".replace("_", " ").title()
            assert label in report or slug in report

    def test_remediation_plan_in_json(self) -> None:
        result = _make_harden_result()
        result.remediation_plan = _make_plan()
        with patch("aeos.cli.run_reclaim_harden", return_value=result):
            r = runner.invoke(
                app, ["reclaim", "harden", "--path", "/fake/project", "--json"]
            )
        data = json.loads(r.output)
        assert "remediation_plan" in data
        assert data["remediation_plan"] is not None
        assert data["remediation_plan"]["phases_count"] == 1

    def test_json_remediation_plan_has_phases(self) -> None:
        result = _make_harden_result()
        result.remediation_plan = _make_plan()
        with patch("aeos.cli.run_reclaim_harden", return_value=result):
            r = runner.invoke(
                app, ["reclaim", "harden", "--path", "/fake/project", "--json"]
            )
        data = json.loads(r.output)
        phases = data["remediation_plan"]["phases"]
        assert isinstance(phases, list)
        assert len(phases) == 1
        ph = phases[0]
        assert "id" in ph
        assert "priority" in ph
        assert "goal" in ph
        assert "actions" in ph
        assert "automation_level" in ph
        assert "risk_if_skipped" in ph

    def test_json_remediation_plan_none_when_not_set(self) -> None:
        result = _make_harden_result()
        result.remediation_plan = None
        with patch("aeos.cli.run_reclaim_harden", return_value=result):
            r = runner.invoke(
                app, ["reclaim", "harden", "--path", "/fake/project", "--json"]
            )
        data = json.loads(r.output)
        assert data["remediation_plan"] is None

    def test_text_output_shows_remediation_plan_summary(self) -> None:
        result = _make_harden_result()
        result.remediation_plan = _make_plan()
        with patch("aeos.cli.run_reclaim_harden", return_value=result):
            r = runner.invoke(app, ["reclaim", "harden", "--path", "/fake/project"])
        assert "Remediation Plan" in r.output
        assert "phase_0" in r.output

    def test_text_output_no_plan_section_when_none(self) -> None:
        result = _make_harden_result()
        result.remediation_plan = None
        with patch("aeos.cli.run_reclaim_harden", return_value=result):
            r = runner.invoke(app, ["reclaim", "harden", "--path", "/fake/project"])
        assert "Remediation Plan" not in r.output

    def test_markdown_no_plan_section_when_none(self) -> None:
        result = _make_harden_result()
        result.remediation_plan = None
        report = build_harden_report(result)
        assert "## Remediation Plan" not in report

    def test_output_file_contains_remediation_plan(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        result = _make_harden_result()
        result.remediation_plan = _make_plan()
        with patch("aeos.cli.run_reclaim_harden", return_value=result):
            runner.invoke(
                app,
                [
                    "reclaim",
                    "harden",
                    "--path",
                    "/fake/project",
                    "--output",
                    str(out),
                ],
            )
        content = out.read_text()
        assert "## Remediation Plan" in content
        assert "Phase 0" in content


# ---------------------------------------------------------------------------
# TestCLIReclaimHarden (text output)
# ---------------------------------------------------------------------------


class TestCLIReclaimHarden:
    def _invoke(self, harden_result: ReclaimHardenResult) -> object:
        with patch("aeos.cli.run_reclaim_harden", return_value=harden_result):
            return runner.invoke(app, ["reclaim", "harden", "--path", "/fake/project"])

    def test_title_in_output(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "AEOS Reclaim Harden Report" in result.output

    def test_shows_status(self) -> None:
        result = self._invoke(_make_harden_result(status="WARNING"))
        assert "WARNING" in result.output

    def test_shows_generator(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "lovable" in result.output

    def test_shows_providers(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "supabase" in result.output

    def test_shows_rls_verdict(self) -> None:
        result = self._invoke(_make_harden_result(rls_verdict="WARNING"))
        assert "WARNING" in result.output

    def test_shows_recommendations(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "Recommendations" in result.output

    def test_shows_exit_options(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "Exit Options" in result.output

    def test_shows_read_only_footer(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "read_only: true" in result.output
        assert "applied: false" in result.output

    def test_no_secrets_in_output(self) -> None:
        result = self._invoke(_make_harden_result())
        secret_patterns = [
            "eyJ",  # JWT prefix
            "service_role",
            "sk-",  # OpenAI key prefix
            "xoxb-",  # Slack token
        ]
        for pattern in secret_patterns:
            assert pattern not in result.output

    def test_exit_code_1_on_error(self) -> None:
        result = self._invoke(_make_harden_result(status="ERROR"))
        assert result.exit_code == 1

    def test_exit_code_0_on_warning(self) -> None:
        result = self._invoke(_make_harden_result(status="WARNING"))
        assert result.exit_code == 0

    def test_exit_code_0_on_ok(self) -> None:
        result = self._invoke(_make_harden_result(status="OK"))
        assert result.exit_code == 0

    def test_shows_critical_risks_section(self) -> None:
        result = self._invoke(_make_harden_result(status="ERROR", security_error=True))
        assert "Critical Risks" in result.output

    def test_shows_generatable_fixes(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "Generatable Fixes" in result.output
        assert "25" in result.output

    def test_shows_manual_actions(self) -> None:
        result = self._invoke(_make_harden_result())
        assert "Manual Actions" in result.output

    def test_warning_status_label(self) -> None:
        result = self._invoke(_make_harden_result(status="WARNING"))
        assert "WARNING ⚠" in result.output

    def test_ok_status_label(self) -> None:
        result = self._invoke(_make_harden_result(status="OK"))
        assert "OK ✓" in result.output

    def test_error_status_label(self) -> None:
        result = self._invoke(_make_harden_result(status="ERROR"))
        assert "ERROR ✗" in result.output


# ---------------------------------------------------------------------------
# TestCLIReclaimHardenJSON
# ---------------------------------------------------------------------------


class TestCLIReclaimHardenJSON:
    def _invoke_json(self, harden_result: ReclaimHardenResult) -> dict[str, object]:
        with patch("aeos.cli.run_reclaim_harden", return_value=harden_result):
            r = runner.invoke(
                app, ["reclaim", "harden", "--path", "/fake/project", "--json"]
            )
        return json.loads(r.output)  # type: ignore[no-any-return]

    def test_json_has_status(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "status" in data

    def test_json_read_only_true(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert data["read_only"] is True

    def test_json_applied_false(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert data["applied"] is False

    def test_json_has_project_path(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "project_path" in data

    def test_json_has_summary(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "summary" in data
        s = data["summary"]
        assert "generator_detected" in s
        assert "providers_detected" in s
        assert "control_level" in s
        assert "secrets_exposure" in s
        assert "rls_verdict" in s
        assert "generated_actions" in s
        assert "manual_actions" in s

    def test_json_has_reclaim_section(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "reclaim" in data

    def test_json_has_security_section(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "security" in data

    def test_json_has_sovereignty_section(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "sovereignty" in data

    def test_json_has_supabase_section(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "supabase" in data
        assert data["supabase"] is not None

    def test_json_has_rls_section(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert "rls" in data
        assert data["rls"] is not None

    def test_json_rls_has_verdict(self) -> None:
        data = self._invoke_json(_make_harden_result(rls_verdict="WARNING"))
        assert data["rls"]["verdict"] == "WARNING"

    def test_json_has_recommendations(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert isinstance(data["recommendations"], list)

    def test_json_has_exit_options(self) -> None:
        data = self._invoke_json(_make_harden_result())
        assert isinstance(data["exit_options"], list)

    def test_json_no_rls_when_none(self) -> None:
        result = _make_harden_result()
        result.rls = None
        result.summary.rls_verdict = None
        result.summary.generated_actions = 0
        data = self._invoke_json(result)
        assert data["rls"] is None

    def test_json_no_supabase_when_none(self) -> None:
        result = _make_harden_result()
        result.supabase = None
        result.summary.supabase_status = None
        data = self._invoke_json(result)
        assert data["supabase"] is None

    def test_json_valid_structure_on_error(self) -> None:
        result = _make_harden_result(status="ERROR")
        with patch("aeos.cli.run_reclaim_harden", return_value=result):
            r = runner.invoke(
                app, ["reclaim", "harden", "--path", "/fake/project", "--json"]
            )
        data = json.loads(r.output)
        assert data["status"] == "ERROR"
        assert r.exit_code == 1

    def test_json_no_secret_values(self) -> None:
        data = self._invoke_json(_make_harden_result())
        output = json.dumps(data)
        for pattern in ["eyJ", "sk-", "service_role_key_value", "xoxb-"]:
            assert pattern not in output


# ---------------------------------------------------------------------------
# TestCLIHardenHelp
# ---------------------------------------------------------------------------


class TestCLIHardenHelp:
    def test_help_shows_command(self) -> None:
        import re

        result = runner.invoke(app, ["reclaim", "harden", "--help"])
        plain = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
        assert "--path" in plain
        assert "--json" in plain
        assert "--output" in plain
        assert "--overwrite" in plain


# ---------------------------------------------------------------------------
# TestBuildHardenReport
# ---------------------------------------------------------------------------


class TestBuildHardenReport:
    def test_contains_aeos_header(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "AEOS Reclaim Harden Report" in report

    def test_contains_read_only_true(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "read_only:     true" in report

    def test_contains_applied_false(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "applied:       false" in report

    def test_contains_global_status(self) -> None:
        report = build_harden_report(_make_harden_result(status="WARNING"))
        assert "WARNING" in report

    def test_contains_generator(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "lovable" in report

    def test_contains_providers(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "supabase" in report

    def test_contains_exit_options(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "Exit Options" in report
        assert "Stay on current provider" in report

    def test_contains_recommendations(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "Recommendations" in report

    def test_contains_no_correction_applied_notice(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "No correction has been applied" in report

    def test_no_secrets_in_report(self) -> None:
        report = build_harden_report(_make_harden_result())
        for pattern in ["eyJ", "service_role_key_value", "sk-", "xoxb-"]:
            assert pattern not in report

    def test_date_present(self) -> None:
        import datetime

        today = datetime.date.today().isoformat()
        report = build_harden_report(_make_harden_result())
        assert today in report

    def test_error_status_in_report(self) -> None:
        report = build_harden_report(_make_harden_result(status="ERROR"))
        assert "ERROR" in report

    def test_ok_status_in_report(self) -> None:
        report = build_harden_report(_make_harden_result(status="OK"))
        assert "OK" in report

    def test_critical_risks_section_when_present(self) -> None:
        report = build_harden_report(_make_harden_result(security_error=True))
        assert "Critical Risks" in report

    def test_generatable_fixes_section_when_present(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "Generatable Fixes" in report
        assert "25" in report

    def test_manual_actions_section_when_present(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert "Manual Actions Required" in report

    def test_report_ends_with_newline(self) -> None:
        report = build_harden_report(_make_harden_result())
        assert report.endswith("\n")


# ---------------------------------------------------------------------------
# TestCLIReclaimHardenOutput
# ---------------------------------------------------------------------------


class TestCLIReclaimHardenOutput:
    def _invoke_output(
        self,
        harden_result: ReclaimHardenResult,
        out: Path,
        extra: list[str] | None = None,
    ) -> object:
        args = [
            "reclaim",
            "harden",
            "--path",
            "/fake/project",
            "--output",
            str(out),
            *(extra or []),
        ]
        with patch("aeos.cli.run_reclaim_harden", return_value=harden_result):
            return runner.invoke(app, args)

    def test_no_output_option_writes_no_file(self, tmp_path: Path) -> None:
        with patch("aeos.cli.run_reclaim_harden", return_value=_make_harden_result()):
            runner.invoke(app, ["reclaim", "harden", "--path", "/fake/project"])
        assert not any(tmp_path.iterdir())

    def test_output_writes_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        result = self._invoke_output(_make_harden_result(), out)
        assert result.exit_code == 0, result.output  # type: ignore[union-attr]
        assert out.exists()

    def test_output_contains_read_only(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        self._invoke_output(_make_harden_result(), out)
        assert "read_only:     true" in out.read_text()

    def test_output_contains_applied_false(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        self._invoke_output(_make_harden_result(), out)
        assert "applied:       false" in out.read_text()

    def test_output_contains_status(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        self._invoke_output(_make_harden_result(status="WARNING"), out)
        assert "WARNING" in out.read_text()

    def test_output_contains_exit_options(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        self._invoke_output(_make_harden_result(), out)
        assert "Exit Options" in out.read_text()

    def test_output_no_secrets(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        self._invoke_output(_make_harden_result(), out)
        content = out.read_text()
        for pattern in ["eyJ", "service_role_key_value", "sk-", "xoxb-"]:
            assert pattern not in content

    def test_output_no_migration_applied(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        self._invoke_output(_make_harden_result(), out)
        assert "No correction has been applied" in out.read_text()

    def test_stdout_shows_exported_path(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        result = self._invoke_output(_make_harden_result(), out)
        assert "Exported:" in result.output  # type: ignore[union-attr]

    def test_stdout_shows_status(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        result = self._invoke_output(_make_harden_result(status="WARNING"), out)
        assert "WARNING" in result.output  # type: ignore[union-attr]

    def test_stdout_shows_invariants(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        result = self._invoke_output(_make_harden_result(), out)
        assert "read_only: true" in result.output  # type: ignore[union-attr]
        assert "applied: false" in result.output  # type: ignore[union-attr]

    def test_existing_file_without_overwrite_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        out.write_text("old content")
        result = self._invoke_output(_make_harden_result(), out)
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert out.read_text() == "old content"

    def test_existing_file_without_overwrite_shows_hint(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        out.write_text("old content")
        result = self._invoke_output(_make_harden_result(), out)
        assert "--overwrite" in result.output  # type: ignore[union-attr]

    def test_existing_file_with_overwrite_succeeds(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        out.write_text("old content")
        result = self._invoke_output(_make_harden_result(), out, ["--overwrite"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert out.read_text() != "old content"
        assert "AEOS Reclaim Harden Report" in out.read_text()

    def test_error_status_exits_1_with_output(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        result = self._invoke_output(_make_harden_result(status="ERROR"), out)
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert out.exists()

    def test_env_not_in_output_file(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("SUPABASE_URL=https://secret.supabase.co")
        out = tmp_path / "report.md"
        self._invoke_output(_make_harden_result(), out)
        if out.exists():
            assert "https://secret.supabase.co" not in out.read_text()


# ---------------------------------------------------------------------------
# TestCLIReclaimHardenOutputJSON
# ---------------------------------------------------------------------------


class TestCLIReclaimHardenOutputJSON:
    def _invoke_json_output(
        self,
        harden_result: ReclaimHardenResult,
        out: Path,
        extra: list[str] | None = None,
    ) -> dict[str, object]:
        args = [
            "reclaim",
            "harden",
            "--path",
            "/fake/project",
            "--output",
            str(out),
            "--json",
            *(extra or []),
        ]
        with patch("aeos.cli.run_reclaim_harden", return_value=harden_result):
            r = runner.invoke(app, args)
        return json.loads(r.output)  # type: ignore[no-any-return]

    def test_json_has_output_written_true(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        data = self._invoke_json_output(_make_harden_result(), out)
        assert data["output_written"] is True

    def test_json_has_output_path(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        data = self._invoke_json_output(_make_harden_result(), out)
        assert data["output_path"] == str(out)

    def test_json_no_output_has_output_written_false(self) -> None:
        with patch("aeos.cli.run_reclaim_harden", return_value=_make_harden_result()):
            r = runner.invoke(
                app,
                ["reclaim", "harden", "--path", "/fake/project", "--json"],
            )
        data = json.loads(r.output)
        assert data["output_written"] is False
        assert data["output_path"] == ""

    def test_json_read_only_true_with_output(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        data = self._invoke_json_output(_make_harden_result(), out)
        assert data["read_only"] is True

    def test_json_applied_false_with_output(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        data = self._invoke_json_output(_make_harden_result(), out)
        assert data["applied"] is False

    def test_json_has_summary_with_output(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        data = self._invoke_json_output(_make_harden_result(), out)
        assert "summary" in data

    def test_json_no_secrets_with_output(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        data = self._invoke_json_output(_make_harden_result(), out)
        output_str = json.dumps(data)
        for pattern in ["eyJ", "service_role_key_value", "sk-", "xoxb-"]:
            assert pattern not in output_str


# ---------------------------------------------------------------------------
# TestFixtureWithOutput — real fixture, no mocks
# ---------------------------------------------------------------------------


class TestFixtureWithOutput:
    @pytest.fixture()
    def lovable_project(self, tmp_path: Path) -> Path:
        (tmp_path / ".lovable").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        (tmp_path / "supabase" / "config.toml").write_text(
            "[api]\nenabled = true\n", encoding="utf-8"
        )
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"@supabase/supabase-js": "^2.0.0"}}',
            encoding="utf-8",
        )
        (tmp_path / ".gitignore").write_text(".env\n.env.*\n", encoding="utf-8")
        migration = tmp_path / "supabase" / "migrations" / "20240101_init.sql"
        migration.write_text(
            "CREATE TABLE citizens (id uuid PRIMARY KEY);\n"
            "ALTER TABLE citizens ENABLE ROW LEVEL SECURITY;\n",
            encoding="utf-8",
        )
        return tmp_path

    def test_output_to_tmp_writes_file(
        self, lovable_project: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "reclaim-report.md"
        result = runner.invoke(
            app,
            [
                "reclaim",
                "harden",
                "--path",
                str(lovable_project),
                "--output",
                str(out),
            ],
        )
        assert out.exists(), result.output
        content = out.read_text()
        assert "AEOS Reclaim Harden Report" in content
        assert "read_only:     true" in content
        assert "applied:       false" in content

    def test_output_no_client_files_modified(
        self, lovable_project: Path, tmp_path: Path
    ) -> None:
        import os

        files_before = {
            p: os.path.getmtime(p) for p in lovable_project.rglob("*") if p.is_file()
        }
        out = tmp_path / "report.md"
        runner.invoke(
            app,
            [
                "reclaim",
                "harden",
                "--path",
                str(lovable_project),
                "--output",
                str(out),
            ],
        )
        for p, mtime in files_before.items():
            assert os.path.getmtime(p) == mtime, f"File modified: {p}"

    def test_output_no_secrets_in_file(
        self, lovable_project: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.md"
        runner.invoke(
            app,
            [
                "reclaim",
                "harden",
                "--path",
                str(lovable_project),
                "--output",
                str(out),
            ],
        )
        if out.exists():
            content = out.read_text().lower()
            for pattern in ["eyj", "service_role_key", "sk-"]:
                assert pattern not in content

    def test_overwrite_replaces_existing(
        self, lovable_project: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.md"
        out.write_text("old content")
        runner.invoke(
            app,
            [
                "reclaim",
                "harden",
                "--path",
                str(lovable_project),
                "--output",
                str(out),
                "--overwrite",
            ],
        )
        assert out.read_text() != "old content"
        assert "AEOS Reclaim Harden Report" in out.read_text()

    def test_no_overwrite_refuses_existing(
        self, lovable_project: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.md"
        out.write_text("old content")
        result = runner.invoke(
            app,
            [
                "reclaim",
                "harden",
                "--path",
                str(lovable_project),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1
        assert out.read_text() == "old content"


# ---------------------------------------------------------------------------
# TestFixture — lightweight Lovable/Supabase project
# ---------------------------------------------------------------------------


class TestFixture:
    """Test run_reclaim_harden on a minimal synthetic fixture."""

    @pytest.fixture()
    def lovable_supabase_project(self, tmp_path: Path) -> Path:
        (tmp_path / ".lovable").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        (tmp_path / "supabase" / "config.toml").write_text(
            "[api]\nenabled = true\n", encoding="utf-8"
        )
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"@supabase/supabase-js": "^2.0.0"}}',
            encoding="utf-8",
        )
        (tmp_path / ".gitignore").write_text(".env\n.env.*\n", encoding="utf-8")
        migration = tmp_path / "supabase" / "migrations" / "20240101_init.sql"
        migration.write_text(
            "CREATE TABLE citizens (id uuid PRIMARY KEY);\n"
            "ALTER TABLE citizens ENABLE ROW LEVEL SECURITY;\n",
            encoding="utf-8",
        )
        return tmp_path

    @pytest.fixture()
    def clean_project(self, tmp_path: Path) -> Path:
        (tmp_path / "src").mkdir()
        (tmp_path / "server").mkdir()
        (tmp_path / "prisma").mkdir()
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
        (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
        return tmp_path

    def test_lovable_supabase_fixture_warning_or_error(
        self, lovable_supabase_project: Path
    ) -> None:
        result = run_reclaim_harden(lovable_supabase_project)
        assert result.status in ("WARNING", "ERROR")
        assert result.read_only is True
        assert result.applied is False

    def test_lovable_supabase_fixture_detects_generator(
        self, lovable_supabase_project: Path
    ) -> None:
        result = run_reclaim_harden(lovable_supabase_project)
        assert result.summary.generator_detected == "lovable"

    def test_lovable_supabase_fixture_detects_supabase(
        self, lovable_supabase_project: Path
    ) -> None:
        result = run_reclaim_harden(lovable_supabase_project)
        assert "supabase" in result.summary.providers_detected

    def test_lovable_supabase_fixture_runs_rls(
        self, lovable_supabase_project: Path
    ) -> None:
        result = run_reclaim_harden(lovable_supabase_project)
        assert result.rls is not None

    def test_lovable_supabase_fixture_no_client_files_modified(
        self, lovable_supabase_project: Path
    ) -> None:
        import os

        files_before = {
            p: os.path.getmtime(p)
            for p in lovable_supabase_project.rglob("*")
            if p.is_file()
        }
        run_reclaim_harden(lovable_supabase_project)
        for p, mtime in files_before.items():
            assert os.path.getmtime(p) == mtime, f"File modified: {p}"

    def test_clean_project_ok_or_warning(self, clean_project: Path) -> None:
        result = run_reclaim_harden(clean_project)
        assert result.status in ("OK", "WARNING")
        assert result.read_only is True
        assert result.applied is False

    def test_fixture_json_cli_valid(self, lovable_supabase_project: Path) -> None:
        with patch(
            "aeos.cli.run_reclaim_harden",
            side_effect=lambda p: run_reclaim_harden(p),
        ):
            r = runner.invoke(
                app,
                [
                    "reclaim",
                    "harden",
                    "--path",
                    str(lovable_supabase_project),
                    "--json",
                ],
            )
        data = json.loads(r.output)
        assert data["read_only"] is True
        assert data["applied"] is False
        assert "summary" in data
