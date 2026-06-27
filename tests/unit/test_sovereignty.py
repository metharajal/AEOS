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
