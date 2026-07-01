"""Unit tests for aeos.workspace.doctor."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aeos.cli import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROJECT = {
    "name": "my-proj",
    "type": "recovered-project",
    "memory_dir": "",  # filled per test
    "evidence_dir": None,
    "registered_at": "2026-01-01T00:00:00Z",
    "last_seen_at": "2026-01-01T00:00:00Z",
    "local_only": True,
    "read_only": True,
}


def _write_registry(reg_path: Path, projects: list[dict[str, object]]) -> None:
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-01-01T00:00:00Z",
                "local_only": True,
                "read_only": True,
                "projects": projects,
            }
        )
    )


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# workspace_doctor — library
# ---------------------------------------------------------------------------


class TestWorkspaceDoctor:
    def test_no_home_no_registry(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        reg = tmp_path / "missing" / "projects.json"
        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["AEOS home"] == "ERROR"
        assert statuses["Registry"] == "ERROR"
        assert result.overall_status == "ERROR"
        assert result.suggested_command == "aeos workspace init"

    def test_home_exists_no_registry(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        home.mkdir()
        reg = home / "projects.json"

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["AEOS home"] == "OK"
        assert statuses["Registry"] == "ERROR"
        assert result.overall_status == "ERROR"

    def test_corrupt_registry(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        home.mkdir()
        reg = home / "projects.json"
        reg.write_text("NOT JSON{{{{")

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["Registry readable"] == "ERROR"
        assert result.overall_status == "ERROR"

    def test_empty_registry_warns(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        _write_registry(reg, [])

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["Registry readable"] == "OK"
        assert statuses["Projects registered"] == "WARNING"
        assert result.overall_status == "WARNING"

    def test_project_memory_dir_missing(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(tmp_path / "nonexistent" / "memory")
        _write_registry(reg, [proj])

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["[my-proj] memory_dir"] == "ERROR"
        assert result.overall_status == "ERROR"

    def test_project_memory_dir_exists(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["[my-proj] memory_dir"] == "OK"

    def test_evidence_dir_missing_is_warning(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        proj["evidence_dir"] = str(tmp_path / "evidence-missing")
        _write_registry(reg, [proj])

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["[my-proj] evidence_dir"] == "WARNING"

    def test_evidence_dir_exists_ok(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        ev = tmp_path / "evidence"
        ev.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        proj["evidence_dir"] = str(ev)
        _write_registry(reg, [proj])

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["[my-proj] evidence_dir"] == "OK"

    def test_workspace_index_present_gives_ok(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "index.html").write_text("<html/>")

        result = workspace_doctor(registry_path=reg, workspace_dir=ws)

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["Workspace index"] == "OK"
        assert result.overall_status == "OK"

    def test_workspace_index_missing_is_warning(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        result = workspace_doctor(registry_path=reg, workspace_dir=tmp_path / "no-ws")

        statuses = {c.name: c.status for c in result.checks}
        assert statuses["Workspace index"] == "WARNING"

    def test_suggested_command_no_index(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        ws = tmp_path / "ws"
        result = workspace_doctor(registry_path=reg, workspace_dir=ws)

        assert "aeos workspace demo" in result.suggested_command

    def test_suggested_command_all_ok(self, tmp_path: Path) -> None:
        from aeos.workspace.doctor import workspace_doctor

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "index.html").write_text("<html/>")

        result = workspace_doctor(registry_path=reg, workspace_dir=ws)

        assert "aeos workspace open" in result.suggested_command


# ---------------------------------------------------------------------------
# CLI — workspace doctor
# ---------------------------------------------------------------------------


class TestCliWorkspaceDoctor:
    def test_error_exits_1(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        missing_reg = tmp_path / "nope" / "projects.json"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", missing_reg):
            result = runner.invoke(
                app,
                ["workspace", "doctor", "--output-dir", str(tmp_path / "ws")],
            )

        assert result.exit_code == 1
        assert "[ERROR]" in result.output
        assert "read_only: true" in result.output

    def test_warning_exits_0(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        _write_registry(reg, [])

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app,
                ["workspace", "doctor", "--output-dir", str(tmp_path / "ws")],
            )

        assert result.exit_code == 0
        assert "WARNING" in result.output
        assert "read_only: true" in result.output

    def test_ok_exits_0(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJECT)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "index.html").write_text("<html/>")

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app,
                ["workspace", "doctor", "--output-dir", str(ws)],
            )

        assert result.exit_code == 0
        assert "Overall:           OK" in result.output
        assert "[OK]" in result.output
        assert "read_only: true" in result.output

    def test_output_contains_all_sections(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        import aeos.project.registry as reg_mod

        home = tmp_path / ".aeos"
        reg = home / "projects.json"
        _write_registry(reg, [])

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app,
                ["workspace", "doctor", "--output-dir", str(tmp_path / "ws")],
            )

        assert "AEOS Workspace Doctor" in result.output
        assert "Overall:" in result.output
        assert "Suggested next:" in result.output
