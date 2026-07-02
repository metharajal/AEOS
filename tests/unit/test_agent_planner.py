"""Unit tests for aeos.agent.planner."""

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

_PROJ = {
    "name": "my-proj",
    "type": "recovered-project",
    "memory_dir": "",  # overridden per test
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


def _write_memory_record(
    memory_dir: Path,
    project_name: str,
    critical: int = 0,
    important: int = 0,
) -> None:
    proj_dir = memory_dir / project_name
    proj_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "record_id": "test-record",
        "created_at": "2026-01-01T00:00:00Z",
        "project_path": str(memory_dir.parent),
        "project_name": project_name,
        "rail": "reclaim",
        "command": "reclaim harden",
        "status": "OK",
        "generator": None,
        "providers": [],
        "control_level": "controlled",
        "read_only": True,
        "applied": False,
        "findings_summary": {
            "critical": critical,
            "important": important,
            "manual": 0,
            "generated": 0,
        },
        "remediation_summary": None,
        "strategic_options": [],
        "human_validated": False,
    }
    (proj_dir / "test-record.json").write_text(json.dumps(record))


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# generate_plan — library
# ---------------------------------------------------------------------------


class TestGeneratePlan:
    def test_no_registry(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "missing.json"
        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")

        assert plan.global_status == "ERROR"
        assert plan.projects == []
        assert any("Registry not found" in r for r in plan.risks)
        assert any("workspace init" in a for a in plan.suggested_actions)

    def test_no_projects(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        _write_registry(reg, [])

        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")

        assert plan.global_status == "WARNING"
        assert plan.projects == []
        assert any("project register" in a for a in plan.suggested_actions)

    def test_unknown_project_filter(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        _write_registry(reg, [])

        plan = generate_plan(
            registry_path=reg,
            project_filter="nonexistent",
            workspace_dir=tmp_path / "ws",
        )

        assert plan.global_status == "ERROR"
        assert any("not found in registry" in r for r in plan.risks)

    def test_project_memory_dir_missing_is_error(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        proj = dict(_PROJ)
        proj["memory_dir"] = str(tmp_path / "nonexistent" / "memory")
        _write_registry(reg, [proj])

        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")

        assert plan.global_status == "ERROR"
        assert plan.projects[0].status == "ERROR"
        assert not plan.projects[0].memory_dir_exists

    def test_project_no_records_is_warning(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        proj = dict(_PROJ)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")

        assert plan.projects[0].status == "WARNING"
        assert plan.projects[0].record_count == 0

    def test_project_with_critical_findings(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        _write_memory_record(mem, "my-proj", critical=3, important=0)
        proj = dict(_PROJ)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")

        entry = plan.projects[0]
        assert entry.critical == 3
        assert entry.status == "WARNING"
        assert any("critical" in r for r in entry.risks)

    def test_project_with_important_findings(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        _write_memory_record(mem, "my-proj", critical=0, important=5)
        proj = dict(_PROJ)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")

        entry = plan.projects[0]
        assert entry.important == 5
        assert entry.status == "WARNING"

    def test_project_all_ok_no_workspace(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        _write_memory_record(mem, "my-proj")
        proj = dict(_PROJ)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        ws = tmp_path / "ws"  # no index.html
        plan = generate_plan(registry_path=reg, workspace_dir=ws)

        assert plan.projects[0].status == "OK"
        assert plan.global_status == "WARNING"
        assert not plan.workspace_index_exists
        assert any("workspace demo" in a for a in plan.suggested_actions)

    def test_project_fully_ok(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        _write_memory_record(mem, "my-proj")
        proj = dict(_PROJ)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "index.html").write_text("<html/>")

        plan = generate_plan(registry_path=reg, workspace_dir=ws)

        assert plan.projects[0].status == "OK"
        assert plan.global_status == "OK"
        assert plan.workspace_index_exists

    def test_evidence_dir_missing_is_warning(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        _write_memory_record(mem, "my-proj")
        proj = dict(_PROJ)
        proj["memory_dir"] = str(mem)
        proj["evidence_dir"] = str(tmp_path / "evidence-missing")
        _write_registry(reg, [proj])

        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")

        entry = plan.projects[0]
        assert entry.evidence_dir_exists is False
        assert entry.status == "WARNING"

    def test_project_filter_selects_correct(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan

        reg = tmp_path / "projects.json"
        mem_a = tmp_path / "memory-a"
        mem_b = tmp_path / "memory-b"
        _write_memory_record(mem_a, "proj-a")
        _write_memory_record(mem_b, "proj-b")

        proj_a = dict(_PROJ)
        proj_a["name"] = "proj-a"
        proj_a["memory_dir"] = str(mem_a)
        proj_b = dict(_PROJ)
        proj_b["name"] = "proj-b"
        proj_b["memory_dir"] = str(mem_b)
        _write_registry(reg, [proj_a, proj_b])

        plan = generate_plan(
            registry_path=reg,
            project_filter="proj-a",
            workspace_dir=tmp_path / "ws",
        )

        assert len(plan.projects) == 1
        assert plan.projects[0].name == "proj-a"


# ---------------------------------------------------------------------------
# Markdown and JSON renderers
# ---------------------------------------------------------------------------


class TestRenderers:
    def test_markdown_contains_required_sections(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan, render_plan_markdown

        reg = tmp_path / "projects.json"
        _write_registry(reg, [])
        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")
        md = render_plan_markdown(plan)

        assert "# AEOS Agent Plan" in md
        assert "deterministic read-only planner" in md
        assert "read_only: true" in md
        assert "human validation required" in md

    def test_json_is_valid(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_plan, render_plan_json

        reg = tmp_path / "projects.json"
        _write_registry(reg, [])
        plan = generate_plan(registry_path=reg, workspace_dir=tmp_path / "ws")
        data = json.loads(render_plan_json(plan))

        assert data["agent_mode"] == "deterministic read-only planner"
        assert data["applied"] is False
        assert data["read_only"] is True
        assert "global_status" in data


# ---------------------------------------------------------------------------
# CLI — agent plan
# ---------------------------------------------------------------------------


class TestCliAgentPlan:
    def test_no_registry_exits_1(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        missing = tmp_path / "nope.json"
        with patch.object(reg_mod, "DEFAULT_REGISTRY", missing):
            result = runner.invoke(app, ["agent", "plan"])

        assert result.exit_code == 1
        assert "read_only: true" in result.output

    def test_warning_exits_0(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        reg = tmp_path / "projects.json"
        _write_registry(reg, [])

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(app, ["agent", "plan"])

        assert result.exit_code == 0
        assert "WARNING" in result.output

    def test_ok_exits_0(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod
        import aeos.workspace.ux as ux_mod

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        _write_memory_record(mem, "my-proj")
        proj = dict(_PROJ)
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "index.html").write_text("<html/>")

        with (
            patch.object(reg_mod, "DEFAULT_REGISTRY", reg),
            patch.object(ux_mod, "DEFAULT_WORKSPACE_DIR", ws),
        ):
            result = runner.invoke(app, ["agent", "plan"])

        assert result.exit_code == 0
        assert "OK" in result.output

    def test_json_flag_produces_json(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        reg = tmp_path / "projects.json"
        _write_registry(reg, [])

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(app, ["agent", "plan", "--json"])

        data = json.loads(result.output)
        assert "global_status" in data
        assert data["read_only"] is True

    def test_output_flag_writes_file(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        reg = tmp_path / "projects.json"
        _write_registry(reg, [])
        out = tmp_path / "plan.md"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(app, ["agent", "plan", "--output", str(out)])

        assert out.exists()
        content = out.read_text()
        assert "# AEOS Agent Plan" in content
        assert "Plan written to:" in result.output

    def test_project_flag_filters(self, runner: CliRunner, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        reg = tmp_path / "projects.json"
        mem = tmp_path / "memory"
        _write_memory_record(mem, "proj-a")
        proj = dict(_PROJ)
        proj["name"] = "proj-a"
        proj["memory_dir"] = str(mem)
        _write_registry(reg, [proj])

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(app, ["agent", "plan", "--project", "proj-a"])

        assert result.exit_code == 0
        assert "proj-a" in result.output
