"""
Unit tests for aeos build plan.

Covers:
- create_build_plan: valid type+stack combinations, unknown type, unknown stack
- build_plan_to_dict: read_only, applied, governance_files
- CLI: text output sections, JSON output, unknown type/stack, no files created,
  no secrets in output
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.build.planner import BuildPlan, build_plan_to_dict, create_build_plan
from aeos.cli import app

runner = CliRunner()

# ---------------------------------------------------------------------------
# create_build_plan — valid combinations
# ---------------------------------------------------------------------------


def test_build_plan_web_app_nextjs_supabase() -> None:
    plan = create_build_plan("civic-portal", "web-app", "nextjs-supabase")
    assert isinstance(plan, BuildPlan)
    assert plan.project_name == "civic-portal"
    assert plan.project_type == "web-app"
    assert plan.stack == "nextjs-supabase"
    assert plan.read_only is True
    assert plan.applied is False
    assert plan.architecture_summary != ""
    assert len(plan.folder_structure) > 0
    assert len(plan.security_baseline) > 0
    assert len(plan.sovereignty_baseline) > 0


def test_build_plan_api_fastapi_postgres() -> None:
    plan = create_build_plan("my-api", "api", "fastapi-postgres")
    assert isinstance(plan, BuildPlan)
    assert plan.project_type == "api"
    assert plan.stack == "fastapi-postgres"
    assert "FastAPI" in plan.architecture_summary
    assert any("integration" in t.lower() for t in plan.testing_baseline)


def test_build_plan_internal_tool_generic() -> None:
    plan = create_build_plan("ops-dashboard", "internal-tool", "generic")
    assert isinstance(plan, BuildPlan)
    assert plan.project_type == "internal-tool"
    assert plan.stack == "generic"
    assert plan.governance_files == [
        "README.md",
        "ARCHITECTURE.md",
        ".env.example",
        ".gitignore",
        "docs/DECISIONS.md",
    ]


# ---------------------------------------------------------------------------
# create_build_plan — validation errors
# ---------------------------------------------------------------------------


def test_build_plan_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="Unknown project type"):
        create_build_plan("my-proj", "mobile-app", "generic")


def test_build_plan_unknown_stack_raises() -> None:
    with pytest.raises(ValueError, match="Unknown stack"):
        create_build_plan("my-proj", "web-app", "rails-postgres")


# ---------------------------------------------------------------------------
# CLI — text output sections
# ---------------------------------------------------------------------------


def test_cli_text_output_contains_build_plan() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "web-app",
            "--stack",
            "nextjs-supabase",
        ],
    )
    assert result.exit_code == 0
    assert "Build Plan" in result.output


def test_cli_text_output_contains_project_identity() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "web-app",
            "--stack",
            "nextjs-supabase",
        ],
    )
    assert result.exit_code == 0
    assert "Project Identity" in result.output
    assert "my-app" in result.output


def test_cli_text_output_contains_security_baseline() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "api",
            "--stack",
            "fastapi-postgres",
        ],
    )
    assert result.exit_code == 0
    assert "Security Baseline" in result.output


def test_cli_text_output_contains_sovereignty_baseline() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "internal-tool",
            "--stack",
            "generic",
        ],
    )
    assert result.exit_code == 0
    assert "Sovereignty Baseline" in result.output


# ---------------------------------------------------------------------------
# CLI — JSON output
# ---------------------------------------------------------------------------


def test_cli_json_output_valid() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "civic-portal",
            "--type",
            "web-app",
            "--stack",
            "nextjs-supabase",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["project_name"] == "civic-portal"
    assert payload["command"] == "build plan"
    assert "architecture_summary" in payload
    assert "folder_structure" in payload
    assert "recommended_next_steps" in payload


def test_cli_json_contains_read_only_true() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "api",
            "--stack",
            "fastapi-postgres",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["read_only"] is True


def test_cli_json_contains_applied_false() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "api",
            "--stack",
            "fastapi-postgres",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["applied"] is False


def test_cli_json_contains_governance_files() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "web-app",
            "--stack",
            "generic",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    gov = payload["governance_files"]
    assert isinstance(gov, list)
    assert "README.md" in gov
    assert "ARCHITECTURE.md" in gov
    assert ".env.example" in gov
    assert ".gitignore" in gov
    assert "docs/DECISIONS.md" in gov


# ---------------------------------------------------------------------------
# CLI — no secrets in output
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "sk_live_supersecret",
    "A" * 64,
]


def test_cli_json_no_secrets() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "web-app",
            "--stack",
            "nextjs-supabase",
            "--json",
        ],
    )
    assert result.exit_code == 0
    for secret in _SECRET_PATTERNS:
        assert secret not in result.output


# ---------------------------------------------------------------------------
# CLI — no project files created
# ---------------------------------------------------------------------------


def test_cli_does_not_create_project_files(tmp_path: Path) -> None:
    runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "should-not-be-created",
            "--type",
            "web-app",
            "--stack",
            "nextjs-supabase",
        ],
    )
    assert not (tmp_path / "should-not-be-created").exists()
    assert not Path("should-not-be-created").exists()


# ---------------------------------------------------------------------------
# CLI — error cases
# ---------------------------------------------------------------------------


def test_cli_unknown_type_error() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "mobile-app",
            "--stack",
            "generic",
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_unknown_stack_error() -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "plan",
            "--name",
            "my-app",
            "--type",
            "web-app",
            "--stack",
            "rails-postgres",
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# build_plan_to_dict
# ---------------------------------------------------------------------------


def test_build_plan_to_dict_structure() -> None:
    plan = create_build_plan("test-proj", "api", "fastapi-postgres")
    d = build_plan_to_dict(plan)
    required_keys = {
        "command",
        "read_only",
        "applied",
        "project_name",
        "project_type",
        "stack",
        "architecture_summary",
        "folder_structure",
        "governance_files",
        "security_baseline",
        "sovereignty_baseline",
        "testing_baseline",
        "deployment_baseline",
        "recommended_next_steps",
    }
    assert required_keys.issubset(d.keys())
    assert d["command"] == "build plan"
    assert d["read_only"] is True
    assert d["applied"] is False
