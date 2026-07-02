"""CLI tests for aeos brain ask (CAP-2-D)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aeos.ai.config import AiConfig, AiFrontierConfig, AiLocalConfig
from aeos.ai.router import AiRouterError, AiRouterResponse
from aeos.brain.models import KnowledgeFact
from aeos.brain.store import BrainStore
from aeos.cli import app

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LOCAL_CONFIG = AiConfig(
    mode="local-first",
    frontier_allowed=False,
    require_human_approval=False,
    local=AiLocalConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        default_model="llama3.2",
    ),
    frontier=AiFrontierConfig(
        provider="openai-compatible",
        base_url_env="",
        api_key_env="",
        default_model_env="",
    ),
    source="test",
)

_AI_RESPONSE = AiRouterResponse(text="Test AI answer.", provider_used="local")


def _init_brain(tmp_path: Path, project: str = "test-proj") -> Path:
    brain_dir = tmp_path / "brain"
    with BrainStore.open(brain_dir, project):
        pass
    return brain_dir


def _ask(
    tmp_path: Path,
    project: str = "test-proj",
    question: str = "security risks",
    budget: int | None = None,
    as_json: bool = False,
    ai_response: AiRouterResponse = _AI_RESPONSE,
    ai_error: Exception | None = None,
) -> object:
    brain_dir = tmp_path / "brain"
    args = [
        "brain",
        "ask",
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

    with (
        patch("aeos.cli.read_ai_config", return_value=_LOCAL_CONFIG),
        patch("aeos.cli.ask_ai") as mock_ask,
    ):
        if ai_error is not None:
            mock_ask.side_effect = ai_error
        else:
            mock_ask.return_value = ai_response
        return runner.invoke(app, args)


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------


class TestBrainAskBasic:
    def test_exits_0_on_success(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path)
        assert result.exit_code == 0

    def test_exits_1_when_brain_missing(self, tmp_path: Path) -> None:
        result = _ask(tmp_path, project="ghost")
        assert result.exit_code == 1

    def test_error_message_names_project_when_missing(self, tmp_path: Path) -> None:
        result = _ask(tmp_path, project="no-such-project")
        combined = result.output + (result.stderr or "")
        assert "no-such-project" in combined

    def test_exits_1_when_ai_fails(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, ai_error=AiRouterError("Ollama unreachable"))
        assert result.exit_code == 1

    def test_error_output_on_ai_failure(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, ai_error=AiRouterError("Ollama unreachable"))
        combined = result.output + (result.stderr or "")
        assert "Ollama unreachable" in combined

    def test_output_contains_response_text(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        resp = AiRouterResponse(text="Here is my analysis.", provider_used="local")
        result = _ask(tmp_path, ai_response=resp)
        assert "Here is my analysis." in result.output

    def test_no_frontier_option_exposed(self) -> None:
        result = runner.invoke(app, ["brain", "ask", "--help"])
        assert "frontier" not in result.output.lower()

    def test_ask_always_uses_local_provider(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        with (
            patch("aeos.cli.read_ai_config", return_value=_LOCAL_CONFIG),
            patch("aeos.cli.ask_ai") as mock_ask,
        ):
            mock_ask.return_value = _AI_RESPONSE
            runner.invoke(
                app,
                [
                    "brain",
                    "ask",
                    "--project",
                    "test-proj",
                    "--question",
                    "risks",
                    "--brain-dir",
                    str(tmp_path / "brain"),
                ],
            )
            call_args = mock_ask.call_args
            positional_provider = (
                call_args[0][2] if len(call_args[0]) > 2 else None
            )
            kw_provider = call_args[1].get("provider") if call_args[1] else None
            assert positional_provider == "local" or kw_provider == "local"

    def test_truncated_warning_on_tiny_budget(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        # Insert a fact so the brain has content, then use a tiny budget
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            brain.insert_fact(
                KnowledgeFact(
                    id="f1",
                    fact_type="FINDING",
                    dimension="SECURITY",
                    summary="A security finding",
                    severity="HIGH",
                    created_at="2026-01-01T00:00:00+00:00",
                )
            )
        result = _ask(tmp_path, budget=1)
        # truncated warning goes to stderr; check combined output
        combined = result.output + (result.stderr or "")
        assert "truncated" in combined.lower()


# ---------------------------------------------------------------------------
# Interaction log
# ---------------------------------------------------------------------------


class TestBrainAskInteractionLog:
    def test_interaction_logged_after_success(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        _ask(tmp_path)
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            status = brain.get_status()
        assert status.interactions_count == 1

    def test_interaction_not_logged_on_ai_failure(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        _ask(tmp_path, ai_error=AiRouterError("unreachable"))
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            status = brain.get_status()
        assert status.interactions_count == 0

    def test_each_success_logs_one_interaction(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        _ask(tmp_path, question="question one")
        _ask(tmp_path, question="question two")
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            status = brain.get_status()
        assert status.interactions_count == 2

    def test_interaction_stores_correct_provider(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        _ask(tmp_path)
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            rows = brain._conn.execute(
                "SELECT provider FROM interaction_log LIMIT 1"
            ).fetchone()
        assert rows is not None
        assert rows[0] == "local"

    def test_interaction_stores_question(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        _ask(tmp_path, question="What is the architecture?")
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            rows = brain._conn.execute(
                "SELECT question FROM interaction_log LIMIT 1"
            ).fetchone()
        assert rows is not None
        assert rows[0] == "What is the architecture?"

    def test_interaction_not_logged_when_brain_missing(self, tmp_path: Path) -> None:
        _ask(tmp_path, project="ghost")
        # Brain doesn't even exist — just verifying no crash
        brain_dir = tmp_path / "brain"
        assert not (brain_dir / "ghost.db").exists()


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


class TestBrainAskJson:
    def test_json_output_is_valid_json(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, as_json=True)
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_json_contains_response(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        resp = AiRouterResponse(text="My detailed answer.", provider_used="local")
        result = _ask(tmp_path, as_json=True, ai_response=resp)
        parsed = json.loads(result.output)
        assert parsed["response"] == "My detailed answer."

    def test_json_contains_brain_version(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert "brain_version" in parsed
        assert isinstance(parsed["brain_version"], str)
        assert len(parsed["brain_version"]) > 0

    def test_json_contains_provider_used(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert parsed["provider_used"] == "local"

    def test_json_contains_truncated_flag(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert "truncated" in parsed
        assert isinstance(parsed["truncated"], bool)

    def test_json_contains_dimensions(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert "dimensions" in parsed
        assert isinstance(parsed["dimensions"], list)

    def test_json_contains_question(self, tmp_path: Path) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, question="architecture overview", as_json=True)
        parsed = json.loads(result.output)
        assert parsed["question"] == "architecture overview"

    @pytest.mark.parametrize(
        "key",
        ["question", "brain_version", "dimensions", "provider_used", "model",
         "truncated", "response"],
    )
    def test_json_all_required_keys_present(self, tmp_path: Path, key: str) -> None:
        _init_brain(tmp_path)
        result = _ask(tmp_path, as_json=True)
        parsed = json.loads(result.output)
        assert key in parsed
