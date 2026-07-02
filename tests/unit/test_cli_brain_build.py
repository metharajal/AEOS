"""CLI tests for aeos brain build (CAP-2-B)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.brain.store import BrainStore
from aeos.cli import app
from aeos.memory.models import MemoryRecord

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    record_id: str = "rec-001",
    project_name: str = "test-proj",
    findings_summary: dict[str, int] | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        created_at="2026-01-15T10:00:00+00:00",
        project_path="/nonexistent/test-proj",
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status="OK",
        generator=None,
        providers=[],
        control_level="controlled",
        read_only=True,
        applied=False,
        findings_summary=findings_summary or {},
        remediation_summary=None,
        strategic_options=[],
        human_validated=False,
    )


def _write_record_json(
    memory_dir: Path, project_name: str, record: MemoryRecord
) -> None:
    project_dir = memory_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "record_id": record.record_id,
        "created_at": record.created_at,
        "project_path": record.project_path,
        "project_name": record.project_name,
        "rail": record.rail,
        "command": record.command,
        "status": record.status,
        "generator": record.generator,
        "providers": record.providers,
        "control_level": record.control_level,
        "read_only": record.read_only,
        "applied": record.applied,
        "findings_summary": record.findings_summary,
        "remediation_summary": record.remediation_summary,
        "strategic_options": record.strategic_options,
        "human_validated": record.human_validated,
    }
    (project_dir / f"{record.record_id}.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def _build(
    tmp_path: Path,
    project: str = "test-proj",
    memory_dir: Path | None = None,
) -> object:
    brain_dir = tmp_path / "brain"
    mem_dir = memory_dir or (tmp_path / "memory")
    return runner.invoke(
        app,
        [
            "brain",
            "build",
            "--project",
            project,
            "--brain-dir",
            str(brain_dir),
            "--memory-dir",
            str(mem_dir),
        ],
    )


def _init_with_record(tmp_path: Path, project: str = "test-proj") -> None:
    memory_dir = tmp_path / "memory"
    record = _make_record(project_name=project)
    _write_record_json(memory_dir, project, record)


# ---------------------------------------------------------------------------
# brain build — basic execution
# ---------------------------------------------------------------------------


class TestBrainBuildBasic:
    def test_exits_0_when_memory_dir_exists(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        result = _build(tmp_path)
        assert result.exit_code == 0

    def test_exits_1_when_project_memory_missing(self, tmp_path: Path) -> None:
        result = _build(tmp_path, project="ghost")
        assert result.exit_code == 1

    def test_error_output_mentions_project_name(self, tmp_path: Path) -> None:
        result = _build(tmp_path, project="missing-project")
        combined = result.output + (result.stderr or "")
        assert "missing-project" in combined

    def test_error_output_mentions_memory_directory(self, tmp_path: Path) -> None:
        result = _build(tmp_path, project="ghost")
        combined = result.output + (result.stderr or "")
        assert "memory" in combined.lower()

    def test_exits_0_with_empty_project_memory_dir(self, tmp_path: Path) -> None:
        (tmp_path / "memory" / "test-proj").mkdir(parents=True)
        result = _build(tmp_path)
        assert result.exit_code == 0

    def test_output_shows_project_name(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        result = _build(tmp_path)
        assert "test-proj" in result.output

    def test_output_shows_records_processed(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        result = _build(tmp_path)
        assert (
            "Records processed" in result.output
            or "records" in result.output.lower()
        )

    def test_output_shows_facts_counts(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        result = _build(tmp_path)
        assert "facts" in result.output.lower() or "Facts" in result.output

    def test_output_shows_sovereign_marker(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        result = _build(tmp_path)
        assert "sovereign" in result.output.lower()


# ---------------------------------------------------------------------------
# brain build — Brain state after build
# ---------------------------------------------------------------------------


class TestBrainBuildState:
    def test_brain_has_facts_after_build(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        _build(tmp_path)
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            assert brain.get_status().facts_count > 0

    def test_brain_auto_initialized_if_not_pre_init(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        brain_dir = tmp_path / "brain"
        assert not BrainStore.exists(brain_dir, "test-proj")
        _build(tmp_path)
        assert BrainStore.exists(brain_dir, "test-proj")

    def test_build_is_idempotent_cli(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        result1 = _build(tmp_path)
        result2 = _build(tmp_path)
        assert result1.exit_code == 0
        assert result2.exit_code == 0

    def test_idempotent_facts_count_stable(self, tmp_path: Path) -> None:
        _init_with_record(tmp_path)
        _build(tmp_path)
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            count_after_first = brain.get_status().facts_count
        _build(tmp_path)
        with BrainStore.open(brain_dir, "test-proj") as brain:
            count_after_second = brain.get_status().facts_count
        assert count_after_first == count_after_second

    def test_facts_count_reflects_critical_finding(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / "memory"
        record = _make_record(findings_summary={"critical": 2})
        _write_record_json(memory_dir, "test-proj", record)
        _build(tmp_path)
        brain_dir = tmp_path / "brain"
        with BrainStore.open(brain_dir, "test-proj") as brain:
            security_facts = [
                f
                for f in brain.get_facts(dimension="SECURITY")
                if f.severity == "CRITICAL"
            ]
        assert len(security_facts) == 1
