"""
Integration tests: AEOS supabase rls inspect on the lovable_supabase_vercel
fixture and on an inline realistic fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.providers.supabase.rls import run_rls_inspect

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
