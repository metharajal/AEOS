"""
Unit tests for the Supabase remediation advisor (Sprint 2R).
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.providers.supabase import run_supabase_check
from aeos.providers.supabase.checker import (
    SupabaseCheckResult,
    SupabaseLocalFixes,
    SupabaseRLSEvidence,
    _check_local_fixes,
    _classify_key,
    _compute_key_severity,
    _compute_status,
    _detect_supabase,
    _extract_var_names,
    _scan_rls_evidence,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# TestDataModel
# ---------------------------------------------------------------------------


class TestDataModel:
    def test_result_defaults(self, tmp_path: Path) -> None:
        r = SupabaseCheckResult(path=tmp_path, status="OK", supabase_detected=False)
        assert r.key_risks == []
        assert r.remediation_steps == []
        assert r.requires_manual_action is False

    def test_rls_evidence_fields(self) -> None:
        e = SupabaseRLSEvidence(
            migrations_present=True,
            rls_enable_found=True,
            policies_found=False,
            evidence="RLS: first match migrations/001.sql:8",
        )
        assert e.migrations_present is True
        assert e.rls_enable_found is True
        assert e.policies_found is False
        assert "001.sql" in e.evidence

    def test_local_fixes_fields(self) -> None:
        lf = SupabaseLocalFixes(
            gitignore_protects_env=True,
            env_not_tracked=True,
            env_example_exists=False,
        )
        assert lf.gitignore_protects_env is True
        assert lf.env_example_exists is False


# ---------------------------------------------------------------------------
# TestKeyClassification
# ---------------------------------------------------------------------------


class TestKeyClassification:
    def test_publishable_variants(self) -> None:
        assert _classify_key("VITE_SUPABASE_PUBLISHABLE_KEY") == "publishable"
        assert _classify_key("NEXT_PUBLIC_SUPABASE_ANON_KEY") == "publishable"
        assert _classify_key("SUPABASE_ANON_KEY") == "publishable"

    def test_secret_variants(self) -> None:
        assert _classify_key("SUPABASE_SERVICE_ROLE_KEY") == "secret"
        assert _classify_key("SUPABASE_SECRET_KEY") == "secret"

    def test_url_variants(self) -> None:
        assert _classify_key("VITE_SUPABASE_URL") == "url"
        assert _classify_key("NEXT_PUBLIC_SUPABASE_URL") == "url"
        assert _classify_key("SUPABASE_URL") == "url"

    def test_project_id(self) -> None:
        assert _classify_key("VITE_SUPABASE_PROJECT_ID") == "project_id"
        assert _classify_key("SUPABASE_PROJECT_ID") == "project_id"

    def test_modern_publishable_pattern(self) -> None:
        assert _classify_key("sb_publishable_abc123") == "publishable"

    def test_modern_secret_pattern(self) -> None:
        assert _classify_key("sb_secret_xyz789") == "secret"

    def test_unknown_supabase_var(self) -> None:
        assert _classify_key("SUPABASE_CUSTOM_VAR") == "unknown"


class TestKeySeverity:
    def test_secret_in_history_is_critical(self) -> None:
        assert _compute_key_severity("secret", True, False) == "CRITICAL"

    def test_secret_in_tracking_is_critical(self) -> None:
        assert _compute_key_severity("secret", False, True) == "CRITICAL"

    def test_secret_not_exposed_is_error(self) -> None:
        assert _compute_key_severity("secret", False, False) == "ERROR"

    def test_publishable_in_history_is_error(self) -> None:
        assert _compute_key_severity("publishable", True, False) == "ERROR"

    def test_publishable_in_tracking_is_error(self) -> None:
        assert _compute_key_severity("publishable", False, True) == "ERROR"

    def test_publishable_not_exposed_is_warning(self) -> None:
        assert _compute_key_severity("publishable", False, False) == "WARNING"

    def test_url_not_exposed_is_info(self) -> None:
        assert _compute_key_severity("url", False, False) == "INFO"

    def test_url_in_history_is_warning(self) -> None:
        assert _compute_key_severity("url", True, False) == "WARNING"


# ---------------------------------------------------------------------------
# TestDetectSupabase
# ---------------------------------------------------------------------------


class TestDetectSupabase:
    def test_no_supabase_empty_project(self, tmp_path: Path) -> None:
        assert _detect_supabase(tmp_path) is False

    def test_detected_via_package_json_dep(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        assert _detect_supabase(tmp_path) is True

    def test_detected_via_supabase_ssr(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/ssr": "^0.1.0"}})
        )
        assert _detect_supabase(tmp_path) is True

    def test_detected_via_config_toml(self, tmp_path: Path) -> None:
        supabase_dir = tmp_path / "supabase"
        supabase_dir.mkdir()
        (supabase_dir / "config.toml").write_text("[api]\nport = 54321\n")
        assert _detect_supabase(tmp_path) is True

    def test_detected_via_migrations_dir(self, tmp_path: Path) -> None:
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        assert _detect_supabase(tmp_path) is True

    def test_detected_via_source_import(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "client.ts").write_text(
            "import { createClient } from '@supabase/supabase-js'\n"
        )
        assert _detect_supabase(tmp_path) is True

    def test_not_detected_unrelated_package(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "^18.0.0"}})
        )
        assert _detect_supabase(tmp_path) is False


# ---------------------------------------------------------------------------
# TestExtractVarNames
# ---------------------------------------------------------------------------


class TestExtractVarNames:
    def test_extracts_names_only(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("VITE_SUPABASE_URL=https://secret-url.supabase.co\n")
        names = _extract_var_names(env)
        assert names == ["VITE_SUPABASE_URL"]
        assert "https://secret-url.supabase.co" not in names

    def test_skips_comments(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("# Comment\nVITE_KEY=value\n")
        names = _extract_var_names(env)
        assert names == ["VITE_KEY"]

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert _extract_var_names(tmp_path / ".env") == []

    def test_large_file_skipped(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_bytes(b"X=y\n" * 30000)  # > 100KB
        assert _extract_var_names(env) == []

    def test_no_values_leak(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiJ9.secret_part_here\n")
        names = _extract_var_names(env)
        assert all("eyJ" not in n for n in names)
        assert all("secret_part" not in n for n in names)


# ---------------------------------------------------------------------------
# TestRLSEvidence
# ---------------------------------------------------------------------------


class TestRLSEvidence:
    def test_no_migrations_dir(self, tmp_path: Path) -> None:
        ev = _scan_rls_evidence(tmp_path)
        assert ev.migrations_present is False
        assert ev.rls_enable_found is False
        assert ev.policies_found is False
        assert ev.evidence == ""

    def test_empty_migrations_dir(self, tmp_path: Path) -> None:
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        ev = _scan_rls_evidence(tmp_path)
        assert ev.migrations_present is True
        assert ev.rls_enable_found is False
        assert ev.policies_found is False

    def test_rls_found(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;\n"
        )
        ev = _scan_rls_evidence(tmp_path)
        assert ev.rls_enable_found is True
        assert "001.sql" in ev.evidence

    def test_policy_found(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            'CREATE POLICY "read_own" ON profiles FOR SELECT USING (true);\n'
        )
        ev = _scan_rls_evidence(tmp_path)
        assert ev.policies_found is True

    def test_evidence_never_contains_sql_content(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "ALTER TABLE secret_table ENABLE ROW LEVEL SECURITY;\n"
        )
        ev = _scan_rls_evidence(tmp_path)
        assert "secret_table" not in ev.evidence
        assert "ALTER" not in ev.evidence


# ---------------------------------------------------------------------------
# TestLocalFixes
# ---------------------------------------------------------------------------


class TestLocalFixes:
    def test_gitignore_missing(self, tmp_path: Path) -> None:
        lf = _check_local_fixes(tmp_path, env_not_tracked=True)
        assert lf.gitignore_protects_env is False

    def test_gitignore_with_env(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text(".env\n")
        lf = _check_local_fixes(tmp_path, env_not_tracked=True)
        assert lf.gitignore_protects_env is True

    def test_gitignore_with_env_star(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text(".env.*\n")
        lf = _check_local_fixes(tmp_path, env_not_tracked=True)
        assert lf.gitignore_protects_env is True

    def test_env_not_tracked_passed_through(self, tmp_path: Path) -> None:
        lf = _check_local_fixes(tmp_path, env_not_tracked=False)
        assert lf.env_not_tracked is False

    def test_env_example_detected(self, tmp_path: Path) -> None:
        (tmp_path / ".env.example").write_text("SUPABASE_URL=placeholder\n")
        lf = _check_local_fixes(tmp_path, env_not_tracked=True)
        assert lf.env_example_exists is True

    def test_env_example_missing(self, tmp_path: Path) -> None:
        lf = _check_local_fixes(tmp_path, env_not_tracked=True)
        assert lf.env_example_exists is False


# ---------------------------------------------------------------------------
# TestStatusComputation
# ---------------------------------------------------------------------------


class TestStatusComputation:
    def test_no_supabase_is_ok(self) -> None:
        assert _compute_status(False, []) == "OK"

    def test_supabase_no_risks_is_warning(self) -> None:
        assert _compute_status(True, []) == "WARNING"

    def test_critical_severity_gives_critical(self) -> None:
        from aeos.providers.supabase.checker import SupabaseKeyRisk

        risks = [
            SupabaseKeyRisk(
                "SUPABASE_SERVICE_ROLE_KEY", "secret", "CRITICAL", True, False
            )
        ]
        assert _compute_status(True, risks) == "CRITICAL"

    def test_error_severity_gives_error(self) -> None:
        from aeos.providers.supabase.checker import SupabaseKeyRisk

        risks = [
            SupabaseKeyRisk("SUPABASE_ANON_KEY", "publishable", "ERROR", True, False)
        ]
        assert _compute_status(True, risks) == "ERROR"

    def test_warning_only_gives_warning(self) -> None:
        from aeos.providers.supabase.checker import SupabaseKeyRisk

        risks = [SupabaseKeyRisk("VITE_SUPABASE_URL", "url", "INFO", False, False)]
        assert _compute_status(True, risks) == "WARNING"


# ---------------------------------------------------------------------------
# TestRunSupabaseCheck
# ---------------------------------------------------------------------------


class TestRunSupabaseCheck:
    def test_clean_project_no_supabase_is_ok(self, tmp_path: Path) -> None:
        result = run_supabase_check(tmp_path)
        assert result.status == "OK"
        assert result.supabase_detected is False

    def test_path_is_absolute(self, tmp_path: Path) -> None:
        result = run_supabase_check(tmp_path)
        assert result.path.is_absolute()

    def test_supabase_project_is_warning_minimum(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        result = run_supabase_check(tmp_path)
        assert result.supabase_detected is True
        assert result.status in ("WARNING", "ERROR", "CRITICAL")

    def test_no_sensitive_values_in_key_risks(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        (tmp_path / ".env.example").write_text(
            "SUPABASE_URL=your-project-url\nSUPABASE_ANON_KEY=your-anon-key\n"
        )
        result = run_supabase_check(tmp_path)
        for risk in result.key_risks:
            assert "your-project-url" not in risk.variable_name
            assert "your-anon-key" not in risk.variable_name

    def test_remediation_steps_present_when_supabase(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        result = run_supabase_check(tmp_path)
        assert len(result.remediation_steps) > 0

    def test_read_only_no_files_created(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        before = {str(p) for p in tmp_path.rglob("*") if p.is_file()}
        run_supabase_check(tmp_path)
        after = {str(p) for p in tmp_path.rglob("*") if p.is_file()}
        assert before == after


# ---------------------------------------------------------------------------
# TestCliSupabaseCheck
# ---------------------------------------------------------------------------


class TestCliSupabaseCheck:
    def test_no_supabase_exits_0(self, tmp_path: Path) -> None:
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path)])
        assert r.exit_code == 0
        assert "not detected" in r.output

    def test_supabase_project_text_output(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path)])
        assert "Supabase Check" in r.output
        assert "Supabase detected: yes" in r.output
        assert "RLS Evidence" in r.output
        assert "Local Fixes" in r.output
        assert "Remediation Steps" in r.output

    def test_json_output_valid(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        data = json.loads(r.output)
        assert "status" in data
        assert "supabase_detected" in data
        assert "key_risks" in data
        assert "rls_evidence" in data
        assert "local_fixes" in data
        assert "remediation_steps" in data
        assert "requires_manual_action" in data

    def test_json_no_supabase_structure(self, tmp_path: Path) -> None:
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        data = json.loads(r.output)
        assert data["status"] == "OK"
        assert data["supabase_detected"] is False
        assert data["key_risks"] == []

    def test_nonexistent_path_exits_1(self) -> None:
        r = runner.invoke(app, ["supabase", "check", "--path", "/nonexistent/xyz"])
        assert r.exit_code == 1
        assert "does not exist" in r.output

    def test_json_no_sensitive_values(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        (tmp_path / ".env.example").write_text(
            "SUPABASE_URL=your-placeholder-url\nSUPABASE_ANON_KEY=your-anon-key\n"
        )
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        output = r.output
        assert "your-placeholder-url" not in output
        assert "your-anon-key" not in output

    def test_with_rls_migrations(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;\n"
            'CREATE POLICY "p" ON profiles FOR SELECT USING (true);\n'
        )
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        data = json.loads(r.output)
        assert data["rls_evidence"]["rls_enable_found"] is True
        assert data["rls_evidence"]["policies_found"] is True

    def test_read_only_via_cli(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        before = {str(p) for p in tmp_path.rglob("*") if p.is_file()}
        runner.invoke(app, ["supabase", "check", "--path", str(tmp_path)])
        after = {str(p) for p in tmp_path.rglob("*") if p.is_file()}
        assert before == after

    def test_gitignore_fix_reflected_in_local_fixes(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        (tmp_path / ".gitignore").write_text(".env\n.env.*\n")
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        data = json.loads(r.output)
        assert data["local_fixes"]["gitignore_protects_env"] is True

    def test_env_example_reflected_in_local_fixes(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        (tmp_path / ".env.example").write_text("SUPABASE_URL=placeholder\n")
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        data = json.loads(r.output)
        assert data["local_fixes"]["env_example_exists"] is True

    def test_remediation_steps_ordered(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        data = json.loads(r.output)
        priorities = [s["priority"] for s in data["remediation_steps"]]
        assert priorities == sorted(priorities)


# ---------------------------------------------------------------------------
# TestAntiLeakage (global)
# ---------------------------------------------------------------------------


class TestAntiLeakage:
    def test_no_secret_value_in_any_result_field(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        (tmp_path / ".env").write_text(
            "SUPABASE_URL=https://top-secret.supabase.co\n"
            "SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiJ9.supersecret\n"
        )
        (tmp_path / ".env.example").write_text(
            "SUPABASE_URL=placeholder\nSUPABASE_ANON_KEY=placeholder\n"
        )
        result = run_supabase_check(tmp_path)
        result_str = str(result)
        assert "top-secret.supabase.co" not in result_str
        assert "supersecret" not in result_str
        assert "eyJhbGciOiJIUzI1NiJ9" not in result_str

    def test_cli_json_no_secret_values(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        (tmp_path / ".env").write_text(
            "SUPABASE_ANON_KEY=should_never_appear_in_output\n"
        )
        r = runner.invoke(app, ["supabase", "check", "--path", str(tmp_path), "--json"])
        assert "should_never_appear_in_output" not in r.output
