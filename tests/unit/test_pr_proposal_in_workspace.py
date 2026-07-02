"""Tests for MVP-AGENTS-5: PR Proposal in Workspace and Evidence Pack."""

from __future__ import annotations

from pathlib import Path

from aeos.memory.models import MemoryRecord
from aeos.memory.store import save_record
from aeos.project.registry import ProjectRegistration, register_project


def _make_record(
    project_name: str = "test-proj",
    critical: int = 3,
    important: int = 59,
    manual: int = 15,
    generated: int = 25,
    control_level: str = "weak",
    providers: list[str] | None = None,
    record_suffix: str = "bb002200",
) -> MemoryRecord:
    if providers is None:
        providers = ["supabase"]
    return MemoryRecord(
        record_id=f"{project_name}-20260702T100000-{record_suffix}",
        created_at="2026-07-02T10:00:00",
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


def _write(mem: Path, record: MemoryRecord) -> Path:
    return save_record(record, mem)


def _register(tmp_path: Path, name: str, mem: Path) -> Path:
    reg = tmp_path / "reg.json"
    registration = ProjectRegistration(
        name=name, project_type="recovered-project", memory_dir=mem
    )
    register_project(registration, reg)
    return reg


# ---------------------------------------------------------------------------
# generate_pr_proposal_from_memory
# ---------------------------------------------------------------------------


class TestGeneratePrProposalFromMemory:
    def test_returns_proposal_with_records(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal_from_memory

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))

        proposal = generate_pr_proposal_from_memory("test-proj", mem)

        assert proposal.title
        assert proposal.read_only is True
        assert proposal.applied is False
        assert proposal.human_validation_required is True

    def test_works_without_records(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal_from_memory

        mem = tmp_path / "memory"
        mem.mkdir()

        proposal = generate_pr_proposal_from_memory("test-proj", mem)

        assert proposal.title
        assert proposal.evidence_references["record_count"] == 0

    def test_works_with_missing_memory_dir(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal_from_memory

        proposal = generate_pr_proposal_from_memory(
            "test-proj", tmp_path / "nonexistent"
        )

        assert proposal.title
        assert proposal.evidence_references["record_count"] == 0

    def test_reads_findings_from_records(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal_from_memory

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3, important=59, generated=25))

        proposal = generate_pr_proposal_from_memory("test-proj", mem)

        ev = proposal.evidence_references
        assert ev["critical"] == 3
        assert ev["important"] == 59
        assert ev["generated_sql_blocks"] == 25

    def test_critical_title(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal_from_memory

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))

        proposal = generate_pr_proposal_from_memory("test-proj", mem)

        assert "security" in proposal.title
        assert "critical" in proposal.title

    def test_exported_from_package(self) -> None:
        from aeos.agent import generate_pr_proposal_from_memory  # noqa: F401

    def test_does_not_modify_memory_dir(self, tmp_path: Path) -> None:
        from aeos.agent.pr_proposal import generate_pr_proposal_from_memory

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        files_before = set(mem.rglob("*"))

        generate_pr_proposal_from_memory("test-proj", mem)

        assert set(mem.rglob("*")) == files_before


# ---------------------------------------------------------------------------
# WorkspaceData.pr_proposal field
# ---------------------------------------------------------------------------


class TestWorkspaceDataPrProposal:
    def test_load_workspace_data_sets_pr_proposal(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record())

        ws = load_workspace_data(mem, "test-proj")

        assert ws.pr_proposal is not None
        assert ws.pr_proposal.project_name == "test-proj"
        assert ws.pr_proposal.read_only is True
        assert ws.pr_proposal.applied is False

    def test_pr_proposal_title_reflects_findings(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))

        ws = load_workspace_data(mem, "test-proj")

        assert ws.pr_proposal is not None
        assert "critical" in ws.pr_proposal.title


# ---------------------------------------------------------------------------
# Project Workspace HTML — "Suggested PR" section
# ---------------------------------------------------------------------------


