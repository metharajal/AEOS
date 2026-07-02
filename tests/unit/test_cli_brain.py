"""CLI tests for aeos brain init and aeos brain status (CAP-2-A)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aeos.brain.store import BrainStore
from aeos.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init(tmp_path: Path, project: str = "test-proj") -> object:
    brain_dir = tmp_path / "brain"
    return runner.invoke(
        app,
        ["brain", "init", "--project", project, "--brain-dir", str(brain_dir)],
    )


def _status(tmp_path: Path, project: str = "test-proj") -> object:
    brain_dir = tmp_path / "brain"
    return runner.invoke(
        app,
        ["brain", "status", "--project", project, "--brain-dir", str(brain_dir)],
    )


# ---------------------------------------------------------------------------
# brain init
# ---------------------------------------------------------------------------


class TestBrainInit:
    def test_exits_0(self, tmp_path: Path) -> None:
        result = _init(tmp_path)
        assert result.exit_code == 0

    def test_creates_db_file(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        runner.invoke(
            app,
            ["brain", "init", "--project", "proj", "--brain-dir", str(brain_dir)],
        )
        assert (brain_dir / "proj.db").exists()

    def test_output_mentions_project(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        result = runner.invoke(
            app,
            ["brain", "init", "--project", "my-project", "--brain-dir", str(brain_dir)],
        )
        assert "my-project" in result.output

    def test_output_shows_db_path(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        result = runner.invoke(
            app,
            ["brain", "init", "--project", "proj", "--brain-dir", str(brain_dir)],
        )
        assert "proj.db" in result.output

    def test_creates_brain_dir_if_missing(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "deeply" / "nested" / "brain"
        result = runner.invoke(
            app,
            ["brain", "init", "--project", "proj", "--brain-dir", str(brain_dir)],
        )
        assert result.exit_code == 0
        assert brain_dir.is_dir()

    def test_idempotent_second_init_exits_0(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _init(tmp_path)
        assert result.exit_code == 0

    def test_idempotent_output_mentions_already_exists(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _init(tmp_path)
        output = result.output.lower()
        assert "already" in output or "exists" in output

    def test_db_file_valid_after_init(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        runner.invoke(
            app,
            ["brain", "init", "--project", "proj", "--brain-dir", str(brain_dir)],
        )
        assert BrainStore.exists(brain_dir, "proj")
        with BrainStore.open(brain_dir, "proj") as store:
            assert store.get_status().schema_version == 1


# ---------------------------------------------------------------------------
# brain status
# ---------------------------------------------------------------------------


class TestBrainStatus:
    def test_exits_0_on_initialized_brain(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert result.exit_code == 0

    def test_exits_1_on_missing_brain(self, tmp_path: Path) -> None:
        result = _status(tmp_path, project="ghost")
        assert result.exit_code == 1

    def test_shows_project_name(self, tmp_path: Path) -> None:
        brain_dir = tmp_path / "brain"
        runner.invoke(
            app,
            ["brain", "init", "--project", "my-proj", "--brain-dir", str(brain_dir)],
        )
        result = runner.invoke(
            app,
            ["brain", "status", "--project", "my-proj", "--brain-dir", str(brain_dir)],
        )
        assert "my-proj" in result.output

    def test_shows_schema_version(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "Schema version" in result.output
        assert "1" in result.output

    def test_shows_brain_version(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert (
            "Brain version" in result.output or "brain_version" in result.output.lower()
        )

    def test_shows_facts_label(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "Facts" in result.output

    def test_shows_decisions_label(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "Decisions" in result.output

    def test_shows_vocabulary_label(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "Vocabulary" in result.output

    def test_shows_sovereign_marker(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "sovereign" in result.output.lower()

    def test_shows_offline_marker(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "offline" in result.output.lower()

    def test_missing_brain_error_mentions_project(self, tmp_path: Path) -> None:
        result = _status(tmp_path, project="nonexistent-project")
        combined = result.output + (result.stderr or "")
        assert "nonexistent-project" in combined

    def test_missing_brain_error_suggests_init(self, tmp_path: Path) -> None:
        result = _status(tmp_path, project="ghost")
        combined = result.output + (result.stderr or "")
        assert "init" in combined.lower()

    def test_empty_brain_shows_no_facts_yet(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "no facts yet" in result.output.lower() or "0" in result.output

    def test_status_shows_db_path(self, tmp_path: Path) -> None:
        _init(tmp_path)
        result = _status(tmp_path)
        assert "Path" in result.output
        assert ".db" in result.output
