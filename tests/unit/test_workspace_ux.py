"""Unit tests for aeos.workspace.ux — workspace_status and workspace_open."""

from __future__ import annotations

import webbrowser
from pathlib import Path
from unittest.mock import MagicMock, patch

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
# workspace_status — library
# ---------------------------------------------------------------------------


class TestWorkspaceStatus:
    def test_no_registry(self, tmp_path: Path) -> None:
        from aeos.workspace.ux import workspace_status

        fake_registry = tmp_path / "missing.json"
        result = workspace_status(fake_registry, tmp_path / "ws")

        assert result.registry_exists is False
        assert result.project_count == 0
        assert result.index_exists is False
        assert "aeos project register" in result.suggested_command

    def test_registry_exists_no_projects(self, tmp_path: Path) -> None:
        import json

        from aeos.workspace.ux import workspace_status

        reg_path = tmp_path / "projects.json"
        reg_path.write_text(json.dumps({"projects": []}))

        result = workspace_status(reg_path, tmp_path / "ws")

        assert result.registry_exists is True
        assert result.project_count == 0
        assert "aeos project register" in result.suggested_command

    def test_registry_exists_with_projects_no_index(self, tmp_path: Path) -> None:
        import json

        from aeos.workspace.ux import workspace_status

        reg_path = tmp_path / "projects.json"
        reg_path.write_text(
            json.dumps(
                {
                    "projects": [
                        {
                            "name": "test-proj",
                            "memory_dir": str(tmp_path / "memory"),
                            "evidence_dir": None,
                            "project_type": "recovered-project",
                            "registered_at": "2026-01-01T00:00:00Z",
                            "last_seen": "2026-01-01T00:00:00Z",
                            "local_only": True,
                            "read_only": True,
                        }
                    ]
                }
            )
        )

        ws_dir = tmp_path / "ws"
        result = workspace_status(reg_path, ws_dir)

        assert result.registry_exists is True
        assert result.project_count == 1
        assert result.index_exists is False
        assert "aeos workspace demo" in result.suggested_command

    def test_registry_and_index_both_exist(self, tmp_path: Path) -> None:
        import json

        from aeos.workspace.ux import workspace_status

        reg_path = tmp_path / "projects.json"
        reg_path.write_text(
            json.dumps(
                {
                    "projects": [
                        {
                            "name": "test-proj",
                            "memory_dir": str(tmp_path / "memory"),
                            "evidence_dir": None,
                            "project_type": "recovered-project",
                            "registered_at": "2026-01-01T00:00:00Z",
                            "last_seen": "2026-01-01T00:00:00Z",
                            "local_only": True,
                            "read_only": True,
                        }
                    ]
                }
            )
        )

        ws_dir = tmp_path / "ws"
        ws_dir.mkdir()
        (ws_dir / "index.html").write_text("<html></html>")

        result = workspace_status(reg_path, ws_dir)

        assert result.registry_exists is True
        assert result.project_count == 1
        assert result.index_exists is True
        assert "open" in result.suggested_command
        assert "index.html" in result.suggested_command


# ---------------------------------------------------------------------------
# workspace_open — library
# ---------------------------------------------------------------------------


class TestWorkspaceOpen:
    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        from aeos.workspace.ux import workspace_open

        missing = tmp_path / "nonexistent" / "index.html"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            workspace_open(missing)

    def test_calls_webbrowser_open(self, tmp_path: Path) -> None:
        from aeos.workspace.ux import workspace_open

        index = tmp_path / "index.html"
        index.write_text("<html></html>")

        mock_open = MagicMock(return_value=True)
        with patch.object(webbrowser, "open", mock_open):
            result = workspace_open(index)

        assert result is True
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        assert url.startswith("file://")
        assert "index.html" in url


# ---------------------------------------------------------------------------
# CLI — workspace status
# ---------------------------------------------------------------------------


class TestCliWorkspaceStatus:
    def test_no_registry(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        fake_registry = tmp_path / "missing.json"
        ws_dir = tmp_path / "ws"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", fake_registry):
            result = runner.invoke(
                app,
                ["workspace", "status", "--output-dir", str(ws_dir)],
            )

        assert result.exit_code == 0
        assert "Registry exists:   no" in result.output
        assert "aeos project register" in result.output
        assert "read_only: true" in result.output

    def test_registry_with_project_no_index(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        import json

        import aeos.project.registry as reg_mod

        reg_path = tmp_path / "projects.json"
        reg_path.write_text(
            json.dumps(
                {
                    "projects": [
                        {
                            "name": "my-proj",
                            "memory_dir": str(tmp_path / "memory"),
                            "evidence_dir": None,
                            "project_type": "recovered-project",
                            "registered_at": "2026-01-01T00:00:00Z",
                            "last_seen": "2026-01-01T00:00:00Z",
                            "local_only": True,
                            "read_only": True,
                        }
                    ]
                }
            )
        )
        ws_dir = tmp_path / "ws"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg_path):
            result = runner.invoke(
                app,
                ["workspace", "status", "--output-dir", str(ws_dir)],
            )

        assert result.exit_code == 0
        assert "Registry exists:   yes" in result.output
        assert "1 project" in result.output
        assert "aeos workspace demo" in result.output
        assert "read_only: true" in result.output

    def test_full_workspace_ready(self, runner: CliRunner, tmp_path: Path) -> None:
        import json

        import aeos.project.registry as reg_mod

        reg_path = tmp_path / "projects.json"
        reg_path.write_text(
            json.dumps(
                {
                    "projects": [
                        {
                            "name": "my-proj",
                            "memory_dir": str(tmp_path / "memory"),
                            "evidence_dir": None,
                            "project_type": "recovered-project",
                            "registered_at": "2026-01-01T00:00:00Z",
                            "last_seen": "2026-01-01T00:00:00Z",
                            "local_only": True,
                            "read_only": True,
                        }
                    ]
                }
            )
        )
        ws_dir = tmp_path / "ws"
        ws_dir.mkdir()
        (ws_dir / "index.html").write_text("<html></html>")

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg_path):
            result = runner.invoke(
                app,
                ["workspace", "status", "--output-dir", str(ws_dir)],
            )

        assert result.exit_code == 0
        assert "index.html exists: yes" in result.output
        assert "read_only: true" in result.output


# ---------------------------------------------------------------------------
# CLI — workspace open
# ---------------------------------------------------------------------------


class TestCliWorkspaceOpen:
    def test_missing_file_exits_1(self, runner: CliRunner, tmp_path: Path) -> None:
        missing = tmp_path / "no-ws" / "index.html"
        result = runner.invoke(app, ["workspace", "open", "--path", str(missing)])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_opens_existing_file(self, runner: CliRunner, tmp_path: Path) -> None:
        index = tmp_path / "index.html"
        index.write_text("<html></html>")

        mock_open = MagicMock(return_value=True)
        with patch.object(webbrowser, "open", mock_open):
            result = runner.invoke(app, ["workspace", "open", "--path", str(index)])

        assert result.exit_code == 0
        assert "Opening:" in result.output
        assert "read_only: true" in result.output
        mock_open.assert_called_once()
