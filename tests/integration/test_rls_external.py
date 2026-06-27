"""
Integration tests: AEOS supabase rls inspect, rls plan, and rls generate
on the lovable_supabase_vercel fixture and on inline realistic fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.providers.supabase.rls import (
    run_rls_generate,
    run_rls_inspect,
    run_rls_plan,
    run_rls_review,
)

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


# ---------------------------------------------------------------------------
# TestRLSOnLovableFixture (existing fixture — minimal schema)
# ---------------------------------------------------------------------------


class TestRLSOnLovableFixture:
    def test_returns_result(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result is not None

    def test_path_is_absolute(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result.path.is_absolute()

    def test_migrations_scanned_at_least_one(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result.migrations_scanned >= 1

    def test_profiles_table_rls_enabled(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        profiles = next((t for t in result.tables if t.name == "profiles"), None)
        assert profiles is not None
        assert profiles.rls_enabled is True

    def test_policies_detected(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert len(result.policies) >= 2

    def test_status_is_valid(self) -> None:
        result = run_rls_inspect(FIXTURE_DIR)
        assert result.status in ("OK", "WARNING", "ERROR")

    def test_read_only_does_not_modify_fixture(self) -> None:
        before = _fingerprint(FIXTURE_DIR)
        run_rls_inspect(FIXTURE_DIR)
        after = _fingerprint(FIXTURE_DIR)
        assert before == after

    def test_cli_does_not_modify_fixture(self) -> None:
        before = _fingerprint(FIXTURE_DIR)
        runner.invoke(app, ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR)])
        runner.invoke(
            app,
            ["supabase", "rls", "inspect", "--path", str(FIXTURE_DIR), "--json"],
        )
        after = _fingerprint(FIXTURE_DIR)
        assert before == after


# ---------------------------------------------------------------------------
# TestRLSMultiTenantFixture (inline fixture with multi-tenant patterns)
# ---------------------------------------------------------------------------


@pytest.fixture()
def multi_tenant_project(tmp_path: Path) -> Path:
    """Inline multi-tenant project with realistic Supabase schema."""
    mig = tmp_path / "supabase" / "migrations"
    mig.mkdir(parents=True)

    (mig / "001_init.sql").write_text(
        """
CREATE TABLE IF NOT EXISTS public.communes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  commune_id uuid REFERENCES public.communes(id)
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "profiles_update_own"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Cross-commune risk: agents update without commune scope
CREATE TABLE IF NOT EXISTS public.signalements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  commune_id uuid REFERENCES public.communes(id),
  description text
);

ALTER TABLE public.signalements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "signalements_select_own"
  ON public.signalements
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "signalements_insert_own"
  ON public.signalements
  FOR INSERT
  WITH CHECK (auth.uid() = user_id AND commune_id IS NOT NULL);

