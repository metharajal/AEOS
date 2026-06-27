"""
Integration tests: AEOS Supabase advisor on the lovable_supabase_vercel fixture.
"""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.providers.supabase import run_supabase_check

FIXTURE_DIR = (
    Path(__file__).parent.parent
    / "fixtures"
    / "realistic_projects"
    / "lovable_supabase_vercel"
)

runner = CliRunner()


def _fingerprint(directory: Path) -> dict[str, int]:
    return {
        str(p.relative_to(directory)): p.stat().st_size
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


@pytest.fixture()
def ext_project(tmp_path: Path) -> Path:
    dest = tmp_path / "lovable_project"
    shutil.copytree(FIXTURE_DIR, dest)
    (dest / ".env").write_text(
        "# Test fixture — fake placeholders, not real credentials\n"
        "NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co\n"
        "NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key-here\n"
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key-here\n"
        "STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-here\n"
    )
    return dest


# ---------------------------------------------------------------------------
# TestSupabaseDetection
# ---------------------------------------------------------------------------


class TestSupabaseDetection:
    def test_supabase_detected_in_fixture(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.supabase_detected is True

    def test_path_is_absolute(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.path.is_absolute()

    def test_status_is_not_ok_when_supabase_present(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.status != "OK"


# ---------------------------------------------------------------------------
# TestKeyRisks
# ---------------------------------------------------------------------------


class TestKeyRisks:
    def test_supabase_var_detected(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        var_names = [r.variable_name for r in result.key_risks]
        assert any("SUPABASE" in n for n in var_names)

    def test_no_secret_key_in_fixture(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert all(r.key_type != "secret" for r in result.key_risks)

    def test_no_sensitive_values_in_key_risks(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        for risk in result.key_risks:
            assert "your-project.supabase.co" not in risk.variable_name
            assert "your-supabase-anon-key-here" not in risk.variable_name

    def test_key_risks_have_required_fields(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        valid_types = {"publishable", "secret", "url", "project_id", "unknown"}
        valid_sev = {"INFO", "WARNING", "ERROR", "CRITICAL"}
        for risk in result.key_risks:
            assert risk.variable_name
            assert risk.key_type in valid_types
            assert risk.severity in valid_sev


# ---------------------------------------------------------------------------
# TestRLSEvidence
# ---------------------------------------------------------------------------


class TestRLSEvidence:
    def test_migrations_present_in_fixture(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.rls_evidence.migrations_present is True

    def test_rls_enable_found_in_fixture(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.rls_evidence.rls_enable_found is True

    def test_policies_found_in_fixture(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.rls_evidence.policies_found is True

    def test_evidence_contains_file_reference(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert "001_init.sql" in result.rls_evidence.evidence

    def test_evidence_no_sql_content(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        evidence = result.rls_evidence.evidence
        assert "CREATE TABLE" not in evidence
        assert "gen_random_uuid" not in evidence
        assert "auth.uid()" not in evidence


# ---------------------------------------------------------------------------
# TestLocalFixes
# ---------------------------------------------------------------------------


class TestLocalFixes:
    def test_local_fixes_present(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.local_fixes is not None

    def test_env_example_detected(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.local_fixes.env_example_exists is True

    def test_gitignore_does_not_protect_env_in_fixture(self, ext_project: Path) -> None:
        # The fixture intentionally lacks .env protection to simulate a realistic
        # unpatched project — this triggers the remediation recommendation.
        result = run_supabase_check(ext_project)
        assert result.local_fixes.gitignore_protects_env is False


# ---------------------------------------------------------------------------
# TestRemediationSteps
# ---------------------------------------------------------------------------


class TestRemediationSteps:
    def test_remediation_steps_present(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert len(result.remediation_steps) > 0

    def test_priorities_are_sequential(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        priorities = [s.priority for s in result.remediation_steps]
        assert priorities == sorted(priorities)
        assert priorities[0] == 1

    def test_steps_have_valid_status(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        valid = {"done", "required", "manual"}
        for step in result.remediation_steps:
            assert step.status in valid

    def test_manual_action_required(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        assert result.requires_manual_action is True

    def test_rls_step_always_present(self, ext_project: Path) -> None:
        result = run_supabase_check(ext_project)
        actions = [s.action for s in result.remediation_steps]
        assert any("RLS" in a or "Row Level Security" in a for a in actions)


# ---------------------------------------------------------------------------
# TestCLI
# ---------------------------------------------------------------------------


class TestCLIOnExternalProject:
    def test_cli_text_contains_key_sections(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["supabase", "check", "--path", str(ext_project)])
        assert "Supabase Check" in r.output
        assert "Supabase detected: yes" in r.output
        assert "RLS Evidence" in r.output
        assert "Local Fixes" in r.output
        assert "Remediation Steps" in r.output

    def test_cli_json_is_valid(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["supabase", "check", "--path", str(ext_project), "--json"]
        )
        data = json.loads(r.output)
        assert data["supabase_detected"] is True
        assert "key_risks" in data
        assert "rls_evidence" in data
        assert "local_fixes" in data
        assert "remediation_steps" in data

    def test_cli_json_rls_evidence(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["supabase", "check", "--path", str(ext_project), "--json"]
        )
        data = json.loads(r.output)
        rls = data["rls_evidence"]
        assert rls["migrations_present"] is True
        assert rls["rls_enable_found"] is True
        assert rls["policies_found"] is True

    def test_cli_json_no_sensitive_values(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["supabase", "check", "--path", str(ext_project), "--json"]
        )
        assert "your-project.supabase.co" not in r.output
        assert "your-supabase-anon-key-here" not in r.output
        assert "your-clerk-publishable-key-here" not in r.output


# ---------------------------------------------------------------------------
# TestReadOnlyGuarantee
# ---------------------------------------------------------------------------


class TestReadOnlyGuarantee:
    def test_python_api_does_not_modify_project(self, ext_project: Path) -> None:
        before = _fingerprint(ext_project)
        run_supabase_check(ext_project)
        after = _fingerprint(ext_project)
        assert before == after, "run_supabase_check modified the target project"

    def test_cli_does_not_modify_project(self, ext_project: Path) -> None:
        before = _fingerprint(ext_project)
        runner.invoke(app, ["supabase", "check", "--path", str(ext_project)])
        runner.invoke(app, ["supabase", "check", "--path", str(ext_project), "--json"])
        after = _fingerprint(ext_project)
        assert before == after, "CLI supabase check modified the target project"

    def test_no_new_files_created(self, ext_project: Path) -> None:
        before = set(_fingerprint(ext_project).keys())
        run_supabase_check(ext_project)
        after = set(_fingerprint(ext_project).keys())
        assert before == after, f"New files created: {after - before}"
