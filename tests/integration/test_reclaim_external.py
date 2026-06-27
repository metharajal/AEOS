"""
Integration tests: AEOS reclaim inspect on the lovable_supabase_vercel fixture.
"""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.reclaim import run_reclaim_inspect

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
    # .env already exists in fixture (fake placeholders); overwrite to be explicit
    (dest / ".env").write_text(
        "# Test fixture — fake placeholders, not real credentials\n"
        "NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co\n"
        "NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key-here\n"
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key-here\n"
        "STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-here\n"
    )
    return dest


# ---------------------------------------------------------------------------
# TestReclaimOnFixture
# ---------------------------------------------------------------------------


class TestReclaimOnFixture:
    def test_returns_result(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result is not None

    def test_path_is_absolute(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result.path.is_absolute()

    def test_lovable_detected(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        lovable = next(g for g in result.generators if g.name == "lovable")
        assert lovable.detected is True

    def test_supabase_detected(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        sup = next(p for p in result.providers if p.name == "supabase")
        assert sup.detected is True

    def test_vercel_detected(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        verc = next(p for p in result.providers if p.name == "vercel")
        assert verc.detected is True

    def test_clerk_detected(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        clerk = next(p for p in result.providers if p.name == "clerk")
        assert clerk.detected is True

    def test_firebase_not_detected(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        fb = next(p for p in result.providers if p.name == "firebase")
        assert fb.detected is False

    def test_bolt_not_detected(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        bolt = next(g for g in result.generators if g.name == "bolt")
        assert bolt.detected is False

    def test_status_is_warning_or_higher(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result.status in ("WARNING", "ERROR", "CRITICAL")


# ---------------------------------------------------------------------------
# TestControlMapOnFixture
# ---------------------------------------------------------------------------


class TestControlMapOnFixture:
    def test_frontend_code_partial(self, ext_project: Path) -> None:
        # Lovable detected + src/ present → partial
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.frontend_code == "partial"

    def test_backend_runtime_not_controlled(self, ext_project: Path) -> None:
        # No server/ or api/ in fixture
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.backend_runtime != "controlled"

    def test_database_schema_partial(self, ext_project: Path) -> None:
        # supabase/migrations/ present
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.database_schema == "partial"

    def test_auth_external_or_likely_external(self, ext_project: Path) -> None:
        # Clerk or Supabase auth detected → not "controlled"
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.auth in ("external", "likely_external")

    def test_deployment_not_controlled(self, ext_project: Path) -> None:
        # No Dockerfile in fixture
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.deployment != "controlled"

    def test_portability_not_strong(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.portability != "strong"

    def test_secrets_exposure_is_none(self, ext_project: Path) -> None:
        # No git repo in tmp_path → no history detected
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.secrets_exposure == "none"

    def test_portability_is_weak(self, ext_project: Path) -> None:
        # No local backend + providers + no docker
        result = run_reclaim_inspect(ext_project)
        assert result.control_map.portability == "weak"


# ---------------------------------------------------------------------------
# TestMissingAssetsOnFixture
# ---------------------------------------------------------------------------


class TestMissingAssetsOnFixture:
    def test_six_assets_checked(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert len(result.missing_assets) == 6

    def test_dockerfile_missing(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        dockerfile = next(a for a in result.missing_assets if a.asset == "Dockerfile")
        assert dockerfile.present is False

    def test_local_backend_missing(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        backend = next(a for a in result.missing_assets if a.asset == "server/ or api/")
        assert backend.present is False

    def test_env_example_present(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        example = next(a for a in result.missing_assets if a.asset == ".env.example")
        assert example.present is True

    def test_all_missing_assets_have_impact(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        for asset in result.missing_assets:
            assert asset.impact != ""


# ---------------------------------------------------------------------------
# TestExitOptionsOnFixture
# ---------------------------------------------------------------------------


class TestExitOptionsOnFixture:
    def test_five_options_present(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert len(result.exit_options) == 5

    def test_secure_in_place_is_first(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result.exit_options[0].id == "secure_in_place"

    def test_full_sovereign_rebuild_is_last(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result.exit_options[-1].id == "full_sovereign_rebuild"

    def test_options_have_next_action(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        for opt in result.exit_options:
            assert opt.next_action != ""

    def test_requires_manual_action(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result.requires_manual_action is True

    def test_recommended_next_action_not_empty(self, ext_project: Path) -> None:
        result = run_reclaim_inspect(ext_project)
        assert result.recommended_next_action != ""


# ---------------------------------------------------------------------------
# TestCLIOutput
# ---------------------------------------------------------------------------


class TestCLIOutput:
    def test_cli_text_contains_header(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project)])
        assert "Reclaim Inspect" in r.output

    def test_cli_text_contains_generator_section(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project)])
        assert "Generator Detection" in r.output

    def test_cli_text_contains_lovable_detected(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project)])
        assert "lovable" in r.output.lower()
        assert "detected" in r.output

    def test_cli_text_contains_control_map(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project)])
        assert "Control Map" in r.output

    def test_cli_text_contains_exit_options(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project)])
        assert "Exit Options" in r.output

    def test_cli_text_contains_recommended_action(self, ext_project: Path) -> None:
        r = runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project)])
        assert "Recommended Next Action" in r.output

    def test_cli_json_is_valid(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["reclaim", "inspect", "--path", str(ext_project), "--json"]
        )
        data = json.loads(r.output)
        assert "path" in data
        assert "status" in data
        assert "generators" in data
        assert "providers" in data
        assert "control_map" in data
        assert "exit_options" in data

    def test_cli_json_lovable_detected(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["reclaim", "inspect", "--path", str(ext_project), "--json"]
        )
        data = json.loads(r.output)
        lovable = next(g for g in data["generators"] if g["name"] == "lovable")
        assert lovable["detected"] is True

    def test_cli_json_supabase_detected(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["reclaim", "inspect", "--path", str(ext_project), "--json"]
        )
        data = json.loads(r.output)
        sup = next(p for p in data["providers"] if p["name"] == "supabase")
        assert sup["detected"] is True

    def test_cli_json_five_exit_options(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["reclaim", "inspect", "--path", str(ext_project), "--json"]
        )
        data = json.loads(r.output)
        assert len(data["exit_options"]) == 5

    def test_cli_json_no_sensitive_values(self, ext_project: Path) -> None:
        r = runner.invoke(
            app, ["reclaim", "inspect", "--path", str(ext_project), "--json"]
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
        run_reclaim_inspect(ext_project)
        after = _fingerprint(ext_project)
        assert before == after, "run_reclaim_inspect modified the target project"

    def test_cli_does_not_modify_project(self, ext_project: Path) -> None:
        before = _fingerprint(ext_project)
        runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project)])
        runner.invoke(app, ["reclaim", "inspect", "--path", str(ext_project), "--json"])
        after = _fingerprint(ext_project)
        assert before == after, "CLI reclaim inspect modified the target project"

    def test_no_new_files_created(self, ext_project: Path) -> None:
        before = set(_fingerprint(ext_project).keys())
        run_reclaim_inspect(ext_project)
        after = set(_fingerprint(ext_project).keys())
        assert before == after, f"New files created: {after - before}"