-- Missing commune scope on UPDATE — should be flagged
CREATE POLICY "signalements_update_agents"
  ON public.signalements
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
"""
    )
    return tmp_path


class TestRLSMultiTenantFixture:
    def test_returns_result(self, multi_tenant_project: Path) -> None:
        result = run_rls_inspect(multi_tenant_project)
        assert result is not None

    def test_missing_tenant_scope_detected(self, multi_tenant_project: Path) -> None:
        result = run_rls_inspect(multi_tenant_project)
        assert any(f.rule == "MISSING_TENANT_SCOPE" for f in result.findings)

    def test_profiles_detected(self, multi_tenant_project: Path) -> None:
        result = run_rls_inspect(multi_tenant_project)
        names = {t.name for t in result.tables}
        assert "profiles" in names

    def test_recommendations_mention_tenant(self, multi_tenant_project: Path) -> None:
        result = run_rls_inspect(multi_tenant_project)
        combined = " ".join(result.recommendations)
        assert any(
            token in combined
            for token in ("commune_id", "tenant_id", "org_id", "tenant")
        )

    def test_read_only(self, multi_tenant_project: Path) -> None:
        before = _fingerprint(multi_tenant_project)
        run_rls_inspect(multi_tenant_project)
        after = _fingerprint(multi_tenant_project)
        assert before == after


# ---------------------------------------------------------------------------
# TestRLSNoMigrations
# ---------------------------------------------------------------------------


class TestRLSNoMigrations:
    def test_no_migrations_dir_ok(self, tmp_path: Path) -> None:
        result = run_rls_inspect(tmp_path)
        assert result.status == "OK"
        assert result.migrations_scanned == 0
        assert result.tables == []
        assert result.policies == []

    def test_cli_no_migrations_exits_0(self, tmp_path: Path) -> None:
        r = runner.invoke(app, ["supabase", "rls", "inspect", "--path", str(tmp_path)])
        assert r.exit_code == 0

    def test_json_no_migrations_structure(self, tmp_path: Path) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "inspect", "--path", str(tmp_path), "--json"]
        )
        data = json.loads(r.output)
        assert data["migrations_scanned"] == 0
        assert data["tables"] == []
        assert data["policies"] == []
        assert data["findings"] == []


# ---------------------------------------------------------------------------
# TestRLSPlanOnLovableFixture
# ---------------------------------------------------------------------------


class TestRLSPlanOnLovableFixture:
    def test_returns_result(self) -> None:
        result = run_rls_plan(FIXTURE_DIR)
        assert result is not None

    def test_path_is_absolute(self) -> None:
        result = run_rls_plan(FIXTURE_DIR)
        assert result.path.is_absolute()

    def test_read_only_flag(self) -> None:
        result = run_rls_plan(FIXTURE_DIR)
        assert result.read_only is True

    def test_status_valid(self) -> None:
        result = run_rls_plan(FIXTURE_DIR)
        assert result.status in ("OK", "WARNING", "ERROR")

    def test_actions_ordered(self) -> None:
        result = run_rls_plan(FIXTURE_DIR)
        order_map = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        priorities = [order_map[a.priority] for a in result.actions]
        assert priorities == sorted(priorities)

    def test_summary_totals_match(self) -> None:
        result = run_rls_plan(FIXTURE_DIR)
        assert result.summary.total_actions == len(result.actions)
        assert sum(result.summary.by_priority.values()) == len(result.actions)

    def test_does_not_modify_fixture(self) -> None:
        before = _fingerprint(FIXTURE_DIR)
        run_rls_plan(FIXTURE_DIR)
        after = _fingerprint(FIXTURE_DIR)
        assert before == after

    def test_cli_text_output(self) -> None:
        r = runner.invoke(app, ["supabase", "rls", "plan", "--path", str(FIXTURE_DIR)])
        assert "Supabase RLS Plan Advisor" in r.output
        assert "Executive Summary" in r.output
        assert "Read-only audit" in r.output

    def test_cli_json_output(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "plan", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        assert data["read_only"] is True
        assert "summary" in data
        assert "actions" in data


# ---------------------------------------------------------------------------
# TestRLSPlanMultiTenantFixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def multi_tenant_plan_project(tmp_path: Path) -> Path:
    mig = tmp_path / "supabase" / "migrations"
    mig.mkdir(parents=True)
    (mig / "001_init.sql").write_text(
        """
CREATE TABLE IF NOT EXISTS public.signalements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  commune_id uuid,
  description text
);

ALTER TABLE public.signalements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "signalements_select_own"
  ON public.signalements
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "signalements_insert_own"
  ON public.signalements
  FOR INSERT
  WITH CHECK (auth.uid() = user_id AND commune_id IS NOT NULL);

-- UPDATE without commune scope -- should be MISSING_TENANT_SCOPE (HIGH)
CREATE POLICY "signalements_update_agents"
  ON public.signalements
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.personnel (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  commune_id uuid,
  email text
);

ALTER TABLE public.personnel ENABLE ROW LEVEL SECURITY;

-- Sensitive table open SELECT — should be CRITICAL
CREATE POLICY "personnel_select_all"
  ON public.personnel
  FOR SELECT
  USING (true);
