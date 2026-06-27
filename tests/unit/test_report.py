"""Unit tests for aeos.report.generator — Sprint 2P Project Report MVP."""

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.project.inspector import InspectResult
from aeos.report.generator import (
    ProjectReport,
    ReportRecommendation,
    ReportRisk,
    ReportSection,
    _build_governance_section,
    _build_project_section,
    _build_recommendations,
    _build_security_section,
    _build_sovereignty_section,
    _build_top_risks,
    _compute_report_status,
    generate_report,
)
from aeos.security.checker import SecurityCheckResult, SecurityFinding
from aeos.sovereignty.checker import SovereigntyCheckResult, SovereigntyFinding

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _inspect(
    tmp: Path,
    *,
    name: str = "test-project",
    aeos_toml: bool = True,
    pyproject_toml: bool = True,
    readme: bool = True,
    manifesto: bool = True,
    constitution: bool = True,
    governance: bool = True,
    docs: bool = True,
    src: bool = True,
    tests: bool = True,
    ci_yml: bool = True,
    git_present: bool = True,
    remote_origin: str = "",
) -> InspectResult:
    return InspectResult(
        path=tmp,
        name=name,
        aeos_toml=aeos_toml,
        pyproject_toml=pyproject_toml,
        readme=readme,
        manifesto=manifesto,
        constitution=constitution,
        governance=governance,
        docs=docs,
        src=src,
        tests=tests,
        ci_yml=ci_yml,
        git_present=git_present,
        remote_origin=remote_origin,
    )


def _sov_finding(
    category: str,
    severity: str,
    message: str,
    location: str = "file.ts",
) -> SovereigntyFinding:
    return SovereigntyFinding(
        category=category,
        severity=severity,
        message=message,
        location=location,
        recommendation="fix it",
    )


def _sec_finding(
    category: str,
    severity: str,
    message: str,
    location: str = "file.py",
) -> SecurityFinding:
    return SecurityFinding(
        category=category,
        severity=severity,
        message=message,
        location=location,
        recommendation="fix it",
    )


def _empty_sov(tmp: Path) -> SovereigntyCheckResult:
    return SovereigntyCheckResult(path=tmp, status="OK", findings=[])


def _empty_sec(tmp: Path) -> SecurityCheckResult:
    return SecurityCheckResult(path=tmp, status="OK", findings=[])


def _ok_gov_section() -> ReportSection:
    return ReportSection(
        status="OK",
        summary="11/11 items present",
        details={"total": 11, "present": 11, "missing": []},
    )


def _warn_gov_section() -> ReportSection:
    return ReportSection(
        status="WARNING",
        summary="9/11 items present",
        details={"total": 11, "present": 9, "missing": ["governance/adr", "docs"]},
    )


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class TestDataModel:
    def test_report_section_fields(self) -> None:
        sec = ReportSection(status="OK", summary="all good", details={})
        assert sec.status == "OK"
        assert sec.summary == "all good"
        assert sec.details == {}

    def test_report_risk_fields(self) -> None:
        risk = ReportRisk(
            severity="ERROR",
            category="secrets",
            message="key found",
            location="src/config.ts",
        )
        assert risk.severity == "ERROR"
        assert risk.location == "src/config.ts"

    def test_report_recommendation_fields(self) -> None:
        rec = ReportRecommendation(priority=1, action="Fix it now")
        assert rec.priority == 1
        assert rec.action == "Fix it now"

    def test_project_report_defaults(self, tmp_path: Path) -> None:
        r = ProjectReport(
            path=tmp_path,
            status="OK",
            sections={},
        )
        assert r.top_risks == []
        assert r.recommendations == []

    def test_project_report_with_data(self, tmp_path: Path) -> None:
        sec = ReportSection(status="OK", summary="s", details={})
        risk = ReportRisk("WARNING", "portability", "msg", "Dockerfile")
        rec = ReportRecommendation(1, "action")
        r = ProjectReport(
            path=tmp_path,
            status="WARNING",
            sections={"project": sec},
            top_risks=[risk],
            recommendations=[rec],
        )
        assert r.status == "WARNING"
        assert len(r.sections) == 1
        assert len(r.top_risks) == 1
        assert len(r.recommendations) == 1


# ---------------------------------------------------------------------------
# _build_project_section
# ---------------------------------------------------------------------------


