"""Tests for CAP-1 Sprint B: apply_engine and build_memory_record_from_apply."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aeos.agent.apply_engine import ApplyContext, ApplyResult, run_apply
from aeos.agent.pr_management import Proposal, ProposalStatus
from aeos.memory.store import build_memory_record_from_apply

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_proposal_file(
    proposals_dir: Path,
    proposal_id: str,
    title: str = "fix: harden RLS policies",
    status: str = "pending",
    summary: str = "Harden all RLS policies.",
    files: list[str] | None = None,
) -> None:
    entry = proposals_dir / proposal_id
    entry.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {
        "id": proposal_id,
        "title": title,
        "status": status,
        "created_at": "2026-07-02T10:00:00",
        "summary": summary,
        "files": files or [],
    }
    (entry / "proposal.json").write_text(json.dumps(data), encoding="utf-8")


def _make_proposal(
    proposal_id: str = "pr-001",
    title: str = "fix: harden RLS policies",
    status: ProposalStatus = ProposalStatus.pending,
    summary: str = "Harden all RLS policies.",
    files: list[str] | None = None,
) -> Proposal:
    return Proposal(
        id=proposal_id,
        title=title,
        status=status,
        created_at="2026-07-02T10:00:00",
        summary=summary,
        files=files or [],
    )


def _make_context(
    proposals_dir: Path,
    memory_dir: Path,
    proposal_id: str = "pr-001",
    title: str = "fix: harden RLS policies",
    summary: str = "Harden all RLS policies.",
    files: list[str] | None = None,
    confirmation: str | None = None,
    project_name: str = "test-project",
    project_path: str = "/private/tmp/test-project",
) -> ApplyContext:
    _write_proposal_file(
        proposals_dir,
        proposal_id,
        title=title,
        summary=summary,
        files=files,
    )
    return ApplyContext(
        proposal=_make_proposal(
            proposal_id=proposal_id,
            title=title,
            summary=summary,
            files=files,
        ),
        proposals_dir=proposals_dir,
        memory_dir=memory_dir,
        project_name=project_name,
        project_path=project_path,
        confirmation=(
            confirmation if confirmation is not None else f"APPLY {proposal_id}"
        ),
    )


# ---------------------------------------------------------------------------
# build_memory_record_from_apply
# ---------------------------------------------------------------------------


class TestBuildMemoryRecordFromApply:
    def test_rail_is_agent(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.rail == "agent"

    def test_command_is_agent_pr_apply(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.command == "agent pr apply"

    def test_human_validated_true(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.human_validated is True

    def test_applied_true(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.applied is True

    def test_read_only_false(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.read_only is False

    def test_status_ok(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.status == "OK"

    def test_project_name_set(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="my-app",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.project_name == "my-app"

    def test_project_path_set(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/srv/my-app",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.project_path == "/srv/my-app"

    def test_notes_contains_proposal_id(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-abc",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.notes is not None
        assert "pr-abc" in record.notes

    def test_record_id_not_empty(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.record_id != ""

    def test_created_at_not_empty(self, tmp_path: Path) -> None:
        record = build_memory_record_from_apply(
            proposal_id="pr-001",
            project_name="proj",
            project_path="/private/tmp/proj",
            apply_log_path=tmp_path / "apply-log.json",
        )
        assert record.created_at != ""


# ---------------------------------------------------------------------------
# run_apply — success path
# ---------------------------------------------------------------------------


class TestRunApplySuccess:
    def test_writes_apply_log_json(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        run_apply(ctx)

        assert (p_dir / "pr-001" / "apply-log.json").exists()

    def test_apply_log_contains_proposal_id(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", proposal_id="pr-007")

        run_apply(ctx)

        content = (p_dir / "pr-007" / "apply-log.json").read_text()
        assert "pr-007" in content

    def test_apply_log_contains_proposal_title(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", title="feat: add audit trail")

        run_apply(ctx)

        content = (p_dir / "pr-001" / "apply-log.json").read_text()
        assert "feat: add audit trail" in content

    def test_apply_log_contains_applied_at_timestamp(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        run_apply(ctx)

        content = (p_dir / "pr-001" / "apply-log.json").read_text()
        assert '"applied_at"' in content

    def test_apply_log_contains_confirmation_string(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        run_apply(ctx)

        content = (p_dir / "pr-001" / "apply-log.json").read_text()
        assert "APPLY pr-001" in content

    def test_apply_log_contains_human_confirmed_true(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        run_apply(ctx)

        content = (p_dir / "pr-001" / "apply-log.json").read_text()
        assert '"human_confirmed": true' in content

    def test_apply_log_validation_result_passed(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        run_apply(ctx)

        content = (p_dir / "pr-001" / "apply-log.json").read_text()
        assert '"validation_result": "passed"' in content

    def test_apply_log_applied_by_is_agent_pr_apply(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        run_apply(ctx)

        content = (p_dir / "pr-001" / "apply-log.json").read_text()
        assert "aeos agent pr apply" in content

    def test_proposal_json_status_updated_to_applied(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        run_apply(ctx)

        raw = json.loads((p_dir / "pr-001" / "proposal.json").read_text())
        assert raw["status"] == "applied"

    def test_creates_memory_record_on_disk(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        mem_dir = tmp_path / "memory"
        ctx = _make_context(p_dir, mem_dir, project_name="my-app")

        run_apply(ctx)

        record_files = list((mem_dir / "my-app").glob("*.json"))
        assert len(record_files) == 1

    def test_memory_record_human_validated_true(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        mem_dir = tmp_path / "memory"
        ctx = _make_context(p_dir, mem_dir, project_name="my-app")

        result = run_apply(ctx)

        assert result.memory_record.human_validated is True

    def test_memory_record_applied_true(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        result = run_apply(ctx)

        assert result.memory_record.applied is True

    def test_memory_record_read_only_false(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        result = run_apply(ctx)

        assert result.memory_record.read_only is False

    def test_memory_record_rail_is_agent(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        result = run_apply(ctx)

        assert result.memory_record.rail == "agent"

    def test_memory_record_command_is_agent_pr_apply(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        result = run_apply(ctx)

        assert result.memory_record.command == "agent pr apply"

    def test_returns_apply_result_with_correct_paths(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        mem_dir = tmp_path / "memory"
        ctx = _make_context(p_dir, mem_dir, project_name="my-app")

        result = run_apply(ctx)

        assert isinstance(result, ApplyResult)
        assert result.apply_log_path == p_dir / "pr-001" / "apply-log.json"
        assert result.apply_log_path.exists()
        assert result.memory_record_path.exists()

    def test_result_proposal_status_is_applied(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory")

        result = run_apply(ctx)

        assert result.proposal.status == ProposalStatus.applied

    def test_apply_log_files_section_lists_files(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(
            p_dir,
            tmp_path / "memory",
            files=["src/auth/rls.sql", "migrations/001.sql"],
        )

        run_apply(ctx)

        content = (p_dir / "pr-001" / "apply-log.json").read_text()
        assert "src/auth/rls.sql" in content
        assert "migrations/001.sql" in content

    def test_apply_log_no_files_shows_empty_array(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", files=[])

        run_apply(ctx)

        payload = json.loads((p_dir / "pr-001" / "apply-log.json").read_text())
        assert payload["files"] == []


# ---------------------------------------------------------------------------
# run_apply — guards (nothing written on any guard failure)
# ---------------------------------------------------------------------------


class TestRunApplyGuards:
    def test_rejects_applied_proposal_raises_value_error(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal_file(p_dir, "pr-001", status="applied")
        proposal = _make_proposal(status=ProposalStatus.applied)
        ctx = ApplyContext(
            proposal=proposal,
            proposals_dir=p_dir,
            memory_dir=tmp_path / "memory",
            project_name="proj",
            project_path="/private/tmp/proj",
            confirmation="APPLY pr-001",
        )

        with pytest.raises(ValueError, match="pending"):
            run_apply(ctx)

    def test_rejects_applied_proposal_writes_nothing(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal_file(p_dir, "pr-001", status="applied")
        proposal = _make_proposal(status=ProposalStatus.applied)
        ctx = ApplyContext(
            proposal=proposal,
            proposals_dir=p_dir,
            memory_dir=tmp_path / "memory",
            project_name="proj",
            project_path="/private/tmp/proj",
            confirmation="APPLY pr-001",
        )
        files_before = {f: f.read_bytes() for f in p_dir.rglob("*") if f.is_file()}

        with pytest.raises(ValueError):
            run_apply(ctx)

        files_after = {f: f.read_bytes() for f in p_dir.rglob("*") if f.is_file()}
        assert files_before == files_after

    def test_rejects_dismissed_proposal_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal_file(p_dir, "pr-001", status="dismissed")
        proposal = _make_proposal(status=ProposalStatus.dismissed)
        ctx = ApplyContext(
            proposal=proposal,
            proposals_dir=p_dir,
            memory_dir=tmp_path / "memory",
            project_name="proj",
            project_path="/private/tmp/proj",
            confirmation="APPLY pr-001",
        )

        with pytest.raises(ValueError, match="pending"):
            run_apply(ctx)

    def test_rejects_wrong_confirmation_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", confirmation="yes")

        with pytest.raises(ValueError):
            run_apply(ctx)

    def test_rejects_wrong_confirmation_writes_nothing(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", confirmation="yes")
        files_before = {f: f.read_bytes() for f in p_dir.rglob("*") if f.is_file()}

        with pytest.raises(ValueError):
            run_apply(ctx)

        files_after = {f: f.read_bytes() for f in p_dir.rglob("*") if f.is_file()}
        assert files_before == files_after

    def test_rejects_partial_confirmation_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", confirmation="APPLY")

        with pytest.raises(ValueError):
            run_apply(ctx)

    def test_rejects_wrong_id_in_confirmation_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", confirmation="APPLY pr-999")

        with pytest.raises(ValueError):
            run_apply(ctx)

    def test_rejects_lowercase_apply_in_confirmation(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        ctx = _make_context(p_dir, tmp_path / "memory", confirmation="apply pr-001")

        with pytest.raises(ValueError):
            run_apply(ctx)

    def test_rejects_if_apply_log_already_exists_raises_file_exists_error(
        self, tmp_path: Path
    ) -> None:
        """APPLY.PRE.05: apply-log.json must not exist before apply runs."""
        p_dir = tmp_path / "proposals"
        _write_proposal_file(p_dir, "pr-001")
        (p_dir / "pr-001" / "apply-log.json").write_text("{}", encoding="utf-8")
        ctx = _make_context(p_dir, tmp_path / "memory")

        with pytest.raises(FileExistsError):
            run_apply(ctx)

    def test_rejects_if_apply_log_exists_proposal_stays_pending(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal_file(p_dir, "pr-001")
        (p_dir / "pr-001" / "apply-log.json").write_text("{}", encoding="utf-8")
        ctx = _make_context(p_dir, tmp_path / "memory")

        with pytest.raises(FileExistsError):
            run_apply(ctx)

        raw = json.loads((p_dir / "pr-001" / "proposal.json").read_text())
        assert raw["status"] == "pending"


# ---------------------------------------------------------------------------
# run_apply — ordering invariant
# ---------------------------------------------------------------------------


class TestRunApplyOrdering:
    def test_proposal_stays_pending_if_apply_log_guard_fires(
        self, tmp_path: Path
    ) -> None:
        """Ordering guarantee: C2 guard (APPLY.PRE.05) fires before any write."""
        p_dir = tmp_path / "proposals"
        _write_proposal_file(p_dir, "pr-001")

        # Placing a directory at apply-log.json triggers .exists() → FileExistsError
        apply_log_blocker = p_dir / "pr-001" / "apply-log.json"
        apply_log_blocker.mkdir(parents=True, exist_ok=True)

        proposal = _make_proposal()
        ctx = ApplyContext(
            proposal=proposal,
            proposals_dir=p_dir,
            memory_dir=tmp_path / "memory",
            project_name="proj",
            project_path="/private/tmp/proj",
            confirmation="APPLY pr-001",
        )

        with pytest.raises(OSError):  # FileExistsError is a subclass of OSError
            run_apply(ctx)

        raw = json.loads((p_dir / "pr-001" / "proposal.json").read_text())
        assert raw["status"] == "pending"


# ---------------------------------------------------------------------------
# Package exports
# ---------------------------------------------------------------------------


class TestApplyEngineExports:
    def test_apply_context_exported(self) -> None:
        from aeos.agent import ApplyContext  # noqa: F401

    def test_apply_result_exported(self) -> None:
        from aeos.agent import ApplyResult  # noqa: F401

    def test_run_apply_exported(self) -> None:
        from aeos.agent import run_apply  # noqa: F401
