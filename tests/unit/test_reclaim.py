"""
Unit tests for aeos.reclaim.inspector — no network, no real git repos.
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.reclaim import run_reclaim_inspect
from aeos.reclaim.inspector import (
    ReclaimControlMap,
    ReclaimExitOption,
    ReclaimGenerator,
    ReclaimInspectResult,
    ReclaimMissingAsset,
    ReclaimProvider,
    _build_control_map,
    _build_exit_options,
    _check_gitignore_protects,
    _compute_status,
    _detect_generators,
    _detect_missing_assets,
    _detect_providers,
    _extract_env_var_names,
    _get_package_deps,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# TestDataModel
# ---------------------------------------------------------------------------


class TestDataModel:
    def test_generator_fields(self) -> None:
        g = ReclaimGenerator(name="lovable", detected=True, evidence="src/:1")
        assert g.name == "lovable"
        assert g.detected is True
        assert g.evidence == "src/:1"

    def test_provider_fields(self) -> None:
        p = ReclaimProvider(
            name="supabase",
            detected=True,
            roles=["auth", "database"],
            evidence="supabase/migrations/:1",
        )
        assert p.name == "supabase"
        assert p.roles == ["auth", "database"]

    def test_control_map_fields(self) -> None:
        cm = ReclaimControlMap(
            frontend_code="partial",
            backend_runtime="likely_external",
            database_schema="partial",
            auth="likely_external",
            storage="likely_external",
            secrets_control="local",
            secrets_exposure="none",
            deployment="likely_external",
            portability="weak",
        )
        assert cm.portability == "weak"
        assert cm.secrets_exposure == "none"

    def test_missing_asset_default_not_present(self) -> None:
        m = ReclaimMissingAsset(asset="Dockerfile", impact="no deploy")
        assert m.present is False

    def test_exit_option_fields(self) -> None:
        e = ReclaimExitOption(
            id="secure_in_place",
            label="Stay on current provider but secure",
            complexity="low",
            sovereignty="partial",
            advantages=["fast"],
            risks=["lock-in"],
            next_action="rotate keys",
        )
        assert e.id == "secure_in_place"
        assert e.complexity == "low"

    def test_inspect_result_defaults(self, tmp_path: Path) -> None:
        r = ReclaimInspectResult(path=tmp_path, status="OK")
        assert r.generators == []
        assert r.providers == []
        assert r.requires_manual_action is False


# ---------------------------------------------------------------------------
# TestExtractEnvVarNames
# ---------------------------------------------------------------------------


class TestExtractEnvVarNames:
    def test_extracts_names_only(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("FOO=secret_value\nBAR=another_value\n")
        names = _extract_env_var_names(env)
        assert "FOO" in names
        assert "BAR" in names
        assert "secret_value" not in names
        assert "another_value" not in names

    def test_skips_comments(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("# comment\nFOO=bar\n# another comment\n")
        names = _extract_env_var_names(env)
        assert names == ["FOO"]

    def test_empty_file(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("")
        assert _extract_env_var_names(env) == []

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        assert _extract_env_var_names(tmp_path / ".env") == []

    def test_file_too_large_skipped(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_bytes(b"X=y\n" * 30_000)  # > 100 KB
        assert _extract_env_var_names(env) == []


# ---------------------------------------------------------------------------
# TestGetPackageDeps
# ---------------------------------------------------------------------------


class TestGetPackageDeps:
    def test_returns_deps(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        deps = _get_package_deps(tmp_path)
        assert "@supabase/supabase-js" in deps

    def test_merges_dev_deps(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps(
                {
                    "dependencies": {"react": "^18.0.0"},
                    "devDependencies": {"@clerk/nextjs": "^4.0.0"},
                }
            )
        )
        deps = _get_package_deps(tmp_path)
        assert "react" in deps
        assert "@clerk/nextjs" in deps

    def test_empty_on_missing(self, tmp_path: Path) -> None:
        assert _get_package_deps(tmp_path) == set()

    def test_empty_on_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text("{invalid}")
        assert _get_package_deps(tmp_path) == set()


# ---------------------------------------------------------------------------
# TestGeneratorDetection
# ---------------------------------------------------------------------------


class TestGeneratorDetection:
    def test_always_returns_three_generators(self, tmp_path: Path) -> None:
        generators = _detect_generators(tmp_path)
        assert len(generators) == 3
        names = [g.name for g in generators]
        assert "lovable" in names
        assert "bolt" in names
        assert "replit" in names

    def test_lovable_detected_by_dot_lovable(self, tmp_path: Path) -> None:
        (tmp_path / ".lovable").mkdir()
        generators = _detect_generators(tmp_path)
        lovable = next(g for g in generators if g.name == "lovable")
        assert lovable.detected is True
        assert ".lovable" in lovable.evidence

    def test_lovable_detected_by_integrations_dir(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "integrations" / "supabase").mkdir(parents=True)
        generators = _detect_generators(tmp_path)
        lovable = next(g for g in generators if g.name == "lovable")
        assert lovable.detected is True
        assert "src/integrations/supabase" in lovable.evidence

    def test_lovable_detected_by_config_file(self, tmp_path: Path) -> None:
        (tmp_path / "lovable.config.ts").write_text("export default {}")
        generators = _detect_generators(tmp_path)
        lovable = next(g for g in generators if g.name == "lovable")
        assert lovable.detected is True

    def test_lovable_detected_by_env_var(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("LOVABLE_PROJECT_ID=fake-id\n")
        generators = _detect_generators(tmp_path)
        lovable = next(g for g in generators if g.name == "lovable")
        assert lovable.detected is True
        assert "fake-id" not in lovable.evidence  # never leak values

    def test_lovable_not_detected_in_plain_project(self, tmp_path: Path) -> None:
        generators = _detect_generators(tmp_path)
        lovable = next(g for g in generators if g.name == "lovable")
        assert lovable.detected is False
        assert lovable.evidence == ""

    def test_bolt_detected_by_dot_bolt(self, tmp_path: Path) -> None:
        (tmp_path / ".bolt").mkdir()
        generators = _detect_generators(tmp_path)
        bolt = next(g for g in generators if g.name == "bolt")
        assert bolt.detected is True
        assert ".bolt" in bolt.evidence

    def test_bolt_detected_by_env_var(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("BOLT_TOKEN=fake-token\n")
        generators = _detect_generators(tmp_path)
        bolt = next(g for g in generators if g.name == "bolt")
        assert bolt.detected is True
        assert "fake-token" not in bolt.evidence

    def test_bolt_not_detected_in_plain_project(self, tmp_path: Path) -> None:
        generators = _detect_generators(tmp_path)
        bolt = next(g for g in generators if g.name == "bolt")
        assert bolt.detected is False

    def test_replit_detected_by_dot_replit(self, tmp_path: Path) -> None:
        (tmp_path / ".replit").write_text("[nix]\n")
        generators = _detect_generators(tmp_path)
        replit = next(g for g in generators if g.name == "replit")
        assert replit.detected is True
        assert ".replit" in replit.evidence

    def test_replit_detected_by_replit_nix(self, tmp_path: Path) -> None:
        (tmp_path / "replit.nix").write_text("{pkgs}: {}")
        generators = _detect_generators(tmp_path)
        replit = next(g for g in generators if g.name == "replit")
        assert replit.detected is True

    def test_replit_not_detected_in_plain_project(self, tmp_path: Path) -> None:
        generators = _detect_generators(tmp_path)
        replit = next(g for g in generators if g.name == "replit")
        assert replit.detected is False


# ---------------------------------------------------------------------------
# TestProviderDetection
# ---------------------------------------------------------------------------


class TestProviderDetection:
    def test_always_returns_four_providers(self, tmp_path: Path) -> None:
        providers = _detect_providers(tmp_path)
        assert len(providers) == 4
        names = [p.name for p in providers]
        assert "supabase" in names
        assert "vercel" in names
        assert "firebase" in names
        assert "clerk" in names

    def test_supabase_detected_by_migrations(self, tmp_path: Path) -> None:
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        providers = _detect_providers(tmp_path)
        sup = next(p for p in providers if p.name == "supabase")
        assert sup.detected is True
        assert "database" in sup.roles

    def test_supabase_detected_by_client_dep(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}})
        )
        providers = _detect_providers(tmp_path)
        sup = next(p for p in providers if p.name == "supabase")
        assert sup.detected is True
        assert "auth" in sup.roles

    def test_supabase_detected_by_env_var(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("NEXT_PUBLIC_SUPABASE_URL=https://x.co\n")
        providers = _detect_providers(tmp_path)
        sup = next(p for p in providers if p.name == "supabase")
        assert sup.detected is True
        assert "https://x.co" not in sup.evidence

    def test_supabase_detected_by_integrations_dir(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "integrations" / "supabase").mkdir(parents=True)
        providers = _detect_providers(tmp_path)
        sup = next(p for p in providers if p.name == "supabase")
        assert sup.detected is True

    def test_vercel_detected_by_vercel_json(self, tmp_path: Path) -> None:
        (tmp_path / "vercel.json").write_text("{}")
        providers = _detect_providers(tmp_path)
        verc = next(p for p in providers if p.name == "vercel")
        assert verc.detected is True
        assert "deployment" in verc.roles

    def test_vercel_detected_by_dot_vercel(self, tmp_path: Path) -> None:
        (tmp_path / ".vercel").mkdir()
        providers = _detect_providers(tmp_path)
        verc = next(p for p in providers if p.name == "vercel")
        assert verc.detected is True

    def test_firebase_detected_by_firebase_json(self, tmp_path: Path) -> None:
        (tmp_path / "firebase.json").write_text("{}")
        providers = _detect_providers(tmp_path)
        fb = next(p for p in providers if p.name == "firebase")
        assert fb.detected is True

    def test_firebase_detected_by_firebaserc(self, tmp_path: Path) -> None:
        (tmp_path / ".firebaserc").write_text("{}")
        providers = _detect_providers(tmp_path)
        fb = next(p for p in providers if p.name == "firebase")
        assert fb.detected is True

    def test_clerk_detected_by_dep(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@clerk/nextjs": "^4.0.0"}})
        )
        providers = _detect_providers(tmp_path)
        clerk = next(p for p in providers if p.name == "clerk")
        assert clerk.detected is True
        assert "auth" in clerk.roles

    def test_clerk_detected_by_env_var(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_fake\n")
        providers = _detect_providers(tmp_path)
        clerk = next(p for p in providers if p.name == "clerk")
        assert clerk.detected is True
        assert "pk_fake" not in clerk.evidence

    def test_no_provider_in_plain_project(self, tmp_path: Path) -> None:
        providers = _detect_providers(tmp_path)
        assert not any(p.detected for p in providers)


# ---------------------------------------------------------------------------
# TestCheckGitignoreProtects
# ---------------------------------------------------------------------------


class TestCheckGitignoreProtects:
    def test_protects_when_env_in_gitignore(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text(".env\n.env.*\nnode_modules/\n")
        assert _check_gitignore_protects(tmp_path) is True

    def test_no_protection_when_not_in_gitignore(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("node_modules/\ndist/\n")
        assert _check_gitignore_protects(tmp_path) is False

    def test_no_protection_when_no_gitignore(self, tmp_path: Path) -> None:
        assert _check_gitignore_protects(tmp_path) is False


# ---------------------------------------------------------------------------
# TestControlMap
# ---------------------------------------------------------------------------


def _make_generators(
    lovable: bool = False, bolt: bool = False, replit: bool = False
) -> list[ReclaimGenerator]:
    return [
        ReclaimGenerator(name="lovable", detected=lovable, evidence=""),
        ReclaimGenerator(name="bolt", detected=bolt, evidence=""),
        ReclaimGenerator(name="replit", detected=replit, evidence=""),
    ]


def _make_providers(
    supabase: bool = False,
    vercel: bool = False,
    firebase: bool = False,
    clerk: bool = False,
    supabase_roles: list[str] | None = None,
) -> list[ReclaimProvider]:
    return [
        ReclaimProvider(
            name="supabase",
            detected=supabase,
            roles=supabase_roles or (["auth", "database"] if supabase else []),
            evidence="",
        ),
        ReclaimProvider(
            name="vercel",
            detected=vercel,
            roles=["deployment"] if vercel else [],
            evidence="",
        ),
        ReclaimProvider(
            name="firebase",
            detected=firebase,
            roles=["auth", "database"] if firebase else [],
            evidence="",
        ),
        ReclaimProvider(
            name="clerk",
            detected=clerk,
            roles=["auth"] if clerk else [],
            evidence="",
        ),
    ]


class TestControlMap:
    def test_frontend_partial_when_lovable_and_src(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        cm = _build_control_map(
            tmp_path,
            _make_generators(lovable=True),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.frontend_code == "partial"

    def test_frontend_controlled_when_src_no_generator(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.frontend_code == "controlled"

    def test_frontend_unknown_when_no_src(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.frontend_code == "unknown"

    def test_backend_controlled_when_server_dir(self, tmp_path: Path) -> None:
        (tmp_path / "server").mkdir()
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.backend_runtime == "controlled"

    def test_backend_controlled_when_api_dir(self, tmp_path: Path) -> None:
        (tmp_path / "api").mkdir()
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.backend_runtime == "controlled"

    def test_backend_likely_external_when_no_server_but_provider(
        self, tmp_path: Path
    ) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(supabase=True),
            False,
            False,
            False,
        )
        assert cm.backend_runtime == "likely_external"

    def test_backend_unknown_when_nothing(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.backend_runtime == "unknown"

    def test_schema_partial_when_supabase_migrations(self, tmp_path: Path) -> None:
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(supabase=True),
            False,
            False,
            False,
        )
        assert cm.database_schema == "partial"

    def test_schema_controlled_when_prisma(self, tmp_path: Path) -> None:
        (tmp_path / "prisma").mkdir()
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.database_schema == "controlled"

    def test_schema_missing_when_nothing(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.database_schema == "missing"

    def test_auth_external_when_clerk(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(clerk=True),
            False,
            False,
            False,
        )
        assert cm.auth == "external"

    def test_auth_external_when_firebase(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(firebase=True),
            False,
            False,
            False,
        )
        assert cm.auth == "external"

    def test_auth_likely_external_when_supabase_with_auth_role(
        self, tmp_path: Path
    ) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(supabase=True, supabase_roles=["auth", "database"]),
            False,
            False,
            False,
        )
        assert cm.auth == "likely_external"

    def test_auth_unknown_when_no_auth_provider(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(supabase=True, supabase_roles=["database"]),
            False,
            False,
            False,
        )
        assert cm.auth == "unknown"

    def test_secrets_control_local_when_gitignored_not_tracked(
        self, tmp_path: Path
    ) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            True,  # gitignore_protects=True
        )
        assert cm.secrets_control == "local"

    def test_secrets_control_external_when_tracked(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            True,
            True,  # env_currently_tracked=True
        )
        assert cm.secrets_control == "external"

    def test_secrets_exposure_confirmed_when_in_history(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            True,
            False,
            True,  # in_env_history=True
        )
        assert cm.secrets_exposure == "confirmed"

    def test_secrets_exposure_risk_when_tracked(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            True,
            False,  # tracked but not in history
        )
        assert cm.secrets_exposure == "risk"

    def test_secrets_exposure_none_when_protected(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            True,
        )
        assert cm.secrets_exposure == "none"

    def test_secrets_control_independent_of_history(self, tmp_path: Path) -> None:
        # .env was in history but is now gitignored — control=local, exposure=confirmed
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            True,
            False,
            True,  # history=True, tracked=False, gitignore=True
        )
        assert cm.secrets_control == "local"
        assert cm.secrets_exposure == "confirmed"

    def test_deployment_controlled_when_dockerfile(self, tmp_path: Path) -> None:
        (tmp_path / "Dockerfile").write_text("FROM python:3.12")
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.deployment == "controlled"

    def test_deployment_controlled_when_compose(self, tmp_path: Path) -> None:
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.deployment == "controlled"

    def test_deployment_external_when_vercel(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(vercel=True),
            False,
            False,
            False,
        )
        assert cm.deployment == "external"

    def test_portability_weak_when_all_external(self, tmp_path: Path) -> None:
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(supabase=True, vercel=True),
            False,
            False,
            False,
        )
        assert cm.portability == "weak"

    def test_portability_strong_when_docker_and_local(self, tmp_path: Path) -> None:
        (tmp_path / "Dockerfile").write_text("FROM python")
        (tmp_path / "server").mkdir()
        (tmp_path / "migrations").mkdir()
        cm = _build_control_map(
            tmp_path,
            _make_generators(),
            _make_providers(),
            False,
            False,
            False,
        )
        assert cm.portability == "strong"


# ---------------------------------------------------------------------------
# TestMissingAssets
# ---------------------------------------------------------------------------


class TestMissingAssets:
    def test_always_six_assets(self, tmp_path: Path) -> None:
        assets = _detect_missing_assets(tmp_path)
        assert len(assets) == 6

    def test_dockerfile_missing_by_default(self, tmp_path: Path) -> None:
        assets = _detect_missing_assets(tmp_path)
        dockerfile = next(a for a in assets if a.asset == "Dockerfile")
        assert dockerfile.present is False

    def test_dockerfile_present(self, tmp_path: Path) -> None:
        (tmp_path / "Dockerfile").write_text("FROM python")
        assets = _detect_missing_assets(tmp_path)
        dockerfile = next(a for a in assets if a.asset == "Dockerfile")
        assert dockerfile.present is True

    def test_local_backend_missing(self, tmp_path: Path) -> None:
        assets = _detect_missing_assets(tmp_path)
        backend = next(a for a in assets if a.asset == "server/ or api/")
        assert backend.present is False

    def test_env_example_present(self, tmp_path: Path) -> None:
        (tmp_path / ".env.example").write_text("FOO=bar\n")
        assets = _detect_missing_assets(tmp_path)
        example = next(a for a in assets if a.asset == ".env.example")
        assert example.present is True

    def test_assets_have_impact(self, tmp_path: Path) -> None:
        assets = _detect_missing_assets(tmp_path)
        for a in assets:
            assert a.impact != ""


# ---------------------------------------------------------------------------
# TestExitOptions
# ---------------------------------------------------------------------------


class TestExitOptions:
    def _cm(self) -> ReclaimControlMap:
        return ReclaimControlMap(
            frontend_code="partial",
            backend_runtime="likely_external",
            database_schema="partial",
            auth="likely_external",
            storage="likely_external",
            secrets_control="local",
            secrets_exposure="none",
            deployment="likely_external",
            portability="weak",
        )

    def test_always_five_options(self) -> None:
        options = _build_exit_options(self._cm(), [])
        assert len(options) == 5

    def test_option_order(self) -> None:
        options = _build_exit_options(self._cm(), [])
        assert options[0].id == "secure_in_place"
        assert options[1].id == "own_supabase_cloud"
        assert options[2].id == "self_hosted_supabase"
        assert options[3].id == "postgres_open_backend"
        assert options[4].id == "full_sovereign_rebuild"

    def test_all_have_next_action(self) -> None:
        options = _build_exit_options(self._cm(), [])
        for opt in options:
            assert opt.next_action != ""

    def test_valid_complexity_values(self) -> None:
        valid = {"low", "medium", "high", "very_high", "extreme"}
        options = _build_exit_options(self._cm(), [])
        for opt in options:
            assert opt.complexity in valid

    def test_valid_sovereignty_values(self) -> None:
        valid = {"partial", "medium", "high", "very_high", "maximum"}
        options = _build_exit_options(self._cm(), [])
        for opt in options:
            assert opt.sovereignty in valid

    def test_next_action_adapted_when_secrets_exposed(self) -> None:
        cm = self._cm()
        cm.secrets_exposure = "confirmed"
        options = _build_exit_options(cm, [])
        assert "rotate" in options[0].next_action.lower()

    def test_all_have_advantages_and_risks(self) -> None:
        options = _build_exit_options(self._cm(), [])
        for opt in options:
            assert len(opt.advantages) > 0
            assert len(opt.risks) > 0


# ---------------------------------------------------------------------------
# TestStatusComputation
# ---------------------------------------------------------------------------


class TestStatusComputation:
    def _generators(self, lovable: bool = False) -> list[ReclaimGenerator]:
        return _make_generators(lovable=lovable)

    def _cm(
        self, exposure: str = "none", portability: str = "partial"
    ) -> ReclaimControlMap:
        return ReclaimControlMap(
            frontend_code="controlled",
            backend_runtime="unknown",
            database_schema="unknown",
            auth="unknown",
            storage="unknown",
            secrets_control="local",
            secrets_exposure=exposure,
            deployment="unknown",
            portability=portability,
        )

    def test_ok_when_no_issues(self) -> None:
        result = _compute_status(self._cm(portability="strong"), self._generators())
        assert result == "OK"

    def test_warning_when_generator(self) -> None:
        result = _compute_status(self._cm(), self._generators(lovable=True))
        assert result == "WARNING"

    def test_warning_when_portability_weak(self) -> None:
        result = _compute_status(self._cm(portability="weak"), self._generators())
        assert result == "WARNING"

    def test_warning_when_portability_partial(self) -> None:
        result = _compute_status(self._cm(portability="partial"), self._generators())
        assert result == "WARNING"

    def test_error_when_secrets_exposure_confirmed(self) -> None:
        result = _compute_status(self._cm(exposure="confirmed"), self._generators())
        assert result == "ERROR"

    def test_error_when_secrets_exposure_risk(self) -> None:
        result = _compute_status(self._cm(exposure="risk"), self._generators())
        assert result == "ERROR"


# ---------------------------------------------------------------------------
# TestRunReclaimInspect
# ---------------------------------------------------------------------------


class TestRunReclaimInspect:
    def test_returns_result(self, tmp_path: Path) -> None:
        result = run_reclaim_inspect(tmp_path)
        assert isinstance(result, ReclaimInspectResult)

    def test_path_is_absolute(self, tmp_path: Path) -> None:
        result = run_reclaim_inspect(tmp_path)
        assert result.path.is_absolute()

    def test_always_five_exit_options(self, tmp_path: Path) -> None:
        result = run_reclaim_inspect(tmp_path)
        assert len(result.exit_options) == 5

    def test_always_three_generators(self, tmp_path: Path) -> None:
        result = run_reclaim_inspect(tmp_path)
        assert len(result.generators) == 3

    def test_always_four_providers(self, tmp_path: Path) -> None:
        result = run_reclaim_inspect(tmp_path)
        assert len(result.providers) == 4

    def test_no_generators_in_plain_project(self, tmp_path: Path) -> None:
        result = run_reclaim_inspect(tmp_path)
        assert not any(g.detected for g in result.generators)

    def test_recommended_next_action_not_empty(self, tmp_path: Path) -> None:
        result = run_reclaim_inspect(tmp_path)
        assert result.recommended_next_action != ""


# ---------------------------------------------------------------------------
# TestCliReclaimInspect
# ---------------------------------------------------------------------------


class TestCliReclaimInspect:
    def _invoke_text(self, tmp_path: Path) -> str:
        r = runner.invoke(app, ["reclaim", "inspect", "--path", str(tmp_path)])
        return r.output

    def _invoke_json(self, tmp_path: Path) -> dict:  # type: ignore[type-arg]
        r = runner.invoke(
            app, ["reclaim", "inspect", "--path", str(tmp_path), "--json"]
        )
        return json.loads(r.output)  # type: ignore[no-any-return]

    def test_cli_text_has_header(self, tmp_path: Path) -> None:
        assert "Reclaim Inspect" in self._invoke_text(tmp_path)

    def test_cli_text_has_generator_section(self, tmp_path: Path) -> None:
        assert "Generator Detection" in self._invoke_text(tmp_path)

    def test_cli_text_has_provider_section(self, tmp_path: Path) -> None:
        assert "Provider Detection" in self._invoke_text(tmp_path)

    def test_cli_text_has_control_map(self, tmp_path: Path) -> None:
        assert "Control Map" in self._invoke_text(tmp_path)

    def test_cli_text_has_missing_assets(self, tmp_path: Path) -> None:
        assert "Missing Local Assets" in self._invoke_text(tmp_path)

    def test_cli_text_has_exit_options(self, tmp_path: Path) -> None:
        assert "Exit Options" in self._invoke_text(tmp_path)

    def test_cli_text_has_recommended_action(self, tmp_path: Path) -> None:
        assert "Recommended Next Action" in self._invoke_text(tmp_path)

    def test_cli_json_is_valid(self, tmp_path: Path) -> None:
        data = self._invoke_json(tmp_path)
        assert "path" in data
        assert "status" in data

    def test_cli_json_has_generators(self, tmp_path: Path) -> None:
        data = self._invoke_json(tmp_path)
        assert "generators" in data
        assert len(data["generators"]) == 3

    def test_cli_json_has_control_map(self, tmp_path: Path) -> None:
        data = self._invoke_json(tmp_path)
        cm = data["control_map"]
        expected_keys = {
            "frontend_code",
            "backend_runtime",
            "database_schema",
            "auth",
            "storage",
            "secrets_control",
            "secrets_exposure",
            "deployment",
            "portability",
        }
        assert expected_keys.issubset(set(cm.keys()))

    def test_cli_json_has_exit_options(self, tmp_path: Path) -> None:
        data = self._invoke_json(tmp_path)
        assert len(data["exit_options"]) == 5

    def test_cli_json_has_recommended_action(self, tmp_path: Path) -> None:
        data = self._invoke_json(tmp_path)
        assert "recommended_next_action" in data


# ---------------------------------------------------------------------------
# TestAntiLeakage
# ---------------------------------------------------------------------------


class TestAntiLeakage:
    def test_generator_evidence_no_values(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("LOVABLE_SECRET=super-secret-value\n")
        result = run_reclaim_inspect(tmp_path)
        for g in result.generators:
            assert "super-secret-value" not in g.evidence

    def test_provider_evidence_no_values(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("NEXT_PUBLIC_SUPABASE_URL=https://real.url\n")
        result = run_reclaim_inspect(tmp_path)
        for p in result.providers:
            assert "https://real.url" not in p.evidence

    def test_clerk_evidence_no_values(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text(
            "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xyz\n"
        )
        result = run_reclaim_inspect(tmp_path)
        clerk = next(p for p in result.providers if p.name == "clerk")
        assert "pk_live_xyz" not in clerk.evidence

    def test_exit_option_next_action_no_secrets(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SUPABASE_URL=https://secret.url\n")
        result = run_reclaim_inspect(tmp_path)
        for opt in result.exit_options:
            assert "https://secret.url" not in opt.next_action

    def test_json_no_secret_values(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text(
            "NEXT_PUBLIC_SUPABASE_URL=https://secret.project.supabase.co\n"
            "NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiJ9.secret\n"
        )
        r = runner.invoke(
            app, ["reclaim", "inspect", "--path", str(tmp_path), "--json"]
        )
        assert "https://secret.project.supabase.co" not in r.output
        assert "eyJhbGciOiJIUzI1NiJ9.secret" not in r.output

    def test_recommended_action_no_secrets(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SUPABASE_SERVICE_ROLE_KEY=sbp_realkey\n")
        result = run_reclaim_inspect(tmp_path)
        assert "sbp_realkey" not in result.recommended_next_action