class TestBuildProjectSection:
    def test_status_always_ok(self, tmp_path: Path) -> None:
        result = _build_project_section(_inspect(tmp_path))
        assert result.status == "OK"

    def test_name_in_details(self, tmp_path: Path) -> None:
        result = _build_project_section(_inspect(tmp_path, name="my-app"))
        assert result.details["name"] == "my-app"

    def test_remote_in_summary_when_present(self, tmp_path: Path) -> None:
        result = _build_project_section(
            _inspect(tmp_path, remote_origin="https://github.com/org/repo.git")
        )
        assert "https://github.com/org/repo.git" in result.summary

    def test_no_remote_no_separator(self, tmp_path: Path) -> None:
        result = _build_project_section(_inspect(tmp_path, remote_origin=""))
        assert "·" not in result.summary

    def test_all_fields_in_details(self, tmp_path: Path) -> None:
        result = _build_project_section(_inspect(tmp_path))
        for key in (
            "aeos_toml",
            "pyproject_toml",
            "readme",
            "manifesto",
            "constitution",
            "governance",
            "src",
            "tests",
            "docs",
            "ci_yml",
            "git_present",
        ):
            assert key in result.details


# ---------------------------------------------------------------------------
# _build_governance_section
# ---------------------------------------------------------------------------


class TestBuildGovernanceSection:
    def test_all_present_is_ok(self) -> None:
        items = [("README.md", True), ("aeos.toml", True), ("src", True)]
        result = _build_governance_section(items)
        assert result.status == "OK"
        assert result.details["missing"] == []

    def test_missing_item_is_warning(self) -> None:
        items = [("README.md", True), ("aeos.toml", False), ("src", True)]
        result = _build_governance_section(items)
        assert result.status == "WARNING"
        assert "aeos.toml" in result.details["missing"]

    def test_counts_correct(self) -> None:
        items = [("a", True), ("b", False), ("c", True), ("d", False)]
        result = _build_governance_section(items)
        assert result.details["total"] == 4
        assert result.details["present"] == 2
        assert len(result.details["missing"]) == 2

    def test_empty_missing_list_in_ok_case(self) -> None:
        items = [("x", True)]
        result = _build_governance_section(items)
        assert result.details["missing"] == []

    def test_summary_contains_counts(self) -> None:
        items = [("a", True), ("b", True), ("c", False)]
        result = _build_governance_section(items)
        assert "2/3" in result.summary


# ---------------------------------------------------------------------------
# _build_sovereignty_section / _build_security_section
# ---------------------------------------------------------------------------


class TestBuildAuditSections:
    def test_sovereignty_ok_when_no_findings(self, tmp_path: Path) -> None:
        result = _build_sovereignty_section(_empty_sov(tmp_path))
        assert result.status == "OK"
        assert result.details["findings_count"] == 0

    def test_sovereignty_propagates_status(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[_sov_finding("portability", "WARNING", "Dockerfile not found")],
        )
        result = _build_sovereignty_section(sov)
        assert result.status == "WARNING"

    def test_sovereignty_counts_by_severity(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[
                _sov_finding("secrets", "ERROR", "msg1"),
                _sov_finding("portability", "WARNING", "msg2"),
                _sov_finding("portability", "WARNING", "msg3"),
            ],
        )
        result = _build_sovereignty_section(sov)
        assert result.details["error_count"] == 1
        assert result.details["warning_count"] == 2
        assert result.details["findings_count"] == 3

    def test_sovereignty_top_findings_capped_at_5(self, tmp_path: Path) -> None:
        findings = [_sov_finding("portability", "WARNING", f"msg{i}") for i in range(8)]
        sov = SovereigntyCheckResult(path=tmp_path, status="WARNING", findings=findings)
        result = _build_sovereignty_section(sov)
        assert len(result.details["top_findings"]) == 5

    def test_top_findings_no_evidence(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[_sov_finding("portability", "WARNING", "Dockerfile not found")],
        )
        result = _build_sovereignty_section(sov)
        for finding in result.details["top_findings"]:
            assert "evidence" not in finding
            assert "recommendation" not in finding

    def test_security_propagates_status(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[_sec_finding("env_files", "ERROR", ".env exposed")],
        )
        result = _build_security_section(sec)
        assert result.status == "ERROR"

    def test_security_counts(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[
                _sec_finding("env_files", "ERROR", "err"),
                _sec_finding("secrets", "WARNING", "warn"),
            ],
        )
        result = _build_security_section(sec)
        assert result.details["error_count"] == 1
        assert result.details["warning_count"] == 1