"""
    )
    return tmp_path


class TestRLSPlanMultiTenantFixture:
    def test_critical_detected(self, multi_tenant_plan_project: Path) -> None:
        result = run_rls_plan(multi_tenant_plan_project)
        assert any(a.priority == "CRITICAL" for a in result.actions)

    def test_high_missing_tenant_detected(
        self, multi_tenant_plan_project: Path
    ) -> None:
        result = run_rls_plan(multi_tenant_plan_project)
        assert any(
            a.risk_type == "MISSING_TENANT_SCOPE" and a.priority == "HIGH"
            for a in result.actions
        )

    def test_critical_before_high(self, multi_tenant_plan_project: Path) -> None:
        result = run_rls_plan(multi_tenant_plan_project)
        priorities = [a.priority for a in result.actions]
        if "CRITICAL" in priorities and "HIGH" in priorities:
            assert priorities.index("CRITICAL") < priorities.index("HIGH")

    def test_read_only(self, multi_tenant_plan_project: Path) -> None:
        before = _fingerprint(multi_tenant_plan_project)
        run_rls_plan(multi_tenant_plan_project)
        after = _fingerprint(multi_tenant_plan_project)
        assert before == after

    def test_personnel_flagged_critical(self, multi_tenant_plan_project: Path) -> None:
        result = run_rls_plan(multi_tenant_plan_project)
        critical_tables = {a.table for a in result.actions if a.priority == "CRITICAL"}
        assert "personnel" in critical_tables


# ---------------------------------------------------------------------------
# TestRLSPlanNoMigrations
# ---------------------------------------------------------------------------


class TestRLSPlanNoMigrations:
    def test_no_migrations_ok(self, tmp_path: Path) -> None:
        result = run_rls_plan(tmp_path)
        assert result.status == "OK"
        assert result.actions == []

    def test_cli_exits_zero(self, tmp_path: Path) -> None:
        r = runner.invoke(app, ["supabase", "rls", "plan", "--path", str(tmp_path)])
        assert r.exit_code == 0

    def test_json_zero_actions(self, tmp_path: Path) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "plan", "--path", str(tmp_path), "--json"]
        )
        data = json.loads(r.output)
        assert data["summary"]["total_actions"] == 0
        assert data["actions"] == []
        assert data["read_only"] is True


# ---------------------------------------------------------------------------
# TestRLSGenerateOnLovableFixture
# ---------------------------------------------------------------------------

_MULTI_TENANT_SQL = """
CREATE TABLE IF NOT EXISTS public.personnel (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  commune_id uuid NOT NULL,
  user_id uuid NOT NULL,
  full_name text,
  phone text
);
ALTER TABLE public.personnel ENABLE ROW LEVEL SECURITY;

CREATE POLICY "personnel_select_agents"
  ON public.personnel
  FOR SELECT
  USING (auth.uid() IS NOT NULL);

CREATE POLICY "personnel_insert_agents"
  ON public.personnel
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.signalements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  commune_id uuid NOT NULL,
  description text
);
ALTER TABLE public.signalements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "signalements_update_agents"
  ON public.signalements
  FOR UPDATE
  USING (public.has_role(auth.uid(), 'agent'::app_role));
