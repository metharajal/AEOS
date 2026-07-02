"""Tests for MVP-AGENTS-3: Agent Recommendations in workspace/evidence-pack."""

from __future__ import annotations

from pathlib import Path

from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record


def _make_record(
    project_name: str = "test-proj",
    critical: int = 2,
    important: int = 5,
    manual: int = 1,
    generated: int = 3,
    record_suffix: str = "aa001100",
) -> MemoryRecord:
    return MemoryRecord(
        record_id=f"{project_name}-20260630T110000-{record_suffix}",
        created_at="2026-06-30T11:00:00",
        project_path=f"/private/tmp/{project_name}",
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status="ERROR",
        generator="lovable",
        providers=["supabase"],
        control_level="weak",
        read_only=True,
        applied=False,
        findings_summary={
            "critical": critical,
            "important": important,
            "manual": manual,
            "generated": generated,
        },
        remediation_summary=None,
        strategic_options=[],
        human_validated=False,
        notes=None,
    )


def _write(tmp_path: Path, record: MemoryRecord) -> Path:
    return save_record(record, tmp_path)


# ---------------------------------------------------------------------------
# generate_project_entry
# ---------------------------------------------------------------------------


class TestGenerateProjectEntry:
    def test_memory_dir_missing_is_error(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_project_entry

        entry = generate_project_entry(name="proj", memory_dir=tmp_path / "nonexistent")
        assert entry.status == "ERROR"
        assert not entry.memory_dir_exists
        assert entry.record_count == 0

    def test_no_records_is_warning(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_project_entry

        mem = tmp_path / "memory"
        mem.mkdir()
        entry = generate_project_entry(name="proj", memory_dir=mem)
        assert entry.status == "WARNING"
        assert entry.record_count == 0
        assert any("No MemoryRecords" in r for r in entry.risks)

    def test_critical_findings_is_warning(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_project_entry

        mem = tmp_path / "memory"
        _write(mem, _make_record("proj", critical=3))
        entry = generate_project_entry(name="proj", memory_dir=mem)
        assert entry.status == "WARNING"
        assert entry.critical == 3
        assert any("critical" in r for r in entry.risks)

    def test_ok_project(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_project_entry

        mem = tmp_path / "memory"
        rec = _make_record("proj", critical=0, important=0, manual=0, generated=0)
        _write(mem, rec)
        entry = generate_project_entry(name="proj", memory_dir=mem)
        assert entry.status == "OK"
        assert entry.memory_dir_exists
        assert entry.record_count == 1

    def test_custom_project_type(self, tmp_path: Path) -> None:
        from aeos.agent.planner import generate_project_entry

        mem = tmp_path / "memory"
        mem.mkdir()
        entry = generate_project_entry(
            name="proj", memory_dir=mem, project_type="greenfield"
        )
        assert entry.project_type == "greenfield"

    def test_exported_from_package(self) -> None:
        from aeos.agent import generate_project_entry  # noqa: F401


# ---------------------------------------------------------------------------
# Project Workspace — Agent Recommendations section in HTML
# ---------------------------------------------------------------------------


class TestWorkspaceAgentRecommendations:
    def test_workspace_data_has_agent_plan_entry(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")
        assert data.agent_plan_entry is not None

    def test_workspace_data_agent_entry_status_is_warning(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=2, important=5))
        data = load_workspace_data(mem, "test-proj")
        assert data.agent_plan_entry is not None
        assert data.agent_plan_entry.status == "WARNING"

    def test_workspace_html_contains_agent_recommendations_section(
        self, tmp_path: Path
    ) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")
        html = render_workspace(data)
        assert "Agent Recommendations" in html

    def test_workspace_html_shows_planner_mode(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")
        html = render_workspace(data)
        assert "deterministic read-only planner" in html

    def test_workspace_html_shows_read_only_applied_false(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")
        html = render_workspace(data)
        assert "read_only: true" in html
        assert "applied: false" in html

    def test_workspace_html_shows_human_validation_required(
        self, tmp_path: Path
    ) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")
        html = render_workspace(data)
        assert "human validation required" in html

    def test_workspace_html_shows_risk_text(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))
        data = load_workspace_data(mem, "test-proj")
        html = render_workspace(data)
        assert "critical" in html.lower()


# ---------------------------------------------------------------------------
# Evidence Pack — agent-plan.md
# ---------------------------------------------------------------------------


class TestEvidencePackAgentPlan:
    def test_pack_files_includes_agent_plan(self) -> None:
        from aeos.ui.evidence_pack import _PACK_FILES

        assert "agent-plan.md" in _PACK_FILES

    def test_generate_evidence_pack_creates_agent_plan(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"

        generate_evidence_pack(mem, "test-proj", out)
        assert (out / "agent-plan.md").exists()

    def test_agent_plan_md_contains_aeos_header(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"
        generate_evidence_pack(mem, "test-proj", out)
        content = (out / "agent-plan.md").read_text()
        assert "# AEOS Agent Plan" in content

    def test_agent_plan_md_shows_read_only(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"
        generate_evidence_pack(mem, "test-proj", out)
        content = (out / "agent-plan.md").read_text()
        assert "read_only: true" in content

    def test_agent_plan_md_shows_applied_false(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"
        generate_evidence_pack(mem, "test-proj", out)
        content = (out / "agent-plan.md").read_text()
        assert "applied: false" in content

    def test_agent_plan_md_shows_planner_mode(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"
        generate_evidence_pack(mem, "test-proj", out)
        content = (out / "agent-plan.md").read_text()
        assert "deterministic read-only planner" in content

    def test_render_agent_plan_md_no_entry(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import render_agent_plan_md
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")
        data.agent_plan_entry = None
        md = render_agent_plan_md(data)
        assert "read_only: true" in md

    def test_index_html_lists_agent_plan(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"
        generate_evidence_pack(mem, "test-proj", out)
        index = (out / "index.html").read_text()
        assert "agent-plan.md" in index


# ---------------------------------------------------------------------------
# Workspace Demo — agent-plan.md generated per project
# ---------------------------------------------------------------------------


class TestWorkspaceDemoAgentPlan:
    def _register(self, tmp_path: Path, name: str, mem: Path) -> Path:
        from aeos.project.registry import ProjectRegistration, register_project

        reg = tmp_path / "reg.json"
        registration = ProjectRegistration(
            name=name,
            project_type="recovered-project",
            memory_dir=mem,
        )
        register_project(registration, reg)
        return reg

    def test_demo_generates_agent_plan_in_evidence_pack(self, tmp_path: Path) -> None:
        from aeos.workspace.demo import generate_workspace_demo

        mem = tmp_path / "memory"
        _write(mem, _make_record("proj-a"))
        reg = self._register(tmp_path, "proj-a", mem)

        out = tmp_path / "ws"
        generate_workspace_demo(reg, out, overwrite=True)

        agent_plan = out / "proj-a" / "evidence-pack" / "agent-plan.md"
        assert agent_plan.exists()

    def test_demo_agent_plan_content(self, tmp_path: Path) -> None:
        from aeos.workspace.demo import generate_workspace_demo

        mem = tmp_path / "memory"
        _write(mem, _make_record("proj-a"))
        reg = self._register(tmp_path, "proj-a", mem)

        out = tmp_path / "ws"
        generate_workspace_demo(reg, out, overwrite=True)

        content = (out / "proj-a" / "evidence-pack" / "agent-plan.md").read_text()
        assert "# AEOS Agent Plan" in content
        assert "deterministic read-only planner" in content
        assert "read_only: true" in content

    def test_demo_project_workspace_html_has_agent_section(
        self, tmp_path: Path
    ) -> None:
        from aeos.workspace.demo import generate_workspace_demo

        mem = tmp_path / "memory"
        _write(mem, _make_record("proj-a"))
        reg = self._register(tmp_path, "proj-a", mem)

        out = tmp_path / "ws"
        generate_workspace_demo(reg, out, overwrite=True)

        ws_html = (out / "proj-a" / "project-workspace.html").read_text()
        assert "Agent Recommendations" in ws_html
        assert "deterministic read-only planner" in ws_html


# ---------------------------------------------------------------------------
# Safety invariants — no mutation, no network, no LLM
# ---------------------------------------------------------------------------


class TestAgentRecommendationsSafety:
    def test_generate_project_entry_does_not_modify_memory_dir(
        self, tmp_path: Path
    ) -> None:
        from aeos.agent.planner import generate_project_entry

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        files_before = set(mem.rglob("*"))
        generate_project_entry(name="test-proj", memory_dir=mem)
        files_after = set(mem.rglob("*"))
        assert files_before == files_after

    def test_load_workspace_data_does_not_modify_memory_dir(
        self, tmp_path: Path
    ) -> None:
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        files_before = set(mem.rglob("*"))
        load_workspace_data(mem, "test-proj")
        files_after = set(mem.rglob("*"))
        assert files_before == files_after

    def test_agent_plan_entry_always_read_only(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")
        assert data.agent_plan_entry is not None

    def test_render_agent_plan_md_does_not_call_network(self, tmp_path: Path) -> None:
        import socket

        from aeos.ui.evidence_pack import render_agent_plan_md
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        data = load_workspace_data(mem, "test-proj")

        original_connect = socket.socket.connect

        def _no_connect(*_args: object, **_kw: object) -> None:
            raise AssertionError("Network call detected in render_agent_plan_md!")

        socket.socket.connect = _no_connect  # type: ignore[method-assign]
        try:
            render_agent_plan_md(data)
        finally:
            socket.socket.connect = original_connect  # type: ignore[method-assign]