# ---------------------------------------------------------------------------
# _compute_report_status
# ---------------------------------------------------------------------------


class TestComputeReportStatus:
    def test_all_ok_is_ok(self) -> None:
        sections = {
            "a": ReportSection("OK", "", {}),
            "b": ReportSection("OK", "", {}),
        }
        assert _compute_report_status(sections) == "OK"

    def test_one_warning_is_warning(self) -> None:
        sections = {
            "a": ReportSection("OK", "", {}),
            "b": ReportSection("WARNING", "", {}),
        }
        assert _compute_report_status(sections) == "WARNING"

    def test_one_error_is_error(self) -> None:
        sections = {
            "a": ReportSection("WARNING", "", {}),
            "b": ReportSection("ERROR", "", {}),
        }
        assert _compute_report_status(sections) == "ERROR"

    def test_error_beats_warning(self) -> None:
        sections = {
            "a": ReportSection("ERROR", "", {}),
            "b": ReportSection("WARNING", "", {}),
            "c": ReportSection("OK", "", {}),
        }
        assert _compute_report_status(sections) == "ERROR"


# ---------------------------------------------------------------------------
# _build_top_risks
# ---------------------------------------------------------------------------


class TestBuildTopRisks:
    def test_empty_findings_no_risks(self, tmp_path: Path) -> None:
        risks = _build_top_risks(
            _empty_sov(tmp_path), _empty_sec(tmp_path), _ok_gov_section()
        )
        assert risks == []

    def test_capped_at_five(self, tmp_path: Path) -> None:
        findings = [_sec_finding("secrets", "WARNING", f"msg{i}") for i in range(8)]
        sec = SecurityCheckResult(path=tmp_path, status="WARNING", findings=findings)
        risks = _build_top_risks(_empty_sov(tmp_path), sec, _ok_gov_section())
        assert len(risks) <= 5

    def test_errors_before_warnings(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[
                _sec_finding("secrets", "WARNING", "warn-first"),
                _sec_finding("env_files", "ERROR", "err-first"),
            ],
        )
        risks = _build_top_risks(_empty_sov(tmp_path), sec, _ok_gov_section())
        assert risks[0].severity == "ERROR"

    def test_security_before_sovereignty(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[_sov_finding("secrets", "ERROR", "sov-error")],
        )
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[_sec_finding("env_files", "ERROR", "sec-error")],
        )
        risks = _build_top_risks(sov, sec, _ok_gov_section())
        assert risks[0].message == "sec-error"

    def test_deduplication(self, tmp_path: Path) -> None:
        finding = _sec_finding("secrets", "WARNING", "same-msg")
        sec = SecurityCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[finding, finding, finding],
        )
        risks = _build_top_risks(_empty_sov(tmp_path), sec, _ok_gov_section())
        assert len(risks) == 1

    def test_governance_missing_adds_risk(self, tmp_path: Path) -> None:
        risks = _build_top_risks(
            _empty_sov(tmp_path),
            _empty_sec(tmp_path),
            _warn_gov_section(),
        )
        assert any(r.category == "governance" for r in risks)

    def test_no_governance_risk_when_complete(self, tmp_path: Path) -> None:
        risks = _build_top_risks(
            _empty_sov(tmp_path),
            _empty_sec(tmp_path),
            _ok_gov_section(),
        )
        assert not any(r.category == "governance" for r in risks)

    def test_risk_has_no_evidence_field(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[_sec_finding("secrets", "WARNING", "key")],
        )
        risks = _build_top_risks(_empty_sov(tmp_path), sec, _ok_gov_section())
        for risk in risks:
            assert not hasattr(risk, "evidence")
            assert not hasattr(risk, "recommendation")


# ---------------------------------------------------------------------------
# _build_recommendations
# ---------------------------------------------------------------------------


