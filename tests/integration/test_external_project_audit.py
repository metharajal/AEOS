"""
Integration tests: AEOS auditing an external project cloned locally.

Validates that:
- all audit commands support --path <external_dir>
- findings are coherent for a realistic SaaS project fixture
- the audit pipeline is strictly read-only (no files created or modified)
"""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.onboarding import check_project
from aeos.project import inspect_project
from aeos.report import generate_report
from aeos.security import run_security_check
from aeos.sovereignty import run_sovereignty_check

FIXTURE_DIR = (
    Path(__file__).parent.parent
    / "fixtures"
    / "realistic_projects"
    / "lovable_supabase_vercel"
)

runner = CliRunner()


def _fingerprint(directory: Path) -> dict[str, int]:
    """Map relative file paths to sizes — detects any write to the directory."""
    return {
        str(p.relative_to(directory)): p.stat().st_size
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


@pytest.fixture()
def ext_project(tmp_path: Path) -> Path:
    dest = tmp_path / "lovable_project"
    shutil.copytree(FIXTURE_DIR, dest)
    # .env is gitignored in the AEOS repo — create it at test runtime so it
    # exists on CI exactly as it would in a real project cloned locally.
    (dest / ".env").write_text(
        "# Test fixture — values are fake placeholders, not real credentials\n"
        "NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co\n"
        "NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key-here\n"
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key-here\n"
        "STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-here\n"
    )
    return dest


# ---------------------------------------------------------------------------
# onboard --path option
# ---------------------------------------------------------------------------


class TestOnboardPathOption:
    def test_check_with_path_option(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["onboard", "--check", "--path", str(ext_project)])
        assert r.exit_code == 1
        assert "MISSING" in r.output

    def test_check_json_with_path_option(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["onboard", "--check", "--path", str(ext_project), "--json"]
        )
        assert r.exit_code == 1
        data = json.loads(r.output)
        assert data["ok"] is False
        assert str(ext_project) in data["path"]

    def test_json_path_is_absolute(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["onboard", "--check", "--path", str(ext_project), "--json"]
        )
        data = json.loads(r.output)
        assert Path(data["path"]).is_absolute()

    def test_nonexistent_path_fails_cleanly(self) -> None:
        r = runner.invoke(
            app, ["onboard", "--check", "--path", "/nonexistent/xyz/project"]
        )
        assert r.exit_code == 1
        assert "does not exist" in r.output


# ---------------------------------------------------------------------------
# Security findings on the fixture
# ---------------------------------------------------------------------------


class TestSecurityOnExternalProject:
    def test_env_file_not_gitignored_is_error(self, ext_project: Path) -> None:
        result = run_security_check(ext_project)
        env_errors = [
            f
            for f in result.findings
            if f.category == "env_files" and f.severity == "ERROR"
        ]
        assert len(env_errors) > 0

    def test_status_is_error_due_to_env(self, ext_project: Path) -> None:
        result = run_security_check(ext_project)
        assert result.status == "ERROR"

    def test_no_sensitive_values_in_findings(self, ext_project: Path) -> None:
        result = run_security_check(ext_project)
        for f in result.findings:
            assert "your-project.supabase.co" not in f.evidence
            assert "your-supabase-anon-key-here" not in f.evidence
            assert "your-clerk-publishable-key-here" not in f.evidence

    def test_dependencies_no_lock_file(self, ext_project: Path) -> None:
        result = run_security_check(ext_project)
        dep_findings = [f for f in result.findings if f.category == "dependencies"]
        assert len(dep_findings) > 0

    def test_path_is_absolute(self, ext_project: Path) -> None:
        result = run_security_check(ext_project)
        assert result.path.is_absolute()


# ---------------------------------------------------------------------------
# Sovereignty findings on the fixture
# ---------------------------------------------------------------------------


class TestSovereigntyOnExternalProject:
    def test_supabase_dependency_detected(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        messages = [f.message.lower() for f in result.findings]
        assert any("supabase" in m for m in messages)

    def test_clerk_dependency_detected(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        messages = [f.message.lower() for f in result.findings]
        assert any("clerk" in m for m in messages)

    def test_stripe_dependency_detected(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        messages = [f.message.lower() for f in result.findings]
        assert any("stripe" in m for m in messages)

    def test_portability_no_dockerfile(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        portability = [f for f in result.findings if f.category == "portability"]
        locations = [f.location for f in portability]
        assert "Dockerfile" in locations

    def test_vercel_hosting_detected(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        messages = [f.message.lower() for f in result.findings]
        assert any("vercel" in m for m in messages)

    def test_source_scan_supabase_import(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        source_findings = [f for f in result.findings if f.category == "source_scan"]
        messages = [f.message.lower() for f in source_findings]
        assert any("supabase" in m for m in messages)

    def test_no_sensitive_values_in_findings(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        for f in result.findings:
            assert "your-project.supabase.co" not in f.evidence
            assert "your-anon-key-here" not in f.evidence

    def test_status_is_warning_or_worse(self, ext_project: Path) -> None:
        result = run_sovereignty_check(ext_project)
        assert result.status in ("WARNING", "ERROR")


# ---------------------------------------------------------------------------
# Report on the fixture
# ---------------------------------------------------------------------------


class TestReportOnExternalProject:
    def test_report_status_is_error(self, ext_project: Path) -> None:
        result = generate_report(ext_project)
        assert result.status == "ERROR"

    def test_report_sections_present(self, ext_project: Path) -> None:
        result = generate_report(ext_project)
        assert set(result.sections.keys()) == {
            "project",
            "governance",
            "sovereignty",
            "security",
        }

    def test_top_risks_capped_at_five(self, ext_project: Path) -> None:
        result = generate_report(ext_project)
        assert len(result.top_risks) <= 5

    def test_top_risks_contain_no_sensitive_values(self, ext_project: Path) -> None:
        result = generate_report(ext_project)
        for risk in result.top_risks:
            assert "your-project.supabase.co" not in risk.message
            assert "your-anon-key-here" not in risk.message

    def test_recommendations_not_empty(self, ext_project: Path) -> None:
        result = generate_report(ext_project)
        assert len(result.recommendations) > 0

    def test_json_output_is_valid(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["report", "--path", str(ext_project), "--json"])
        assert r.exit_code == 1
        data = json.loads(r.output)
        assert data["status"] == "ERROR"
        assert "sections" in data
        assert "top_risks" in data
        assert "recommendations" in data

    def test_cli_report_error_exits_1(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["report", "--path", str(ext_project)])
        assert r.exit_code == 1


# ---------------------------------------------------------------------------
# Read-only guarantee
# ---------------------------------------------------------------------------


class TestReadOnlyGuarantee:
    def test_python_api_does_not_modify_project(self, ext_project: Path) -> None:
        before = _fingerprint(ext_project)

        inspect_project(ext_project)
        check_project(ext_project)
        run_sovereignty_check(ext_project)
        run_security_check(ext_project)
        generate_report(ext_project)

        after = _fingerprint(ext_project)
        assert before == after, "Audit modified the target project via Python API"

    def test_cli_does_not_modify_project(self, ext_project: Path) -> None:
        before = _fingerprint(ext_project)
        path_str = str(ext_project)

        runner.invoke(app, ["project", "inspect", "--path", path_str])
        runner.invoke(app, ["onboard", "--check", "--path", path_str])
        runner.invoke(app, ["sovereignty", "check", "--path", path_str])
        runner.invoke(app, ["security", "check", "--path", path_str])
        runner.invoke(app, ["report", "--path", path_str])
        runner.invoke(app, ["report", "--path", path_str, "--json"])

        after = _fingerprint(ext_project)
        assert before == after, "CLI audit modified the target project"

    def test_no_new_files_created(self, ext_project: Path) -> None:
        before = set(_fingerprint(ext_project).keys())

        generate_report(ext_project)

        after = set(_fingerprint(ext_project).keys())
        assert before == after, f"New files created: {after - before}"
