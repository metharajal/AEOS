"""Tests for MVP-AGENTS-6: ProposalRepository, renderers, and CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.agent.pr_management import (
    DEFAULT_PROPOSALS_DIR,
    Proposal,
    ProposalRepository,
    ProposalStatus,
    render_proposal_detail,
    render_proposal_list,
    update_proposal_status,
)
from aeos.cli import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_proposal(
    proposals_dir: Path,
    proposal_id: str,
    title: str = "fix: harden RLS policies",
    status: str = "pending",
    created_at: str = "2026-07-02T10:00:00",
    summary: str = "Harden all RLS policies for production readiness.",
    files: list[str] | None = None,
    diff_preview: str | None = None,
) -> Path:
    entry = proposals_dir / proposal_id
    entry.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {
        "id": proposal_id,
        "title": title,
        "status": status,
        "created_at": created_at,
        "summary": summary,
        "files": files or [],
    }
    if diff_preview is not None:
        data["diff_preview"] = diff_preview
    (entry / "proposal.json").write_text(json.dumps(data), encoding="utf-8")
    return entry / "proposal.json"


# ---------------------------------------------------------------------------
# ProposalRepository.list()
# ---------------------------------------------------------------------------


class TestProposalRepositoryList:
    def test_empty_workspace_returns_empty_list(self, tmp_path: Path) -> None:
        repo = ProposalRepository(tmp_path / "proposals")
        assert repo.list() == []

    def test_nonexistent_dir_returns_empty_list(self, tmp_path: Path) -> None:
        repo = ProposalRepository(tmp_path / "does-not-exist")
        assert repo.list() == []

    def test_one_proposal_shown_in_list(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert len(proposals) == 1
        assert proposals[0].id == "pr-001"
        assert proposals[0].title == "fix: harden RLS policies"

    def test_multiple_proposals_all_shown(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", created_at="2026-07-01T10:00:00")
        _write_proposal(p_dir, "pr-002", created_at="2026-07-02T10:00:00")
        _write_proposal(p_dir, "pr-003", created_at="2026-07-03T10:00:00")

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert len(proposals) == 3

    def test_proposals_sorted_by_date_descending(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-old", created_at="2026-06-01T10:00:00")
        _write_proposal(p_dir, "pr-new", created_at="2026-07-02T10:00:00")
        _write_proposal(p_dir, "pr-mid", created_at="2026-06-15T10:00:00")

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert [p.id for p in proposals] == ["pr-new", "pr-mid", "pr-old"]

    def test_skips_non_directory_entries(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        p_dir.mkdir()
        (p_dir / "stray-file.txt").write_text("ignored")
        _write_proposal(p_dir, "pr-001")

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert len(proposals) == 1

    def test_skips_directories_without_proposal_json(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        p_dir.mkdir()
        (p_dir / "empty-dir").mkdir()
        _write_proposal(p_dir, "pr-001")

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert len(proposals) == 1

    def test_silently_skips_invalid_json_in_list(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        bad = p_dir / "pr-bad"
        bad.mkdir()
        (bad / "proposal.json").write_text("NOT JSON", encoding="utf-8")

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert len(proposals) == 1
        assert proposals[0].id == "pr-001"

    def test_silently_skips_invalid_status_in_list(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        _write_proposal(p_dir, "pr-bad", status="unknown-status")

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert len(proposals) == 1
        assert proposals[0].id == "pr-001"

    def test_proposal_status_parsed_correctly(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-pending", status="pending")
        _write_proposal(
            p_dir, "pr-applied", status="applied", created_at="2026-06-01T00:00:00"
        )
        _write_proposal(
            p_dir, "pr-dismissed", status="dismissed", created_at="2026-05-01T00:00:00"
        )

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        statuses = {p.id: p.status for p in proposals}
        assert statuses["pr-pending"] == ProposalStatus.pending
        assert statuses["pr-applied"] == ProposalStatus.applied
        assert statuses["pr-dismissed"] == ProposalStatus.dismissed

    def test_files_list_populated(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(
            p_dir, "pr-001", files=["src/auth/rls.sql", "supabase/migrations/001.sql"]
        )

        repo = ProposalRepository(p_dir)
        proposals = repo.list()

        assert proposals[0].files == ["src/auth/rls.sql", "supabase/migrations/001.sql"]


# ---------------------------------------------------------------------------
# ProposalRepository.get()
# ---------------------------------------------------------------------------


class TestProposalRepositoryGet:
    def test_missing_proposal_returns_none(self, tmp_path: Path) -> None:
        repo = ProposalRepository(tmp_path / "proposals")
        assert repo.get("does-not-exist") is None

    def test_existing_proposal_returned(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", title="fix: add RLS")

        repo = ProposalRepository(p_dir)
        proposal = repo.get("pr-001")

        assert proposal is not None
        assert proposal.id == "pr-001"
        assert proposal.title == "fix: add RLS"

    def test_invalid_json_raises_value_error(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        bad = p_dir / "pr-bad"
        bad.mkdir(parents=True)
        (bad / "proposal.json").write_text("INVALID JSON{{{", encoding="utf-8")

        repo = ProposalRepository(p_dir)
        with pytest.raises(ValueError, match="Invalid JSON"):
            repo.get("pr-bad")

    def test_invalid_status_raises_value_error(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-bad", status="not-a-real-status")

        repo = ProposalRepository(p_dir)
        with pytest.raises(ValueError, match="Invalid status"):
            repo.get("pr-bad")

    def test_invalid_status_error_mentions_allowed_values(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-bad", status="ghost")

        repo = ProposalRepository(p_dir)
        with pytest.raises(ValueError, match="pending"):
            repo.get("pr-bad")

    def test_diff_preview_populated(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(
            p_dir, "pr-001", diff_preview="--- a/old\n+++ b/new\n+ added line"
        )

        repo = ProposalRepository(p_dir)
        proposal = repo.get("pr-001")

        assert proposal is not None
        assert proposal.diff_preview is not None
        assert "added line" in proposal.diff_preview

    def test_diff_preview_none_when_absent(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        repo = ProposalRepository(p_dir)
        proposal = repo.get("pr-001")

        assert proposal is not None
        assert proposal.diff_preview is None

    def test_id_falls_back_to_dirname(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        entry = p_dir / "pr-fallback"
        entry.mkdir(parents=True)
        data = {
            "title": "no-id-field",
            "status": "pending",
            "created_at": "",
            "summary": "",
        }
        (entry / "proposal.json").write_text(json.dumps(data), encoding="utf-8")

        repo = ProposalRepository(p_dir)
        proposal = repo.get("pr-fallback")

        assert proposal is not None
        assert proposal.id == "pr-fallback"


# ---------------------------------------------------------------------------
# render_proposal_list
# ---------------------------------------------------------------------------


class TestRenderProposalList:
    def test_empty_list_message(self) -> None:
        output = render_proposal_list([])
        assert "No proposals found" in output

    def test_header_present(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        proposals = ProposalRepository(p_dir).list()

        output = render_proposal_list(proposals)

        assert "ID" in output
        assert "STATUS" in output
        assert "TITLE" in output

    def test_proposal_row_present(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", title="fix: harden RLS")
        proposals = ProposalRepository(p_dir).list()

        output = render_proposal_list(proposals)

        assert "pr-001" in output
        assert "pending" in output
        assert "fix: harden RLS" in output

    def test_multiple_proposals_in_output(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(
            p_dir, "pr-001", title="first", created_at="2026-07-02T10:00:00"
        )
        _write_proposal(
            p_dir, "pr-002", title="second", created_at="2026-07-01T10:00:00"
        )
        proposals = ProposalRepository(p_dir).list()

        output = render_proposal_list(proposals)

        assert "pr-001" in output
        assert "pr-002" in output

    def test_separator_line_present(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        proposals = ProposalRepository(p_dir).list()

        output = render_proposal_list(proposals)

        assert "---" in output


# ---------------------------------------------------------------------------
# render_proposal_detail
# ---------------------------------------------------------------------------


class TestRenderProposalDetail:
    def _make_proposal(
        self,
        proposal_id: str = "pr-001",
        title: str = "fix: harden RLS",
        status: ProposalStatus = ProposalStatus.pending,
        created_at: str = "2026-07-02T10:00:00",
        summary: str = "Harden policies.",
        files: list[str] | None = None,
        diff_preview: str | None = None,
    ) -> Proposal:
        return Proposal(
            id=proposal_id,
            title=title,
            status=status,
            created_at=created_at,
            summary=summary,
            files=files or [],
            diff_preview=diff_preview,
        )

    def test_header_present(self) -> None:
        output = render_proposal_detail(self._make_proposal())
        assert "AEOS PR Proposal" in output

    def test_title_present(self) -> None:
        output = render_proposal_detail(self._make_proposal(title="fix: add RLS"))
        assert "fix: add RLS" in output

    def test_id_present(self) -> None:
        output = render_proposal_detail(self._make_proposal(proposal_id="pr-999"))
        assert "pr-999" in output

    def test_status_present(self) -> None:
        output = render_proposal_detail(
            self._make_proposal(status=ProposalStatus.applied)
        )
        assert "applied" in output

    def test_created_at_present(self) -> None:
        output = render_proposal_detail(
            self._make_proposal(created_at="2026-07-02T10:00:00")
        )
        assert "2026-07-02T10:00:00" in output

    def test_summary_present(self) -> None:
        output = render_proposal_detail(
            self._make_proposal(summary="Fix the policies.")
        )
        assert "Fix the policies." in output

    def test_no_summary_fallback(self) -> None:
        output = render_proposal_detail(self._make_proposal(summary=""))
        assert "no summary" in output

    def test_files_listed(self) -> None:
        output = render_proposal_detail(
            self._make_proposal(files=["src/auth/rls.sql", "migrations/001.sql"])
        )
        assert "src/auth/rls.sql" in output
        assert "migrations/001.sql" in output

    def test_diff_preview_shown(self) -> None:
        output = render_proposal_detail(
            self._make_proposal(diff_preview="--- a/old\n+++ b/new\n+ added line")
        )
        assert "Diff Preview" in output
        assert "added line" in output

    def test_diff_preview_capped_at_20_lines(self) -> None:
        preview = "\n".join(f"line {i}" for i in range(30))
        output = render_proposal_detail(self._make_proposal(diff_preview=preview))
        assert "line 19" in output
        assert "line 20" not in output

    def test_suggested_command_present(self) -> None:
        output = render_proposal_detail(self._make_proposal(proposal_id="pr-001"))
        assert "aeos agent pr apply pr-001" in output

    def test_read_only_statement_present(self) -> None:
        output = render_proposal_detail(self._make_proposal())
        assert "read_only: true" in output
        assert "applied: false" in output
        assert "human validation required" in output


# ---------------------------------------------------------------------------
# CLI — aeos agent pr list
# ---------------------------------------------------------------------------


runner = CliRunner()


class TestCliAgentPrList:
    def test_list_empty_workspace(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["agent", "pr", "list", "--proposals-dir", str(tmp_path / "proposals")],
        )
        assert result.exit_code == 0
        assert "No proposals found" in result.output

    def test_list_shows_proposal(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", title="fix: harden RLS")

        result = runner.invoke(
            app, ["agent", "pr", "list", "--proposals-dir", str(p_dir)]
        )

        assert result.exit_code == 0
        assert "pr-001" in result.output
        assert "pending" in result.output
        assert "fix: harden RLS" in result.output

    def test_list_multiple_proposals(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", created_at="2026-07-02T00:00:00")
        _write_proposal(p_dir, "pr-002", created_at="2026-07-01T00:00:00")

        result = runner.invoke(
            app, ["agent", "pr", "list", "--proposals-dir", str(p_dir)]
        )

        assert result.exit_code == 0
        assert "pr-001" in result.output
        assert "pr-002" in result.output

    def test_list_read_only_no_network(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        files_before = set(p_dir.rglob("*"))

        runner.invoke(app, ["agent", "pr", "list", "--proposals-dir", str(p_dir)])

        assert set(p_dir.rglob("*")) == files_before


# ---------------------------------------------------------------------------
# CLI — aeos agent pr show
# ---------------------------------------------------------------------------


class TestCliAgentPrShow:
    def test_show_existing_proposal(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", title="fix: harden RLS", summary="Fix all.")

        result = runner.invoke(
            app,
            ["agent", "pr", "show", "pr-001", "--proposals-dir", str(p_dir)],
        )

        assert result.exit_code == 0
        assert "AEOS PR Proposal" in result.output
        assert "fix: harden RLS" in result.output
        assert "Fix all." in result.output

    def test_show_missing_proposal_exits_1(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "show",
                "does-not-exist",
                "--proposals-dir",
                str(tmp_path / "proposals"),
            ],
        )
        assert result.exit_code == 1

    def test_show_missing_proposal_error_message(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "show",
                "ghost-pr",
                "--proposals-dir",
                str(tmp_path / "proposals"),
            ],
        )
        assert "ghost-pr" in result.output or "ghost-pr" in (result.stderr or "")

    def test_show_invalid_json_exits_1(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        bad = p_dir / "pr-bad"
        bad.mkdir(parents=True)
        (bad / "proposal.json").write_text("BROKEN", encoding="utf-8")

        result = runner.invoke(
            app,
            ["agent", "pr", "show", "pr-bad", "--proposals-dir", str(p_dir)],
        )

        assert result.exit_code == 1

    def test_show_contains_read_only_statement(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = runner.invoke(
            app,
            ["agent", "pr", "show", "pr-001", "--proposals-dir", str(p_dir)],
        )

        assert "read_only: true" in result.output
        assert "applied: false" in result.output

    def test_show_contains_suggested_command(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = runner.invoke(
            app,
            ["agent", "pr", "show", "pr-001", "--proposals-dir", str(p_dir)],
        )

        assert "aeos agent pr apply pr-001" in result.output

    def test_show_does_not_write_to_proposals_dir(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        files_before = set(p_dir.rglob("*"))

        runner.invoke(
            app,
            ["agent", "pr", "show", "pr-001", "--proposals-dir", str(p_dir)],
        )

        assert set(p_dir.rglob("*")) == files_before


# ---------------------------------------------------------------------------
# ProposalStatus enum
# ---------------------------------------------------------------------------


class TestProposalStatus:
    def test_all_values_accessible(self) -> None:
        assert ProposalStatus.pending == "pending"
        assert ProposalStatus.applied == "applied"
        assert ProposalStatus.dismissed == "dismissed"

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValueError):
            ProposalStatus("not-a-status")


# ---------------------------------------------------------------------------
# DEFAULT_PROPOSALS_DIR
# ---------------------------------------------------------------------------


class TestDefaultProposalsDir:
    def test_default_proposals_dir_under_home(self) -> None:
        home = Path.home()
        assert DEFAULT_PROPOSALS_DIR.is_relative_to(home)

    def test_default_proposals_dir_path(self) -> None:
        expected = Path.home() / ".aeos" / "workspace" / "proposals"
        assert DEFAULT_PROPOSALS_DIR == expected


# ---------------------------------------------------------------------------
# Package exports
# ---------------------------------------------------------------------------


class TestPackageExports:
    def test_proposal_exported(self) -> None:
        from aeos.agent import Proposal  # noqa: F401

    def test_proposal_repository_exported(self) -> None:
        from aeos.agent import ProposalRepository  # noqa: F401

    def test_proposal_status_exported(self) -> None:
        from aeos.agent import ProposalStatus  # noqa: F401


# ---------------------------------------------------------------------------
# Safety invariants
# ---------------------------------------------------------------------------


class TestPrManagementSafety:
    def test_list_never_writes(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        _write_proposal(p_dir, "pr-002", created_at="2026-06-01T00:00:00")
        before = {f: f.stat().st_mtime for f in p_dir.rglob("*")}

        ProposalRepository(p_dir).list()

        after = {f: f.stat().st_mtime for f in p_dir.rglob("*")}
        assert before == after

    def test_get_never_writes(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        before = {f: f.stat().st_mtime for f in p_dir.rglob("*")}

        ProposalRepository(p_dir).get("pr-001")

        after = {f: f.stat().st_mtime for f in p_dir.rglob("*")}
        assert before == after

    def test_render_detail_no_network_references(self) -> None:
        proposal = Proposal(
            id="pr-test",
            title="test",
            status=ProposalStatus.pending,
            created_at="2026-07-02T10:00:00",
            summary="test summary",
        )
        output = render_proposal_detail(proposal)
        assert "http://" not in output
        assert "https://" not in output

    def test_render_detail_no_llm_references(self) -> None:
        proposal = Proposal(
            id="pr-test",
            title="test",
            status=ProposalStatus.pending,
            created_at="2026-07-02T10:00:00",
            summary="test summary",
        )
        output = render_proposal_detail(proposal)
        assert "openai" not in output.lower()
        assert "ollama" not in output.lower()
        assert "llm" not in output.lower()


# ---------------------------------------------------------------------------
# update_proposal_status
# ---------------------------------------------------------------------------


class TestUpdateProposalStatus:
    def test_update_status_pending_to_applied_writes_json(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        update_proposal_status(p_dir, "pr-001", ProposalStatus.applied)

        raw = json.loads((p_dir / "pr-001" / "proposal.json").read_text())
        assert raw["status"] == "applied"

    def test_update_status_returns_updated_proposal_object(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", title="fix: harden RLS")

        result = update_proposal_status(p_dir, "pr-001", ProposalStatus.applied)

        assert isinstance(result, Proposal)
        assert result.status == ProposalStatus.applied
        assert result.id == "pr-001"

    def test_update_status_written_json_has_correct_status(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        update_proposal_status(p_dir, "pr-001", ProposalStatus.dismissed)

        raw = json.loads((p_dir / "pr-001" / "proposal.json").read_text())
        assert raw["status"] == "dismissed"

    def test_update_status_already_applied_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", status="applied")

        with pytest.raises(ValueError, match="pending"):
            update_proposal_status(p_dir, "pr-001", ProposalStatus.applied)

    def test_update_status_dismissed_raises_value_error(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", status="dismissed")

        with pytest.raises(ValueError, match="pending"):
            update_proposal_status(p_dir, "pr-001", ProposalStatus.applied)

    def test_update_status_missing_proposal_raises_file_not_found(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"

        with pytest.raises(FileNotFoundError):
            update_proposal_status(p_dir, "does-not-exist", ProposalStatus.applied)

    def test_update_status_preserves_all_other_fields(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(
            p_dir,
            "pr-001",
            title="fix: RLS hardening",
            summary="Harden all policies for production.",
            files=["src/auth/rls.sql", "migrations/001.sql"],
            created_at="2026-07-02T10:00:00",
            diff_preview="--- a\n+++ b\n+ added",
        )

        result = update_proposal_status(p_dir, "pr-001", ProposalStatus.applied)

        assert result.title == "fix: RLS hardening"
        assert result.summary == "Harden all policies for production."
        assert result.files == ["src/auth/rls.sql", "migrations/001.sql"]
        assert result.created_at == "2026-07-02T10:00:00"
        assert result.diff_preview == "--- a\n+++ b\n+ added"
        assert result.id == "pr-001"

    def test_update_status_result_parseable_by_repository(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        update_proposal_status(p_dir, "pr-001", ProposalStatus.applied)

        repo = ProposalRepository(p_dir)
        proposal = repo.get("pr-001")
        assert proposal is not None
        assert proposal.status == ProposalStatus.applied

    def test_update_status_never_writes_when_not_pending(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", status="applied")
        before = {f: f.read_bytes() for f in p_dir.rglob("*") if f.is_file()}

        with pytest.raises(ValueError):
            update_proposal_status(p_dir, "pr-001", ProposalStatus.applied)

        after = {f: f.read_bytes() for f in p_dir.rglob("*") if f.is_file()}
        assert before == after