class TestBuildRecommendations:
    def test_fallback_when_no_findings(self, tmp_path: Path) -> None:
        recs = _build_recommendations(
            _ok_gov_section(), _empty_sov(tmp_path), _empty_sec(tmp_path)
        )
        assert len(recs) == 1
        assert "No blocking issues" in recs[0].action

    def test_env_files_error_produces_gitignore_rec(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[_sec_finding("env_files", "ERROR", ".env exposed")],
        )
        recs = _build_recommendations(_ok_gov_section(), _empty_sov(tmp_path), sec)
        assert any(".gitignore" in r.action for r in recs)

    def test_secrets_error_produces_remove_rec(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[_sec_finding("secrets", "ERROR", "API key found")],
        )
        recs = _build_recommendations(_ok_gov_section(), _empty_sov(tmp_path), sec)
        assert any("hardcoded secrets" in r.action for r in recs)

    def test_governance_missing_produces_complete_rec(self, tmp_path: Path) -> None:
        recs = _build_recommendations(
            _warn_gov_section(), _empty_sov(tmp_path), _empty_sec(tmp_path)
        )
        assert any("governance" in r.action.lower() for r in recs)

    def test_portability_produces_dockerfile_rec(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[_sov_finding("portability", "WARNING", "Dockerfile not found")],
        )
        recs = _build_recommendations(_ok_gov_section(), sov, _empty_sec(tmp_path))
        assert any("Dockerfile" in r.action for r in recs)

    def test_source_scan_produces_exit_strategy_rec(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[_sov_finding("source_scan", "WARNING", "Supabase SDK detected")],
        )
        recs = _build_recommendations(_ok_gov_section(), sov, _empty_sec(tmp_path))
        assert any("exit strategy" in r.action.lower() for r in recs)

    def test_dependencies_warning_produces_lockfile_rec(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[_sec_finding("dependencies", "WARNING", "no lockfile")],
        )
        recs = _build_recommendations(_ok_gov_section(), _empty_sov(tmp_path), sec)
        assert any("lockfile" in r.action.lower() for r in recs)

    def test_no_duplicate_actions(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[
                _sov_finding("portability", "WARNING", "Dockerfile not found"),
                _sov_finding("portability", "WARNING", "Dockerfile not found"),
            ],
        )
        recs = _build_recommendations(_ok_gov_section(), sov, _empty_sec(tmp_path))
        actions = [r.action for r in recs]
        assert len(actions) == len(set(actions))

    def test_max_six_recommendations(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[
                _sec_finding("env_files", "ERROR", "err"),
                _sec_finding("secrets", "ERROR", "err"),
                _sec_finding("dependencies", "WARNING", "warn"),
                _sec_finding("config", "WARNING", "USER root in Dockerfile"),
                _sec_finding("config", "WARNING", "pull_request_target"),
            ],
        )
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[
                _sov_finding("portability", "WARNING", "Dockerfile not found"),
                _sov_finding("source_scan", "WARNING", "Supabase SDK"),
            ],
        )
        recs = _build_recommendations(_warn_gov_section(), sov, sec)
        assert len(recs) <= 6

    def test_priorities_are_sequential(self, tmp_path: Path) -> None:
        sov = SovereigntyCheckResult(
            path=tmp_path,
            status="WARNING",
            findings=[
                _sov_finding("portability", "WARNING", "Dockerfile not found"),
                _sov_finding("source_scan", "WARNING", "Supabase SDK"),
            ],
        )
        recs = _build_recommendations(_warn_gov_section(), sov, _empty_sec(tmp_path))
        for i, rec in enumerate(recs, start=1):
            assert rec.priority == i

    def test_no_sensitive_values_in_actions(self, tmp_path: Path) -> None:
        sec = SecurityCheckResult(
            path=tmp_path,
            status="ERROR",
            findings=[_sec_finding("env_files", "ERROR", ".env exposed")],
        )
        recs = _build_recommendations(_ok_gov_section(), _empty_sov(tmp_path), sec)
        for rec in recs:
            for sensitive in ("sk-", "AKIA", "ghp_", "xoxb-"):
                assert sensitive not in rec.action


# ---------------------------------------------------------------------------
# generate_report (integration)
# ---------------------------------------------------------------------------