class TestWorkspaceHtmlSuggestedPr:
    def test_suggested_pr_section_present(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        ws = load_workspace_data(mem, "test-proj")

        html = render_workspace(ws)

        assert "Suggested PR" in html

    def test_suggested_pr_contains_title(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))
        ws = load_workspace_data(mem, "test-proj")

        html = render_workspace(ws)

        assert "security" in html
        assert "critical" in html

    def test_suggested_pr_contains_read_only(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        ws = load_workspace_data(mem, "test-proj")

        html = render_workspace(ws)

        assert "read_only: true" in html
        assert "applied: false" in html

    def test_suggested_pr_contains_final_statement(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        ws = load_workspace_data(mem, "test-proj")

        html = render_workspace(ws)

        assert "No changes were applied" in html

    def test_suggested_pr_contains_why_now(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=3))
        ws = load_workspace_data(mem, "test-proj")

        html = render_workspace(ws)

        assert "Why this PR now" in html

    def test_suggested_pr_section_order(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        ws = load_workspace_data(mem, "test-proj")

        html = render_workspace(ws)

        idx_agent = html.find("Agent Recommendations")
        idx_pr = html.find("Suggested PR")
        idx_prod = html.find("Production Readiness")

        assert idx_agent < idx_pr < idx_prod


# ---------------------------------------------------------------------------
# Evidence Pack — pr-proposal.md
# ---------------------------------------------------------------------------


class TestEvidencePackPrProposal:
    def test_evidence_pack_contains_pr_proposal_md(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"

        result = generate_evidence_pack(mem, "test-proj", out)

        file_names = [f.name for f in result.files]
        assert "pr-proposal.md" in file_names

    def test_pr_proposal_md_exists_on_disk(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"

        generate_evidence_pack(mem, "test-proj", out)

        pr_file = out / "pr-proposal.md"
        assert pr_file.exists()

    def test_pr_proposal_md_has_14_sections(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"

        generate_evidence_pack(mem, "test-proj", out)

        content = (out / "pr-proposal.md").read_text()
        for header in [
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
            assert header in content, f"Missing section in pr-proposal.md: {header}"

    def test_pr_proposal_md_read_only_statement(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"

        generate_evidence_pack(mem, "test-proj", out)

        content = (out / "pr-proposal.md").read_text()
        assert "read_only: true" in content
        assert "applied: false" in content
        assert "No changes were applied" in content

    def test_evidence_pack_has_9_files(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import _PACK_FILES, generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"

        result = generate_evidence_pack(mem, "test-proj", out)

        assert len(result.files) == len(_PACK_FILES)

    def test_index_html_references_pr_proposal(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"

        generate_evidence_pack(mem, "test-proj", out)

        index_html = (out / "index.html").read_text()
        assert "pr-proposal.md" in index_html

    def test_no_mutation_memory_dir(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        files_before = set(mem.rglob("*"))
        out = tmp_path / "pack"

        generate_evidence_pack(mem, "test-proj", out)

        assert set(mem.rglob("*")) == files_before


# ---------------------------------------------------------------------------
# Workspace demo — pr-proposal.md in each project and evidence-pack
# ---------------------------------------------------------------------------


class TestWorkspaceDemoPrProposal:
    def _setup_registry(self, tmp_path: Path) -> tuple[Path, Path]:
        mem = tmp_path / "memory"
        _write(mem, _make_record())
        reg = _register(tmp_path, "test-proj", mem)
        return mem, reg

    def test_demo_generates_pr_proposal_in_evidence_pack(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        import aeos.project.registry as reg_mod
        from aeos.workspace.demo import generate_workspace_demo

        _, reg = self._setup_registry(tmp_path)
        out = tmp_path / "demo"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            generate_workspace_demo(output_dir=out, registry_path=reg)

        pr_files = list(out.rglob("pr-proposal.md"))
        assert len(pr_files) >= 1, "pr-proposal.md not found in demo output"

    def test_demo_pr_proposal_in_evidence_pack_subdir(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        import aeos.project.registry as reg_mod
        from aeos.workspace.demo import generate_workspace_demo

        _, reg = self._setup_registry(tmp_path)
        out = tmp_path / "demo"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            generate_workspace_demo(output_dir=out, registry_path=reg)

        ep_pr = out / "test-proj" / "evidence-pack" / "pr-proposal.md"
        assert ep_pr.exists(), f"Expected {ep_pr} to exist"

    def test_demo_pr_proposal_md_has_correct_content(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        import aeos.project.registry as reg_mod
        from aeos.workspace.demo import generate_workspace_demo

        _, reg = self._setup_registry(tmp_path)
        out = tmp_path / "demo"

        with patch.object(reg_mod, "DEFAULT_REGISTRY", reg):
            generate_workspace_demo(output_dir=out, registry_path=reg)

        ep_pr = out / "test-proj" / "evidence-pack" / "pr-proposal.md"
        content = ep_pr.read_text()
        assert "# AEOS PR Proposal" in content
        assert "No changes were applied" in content


# ---------------------------------------------------------------------------
# Safety invariants
# ---------------------------------------------------------------------------


class TestPrProposalInWorkspaceSafety:
    def test_workspace_html_no_llm_mention(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        ws = load_workspace_data(mem, "test-proj")
        html = render_workspace(ws)

        assert "openai" not in html.lower()
        assert "ollama" not in html.lower()

    def test_evidence_pack_no_llm_in_pr_proposal(self, tmp_path: Path) -> None:
        from aeos.ui.evidence_pack import generate_evidence_pack

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        out = tmp_path / "pack"
        generate_evidence_pack(mem, "test-proj", out)

        content = (out / "pr-proposal.md").read_text()
        assert "openai" not in content.lower()
        assert "ollama" not in content.lower()

    def test_pr_proposal_always_read_only_in_html(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record(critical=0, important=0, manual=0, generated=0))
        ws = load_workspace_data(mem, "test-proj")
        html = render_workspace(ws)

        assert "read_only: true" in html

    def test_pr_proposal_always_applied_false_in_html(self, tmp_path: Path) -> None:
        from aeos.ui.workspace import load_workspace_data, render_workspace

        mem = tmp_path / "memory"
        _write(mem, _make_record())
        ws = load_workspace_data(mem, "test-proj")
        html = render_workspace(ws)

        assert "applied: false" in html