"""


class TestRLSGenerateOnLovableFixture:
    def test_returns_result(self) -> None:
        result = run_rls_generate(FIXTURE_DIR)
        assert result is not None

    def test_applied_false(self) -> None:
        result = run_rls_generate(FIXTURE_DIR)
        assert result.applied is False

    def test_read_only_true(self) -> None:
        result = run_rls_generate(FIXTURE_DIR)
        assert result.read_only is True

    def test_cli_json_structure(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "generate", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        assert "status" in data
        assert "applied" in data
        assert "read_only" in data
        assert "generated_sql" in data
        assert "summary" in data
        assert data["applied"] is False
        assert data["read_only"] is True


class TestRLSGenerateMultiTenantFixture:
    def test_generates_blocks_for_missing_tenant(self, tmp_path: Path) -> None:
        mig_dir = tmp_path / "supabase" / "migrations"
        mig_dir.mkdir(parents=True)
        (mig_dir / "001_multi_tenant.sql").write_text(_MULTI_TENANT_SQL)
        result = run_rls_generate(tmp_path)
        assert result.summary.total_blocks > 0
        assert result.applied is False

    def test_sql_contains_begin_commit(self, tmp_path: Path) -> None:
        mig_dir = tmp_path / "supabase" / "migrations"
        mig_dir.mkdir(parents=True)
        (mig_dir / "001_multi_tenant.sql").write_text(_MULTI_TENANT_SQL)
        result = run_rls_generate(tmp_path)
        assert "BEGIN;" in result.generated_sql
        assert "COMMIT;" in result.generated_sql

    def test_select_too_permissive_is_todo(self, tmp_path: Path) -> None:
        mig_dir = tmp_path / "supabase" / "migrations"
        mig_dir.mkdir(parents=True)
        (mig_dir / "001_multi_tenant.sql").write_text(_MULTI_TENANT_SQL)
        result = run_rls_generate(tmp_path)
        # personnel_select_agents uses auth.uid() IS NOT NULL → SELECT_TOO_PERMISSIVE
        todo_blocks = [b for b in result.blocks if b.is_todo]
        assert any("SELECT" in b.sql or "TODO" in b.sql for b in todo_blocks)

    def test_no_files_modified(self, tmp_path: Path) -> None:
        mig_dir = tmp_path / "supabase" / "migrations"
        mig_dir.mkdir(parents=True)
        sql_file = mig_dir / "001_multi_tenant.sql"
        sql_file.write_text(_MULTI_TENANT_SQL)
        before = {str(p): p.stat().st_mtime for p in tmp_path.rglob("*") if p.is_file()}
        run_rls_generate(tmp_path)
        after = {str(p): p.stat().st_mtime for p in tmp_path.rglob("*") if p.is_file()}
        assert before == after


class TestRLSGenerateNoMigrations:
    def test_no_migrations_ok(self, tmp_path: Path) -> None:
        result = run_rls_generate(tmp_path)
        assert result.summary.total_blocks == 0
        assert result.applied is False

    def test_cli_exits_zero(self, tmp_path: Path) -> None:
        r = runner.invoke(app, ["supabase", "rls", "generate", "--path", str(tmp_path)])
        assert r.exit_code == 0

    def test_json_zero_blocks(self, tmp_path: Path) -> None:
        r = runner.invoke(
            app,
            ["supabase", "rls", "generate", "--path", str(tmp_path), "--json"],
        )
        data = json.loads(r.output)
        assert data["summary"]["total_blocks"] == 0
        assert data["applied"] is False
        assert data["read_only"] is True


# ---------------------------------------------------------------------------
# TestRLSReviewOnLovableFixture
# ---------------------------------------------------------------------------


class TestRLSReviewOnLovableFixture:
    def test_returns_result(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result is not None

    def test_applied_false(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.applied is False

    def test_read_only_true(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.read_only is True

    def test_verdict_not_blocked(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.verdict in ("PASS", "WARNING")

    def test_does_not_modify_fixture(self) -> None:
        before = _fingerprint(FIXTURE_DIR)
        run_rls_review(FIXTURE_DIR)
        after = _fingerprint(FIXTURE_DIR)
        assert before == after

    def test_cli_json_structure(self) -> None:
        r = runner.invoke(
            app, ["supabase", "rls", "review", "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(r.output)
        assert "verdict" in data
        assert data["applied"] is False
        assert data["read_only"] is True
        assert data["summary"]["total_blocks"] >= 0


class TestRLSReviewNoMigrations:
    def test_pass_on_empty(self, tmp_path: Path) -> None:
        result = run_rls_review(tmp_path)
        assert result.verdict == "PASS"
        assert result.applied is False

    def test_cli_exits_zero(self, tmp_path: Path) -> None:
        r = runner.invoke(app, ["supabase", "rls", "review", "--path", str(tmp_path)])
        assert r.exit_code == 0

    def test_json_zero_blocks(self, tmp_path: Path) -> None:
        r = runner.invoke(
            app,
            ["supabase", "rls", "review", "--path", str(tmp_path), "--json"],
        )
        data = json.loads(r.output)
        assert data["summary"]["total_blocks"] == 0
        assert data["verdict"] == "PASS"
        assert data["applied"] is False
        assert data["read_only"] is True