class TestGenerateReport:
    def test_returns_project_report(self, tmp_path: Path) -> None:
        result = generate_report(tmp_path)
        assert isinstance(result, ProjectReport)

    def test_path_is_absolute(self, tmp_path: Path) -> None:
        result = generate_report(tmp_path)
        assert result.path.is_absolute()

    def test_clean_project_is_ok(self, tmp_path: Path) -> None:
        # Full .gitignore → security OK; no package.json → no missing lock
        (tmp_path / ".gitignore").write_text(
            ".env\n.env.*\n*.pem\n*.key\nnode_modules/\n.venv/\n"
        )
        result = generate_report(tmp_path)
        assert result.status in {"OK", "WARNING"}

    def test_project_with_bare_env_has_error(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SECRET=real\n")
        result = generate_report(tmp_path)
        assert result.status == "ERROR"

    def test_sections_present(self, tmp_path: Path) -> None:
        result = generate_report(tmp_path)
        assert "project" in result.sections
        assert "governance" in result.sections
        assert "sovereignty" in result.sections
        assert "security" in result.sections

    def test_top_risks_never_exceed_five(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SECRET=real\n")
        result = generate_report(tmp_path)
        assert len(result.top_risks) <= 5

    def test_recommendations_not_empty(self, tmp_path: Path) -> None:
        result = generate_report(tmp_path)
        assert len(result.recommendations) >= 1

    def test_json_serializable(self, tmp_path: Path) -> None:
        result = generate_report(tmp_path)
        payload = {
            "path": str(result.path),
            "status": result.status,
            "sections": {
                name: {
                    "status": sec.status,
                    "summary": sec.summary,
                    "details": sec.details,
                }
                for name, sec in result.sections.items()
            },
            "top_risks": [
                {
                    "severity": r.severity,
                    "category": r.category,
                    "message": r.message,
                    "location": r.location,
                }
                for r in result.top_risks
            ],
            "recommendations": [
                {"priority": r.priority, "action": r.action}
                for r in result.recommendations
            ],
        }
        dumped = json.dumps(payload)
        loaded = json.loads(dumped)
        assert loaded["status"] == result.status

    def test_no_sensitive_values_in_top_risks(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.ts").write_text("const k = 'AKIAIOSFODNN7EXAMPLE';\n")
        (tmp_path / ".gitignore").write_text(
            ".env\n.env.*\n*.pem\n*.key\nnode_modules/\n.venv/\n"
        )
        result = generate_report(tmp_path)
        for risk in result.top_risks:
            for field_val in (risk.message, risk.location, risk.category):
                assert "AKIAIOSFODNN7EXAMPLE" not in field_val


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestCliReport:
    def test_report_text_output_contains_header(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
        assert "AEOS Project Report" in result.output

    def test_report_text_output_contains_sections(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
        assert "Project" in result.output
        assert "Governance" in result.output
        assert "Sovereignty" in result.output
        assert "Security" in result.output

    def test_report_text_contains_top_risks(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
        assert "Top Risks" in result.output

    def test_report_text_contains_recommendations(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
        assert "Recommended Next Actions" in result.output

    def test_report_json_is_valid(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["report", "--path", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert "status" in data
        assert "sections" in data
        assert "top_risks" in data
        assert "recommendations" in data

    def test_report_json_sections_structure(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["report", "--path", str(tmp_path), "--json"])
        data = json.loads(result.output)
        for section_name in ("project", "governance", "sovereignty", "security"):
            assert section_name in data["sections"]
            assert "status" in data["sections"][section_name]
            assert "summary" in data["sections"][section_name]
            assert "details" in data["sections"][section_name]

    def test_report_warning_exits_0(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("")
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
        assert result.exit_code == 0

    def test_report_error_exits_1(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SECRET=real\n")
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
        assert result.exit_code == 1

    def test_report_json_error_exits_1(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SECRET=real\n")
        result = runner.invoke(app, ["report", "--path", str(tmp_path), "--json"])
        assert result.exit_code == 1

    def test_report_nonexistent_path_exits_1(self) -> None:
        result = runner.invoke(app, ["report", "--path", "/nonexistent/path"])
        assert result.exit_code == 1

    def test_report_default_path_works(self) -> None:
        result = runner.invoke(app, ["report"])
        assert result.exit_code in {0, 1}
        assert "AEOS Project Report" in result.output

    def test_report_json_top_risks_capped(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["report", "--path", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert len(data["top_risks"]) <= 5

    def test_report_json_no_sensitive_values_in_risks(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "cfg.ts").write_text("const k = 'AKIAIOSFODNN7EXAMPLE';\n")
        (tmp_path / ".gitignore").write_text(
            ".env\n.env.*\n*.pem\n*.key\nnode_modules/\n.venv/\n"
        )
        result = runner.invoke(app, ["report", "--path", str(tmp_path), "--json"])
        data = json.loads(result.output)
        output_str = json.dumps(data["top_risks"])
        assert "AKIAIOSFODNN7EXAMPLE" not in output_str
