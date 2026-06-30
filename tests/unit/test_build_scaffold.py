"""
Unit tests for aeos build scaffold.

Covers:
- scaffold_build_project: valid combinations, non-empty output without force,
  force flag, unknown type/stack
- File content: .env.example no secrets, .gitignore protects .env,
  aeos.toml has local_first = true
- CLI: text output, JSON output, error cases
- Safety: no files written outside output directory
- All tests use tmp_path fixture
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.build.scaffold import BuildScaffoldResult, scaffold_build_project
from aeos.cli import app

runner = CliRunner()

_EXPECTED_FILES = [
    "README.md",
    "ARCHITECTURE.md",
    ".env.example",
    ".gitignore",
    "aeos.toml",
    "docs/DECISIONS.md",
    "docs/SECURITY.md",
    "docs/SOVEREIGNTY.md",
]

# ---------------------------------------------------------------------------
# scaffold_build_project — valid combinations
# ---------------------------------------------------------------------------


def test_scaffold_web_app_nextjs_supabase_creates_files(tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = scaffold_build_project(
        "civic-portal", "web-app", "nextjs-supabase", output
    )
    assert isinstance(result, BuildScaffoldResult)
    assert result.project_name == "civic-portal"
    assert result.applied is True
    assert result.read_only is False
    for rel in _EXPECTED_FILES:
        assert (output / rel).exists(), f"Missing: {rel}"
    assert set(result.files_created) == set(_EXPECTED_FILES)


def test_scaffold_api_fastapi_postgres_creates_files(tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = scaffold_build_project("my-api", "api", "fastapi-postgres", output)
    assert isinstance(result, BuildScaffoldResult)
    assert result.stack == "fastapi-postgres"
    for rel in _EXPECTED_FILES:
        assert (output / rel).exists(), f"Missing: {rel}"
    assert len(result.files_created) == len(_EXPECTED_FILES)


def test_scaffold_internal_tool_generic_creates_files(tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = scaffold_build_project("ops-dash", "internal-tool", "generic", output)
    assert isinstance(result, BuildScaffoldResult)
    assert result.project_type == "internal-tool"
    for rel in _EXPECTED_FILES:
        assert (output / rel).exists(), f"Missing: {rel}"


# ---------------------------------------------------------------------------
# ensure_safe_output_directory
# ---------------------------------------------------------------------------


def test_scaffold_refuses_nonempty_output_without_force(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "existing.txt").write_text("existing content")

    with pytest.raises(ValueError, match="not empty"):
        scaffold_build_project("my-proj", "web-app", "generic", output, force=False)


def test_scaffold_force_overwrites_nonempty_output(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "existing.txt").write_text("existing content")

    result = scaffold_build_project("my-proj", "web-app", "generic", output, force=True)
    assert result.applied is True
    assert (output / "README.md").exists()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_scaffold_unknown_type_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown project type"):
        scaffold_build_project("proj", "mobile-app", "generic", tmp_path / "out")


def test_scaffold_unknown_stack_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown stack"):
        scaffold_build_project("proj", "web-app", "rails-postgres", tmp_path / "out")


# ---------------------------------------------------------------------------
# File content checks
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "sk_live_supersecret",
    "A" * 64,
]


def test_env_example_no_secrets(tmp_path: Path) -> None:
    output = tmp_path / "output"
    scaffold_build_project("proj", "web-app", "nextjs-supabase", output)
    content = (output / ".env.example").read_text()
    for secret in _SECRET_PATTERNS:
        assert secret not in content, f"Secret pattern found in .env.example: {secret}"


def test_gitignore_protects_env(tmp_path: Path) -> None:
    output = tmp_path / "output"
    scaffold_build_project("proj", "api", "fastapi-postgres", output)
    content = (output / ".gitignore").read_text()
    assert ".env" in content
    assert ".env.*" in content
    assert "!.env.example" in content


def test_aeos_toml_contains_local_first_true(tmp_path: Path) -> None:
    output = tmp_path / "output"
    scaffold_build_project("proj", "internal-tool", "generic", output)
    content = (output / "aeos.toml").read_text()
    assert "local_first = true" in content
    assert "human_approval_required = true" in content
    assert "read_only_generated = false" in content


# ---------------------------------------------------------------------------
# CLI — JSON output
# ---------------------------------------------------------------------------


def test_cli_json_output_valid(tmp_path: Path) -> None:
    output = tmp_path / "scaffold"
    result = runner.invoke(
        app,
        [
            "build",
            "scaffold",
            "--name",
            "civic-portal",
            "--type",
            "web-app",
            "--stack",
            "nextjs-supabase",
            "--output",
            str(output),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["project_name"] == "civic-portal"
    assert payload["command"] == "build scaffold"
    assert "files_created" in payload
    assert "safety_guarantees" in payload
    assert "recommended_next_steps" in payload


def test_cli_json_contains_applied_true(tmp_path: Path) -> None:
    output = tmp_path / "scaffold"
    result = runner.invoke(
        app,
        [
            "build",
            "scaffold",
            "--name",
            "my-app",
            "--type",
            "api",
            "--stack",
            "fastapi-postgres",
            "--output",
            str(output),
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["applied"] is True


def test_cli_json_contains_read_only_false(tmp_path: Path) -> None:
    output = tmp_path / "scaffold"
    result = runner.invoke(
        app,
        [
            "build",
            "scaffold",
            "--name",
            "my-app",
            "--type",
            "api",
            "--stack",
            "fastapi-postgres",
            "--output",
            str(output),
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["read_only"] is False


# ---------------------------------------------------------------------------
# CLI — text output
# ---------------------------------------------------------------------------


def test_cli_text_output_contains_files_created(tmp_path: Path) -> None:
    output = tmp_path / "scaffold"
    result = runner.invoke(
        app,
        [
            "build",
            "scaffold",
            "--name",
            "my-app",
            "--type",
            "web-app",
            "--stack",
            "nextjs-supabase",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Build Scaffold" in result.output
    assert "Files Created" in result.output
    assert "README.md" in result.output
    assert "aeos.toml" in result.output
    assert "Safety Guarantees" in result.output


# ---------------------------------------------------------------------------
# Safety — no files written outside output
# ---------------------------------------------------------------------------


def test_scaffold_writes_only_inside_output(tmp_path: Path) -> None:
    output = tmp_path / "project-output"
    scaffold_build_project("proj", "web-app", "nextjs-supabase", output)
    for f in tmp_path.rglob("*"):
        if f.is_file():
            assert str(f).startswith(str(output)), (
                f"File {f} is outside output directory {output}"
            )


# ---------------------------------------------------------------------------
# Docs subdirectory created
# ---------------------------------------------------------------------------


def test_scaffold_creates_docs_files(tmp_path: Path) -> None:
    output = tmp_path / "output"
    scaffold_build_project("proj", "internal-tool", "generic", output)
    assert (output / "docs" / "DECISIONS.md").exists()
    assert (output / "docs" / "SECURITY.md").exists()
    assert (output / "docs" / "SOVEREIGNTY.md").exists()
    content = (output / "docs" / "DECISIONS.md").read_text()
    assert "ADR-NNN" in content
