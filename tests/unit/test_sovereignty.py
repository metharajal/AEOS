import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.sovereignty.checker import run_sovereignty_check

_runner = CliRunner()


def _make_sovereign_project(path: Path) -> None:
    (path / "aeos.toml").write_text(
        '[ai]\nmode = "local-first"\n'
        "require_human_approval = true\n"
        "frontier_allowed = true\n",
        encoding="utf-8",
    )
    (path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (path / "docker-compose.yml").write_text("version: '3'\n", encoding="utf-8")
    (path / "README.md").write_text("# Project\n", encoding="utf-8")
    (path / "migrations").mkdir()
    (path / ".env.example").write_text("PORT=3000\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# AI category
# ---------------------------------------------------------------------------


def test_no_aeos_toml_ai_warning(tmp_path: Path) -> None:
    result = run_sovereignty_check(tmp_path)
    ai = [f for f in result.findings if f.category == "ai"]
    assert any("aeos.toml not found" in f.message for f in ai)


def test_local_first_aeos_toml_no_ai_findings(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text(
        '[ai]\nmode = "local-first"\nrequire_human_approval = true\n',
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    ai = [f for f in result.findings if f.category == "ai"]
    assert ai == []


def test_non_local_first_mode_ai_warning(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text(
        '[ai]\nmode = "cloud-first"\nrequire_human_approval = true\n',
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    ai = [f for f in result.findings if f.category == "ai"]
    assert any("cloud-first" in f.message for f in ai)


def test_no_human_approval_ai_warning(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text(
        '[ai]\nmode = "local-first"\nrequire_human_approval = false\n',
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    ai = [f for f in result.findings if f.category == "ai"]
    assert any("human approval" in f.message for f in ai)


# ---------------------------------------------------------------------------
# Database category
# ---------------------------------------------------------------------------


def test_supabase_package_json_database_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@supabase/supabase-js": "^2.0.0"}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("Supabase" in f.message for f in db)


def test_firebase_package_json_database_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"firebase": "^10.0.0"}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("Firebase" in f.message for f in db)


def test_supabase_url_env_var_warning_no_value(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "SUPABASE_URL=https://secret.supabase.co\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("SUPABASE_URL" in f.message for f in db)
    for f in result.findings:
        assert "https://secret.supabase.co" not in f.message
        assert "https://secret.supabase.co" not in f.recommendation


def test_database_url_env_var_warning(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "DATABASE_URL=postgres://user:pass@host/db\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("DATABASE_URL" in f.message for f in db)


# ---------------------------------------------------------------------------
# Auth category
# ---------------------------------------------------------------------------


def test_clerk_package_json_auth_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@clerk/nextjs": "^4.0.0"}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    auth = [f for f in result.findings if f.category == "auth"]
    assert any("Clerk" in f.message for f in auth)


def test_auth0_package_json_auth_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@auth0/auth0-react": "^2.0.0"}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    auth = [f for f in result.findings if f.category == "auth"]
    assert any("Auth0" in f.message for f in auth)


def test_clerk_deduplicated_when_both_packages(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {
                    "@clerk/nextjs": "^4.0.0",
                    "@clerk/clerk-react": "^4.0.0",
                }
            }
        ),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    auth = [f for f in result.findings if f.category == "auth"]
    clerk = [f for f in auth if "Clerk" in f.message]
    assert len(clerk) == 1


# ---------------------------------------------------------------------------
# Storage category
# ---------------------------------------------------------------------------


def test_cloudinary_package_json_storage_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"cloudinary": "^1.0.0"}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    storage = [f for f in result.findings if f.category == "storage"]
    assert any("Cloudinary" in f.message for f in storage)


def test_s3_sdk_package_json_storage_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@aws-sdk/client-s3": "^3.0.0"}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    storage = [f for f in result.findings if f.category == "storage"]
    assert any("S3" in f.message for f in storage)


# ---------------------------------------------------------------------------
# Hosting category
# ---------------------------------------------------------------------------


def test_vercel_json_hosting_warning(tmp_path: Path) -> None:
    (tmp_path / "vercel.json").write_text("{}", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    hosting = [f for f in result.findings if f.category == "hosting"]
    assert any("Vercel" in f.message for f in hosting)


def test_netlify_toml_hosting_warning(tmp_path: Path) -> None:
    (tmp_path / "netlify.toml").write_text("[build]\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    hosting = [f for f in result.findings if f.category == "hosting"]
    assert any("Netlify" in f.message for f in hosting)


# ---------------------------------------------------------------------------
# MCP / connectors category
# ---------------------------------------------------------------------------


def test_cursor_mcp_json_with_servers(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json").write_text(
        json.dumps({"mcpServers": {"my-server": {"command": "python"}}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    mcp = [f for f in result.findings if f.category == "mcp"]
    assert len(mcp) > 0


def test_root_json_with_mcp_servers(tmp_path: Path) -> None:
    (tmp_path / "mcp-config.json").write_text(
        json.dumps({"mcpServers": {"remote": {"url": "https://example.com"}}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    mcp = [f for f in result.findings if f.category == "mcp"]
    assert any("mcp-config.json" in f.location for f in mcp)


# ---------------------------------------------------------------------------
# Secrets category
# ---------------------------------------------------------------------------


def test_supabase_anon_key_secrets_warning_no_value(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiJ9.secret\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    secrets = [f for f in result.findings if f.category == "secrets"]
    assert any("SUPABASE_ANON_KEY" in f.message for f in secrets)
    for f in result.findings:
        assert "eyJhbGciOiJIUzI1NiJ9.secret" not in f.message
        assert "eyJhbGciOiJIUzI1NiJ9.secret" not in f.recommendation


def test_api_key_secrets_warning_no_value(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "OPENAI_API_KEY=sk-real-secret-key\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    secrets = [f for f in result.findings if f.category == "secrets"]
    assert any("OPENAI_API_KEY" in f.message for f in secrets)
    for f in result.findings:
        assert "sk-real-secret-key" not in f.message
        assert "sk-real-secret-key" not in f.recommendation


def test_dot_env_without_gitignore_error(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=real_value\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    errors = [
        f for f in result.findings if f.category == "secrets" and f.severity == "ERROR"
    ]
    assert len(errors) > 0
    for f in result.findings:
        assert "real_value" not in f.message
        assert "real_value" not in f.recommendation


def test_dot_env_with_gitignore_no_error(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=real\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    errors = [
        f for f in result.findings if f.category == "secrets" and f.severity == "ERROR"
    ]
    assert errors == []


def test_no_secret_value_ever_in_findings(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "API_KEY=my_super_secret\nTOKEN=another_secret\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    for f in result.findings:
        assert "my_super_secret" not in f.message
        assert "my_super_secret" not in f.recommendation
        assert "another_secret" not in f.message
        assert "another_secret" not in f.recommendation


# ---------------------------------------------------------------------------
# Portability category
# ---------------------------------------------------------------------------


def test_empty_project_portability_warnings(tmp_path: Path) -> None:
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    messages = [f.message for f in portability]
    assert any("Dockerfile" in m for m in messages)
    assert any("docker-compose.yml" in m for m in messages)


def test_dockerfile_present_no_portability_finding(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert not any("Dockerfile" in f.message for f in portability)


def test_docker_compose_yaml_accepted(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yaml").write_text("version: '3'\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert not any("docker-compose" in f.message for f in portability)


def test_full_sovereign_project_ok(tmp_path: Path) -> None:
    _make_sovereign_project(tmp_path)
    result = run_sovereignty_check(tmp_path)
    assert result.status == "OK"
    assert result.findings == []


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------


def test_status_warning_when_any_warning(tmp_path: Path) -> None:
    result = run_sovereignty_check(tmp_path)
    assert result.status == "WARNING"


def test_status_error_when_any_error(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("S=v\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    assert result.status == "ERROR"


def test_status_error_beats_warning(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("S=v\n", encoding="utf-8")
    (tmp_path / "vercel.json").write_text("{}", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    assert result.status == "ERROR"


# ---------------------------------------------------------------------------
# CLI — text output
# ---------------------------------------------------------------------------


def test_cli_sovereignty_check_text_output(tmp_path: Path) -> None:
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path)])
    assert "Sovereignty Check" in r.output
    assert "Path:" in r.output
    assert "Status:" in r.output


def test_cli_sovereignty_check_warning_exits_0(tmp_path: Path) -> None:
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path)])
    assert r.exit_code == 0


def test_cli_sovereignty_check_error_exits_1(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("S=v\n", encoding="utf-8")
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path)])
    assert r.exit_code == 1


def test_cli_sovereignty_check_ok_exits_0(tmp_path: Path) -> None:
    _make_sovereign_project(tmp_path)
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path)])
    assert r.exit_code == 0
    assert "No issues found" in r.output


def test_cli_sovereignty_check_nonexistent_path_exits_1(
    tmp_path: Path,
) -> None:
    r = _runner.invoke(
        app,
        ["sovereignty", "check", "--path", str(tmp_path / "does_not_exist")],
    )
    assert r.exit_code == 1


# ---------------------------------------------------------------------------
# CLI — JSON output
# ---------------------------------------------------------------------------


def test_cli_sovereignty_check_json_valid(tmp_path: Path) -> None:
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path), "--json"])
    payload = json.loads(r.output)
    assert "path" in payload
    assert "status" in payload
    assert "findings" in payload
    assert isinstance(payload["findings"], list)


def test_cli_sovereignty_check_json_finding_fields(tmp_path: Path) -> None:
    (tmp_path / "vercel.json").write_text("{}", encoding="utf-8")
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path), "--json"])
    payload = json.loads(r.output)
    assert len(payload["findings"]) > 0
    finding = payload["findings"][0]
    assert "category" in finding
    assert "severity" in finding
    assert "message" in finding
    assert "location" in finding
    assert "recommendation" in finding


def test_cli_sovereignty_check_json_no_secret_values(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("API_KEY=ultra_secret\n", encoding="utf-8")
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path), "--json"])
    assert "ultra_secret" not in r.output


def test_cli_sovereignty_check_json_error_exits_1(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("S=v\n", encoding="utf-8")
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path), "--json"])
    payload = json.loads(r.output)
    assert payload["status"] == "ERROR"
    assert r.exit_code == 1


# ---------------------------------------------------------------------------
# Sprint 2N — New packages
# ---------------------------------------------------------------------------


def test_prisma_client_database_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@prisma/client": "^5.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("Prisma" in f.message for f in db)


def test_prisma_cli_database_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"devDependencies": {"prisma": "^5.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("Prisma" in f.message for f in db)


def test_drizzle_orm_database_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"drizzle-orm": "^0.29.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("Drizzle" in f.message for f in db)


def test_mongodb_database_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"mongodb": "^6.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("MongoDB" in f.message for f in db)


def test_next_auth_package_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"next-auth": "^4.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    auth = [f for f in result.findings if f.category == "auth"]
    assert any("NextAuth" in f.message for f in auth)


def test_stripe_payment_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"stripe": "^14.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    payment = [f for f in result.findings if f.category == "payment"]
    assert any("Stripe" in f.message for f in payment)


def test_resend_services_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"resend": "^2.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    services = [f for f in result.findings if f.category == "services"]
    assert any("Resend" in f.message for f in services)


def test_inngest_services_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"inngest": "^3.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    services = [f for f in result.findings if f.category == "services"]
    assert any("Inngest" in f.message for f in services)


def test_openai_sdk_ai_sdk_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"openai": "^4.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    ai_sdk = [f for f in result.findings if f.category == "ai_sdk"]
    assert any("OpenAI" in f.message for f in ai_sdk)


def test_anthropic_sdk_ai_sdk_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@anthropic-ai/sdk": "^0.20.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    ai_sdk = [f for f in result.findings if f.category == "ai_sdk"]
    assert any("Anthropic" in f.message for f in ai_sdk)


# ---------------------------------------------------------------------------
# Sprint 2N — New env vars
# ---------------------------------------------------------------------------


def test_vite_supabase_url_database_warning(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "VITE_SUPABASE_URL=https://x.supabase.co\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("VITE_SUPABASE_URL" in f.message for f in db)
    for f in result.findings:
        assert "https://x.supabase.co" not in f.message
        assert "https://x.supabase.co" not in f.recommendation
        assert "https://x.supabase.co" not in f.evidence


def test_next_public_supabase_url_database_warning(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "NEXT_PUBLIC_SUPABASE_URL=https://y.supabase.co\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("NEXT_PUBLIC_SUPABASE_URL" in f.message for f in db)


def test_direct_url_database_warning(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "DIRECT_URL=postgres://user:pass@host/db\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    db = [f for f in result.findings if f.category == "database"]
    assert any("DIRECT_URL" in f.message for f in db)
    for f in result.findings:
        assert "postgres://user:pass@host/db" not in f.message


def test_nextauth_secret_env_var(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "NEXTAUTH_SECRET=supersecret\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    secrets = [f for f in result.findings if f.category == "secrets"]
    assert any("NEXTAUTH_SECRET" in f.message for f in secrets)
    for f in result.findings:
        assert "supersecret" not in f.message
        assert "supersecret" not in f.recommendation


def test_stripe_secret_key_env_var(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "STRIPE_SECRET_KEY=sk_test_fake\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    secrets = [f for f in result.findings if f.category == "secrets"]
    assert any("STRIPE_SECRET_KEY" in f.message for f in secrets)
    for f in result.findings:
        assert "sk_test_fake" not in f.message


def test_openai_api_key_env_var(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("OPENAI_API_KEY=sk-fake\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    secrets = [f for f in result.findings if f.category == "secrets"]
    assert any("OPENAI_API_KEY" in f.message for f in secrets)
    for f in result.findings:
        assert "sk-fake" not in f.message


def test_anthropic_api_key_env_var(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "ANTHROPIC_API_KEY=sk-ant-fake\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    secrets = [f for f in result.findings if f.category == "secrets"]
    assert any("ANTHROPIC_API_KEY" in f.message for f in secrets)
    for f in result.findings:
        assert "sk-ant-fake" not in f.message


# ---------------------------------------------------------------------------
# Sprint 2N — New hosting files
# ---------------------------------------------------------------------------


def test_firebase_json_hosting_warning(tmp_path: Path) -> None:
    (tmp_path / "firebase.json").write_text("{}", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    hosting = [f for f in result.findings if f.category == "hosting"]
    assert any("Firebase" in f.message for f in hosting)


def test_supabase_config_toml_hosting_warning(tmp_path: Path) -> None:
    (tmp_path / "supabase").mkdir()
    (tmp_path / "supabase" / "config.toml").write_text(
        "[api]\nenabled = true\n", encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    hosting = [f for f in result.findings if f.category == "hosting"]
    assert any("Supabase" in f.message for f in hosting)


# ---------------------------------------------------------------------------
# Sprint 2N — Portability improvements
# ---------------------------------------------------------------------------


def test_compose_yml_accepted(tmp_path: Path) -> None:
    (tmp_path / "compose.yml").write_text("services:\n  app:\n", encoding="utf-8")
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert not any("docker-compose" in f.message for f in portability)


def test_prisma_migrations_accepted(tmp_path: Path) -> None:
    (tmp_path / "prisma" / "migrations").mkdir(parents=True)
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert not any("migrations" in f.message for f in portability)


def test_drizzle_dir_accepted(tmp_path: Path) -> None:
    (tmp_path / "drizzle").mkdir()
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert not any("migrations" in f.message for f in portability)


def test_package_json_without_dev_script_portability_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"build": "tsc"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert any("dev script" in f.message for f in portability)


def test_package_json_with_dev_script_no_warning(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"dev": "next dev", "build": "next build"}}),
        encoding="utf-8",
    )
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert not any("dev script" in f.message for f in portability)


def test_no_package_json_no_dev_script_warning(tmp_path: Path) -> None:
    result = run_sovereignty_check(tmp_path)
    portability = [f for f in result.findings if f.category == "portability"]
    assert not any("dev script" in f.message for f in portability)


# ---------------------------------------------------------------------------
# Sprint 2N — Source code scanning
# ---------------------------------------------------------------------------


def _make_source_file(tmp_path: Path, rel: str, content: str) -> None:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_supabase_import_in_source_detected(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/lib/supabase.ts",
        "import { createClient } from '@supabase/supabase-js'\n"
        "export const sb = createClient(process.env.URL!, process.env.KEY!)\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert any("Supabase" in f.message for f in scan)
    for f in result.findings:
        assert "process.env.URL" not in f.message
        assert "process.env.KEY" not in f.message
        assert "process.env.URL" not in f.evidence
        assert "process.env.KEY" not in f.evidence


def test_firebase_initializeapp_in_source_detected(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/lib/firebase.ts",
        "import { initializeApp } from 'firebase/app'\n"
        "const app = initializeApp(config)\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert any("Firebase" in f.message for f in scan)


def test_clerk_provider_in_source_detected(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "app/layout.tsx",
        "import { ClerkProvider } from '@clerk/nextjs'\n"
        "export default function RootLayout({ children }) {\n"
        "  return <ClerkProvider>{children}</ClerkProvider>\n"
        "}\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert any("Clerk" in f.message for f in scan)


def test_openai_sdk_in_source_detected(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "lib/ai.ts",
        "import OpenAI from 'openai'\nconst client = new OpenAI()\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert any("OpenAI" in f.message for f in scan)


def test_hardcoded_supabase_url_in_source_detected(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/config.ts",
        "const url = 'https://abc123.supabase.co'\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert any("Supabase" in f.message for f in scan)
    for f in result.findings:
        assert "abc123" not in f.message
        assert "abc123" not in f.evidence


def test_hardcoded_vercel_url_in_source_detected(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/config.ts",
        "const base = 'https://my-app.vercel.app'\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert any("Hosted deployment URL" in f.message for f in scan)
    for f in result.findings:
        assert "my-app" not in f.message
        assert "my-app" not in f.evidence


def test_node_modules_skipped(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "node_modules/@supabase/supabase-js/src/index.ts",
        "import { createClient } from '@supabase/supabase-js'\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert not any("Supabase" in f.message for f in scan)


def test_large_file_skipped(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    large = src / "big.ts"
    large.write_bytes(b"x" * (500 * 1024 + 1))
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert not any("big.ts" in f.location for f in scan)


def test_source_scan_deduplication(tmp_path: Path) -> None:
    for i in range(3):
        _make_source_file(
            tmp_path,
            f"src/lib/supabase{i}.ts",
            "import { createClient } from '@supabase/supabase-js'\n",
        )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    supabase_findings = [f for f in scan if "Supabase" in f.message]
    assert len(supabase_findings) == 1
    assert "3 file(s)" in supabase_findings[0].evidence


def test_no_secret_value_in_source_scan_findings(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/lib/client.ts",
        "const key = 'sk-real-secret-value'\n"
        "import OpenAI from 'openai'\n"
        "const client = new OpenAI({ apiKey: key })\n",
    )
    result = run_sovereignty_check(tmp_path)
    for f in result.findings:
        assert "sk-real-secret-value" not in f.message
        assert "sk-real-secret-value" not in f.recommendation
        assert "sk-real-secret-value" not in f.location
        assert "sk-real-secret-value" not in f.evidence


def test_evidence_field_present_for_source_scan(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/lib/supabase.ts",
        "import { createClient } from '@supabase/supabase-js'\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert len(scan) > 0
    for f in scan:
        assert f.evidence != ""
        assert "file(s)" in f.evidence


def test_evidence_empty_for_package_json_finding(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"stripe": "^14.0.0"}}), encoding="utf-8"
    )
    result = run_sovereignty_check(tmp_path)
    pkg_findings = [f for f in result.findings if f.location == "package.json"]
    assert len(pkg_findings) > 0
    for f in pkg_findings:
        assert f.evidence == ""


def test_evidence_field_in_json_output(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/lib/supabase.ts",
        "import { createClient } from '@supabase/supabase-js'\n",
    )
    r = _runner.invoke(app, ["sovereignty", "check", "--path", str(tmp_path), "--json"])
    payload = json.loads(r.output)
    for finding in payload["findings"]:
        assert "evidence" in finding


def test_source_scan_python_file(tmp_path: Path) -> None:
    _make_source_file(
        tmp_path,
        "src/ai_client.py",
        "from openai import OpenAI\nclient = OpenAI()\n",
    )
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert any("OpenAI" in f.message for f in scan)


def test_nonexistent_scan_dirs_skipped(tmp_path: Path) -> None:
    # project with no src/, app/, etc.
    result = run_sovereignty_check(tmp_path)
    scan = [f for f in result.findings if f.category == "source_scan"]
    assert scan == []
