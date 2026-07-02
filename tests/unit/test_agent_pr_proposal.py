"""Unit tests for aeos.agent.pr_proposal and the `aeos agent pr-proposal` CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aeos.cli import app

if TYPE_CHECKING:
    from aeos.agent.pr_proposal import PRProposal
from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record
from aeos.project.registry import ProjectRegistration, register_project

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    project_name: str = "test-proj",
    critical: int = 3,
    important: int = 59,
    manual: int = 15,
    generated: int = 25,
    control_level: str = "weak",
    providers: list[str] | None = None,
    record_suffix: str = "aa001100",
) -> MemoryRecord:
    if providers is None:
        providers = ["supabase"]
    return MemoryRecord(
        record_id=f"{project_name}-20260702T080000-{record_suffix}",
        created_at="2026-07-02T08:00:00",
        project_path=f"/private/tmp/{project_name}",
        project_name=project_name,
        rail="reclaim",
        command="reclaim harden",
        status="ERROR",
        generator="lovable",
        providers=providers,
        control_level=control_level,
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


def _register(tmp_path: Path, name: str, mem: Path) -> Path:
    reg = tmp_path / "reg.json"
    registration = ProjectRegistration(
        name=name,
        project_type="recovered-project",
        memory_dir=mem,
    )
    register_project(registration, reg)
    return reg


# ---------------------------------------------------------------------------
# generate_pr_proposal — library
# ---------------------------------------------------------------------------


class TestGeneratePrProposal:
    def test_registry_missing_raises(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        with pytest.raises(FileNotFoundError, match="Registry not found"):
            generate_pr_proposal("proj", registry_path=tmp_path / "nope.json")

    def test_project_not_found_raises(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        reg = tmp_path / "reg.json"
        mem = tmp_path / "memory"
        mem.mkdir()
        _register(tmp_path, "other-proj", mem)

        with pytest.raises(ValueError, match="not found in registry"):
            generate_pr_proposal("unknown", registry_path=reg)

    def test_proposal_has_all_sections(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert proposal.title
        assert proposal.objective
        assert proposal.why_now
        assert proposal.recommended_scope
        assert proposal.out_of_scope
        assert proposal.likely_files
        assert proposal.safety_constraints
        assert proposal.implementation_steps
        assert proposal.validation_commands
        assert proposal.approval_checklist
        assert proposal.risks
        assert proposal.rollback_notes
        assert proposal.evidence_references

    def test_critical_findings_drive_title(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert "security" in proposal.title
        assert "critical" in proposal.title

    def test_generated_sql_blocks_in_title_when_no_critical(
        self, tmp_path: Path
    ) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=0, important=0, generated=10))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert "SQL" in proposal.title or "staging" in proposal.title

    def test_ok_project_gets_docs_title(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        rec = _make_record(
            critical=0, important=0, manual=0, generated=0, control_level="strong"
        )
        _write(mem, rec)
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert "docs" in proposal.title or "release" in proposal.title.lower()

    def test_why_now_mentions_critical(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("critical" in r for r in proposal.why_now)

    def test_why_now_mentions_generated_sql(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(generated=25))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("SQL" in r or "block" in r for r in proposal.why_now)

    def test_scope_includes_staging_when_sql_blocks(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(generated=10, critical=0))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("staging" in s.lower() for s in proposal.recommended_scope)

    def test_out_of_scope_always_excludes_production(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("production" in s.lower() for s in proposal.out_of_scope)

    def test_supabase_appears_in_likely_files(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(providers=["supabase"]))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("supabase" in f.lower() for f in proposal.likely_files)

    def test_safety_constraints_present(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("secret" in s.lower() for s in proposal.safety_constraints)
        assert any("production" in s.lower() for s in proposal.safety_constraints)

    def test_implementation_steps_are_numbered(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert proposal.implementation_steps[0].startswith("1.")

    def test_impl_steps_reference_project_name(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(project_name="test-proj"))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        all_steps = " ".join(proposal.implementation_steps)
        assert "test-proj" in all_steps

    def test_validation_commands_include_git_status(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("git status" in c for c in proposal.validation_commands)

    def test_validation_commands_include_aeos_agent_plan(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("aeos agent plan" in c for c in proposal.validation_commands)

    def test_checklist_no_production_item(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("production" in c.lower() for c in proposal.approval_checklist)

    def test_checklist_no_secrets_item(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert any("secret" in c.lower() for c in proposal.approval_checklist)

    def test_evidence_references_populated(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3, important=59, manual=15, generated=25))
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        ev = proposal.evidence_references
        assert ev["record_count"] == 1
        assert ev["critical"] == 3
        assert ev["important"] == 59
        assert ev["generated_sql_blocks"] == 25
        assert ev["latest_record_id"] is not None

    def test_read_only_and_applied_invariants(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert proposal.read_only is True
        assert proposal.applied is False
        assert proposal.human_validation_required is True

    def test_final_statement_present(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert "No changes were applied" in proposal.final_statement
        assert "proposal only" in proposal.final_statement

    def test_no_records_still_produces_proposal(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        mem.mkdir()
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert proposal.title
        assert proposal.evidence_references["record_count"] == 0

    def test_exported_from_package(self) -> None:
        from aeos.agent import PRProposal, generate_pr_proposal  # noqa: F401


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


class TestRenderers:
    def _proposal(self, tmp_path: Path) -> PRProposal:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)
        return generate_pr_proposal("test-proj", registry_path=reg)

    def test_markdown_contains_all_section_headers(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_markdown

        proposal = self._proposal(tmp_path)
        md = render_pr_proposal_markdown(proposal)

        for header in [
            "# AEOS PR Proposal",
            "## 1. Title",
            "## 2. Objective",
            "## 3. Why This PR Now",
            "## 4. Recommended Scope",
            "## 5. Out of Scope",
            "## 6. Likely Files Involved",
            "## 7. Safety Constraints",
            "## 8. Suggested Implementation Steps",
            "## 9. Validation Commands",
            "## 10. Human Approval Checklist",
            "## 11. Risks",
            "## 12. Rollback Notes",
            "## 13. Evidence References",
            "## 14. Final Statement",
        ]:
            assert header in md, f"Missing section: {header}"

    def test_markdown_contains_read_only_statement(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_markdown

        proposal = self._proposal(tmp_path)
        md = render_pr_proposal_markdown(proposal)
        assert "read_only: true" in md
        assert "applied: false" in md

    def test_markdown_contains_final_statement(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_markdown

        proposal = self._proposal(tmp_path)
        md = render_pr_proposal_markdown(proposal)
        assert "No changes were applied" in md

    def test_json_is_valid(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_json

        proposal = self._proposal(tmp_path)
        data = json.loads(render_pr_proposal_json(proposal))

        assert data["read_only"] is True
        assert data["applied"] is False
        assert data["human_validation_required"] is True
        assert "title" in data
        assert "why_now" in data
        assert "approval_checklist" in data

    def test_json_evidence_references(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_json

        proposal = self._proposal(tmp_path)
        data = json.loads(render_pr_proposal_json(proposal))
        assert "evidence_references" in data
        assert data["evidence_references"]["critical"] == 3

    def test_summary_contains_title(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_summary

        proposal = self._proposal(tmp_path)
        summary = render_pr_proposal_summary(proposal)
        assert "AEOS PR Proposal" in summary
        assert proposal.title in summary

    def test_summary_contains_read_only_line(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_summary

        proposal = self._proposal(tmp_path)
        summary = render_pr_proposal_summary(proposal)
        assert "read_only: true" in summary
        assert "applied: false" in summary

    def test_summary_contains_final_statement(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import render_pr_proposal_summary

        proposal = self._proposal(tmp_path)
        summary = render_pr_proposal_summary(proposal)
        assert "No changes were applied" in summary


# ---------------------------------------------------------------------------
# CLI — agent pr-proposal
# ---------------------------------------------------------------------------


class TestCliAgentPrProposal:
    def test_missing_registry_exits_1(self, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        missing = tmp_path / "nope.json"
        with patch.object(reg_mod, "DEFAULT_REGISTRY", missing):
            result = runner.invoke(app, ["agent", "pr-proposal", "--project", "p"])

        assert result.exit_code == 1

    def test_unknown_project_exits_1(self, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        mem = tmp_path / "memory"
        mem.mkdir()
        reg = _register(tmp_path, "other", mem)

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(app, ["agent", "pr-proposal", "--project", "ghost"])

        assert result.exit_code == 1

    def test_valid_project_exits_0(self, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app, ["agent", "pr-proposal", "--project", "test-proj"]
            )

        assert result.exit_code == 0
        assert "AEOS PR Proposal" in result.output

    def test_summary_shows_title(self, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))
        reg = _register(tmp_path, "test-proj", mem)

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app, ["agent", "pr-proposal", "--project", "test-proj"]
            )

        assert "security" in result.output
        assert "critical" in result.output

    def test_output_flag_writes_file(self, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)
        out = tmp_path / "proposal.md"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app,
                [
                    "agent",
                    "pr-proposal",
                    "--project",
                    "test-proj",
                    "--output",
                    str(out),
                ],
            )

        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert "# AEOS PR Proposal" in content
        assert "No changes were applied" in content
        assert "Proposal written to:" in result.output

    def test_json_flag_produces_valid_json(self, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app, ["agent", "pr-proposal", "--project", "test-proj", "--json"]
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["read_only"] is True
        assert data["applied"] is False
        assert "title" in data

    def test_read_only_in_terminal_output(self, tmp_path: Path) -> None:
        import aeos.project.registry as reg_mod

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            result = runner.invoke(
                app, ["agent", "pr-proposal", "--project", "test-proj"]
            )

        assert "read_only: true" in result.output
        assert "applied: false" in result.output


# ---------------------------------------------------------------------------
# Safety invariants
# ---------------------------------------------------------------------------


class TestPrProposalSafety:
    def test_does_not_modify_registry(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)
        mtime_before = reg.stat().st_mtime

        generate_pr_proposal("test-proj", registry_path=reg)

        assert reg.stat().st_mtime == mtime_before

    def test_does_not_modify_memory_dir(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)
        files_before = set(mem.rglob("*"))

        generate_pr_proposal("test-proj", registry_path=reg)

        assert set(mem.rglob("*")) == files_before

    def test_no_llm_in_title(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert "claude" not in proposal.title.lower()
        assert "openai" not in proposal.title.lower()
        assert "gpt" not in proposal.title.lower()

    def test_no_apply_in_final_statement(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)

        proposal = generate_pr_proposal("test-proj", registry_path=reg)

        assert "applied: false" not in proposal.final_statement
        assert "No changes were applied" in proposal.final_statement
