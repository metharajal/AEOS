"""CLI tests for CAP-1 Sprint C: aeos agent pr apply."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_proposal(
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


def _invoke_apply(
    tmp_path: Path,
    proposal_id: str = "pr-001",
    confirmation: str = "APPLY pr-001",
    extra_args: list[str] | None = None,
) -> object:
    p_dir = tmp_path / "proposals"
    mem_dir = tmp_path / "memory"
    args = [
        "agent",
        "pr",
        "apply",
        proposal_id,
        "--proposals-dir",
        str(p_dir),
        "--memory-dir",
        str(mem_dir),
        "--project-name",
        "test-project",
        "--project-path",
        str(tmp_path),
    ] + (extra_args or [])
    return runner.invoke(app, args, input=confirmation + "\n")


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


class TestCliAgentPrApplySuccess:
    def test_correct_confirmation_exits_0(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert result.exit_code == 0

    def test_success_output_contains_applied_successfully(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert "Applied successfully" in result.output

    def test_success_output_shows_apply_log_path(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert "apply-log" in result.output

    def test_success_output_shows_memory_record_path(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert "memory-record" in result.output

    def test_apply_log_created_on_disk(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        _invoke_apply(tmp_path)

        assert (p_dir / "pr-001" / "apply-log.md").exists()

    def test_proposal_json_status_updated_to_applied(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        _invoke_apply(tmp_path)

        raw = json.loads((p_dir / "pr-001" / "proposal.json").read_text())
        assert raw["status"] == "applied"

    def test_memory_record_created_on_disk(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        mem_dir = tmp_path / "memory"
        _write_proposal(p_dir, "pr-001")

        _invoke_apply(tmp_path)

        records = list((mem_dir / "test-project").glob("*.json"))
        assert len(records) == 1

    def test_success_output_contains_human_validated_true(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert "human_validated: true" in result.output

    def test_success_output_contains_applied_true(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert "applied: true" in result.output

    def test_proposal_detail_shown_before_gate(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", title="fix: harden RLS policies")

        result = _invoke_apply(tmp_path)

        assert "fix: harden RLS policies" in result.output

    def test_gate_prompt_shows_correct_apply_token(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert "APPLY pr-001" in result.output

    def test_output_shows_read_only_false(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = _invoke_apply(tmp_path)

        assert "read_only: false" in result.output


# ---------------------------------------------------------------------------
# Wrong / missing confirmation — cancel without side-effects
# ---------------------------------------------------------------------------


class TestCliAgentPrApplyWrongConfirmation:
    def test_wrong_confirmation_exits_0(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="yes\n",
        )

        assert result.exit_code == 0

    def test_wrong_confirmation_says_cancelled(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="yes\n",
        )

        assert "cancelled" in result.output

    def test_wrong_confirmation_writes_no_apply_log(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="wrong\n",
        )

        assert not (p_dir / "pr-001" / "apply-log.md").exists()

    def test_wrong_confirmation_does_not_change_proposal_status(
        self, tmp_path: Path
    ) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")

        runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="APPLY pr-999\n",
        )

        raw = json.loads((p_dir / "pr-001" / "proposal.json").read_text())
        assert raw["status"] == "pending"

    def test_wrong_confirmation_writes_no_memory_record(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        mem_dir = tmp_path / "memory"
        _write_proposal(p_dir, "pr-001")

        runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(mem_dir),
                "--project-name",
                "proj",
            ],
            input="apply pr-001\n",
        )

        assert not mem_dir.exists() or not list(mem_dir.rglob("*.json"))

    def test_partial_confirmation_exits_0_no_files(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001")
        files_before = {f for f in p_dir.rglob("*") if f.is_file()}

        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="APPLY\n",
        )

        assert result.exit_code == 0
        assert {f for f in p_dir.rglob("*") if f.is_file()} == files_before


# ---------------------------------------------------------------------------
# Error cases — non-zero exit
# ---------------------------------------------------------------------------


class TestCliAgentPrApplyErrors:
    def test_missing_proposal_exits_1(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "does-not-exist",
                "--proposals-dir",
                str(tmp_path / "proposals"),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="APPLY does-not-exist\n",
        )
        assert result.exit_code == 1

    def test_missing_proposal_shows_error(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "ghost",
                "--proposals-dir",
                str(tmp_path / "proposals"),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="APPLY ghost\n",
        )
        assert "ghost" in result.output or "ghost" in (result.stderr or "")

    def test_already_applied_proposal_exits_1(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", status="applied")

        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="APPLY pr-001\n",
        )

        assert result.exit_code == 1

    def test_already_applied_shows_status_in_error(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", status="applied")

        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="APPLY pr-001\n",
        )

        assert "applied" in result.output or "applied" in (result.stderr or "")

    def test_dismissed_proposal_exits_1(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        _write_proposal(p_dir, "pr-001", status="dismissed")

        result = runner.invoke(
            app,
            [
                "agent",
                "pr",
                "apply",
                "pr-001",
                "--proposals-dir",
                str(p_dir),
                "--memory-dir",
                str(tmp_path / "memory"),
                "--project-name",
                "proj",
            ],
            input="APPLY pr-001\n",
        )

        assert result.exit_code == 1
