"""Unit tests for aeos.workspace.init — workspace_init and CLI workspace init."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aeos.cli import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# workspace_init — library
# ---------------------------------------------------------------------------


class TestWorkspaceInit:
    def test_creates_home_and_registry(self, tmp_path: Path) -> None:
        from aeos.workspace.init import workspace_init

        home = tmp_path / ".aeos"
        reg = home / "projects.json"

        result = workspace_init(aeos_home=home, registry_path=reg)

        assert home.exists()
        assert reg.exists()
        assert result.initialized is True
        assert result.project_count == 0
        assert result.aeos_home == home
        assert result.registry_path == reg

    def test_registry_content_is_valid_json(self, tmp_path: Path) -> None:
        from aeos.workspace.init import workspace_init

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        workspace_init(aeos_home=home, registry_path=reg)

        data = json.loads(reg.read_text())
        assert data["projects"] == []
        assert data["local_only"] is True
        assert data["read_only"] is True

    def test_idempotent_existing_registry_not_overwritten(self, tmp_path: Path) -> None:
        from aeos.workspace.init import workspace_init

        home = tmp_path / ".aeos"
        reg = home / "projects.json"

        # First call — creates registry
        workspace_init(aeos_home=home, registry_path=reg)
        mtime_after_first = reg.stat().st_mtime

        # Second call — must not touch the file
        result = workspace_init(aeos_home=home, registry_path=reg)
        mtime_after_second = reg.stat().st_mtime

        assert result.initialized is False
        assert mtime_after_first == mtime_after_second

    def test_idempotent_home_already_exists(self, tmp_path: Path) -> None:
        from aeos.workspace.init import workspace_init

        home = tmp_path / ".aeos"
        home.mkdir(parents=True)
        reg = home / "projects.json"

        result = workspace_init(aeos_home=home, registry_path=reg)

        assert home.exists()
        assert result.initialized is True  # registry was still absent

    def test_existing_registry_with_projects(self, tmp_path: Path) -> None:
        from aeos.workspace.init import workspace_init

        home = tmp_path / ".aeos"
        home.mkdir(parents=True)
        reg = home / "projects.json"
        reg.write_text(
            json.dumps(
                {
                    "updated_at": "2026-01-01T00:00:00Z",
                    "local_only": True,
                    "read_only": True,
                    "projects": [
                        {
                            "name": "my-proj",
                            "type": "recovered-project",
                            "memory_dir": str(tmp_path / "memory"),
                            "evidence_dir": None,
                            "registered_at": "2026-01-01T00:00:00Z",
                            "last_seen_at": "2026-01-01T00:00:00Z",
                            "local_only": True,
                            "read_only": True,
                        }
                    ],
                }
            )
        )

        result = workspace_init(aeos_home=home, registry_path=reg)

        assert result.initialized is False
        assert result.project_count == 1
        assert result.suggested_command == "aeos workspace status"

    def test_suggested_command_no_projects(self, tmp_path: Path) -> None:
        from aeos.workspace.init import workspace_init

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        result = workspace_init(aeos_home=home, registry_path=reg)

        assert "aeos project register" in result.suggested_command

    def test_suggested_command_with_projects(self, tmp_path: Path) -> None:
        from aeos.workspace.init import workspace_init

        home = tmp_path / ".aeos"
        home.mkdir(parents=True)
        reg = home / "projects.json"
        reg.write_text(
            json.dumps(
                {
                    "updated_at": "2026-01-01T00:00:00Z",
                    "local_only": True,
                    "read_only": True,
                    "projects": [
                        {
                            "name": "p",
                            "type": "recovered-project",
                            "memory_dir": str(tmp_path / "memory"),
                            "evidence_dir": None,
                            "registered_at": "2026-01-01T00:00:00Z",
                            "last_seen_at": "2026-01-01T00:00:00Z",
                            "local_only": True,
                            "read_only": True,
                        }
                    ],
                }
            )
        )

        result = workspace_init(aeos_home=home, registry_path=reg)

        assert result.suggested_command == "aeos workspace status"


# ---------------------------------------------------------------------------
# CLI — workspace init
# ---------------------------------------------------------------------------


class TestCliWorkspaceInit:
    def test_fresh_init(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.workspace.init as init_mod
        from aeos.workspace.init import WorkspaceInitResult

        home = tmp_path / ".aeos"
        reg = home / "projects.json"

        def _fake_init(**_: object) -> WorkspaceInitResult:
            home.mkdir(parents=True, exist_ok=True)
            return WorkspaceInitResult(
                aeos_home=home,
                registry_path=reg,
                initialized=True,
                project_count=0,
                suggested_command=(
                    "aeos project register --name <project> --memory-dir <path>/memory"
                ),
            )

        with patch.object(init_mod, "workspace_init", _fake_init):
            result = runner.invoke(app, ["workspace", "init"])

        assert result.exit_code == 0
        assert "Initialized:       yes" in result.output
        assert "0 projects" in result.output
        assert "aeos project register" in result.output
        assert "read_only: true" in result.output

    def test_already_exists(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.workspace.init as init_mod
        from aeos.workspace.init import WorkspaceInitResult

        home = tmp_path / ".aeos"
        reg = home / "projects.json"

        def _fake_init(**_: object) -> WorkspaceInitResult:
            return WorkspaceInitResult(
                aeos_home=home,
                registry_path=reg,
                initialized=False,
                project_count=2,
                suggested_command="aeos workspace status",
            )

        with patch.object(init_mod, "workspace_init", _fake_init):
            result = runner.invoke(app, ["workspace", "init"])

        assert result.exit_code == 0
        assert "no (already existed)" in result.output
        assert "2 projects" in result.output
        assert "aeos workspace status" in result.output
        assert "read_only: true" in result.output

    def test_singular_project_noun(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.workspace.init as init_mod
        from aeos.workspace.init import WorkspaceInitResult

        home = tmp_path / ".aeos"
        reg = home / "projects.json"

        def _fake_init(**_: object) -> WorkspaceInitResult:
            return WorkspaceInitResult(
                aeos_home=home,
                registry_path=reg,
                initialized=False,
                project_count=1,
                suggested_command="aeos workspace status",
            )

        with patch.object(init_mod, "workspace_init", _fake_init):
            result = runner.invoke(app, ["workspace", "init"])

        assert result.exit_code == 0
        assert "1 project" in result.output
        assert "1 projects" not in result.output
