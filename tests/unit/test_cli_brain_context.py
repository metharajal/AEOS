"""CLI tests for aeos brain context (CAP-2-C)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.brain.models import KnowledgeFact
from aeos.brain.store import BrainStore
from aeos.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_brain(tmp_path: Path, project: str = "test-proj") -> Path:
    brain_dir = tmp_path / "brain"
    with BrainStore.open(brain_dir, project):
        pass
    return brain_dir


def _context(
    tmp_path: Path,
    project: str = "test-proj",
    question: str = "security risks",
    budget: int | None = None,
    as_json: bool = False,
) -> object:
    brain_dir = tmp_path / "brain"
    args = [
        "brain",
        "context",
        "--project",
        project,
        "--question",
        question,
        "--brain-dir",
        str(brain_dir),
    ]
    if budget is not None:
        args += ["--budget", str(budget)]
    if as_json:
        args += ["--json"]
    return runner.invoke(app, args)


# ---------------------------------------------------------------------------
# Basic execution
# ---------------------------------------------------------------------------


class TestBrainContextBasic:
    def test_exits_0_with_valid_brain(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path)
        assert result.exit_code == 0

    def test_exits_1_when_brain_missing(self, tmp_path: Path) -> None:
        result = _context(tmp_path, project="ghost")
        assert result.exit_code == 1

    def test_error_mentions_project_when_missing(self, tmp_path: Path) -> None:
        result = _context(tmp_path, project="missing-brain")
        combined = result.output + (result.stderr or "")
        assert "missing-brain" in combined

    def test_output_shows_project_name(self, tmp_path: Path) -> None:
        _init_brain(tmp_path, "my-project")
        result = _context(tmp_path, project="my-project")
        assert "my-project" in result.output

    def test_output_shows_brain_version(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path)
        assert "Brain version" in result.output

    def test_output_shows_dimensions(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, question="security risks")
        assert "Dimensions" in result.output
        assert "SECURITY" in result.output

    def test_output_shows_facts_count(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path)
        assert "Facts selected" in result.output

    def test_output_shows_truncated_status(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path)
        assert "Truncated" in result.output

    def test_output_shows_sovereign_marker(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path)
        assert "sovereign" in result.output.lower()

    def test_output_shows_no_ai_called(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path)
        assert "no AI called" in result.output


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


class TestBrainContextJson:
    def test_json_flag_outputs_valid_json(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, as_json=True)
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_json_output_contains_facts_key(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert "facts" in parsed

    def test_json_output_contains_brain_version(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert "brain_version" in parsed

    def test_json_output_contains_dimensions(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert "dimensions" in parsed
        assert isinstance(parsed["dimensions"], list)

    def test_json_output_contains_question(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, question="security risks", as_json=True)
        parsed = json.loads(result.output)
        assert parsed["question"] == "security risks"

    def test_json_output_excludes_project_path(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            from aeos.brain.models import ProjectIdentity

            brain.upsert_identity(
                ProjectIdentity(
                    project_name="test-proj",
                    project_path="/secret/internal/path/test-proj",
                )
            )
        result = _context(tmp_path, as_json=True)
        assert result.exit_code == 0
        output = result.output
        assert "/secret/internal/path/test-proj" not in output
        parsed = json.loads(output)
        identity = parsed.get("project_identity")
        assert identity is not None
        assert "project_path" not in identity


# ---------------------------------------------------------------------------
# Budget flag and fact presence
# ---------------------------------------------------------------------------


class TestBrainContextBudget:
    def test_budget_flag_accepted(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, budget=2000)
        assert result.exit_code == 0

    def test_budget_reflected_in_output(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _context(tmp_path, budget=1234)
        assert "1234" in result.output

    def test_facts_appear_in_output_when_present(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            brain.insert_fact(
                KnowledgeFact(
                    id="test-fact",
                    fact_type="FINDING",
                    dimension="SECURITY",
                    summary="Test security finding",
                    severity="HIGH",
                    created_at="2026-01-15T10:00:00+00:00",
                )
            )
        result = _context(tmp_path, question="security risks")
        assert "Test security finding" in result.output
