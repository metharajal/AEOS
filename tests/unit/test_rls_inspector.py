"""
Unit tests for the Supabase RLS Inspector (Sprint 2T).
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.providers.supabase.rls import run_rls_inspect
from aeos.providers.supabase.rls.inspector import (
    RLSFinding,
    RLSPolicy,
    RLSTableInfo,
    _analyze_table,
    _compute_status,
    _expr_is_too_permissive,
    _expr_lacks_tenant_scope,
    _expr_uses_auth_role_authenticated,
    _is_moderatable_table,
    _is_sensitive_table,
    _normalize_name,
    _parse_policy_rest,
    _scan_migrations,
    _strip_comments,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# TestHelpers
# ---------------------------------------------------------------------------


class TestStripComments:
    def test_removes_line_comments(self) -> None:
        sql = "SELECT 1; -- this is a comment\nSELECT 2;"
        result = _strip_comments(sql)
        assert "this is a comment" not in result
        assert "SELECT 2" in result

    def test_removes_block_comments(self) -> None:
        sql = "SELECT /* block comment */ 1;"
        result = _strip_comments(sql)
        assert "block comment" not in result
        assert "SELECT" in result
        assert "1" in result

    def test_no_comment_unchanged(self) -> None:
        sql = "ALTER TABLE foo ENABLE ROW LEVEL SECURITY;"
        assert _strip_comments(sql) == sql


class TestNormalizeName:
    def test_double_quoted(self) -> None:
        assert _normalize_name('"My Policy"') == "My Policy"

    def test_single_quoted(self) -> None:
        assert _normalize_name("'My Policy'") == "My Policy"

    def test_unquoted(self) -> None:
        assert _normalize_name("policy_name") == "policy_name"

    def test_strips_whitespace(self) -> None:
        assert _normalize_name('  "name"  ') == "name"


class TestParsePolicyRest:
    def test_parse_select_using(self) -> None:
        rest = " FOR SELECT USING (auth.uid() = user_id);"
        cmd, using, check = _parse_policy_rest(rest)
        assert cmd == "SELECT"
        assert "auth.uid()" in using
        assert check == ""

    def test_parse_insert_with_check(self) -> None:
        rest = " FOR INSERT WITH CHECK (auth.uid() = user_id);"
        cmd, using, check = _parse_policy_rest(rest)
        assert cmd == "INSERT"
        assert using == ""
        assert "auth.uid()" in check

    def test_parse_update_both_clauses(self) -> None:
        rest = (
            " FOR UPDATE USING (auth.uid() = user_id)"
            " WITH CHECK (auth.uid() = user_id);"
        )
        cmd, using, check = _parse_policy_rest(rest)
        assert cmd == "UPDATE"
        assert "auth.uid()" in using
        assert "auth.uid()" in check

    def test_parse_all_no_for_clause(self) -> None:
        rest = " USING (true);"
        cmd, using, _check = _parse_policy_rest(rest)
        assert cmd == "ALL"
        assert using == "true"

    def test_parse_delete_using(self) -> None:
        rest = " FOR DELETE USING (auth.uid() = user_id);"
        cmd, using, _check = _parse_policy_rest(rest)
        assert cmd == "DELETE"
        assert "auth.uid()" in using


class TestExprChecks:
    def test_true_is_too_permissive(self) -> None:
        assert _expr_is_too_permissive("true") is True

    def test_true_with_spaces(self) -> None:
        assert _expr_is_too_permissive("  true  ") is True

    def test_TRUE_uppercase(self) -> None:
        assert _expr_is_too_permissive("TRUE") is True

    def test_uid_not_null_is_too_permissive(self) -> None:
        assert _expr_is_too_permissive("auth.uid() IS NOT NULL") is True

    def test_uid_equals_user_id_is_not_permissive(self) -> None:
        assert _expr_is_too_permissive("auth.uid() = user_id") is False

    def test_auth_role_authenticated(self) -> None:
        assert (
            _expr_uses_auth_role_authenticated("auth.role() = 'authenticated'") is True
        )

    def test_auth_role_double_quoted(self) -> None:
        assert (
            _expr_uses_auth_role_authenticated('auth.role() = "authenticated"') is True
        )

    def test_auth_role_not_authenticated(self) -> None:
        assert _expr_uses_auth_role_authenticated("auth.uid() = user_id") is False

    def test_lacks_tenant_scope_plain(self) -> None:
        assert _expr_lacks_tenant_scope("auth.uid() = user_id") is True

    def test_has_commune_id_scope(self) -> None:
        assert (
            _expr_lacks_tenant_scope("commune_id = get_user_commune_id(auth.uid())")
            is False
        )

    def test_has_org_id_scope(self) -> None:
        assert _expr_lacks_tenant_scope("org_id = auth.uid()") is False

    def test_has_tenant_id_scope(self) -> None:
        assert _expr_lacks_tenant_scope("tenant_id IS NOT NULL") is False


class TestTableClassification:
    def test_personnel_is_sensitive(self) -> None:
        assert _is_sensitive_table("personnel") is True

    def test_profiles_is_sensitive(self) -> None:
        assert _is_sensitive_table("profiles") is True

    def test_notifications_is_sensitive(self) -> None:
        assert _is_sensitive_table("notifications") is True

    def test_budget_is_sensitive(self) -> None:
        assert _is_sensitive_table("budget_projets") is True

    def test_ordinary_table_not_sensitive(self) -> None:
        assert _is_sensitive_table("evenements") is False

    def test_forum_posts_is_moderatable(self) -> None:
        assert _is_moderatable_table("forum_posts") is True

    def test_comments_is_moderatable(self) -> None:
        assert _is_moderatable_table("comments") is True

    def test_profiles_not_moderatable(self) -> None:
        assert _is_moderatable_table("profiles") is False


# ---------------------------------------------------------------------------
# TestScanMigrations
# ---------------------------------------------------------------------------


class TestScanMigrations:
    def _make_migrations(self, tmp_path: Path, sql: str) -> Path:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(sql)
        return tmp_path

    def test_detect_create_table(self, tmp_path: Path) -> None:
        p = self._make_migrations(
            tmp_path, "CREATE TABLE IF NOT EXISTS public.orders (id uuid PRIMARY KEY);"
        )
        mig = p / "supabase" / "migrations"
        tables, _, _ = _scan_migrations(mig, p)
        assert "orders" in tables

    def test_detect_rls_enable(self, tmp_path: Path) -> None:
        p = self._make_migrations(
            tmp_path, "ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;"
        )
        mig = p / "supabase" / "migrations"
        tables, _, _ = _scan_migrations(mig, p)
        assert tables["orders"].rls_enabled is True

    def test_detect_rls_force(self, tmp_path: Path) -> None:
        p = self._make_migrations(
            tmp_path, "ALTER TABLE public.orders FORCE ROW LEVEL SECURITY;"
        )
        mig = p / "supabase" / "migrations"
        tables, _, _ = _scan_migrations(mig, p)
        assert tables["orders"].rls_forced is True

    def test_parse_select_policy(self, tmp_path: Path) -> None:
        sql = (
            'CREATE POLICY "select_own" ON public.orders FOR SELECT'
            " USING (auth.uid() = user_id);"
        )
        p = self._make_migrations(tmp_path, sql)
        mig = p / "supabase" / "migrations"
        _, policies, _ = _scan_migrations(mig, p)
        assert len(policies) == 1
        assert policies[0].command == "SELECT"
        assert "auth.uid()" in policies[0].using_expr
        assert policies[0].with_check_expr == ""

    def test_parse_insert_with_check(self, tmp_path: Path) -> None:
        sql = (
            'CREATE POLICY "insert_own" ON public.orders FOR INSERT'
            " WITH CHECK (auth.uid() = user_id);"
        )
        p = self._make_migrations(tmp_path, sql)
        mig = p / "supabase" / "migrations"
        _, policies, _ = _scan_migrations(mig, p)
        assert policies[0].command == "INSERT"
        assert "auth.uid()" in policies[0].with_check_expr

    def test_drop_policy_removes_from_list(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            'CREATE POLICY "old_policy" ON public.orders FOR SELECT USING (true);'
        )
        (mig / "002.sql").write_text(
            'DROP POLICY IF EXISTS "old_policy" ON public.orders;\n'
            'CREATE POLICY "new_policy" ON public.orders'
            " FOR SELECT USING (auth.uid() = user_id);"
        )
        _tables, policies, _ = _scan_migrations(mig, tmp_path)
        names = [p.name for p in policies]
        assert "old_policy" not in names
        assert "new_policy" in names

    def test_files_scanned_count(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text("SELECT 1;")
        (mig / "002.sql").write_text("SELECT 2;")
        _, _, count = _scan_migrations(mig, tmp_path)
        assert count == 2

    def test_no_secrets_in_policy_attributes(self, tmp_path: Path) -> None:
        sql = (
            'CREATE POLICY "p" ON public.orders FOR SELECT'
            " USING (auth.uid() = user_id);"
        )
        p = self._make_migrations(tmp_path, sql)
        mig = p / "supabase" / "migrations"
        _tables, policies, _ = _scan_migrations(mig, p)
        for policy in policies:
            assert policy.source_file != ""
            assert policy.source_line > 0

    def test_schema_prefix_stripped(self, tmp_path: Path) -> None:
        sql = 'CREATE POLICY "p" ON public.orders FOR SELECT USING (true);'
        p = self._make_migrations(tmp_path, sql)
        mig = p / "supabase" / "migrations"
        _, policies, _ = _scan_migrations(mig, p)
        assert policies[0].table == "orders"


# ---------------------------------------------------------------------------
# TestAnalyzeTable
# ---------------------------------------------------------------------------


class TestAnalyzeTable:
    def _make_policy(self, **kwargs: object) -> RLSPolicy:
        defaults: dict[str, object] = {
            "name": "test_policy",
            "table": "test_table",
            "command": "SELECT",
            "using_expr": "auth.uid() = user_id",
            "with_check_expr": "",
            "source_file": "migrations/001.sql",
            "source_line": 1,
        }
        defaults.update(kwargs)
        return RLSPolicy(**defaults)  # type: ignore[arg-type]

    def test_no_rls_gives_error(self) -> None:
        info = RLSTableInfo(name="orders", rls_enabled=False)
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert any(f.rule == "NO_RLS" for f in findings)
        assert any(f.severity == "ERROR" for f in findings)

    def test_rls_no_policies_gives_error(self) -> None:
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert any(f.rule == "NO_POLICIES" for f in findings)

    def test_insert_without_with_check_flagged(self) -> None:
        policy = self._make_policy(command="INSERT", using_expr="", with_check_expr="")
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert any(f.rule == "INSERT_NO_WITH_CHECK" for f in findings)

    def test_insert_with_check_ok(self) -> None:
        policy = self._make_policy(
            command="INSERT",
            using_expr="",
            with_check_expr="auth.uid() = user_id",
        )
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert not any(f.rule == "INSERT_NO_WITH_CHECK" for f in findings)

    def test_update_without_with_check_flagged(self) -> None:
        policy = self._make_policy(
            command="UPDATE", using_expr="auth.uid() = user_id", with_check_expr=""
        )
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert any(f.rule == "UPDATE_NO_WITH_CHECK" for f in findings)

    def test_update_with_check_ok(self) -> None:
        policy = self._make_policy(
            command="UPDATE",
            using_expr="auth.uid() = user_id",
            with_check_expr="auth.uid() = user_id",
        )
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert not any(f.rule == "UPDATE_NO_WITH_CHECK" for f in findings)

    def test_auth_role_authenticated_flagged(self) -> None:
        policy = self._make_policy(
            command="INSERT",
            using_expr="",
            with_check_expr="auth.role() = 'authenticated'",
        )
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert any(f.rule == "AUTH_ROLE_AUTHENTICATED" for f in findings)

    def test_select_true_flagged_as_warning_on_normal_table(self) -> None:
        policy = self._make_policy(command="SELECT", using_expr="true")
        info = RLSTableInfo(name="evenements", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        matching = [f for f in findings if f.rule == "SELECT_TOO_PERMISSIVE"]
        assert len(matching) == 1
        assert matching[0].severity == "WARNING"

    def test_select_true_flagged_as_error_on_sensitive_table(self) -> None:
        policy = self._make_policy(
            command="SELECT", using_expr="true", table="personnel"
        )
        info = RLSTableInfo(name="personnel", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        matching = [f for f in findings if f.rule == "SELECT_TOO_PERMISSIVE"]
        assert len(matching) == 1
        assert matching[0].severity == "ERROR"

    def test_missing_tenant_scope_on_insert_flagged(self) -> None:
        policy = self._make_policy(
            command="INSERT",
            using_expr="",
            with_check_expr="auth.uid() = user_id",
        )
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=True)
        assert any(f.rule == "MISSING_TENANT_SCOPE" for f in findings)

    def test_tenant_scope_present_no_flag(self) -> None:
        policy = self._make_policy(
            command="INSERT",
            using_expr="",
            with_check_expr=(
                "auth.uid() = user_id AND commune_id = get_user_commune_id(auth.uid())"
            ),
        )
        info = RLSTableInfo(name="orders", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=True)
        assert not any(f.rule == "MISSING_TENANT_SCOPE" for f in findings)

    def test_no_delete_policy_on_moderatable(self) -> None:
        select = self._make_policy(
            command="SELECT", using_expr="true", table="forum_posts"
        )
        insert = self._make_policy(
            command="INSERT",
            using_expr="",
            with_check_expr="auth.uid() = user_id",
            table="forum_posts",
        )
        info = RLSTableInfo(
            name="forum_posts", rls_enabled=True, policies=[select, insert]
        )
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert any(f.rule == "NO_DELETE_POLICY" for f in findings)

    def test_delete_policy_present_no_flag(self) -> None:
        delete = self._make_policy(
            command="DELETE", using_expr="auth.uid() = user_id", table="forum_posts"
        )
        info = RLSTableInfo(name="forum_posts", rls_enabled=True, policies=[delete])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert not any(f.rule == "NO_DELETE_POLICY" for f in findings)

    def test_all_command_covers_delete_moderatable(self) -> None:
        policy = self._make_policy(
            command="ALL",
            using_expr="public.has_role(auth.uid(), 'admin')",
            with_check_expr="",
            table="forum_posts",
        )
        info = RLSTableInfo(name="forum_posts", rls_enabled=True, policies=[policy])
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert not any(f.rule == "NO_DELETE_POLICY" for f in findings)

    def test_clean_table_no_findings(self) -> None:
        select = self._make_policy(command="SELECT", using_expr="auth.uid() = user_id")
        insert = self._make_policy(
            command="INSERT",
            using_expr="",
            with_check_expr="auth.uid() = user_id",
        )
        update = self._make_policy(
            command="UPDATE",
            using_expr="auth.uid() = user_id",
            with_check_expr="auth.uid() = user_id",
        )
        info = RLSTableInfo(
            name="orders", rls_enabled=True, policies=[select, insert, update]
        )
        findings = _analyze_table(info, project_has_tenant_columns=False)
        assert findings == []


# ---------------------------------------------------------------------------
# TestComputeStatus
# ---------------------------------------------------------------------------


class TestComputeStatus:
    def test_no_findings_is_ok(self) -> None:
        assert _compute_status([]) == "OK"

    def test_warning_only_is_warning(self) -> None:
        f = RLSFinding("WARNING", "t", "R", "m", "r")
        assert _compute_status([f]) == "WARNING"

    def test_error_gives_error(self) -> None:
        f = RLSFinding("ERROR", "t", "R", "m", "r")
        assert _compute_status([f]) == "ERROR"

    def test_mixed_gives_error(self) -> None:
        findings = [
            RLSFinding("WARNING", "t1", "R", "m", "r"),
            RLSFinding("ERROR", "t2", "R", "m", "r"),
        ]
        assert _compute_status(findings) == "ERROR"


# ---------------------------------------------------------------------------
# TestRunRLSInspect (full integration via fixture)
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "supabase_rls"


class TestRunRLSInspect:
    def test_returns_result(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result is not None

    def test_path_is_absolute(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result.path.is_absolute()

    def test_migrations_scanned(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result.migrations_scanned == 3

    def test_tables_detected(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        table_names = {t.name for t in result.tables}
        assert "profiles" in table_names
        assert "personnel" in table_names
        assert "forum_posts" in table_names
        assert "budget_projets" in table_names
        assert "notifications" in table_names

    def test_rls_enabled_tables(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        rls_tables = {t.name for t in result.tables if t.rls_enabled}
        assert "profiles" in rls_tables
        assert "personnel" in rls_tables
        assert "forum_posts" in rls_tables

    def test_no_rls_tables_detected(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        no_rls = {t.name for t in result.tables if not t.rls_enabled}
        assert "table_no_rls" in no_rls

    def test_policies_detected(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert len(result.policies) > 0

    def test_findings_present(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert len(result.findings) > 0

    def test_no_rls_finding_present(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert any(f.rule == "NO_RLS" for f in result.findings)

    def test_no_policies_finding_present(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert any(f.rule == "NO_POLICIES" for f in result.findings)

    def test_auth_role_finding_present(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert any(f.rule == "AUTH_ROLE_AUTHENTICATED" for f in result.findings)

    def test_no_delete_policy_finding(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert any(f.rule == "NO_DELETE_POLICY" for f in result.findings)

    def test_missing_tenant_scope_finding(self) -> None:
        # budget_projets UPDATE without commune_id scope
        result = run_rls_inspect(FIXTURE_DIR)
        assert any(f.rule == "MISSING_TENANT_SCOPE" for f in result.findings)

    def test_select_permissive_finding_on_personnel(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        personnel_findings = [
            f
            for f in result.findings
            if f.table == "personnel" and f.rule == "SELECT_TOO_PERMISSIVE"
        ]
        assert len(personnel_findings) >= 1

    def test_status_is_error_or_warning(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result.status in ("ERROR", "WARNING")

    def test_recommendations_not_empty(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert len(result.recommendations) > 0

    def test_drop_policy_removes_old(self) -> None:
        # migration 003 drops notifications_insert_auth, replaces with _self
        result = run_rls_inspect(FIXTURE_DIR)
        notif_policies = [p for p in result.policies if p.table == "notifications"]
        names = [p.name for p in notif_policies]
        assert "notifications_insert_auth" not in names
        assert "notifications_insert_self" in names

    def test_no_migration_dir_returns_ok(self, tmp_path: Path) -> None:
        result = run_rls_inspect(tmp_path)
        assert result.status == "OK"
        assert result.migrations_scanned == 0

    def test_read_only_no_files_modified(self) -> None:
        before = {
            str(p): p.stat().st_size for p in FIXTURE_DIR.rglob("*") if p.is_file()
        }
        run_rls_inspect(FIXTURE_DIR)
        after = {
            str(p): p.stat().st_size for p in FIXTURE_DIR.rglob("*") if p.is_file()
        }
        assert before == after

    def test_findings_sorted_errors_first(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        severities = [f.severity for f in result.findings]
        _order = {"ERROR": 0, "WARNING": 1, "OK": 2}
        assert severities == sorted(severities, key=lambda s: _order.get(s, 9))

    def test_no_dot_env_read(self, tmp_path: Path) -> None:
        # Place a .env alongside the migrations dir — inspector must not read it
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;"
        )
        env_file = tmp_path / ".env"
        env_file.write_text("SUPABASE_SERVICE_ROLE_KEY=do_not_read_me\n")
        result = run_rls_inspect(tmp_path)
        # No finding about secrets — confirms .env was not processed
        result_str = str(result)
        assert "do_not_read_me" not in result_str

    def test_rls_forced_detected(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        forced = [t for t in result.tables if t.rls_forced]
        assert any(t.name == "personnel" for t in forced)


# ---------------------------------------------------------------------------
# TestCLISupabaseRLSInspect
# ---------------------------------------------------------------------------


class TestCLISupabaseRLSInspect:
    def test_text_output_contains_header(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)]
        )
        assert "Supabase RLS Inspect" in r.output

    def test_text_output_contains_status(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)]
        )
        assert "Status:" in r.output

    def test_text_output_contains_tables_section(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)]
        )
        assert "Tables" in r.output

    def test_text_output_contains_findings(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)]
        )
        assert "Findings" in r.output

    def test_text_output_contains_recommendations(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)]
        )
        assert "Recommendations" in r.output

    def test_text_output_read_only_disclaimer(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)]
        )
        assert "Read-only" in r.output

    def test_json_output_is_valid(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        assert "status" in data
        assert "migrations_scanned" in data
        assert "tables" in data
        assert "policies" in data
        assert "findings" in data
        assert "recommendations" in data

    def test_json_output_tables_have_required_fields(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        for t in data["tables"]:
            assert "name" in t
            assert "rls_enabled" in t
            assert "rls_forced" in t
            assert "policy_count" in t

    def test_json_output_policies_have_required_fields(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        for p in data["policies"]:
            assert "name" in p
            assert "table" in p
            assert "command" in p
            assert "has_using" in p
            assert "has_with_check" in p
            assert "source_file" in p
            assert "source_line" in p

    def test_json_output_findings_have_required_fields(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        for f in data["findings"]:
            assert "severity" in f
            assert "table" in f
            assert "rule" in f
            assert "message" in f
            assert "recommendation" in f

    def test_json_no_dot_env_values_fixture(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        # The key constraint: no .env values ever appear
        assert "do_not_read_me" not in r.output

    def test_nonexistent_path_exits_1(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", "/nonexistent/xyz123"]
        )
        assert r.exit_code == 1
        assert "does not exist" in r.output

    def test_empty_migrations_dir_exits_0(self, tmp_path: Path) -> None:
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        r = runner.invoke(app, ["supabase", "rls", "inspect", "--path", str(tmp_path)])
        assert r.exit_code == 0

    def test_json_no_dot_env_values(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;"
        )
        (tmp_path / ".env").write_text("SUPABASE_SECRET_KEY=never_leak_this\n")
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(tmp_path), "--json"]
        )
        assert "never_leak_this" not in r.output

    def test_read_only_via_cli(self) -> None:
        before = {
            str(p): p.stat().st_size for p in FIXTURE_DIR.rglob("*") if p.is_file()
        }
        runner.invoke(app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)])
        runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        after = {
            str(p): p.stat().st_size for p in FIXTURE_DIR.rglob("*") if p.is_file()
        }
        assert before == after

    def test_status_in_json_is_valid_value(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        assert data["status"] in ("OK", "WARNING", "ERROR")

    def test_migrations_scanned_count_in_json(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        assert data["migrations_scanned"] == 3

    def test_has_with_check_true_for_insert_with_check(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        policies_with_check = [p for p in data["policies"] if p["has_with_check"]]
        assert len(policies_with_check) > 0


# ---------------------------------------------------------------------------
# TestAntiLeakageGlobal
# ---------------------------------------------------------------------------


class TestAntiLeakageGlobal:
    def test_no_env_values_in_result(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;\n"
            'CREATE POLICY "p" ON public.users FOR SELECT USING (true);'
        )
        (tmp_path / ".env").write_text(
            "SUPABASE_SERVICE_ROLE_KEY=top_secret_should_never_appear\n"
        )
        result = run_rls_inspect(tmp_path)
        result_str = str(result)
        assert "top_secret_should_never_appear" not in result_str

    def test_sql_expressions_never_contain_raw_keys(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;\n"
            'CREATE POLICY "p" ON public.users FOR SELECT USING (auth.uid() = user_id);'
        )
        result = run_rls_inspect(tmp_path)
        for p in result.policies:
            # expressions may contain SQL but never .env values
            assert "secret" not in p.using_expr
