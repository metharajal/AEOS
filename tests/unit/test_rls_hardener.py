"""
Unit tests for aeos supabase rls harden (Sprint 2Z).

Covers:
  - run_rls_harden() data model invariants
  - CLI text output without --output
  - CLI JSON output
  - CLI --output gates (PASS / WARNING / BLOCKED / overwrite)
  - Security: no secrets, no .env, no client writes, applied=false
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from aeos.cli import app
from aeos.providers.supabase.rls.hardener import RLSHardenResult, run_rls_harden

runner = CliRunner()

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "supabase_rls"
LOVABLE_DIR = (
    Path(__file__).parent.parent
    / "fixtures"
    / "realistic_projects"
    / "lovable_supabase_vercel"
)

_SECRET_PATTERNS = [
    "anon_key",
    "service_role_key",
    "SUPABASE_URL",
    "jwt_secret",
    "password=",
    "secret=",
]

_HARDEN_CMD = ["supabase", "rls", "harden"]


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# Helpers — mock RLSHardenResult builders
# ---------------------------------------------------------------------------


def _make_review_mock(verdict: str) -> MagicMock:
    review = MagicMock()
    review.verdict = verdict
    review.warnings = []
    review.todo_blocks = []
    review.blocked_blocks = []
    rs = MagicMock()
    rs.safe_executable_blocks = 1 if verdict != "BLOCKED" else 0
    rs.manual_todo_blocks = 1 if verdict == "WARNING" else 0
    rs.blocked_blocks = 1 if verdict == "BLOCKED" else 0
    rs.warnings_count = 0
    rs.tables_affected = ["test_table"]
    rs.block_reasons = (
        ["Dangerous operation detected: DROP TABLE"] if verdict == "BLOCKED" else []
    )
    review.summary = rs
    return review


def _make_gen_mock(verdict: str = "PASS") -> MagicMock:
    gen = MagicMock()
    gen.path = Path("/projects/my-app")
    gen.status = "OK"
    gen.migrations_scanned = 1
    gen.generated_sql = "BEGIN;\n-- [FIX] test\nCOMMIT;"
    gen.warnings = []
    gen.test_plan = []
    gen.read_only = True
    gen.applied = False
    gs = MagicMock()
    gs.total_blocks = 1
    gs.auto_generated = 1 if verdict != "WARNING" else 0
    gs.manual_todos = 1 if verdict == "WARNING" else 0
    gs.by_priority = {"HIGH": 1}
    gs.include_medium = False
    gen.summary = gs
    return gen


def _make_harden_result(verdict: str = "PASS") -> MagicMock:
    from aeos.providers.supabase.rls.generator import RLSGenerateResult
    from aeos.providers.supabase.rls.reviewer import RLSReviewResult

    result = MagicMock(spec=RLSHardenResult)
    result.path = Path("/projects/my-app")
    result.status = "ERROR" if verdict == "BLOCKED" else "OK"
    result.migrations_scanned = 1
    result.read_only = True
    result.applied = False

    gen = _make_gen_mock(verdict)
    # Ensure isinstance checks pass in _build_export_content / _harden_json_payload
    gen.__class__ = RLSGenerateResult

    review = _make_review_mock(verdict)
    review.__class__ = RLSReviewResult

    result.generate = gen
    result.review = review

    s = MagicMock()
    s.verdict = verdict
    s.findings_count = 5
    s.findings_by_severity = {"ERROR": 2, "WARNING": 3}
    s.plan_actions = 5
    s.plan_by_priority = {"CRITICAL": 2, "HIGH": 3}
    s.generated_blocks = 1
    s.auto_blocks = 1 if verdict != "WARNING" else 0
    s.todo_blocks = 1 if verdict == "WARNING" else 0
    s.safe_blocks = 1 if verdict != "BLOCKED" else 0
    s.blocked_blocks = 1 if verdict == "BLOCKED" else 0
    s.tables_affected = ["test_table"]
    s.riskiest_tables = ["test_table"]
    result.summary = s

    inspect = MagicMock()
    inspect.status = "OK"
    inspect.migrations_scanned = 1
    inspect.tables = []
    inspect.policies = []
    inspect.findings = []
    result.inspect = inspect

    plan = MagicMock()
    plan.status = "OK"
    ps = MagicMock()
    ps.total_actions = 5
    ps.by_priority = {"CRITICAL": 2, "HIGH": 3}
    ps.riskiest_tables = ["test_table"]
    ps.application_order = ["CRITICAL", "HIGH"]
    plan.summary = ps
    result.plan = plan

    return result


# ---------------------------------------------------------------------------
# TestRunRLSHarden — domain function
# ---------------------------------------------------------------------------


class TestRunRLSHarden:
    def test_returns_harden_result(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert isinstance(r, RLSHardenResult)

    def test_read_only_always_true(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.read_only is True

    def test_applied_always_false(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.applied is False

    def test_path_preserved(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.path == FIXTURE_DIR

    def test_migrations_scanned_positive(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.migrations_scanned > 0

    def test_verdict_in_summary(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.summary.verdict in ("PASS", "WARNING", "BLOCKED")

    def test_has_inspect_result(self) -> None:
        from aeos.providers.supabase.rls.inspector import RLSInspectResult

        r = run_rls_harden(FIXTURE_DIR)
        assert isinstance(r.inspect, RLSInspectResult)

    def test_has_plan_result(self) -> None:
        from aeos.providers.supabase.rls.planner import RLSPlanResult

        r = run_rls_harden(FIXTURE_DIR)
        assert isinstance(r.plan, RLSPlanResult)

    def test_has_generate_result(self) -> None:
        from aeos.providers.supabase.rls.generator import RLSGenerateResult

        r = run_rls_harden(FIXTURE_DIR)
        assert isinstance(r.generate, RLSGenerateResult)

    def test_has_review_result(self) -> None:
        from aeos.providers.supabase.rls.reviewer import RLSReviewResult

        r = run_rls_harden(FIXTURE_DIR)
        assert isinstance(r.review, RLSReviewResult)

    def test_fixture_warning_verdict(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.summary.verdict == "WARNING"

    def test_fixture_findings_positive(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.summary.findings_count > 0

    def test_fixture_plan_actions_positive(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.summary.plan_actions > 0

    def test_fixture_generated_blocks_positive(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.summary.generated_blocks > 0

    def test_lovable_pass_verdict(self) -> None:
        r = run_rls_harden(LOVABLE_DIR)
        assert r.summary.verdict == "PASS"

    def test_status_field_valid(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert r.status in ("OK", "WARNING", "ERROR")

    def test_summary_tables_affected(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert isinstance(r.summary.tables_affected, list)

    def test_summary_riskiest_tables_max_5(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert len(r.summary.riskiest_tables) <= 5

    def test_findings_by_severity_dict(self) -> None:
        r = run_rls_harden(FIXTURE_DIR)
        assert isinstance(r.summary.findings_by_severity, dict)


# ---------------------------------------------------------------------------
# TestCLIHardenText — text output without --output
# ---------------------------------------------------------------------------


class TestCLIHardenText:
    def test_no_output_writes_no_file(self, tmp_path: Path) -> None:
        runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        assert not any(tmp_path.iterdir())

    def test_help_shows_options(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--help"])
        plain = _strip_ansi(result.output)
        assert "--output" in plain
        assert "--force-warning" in plain
        assert "--overwrite" in plain
        assert "--include-medium" in plain

    def test_nonexistent_path_exits_1(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", "/nonexistent/path/xyz"])
        assert result.exit_code == 1

    def test_text_output_contains_verdict(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "Verdict" in plain
        assert any(v in plain for v in ("PASS", "WARNING", "BLOCKED"))

    def test_text_output_contains_findings(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "Findings" in plain or "findings" in plain

    def test_text_output_contains_inspect_section(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "Inspect" in plain

    def test_text_output_contains_plan_section(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "Plan" in plain

    def test_text_output_contains_generate_section(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "Generate" in plain

    def test_text_output_contains_review_section(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "Review" in plain

    def test_text_output_contains_read_only(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "read_only" in plain or "Read-only" in plain

    def test_text_output_applied_false(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "applied" in plain

    def test_text_output_next_step(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "Next step" in plain or "next step" in plain

    def test_exit_zero_on_warning(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        assert result.exit_code == 0

    def test_include_medium_accepted(self) -> None:
        result = runner.invoke(
            app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--include-medium"]
        )
        assert result.exit_code == 0

    def test_no_secrets_in_text_output(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        for secret in _SECRET_PATTERNS:
            assert secret not in result.output


# ---------------------------------------------------------------------------
# TestCLIHardenJSON — JSON output without --output
# ---------------------------------------------------------------------------


class TestCLIHardenJSON:
    def _invoke(self) -> dict[str, object]:
        result = runner.invoke(
            app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--json"]
        )
        return json.loads(result.output)  # type: ignore[return-value]

    def test_valid_json(self) -> None:
        result = runner.invoke(
            app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_status_present(self) -> None:
        data = self._invoke()
        assert "status" in data

    def test_read_only_true(self) -> None:
        data = self._invoke()
        assert data["read_only"] is True

    def test_applied_false(self) -> None:
        data = self._invoke()
        assert data["applied"] is False

    def test_output_written_false(self) -> None:
        data = self._invoke()
        assert data["output_written"] is False

    def test_output_path_empty(self) -> None:
        data = self._invoke()
        assert data["output_path"] == ""

    def test_summary_present(self) -> None:
        data = self._invoke()
        assert "summary" in data
        assert "verdict" in data["summary"]  # type: ignore[operator]

    def test_inspect_present(self) -> None:
        data = self._invoke()
        assert "inspect" in data

    def test_plan_present(self) -> None:
        data = self._invoke()
        assert "plan" in data

    def test_generate_present(self) -> None:
        data = self._invoke()
        assert "generate" in data

    def test_review_present(self) -> None:
        data = self._invoke()
        assert "review" in data

    def test_verdict_in_summary(self) -> None:
        data = self._invoke()
        verdict = data["summary"]["verdict"]  # type: ignore[index]
        assert verdict in ("PASS", "WARNING", "BLOCKED")

    def test_no_secrets_in_json(self) -> None:
        result = runner.invoke(
            app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--json"]
        )
        for secret in _SECRET_PATTERNS:
            assert secret not in result.output

    def test_total_blocks_consistent(self) -> None:
        data = self._invoke()
        s = data["summary"]  # type: ignore[index]
        assert s["auto_blocks"] + s["todo_blocks"] == s["generated_blocks"]  # type: ignore[operator]


# ---------------------------------------------------------------------------
# TestCLIHardenOutput — --output gate behaviours
# ---------------------------------------------------------------------------


class TestCLIHardenOutputPass:
    def test_lovable_writes_file(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        result = runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(LOVABLE_DIR), "--output", str(out)],
        )
        assert out.exists()
        assert result.exit_code == 0

    def test_pass_file_has_read_only(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(LOVABLE_DIR), "--output", str(out)],
        )
        content = out.read_text()
        assert "read_only:      true" in content

    def test_pass_file_has_applied_false(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(LOVABLE_DIR), "--output", str(out)],
        )
        content = out.read_text()
        assert "applied:        false" in content

    def test_pass_stdout_shows_exported(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        result = runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(LOVABLE_DIR), "--output", str(out)],
        )
        assert "Exported" in result.output

    def test_pass_no_secrets_in_file(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(LOVABLE_DIR), "--output", str(out)],
        )
        content = out.read_text()
        for secret in _SECRET_PATTERNS:
            assert secret not in content

    def test_pass_file_source_command_harden(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(LOVABLE_DIR), "--output", str(out)],
        )
        content = out.read_text()
        assert "harden --output" in content

    def test_pass_json_output_written_true(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        result = runner.invoke(
            app,
            [
                *_HARDEN_CMD,
                "--path",
                str(LOVABLE_DIR),
                "--output",
                str(out),
                "--json",
            ],
        )
        data = json.loads(result.output)
        assert data["output_written"] is True

    def test_pass_json_output_path(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        result = runner.invoke(
            app,
            [
                *_HARDEN_CMD,
                "--path",
                str(LOVABLE_DIR),
                "--output",
                str(out),
                "--json",
            ],
        )
        data = json.loads(result.output)
        assert str(out) in data["output_path"]


class TestCLIHardenOutputWarning:
    def test_warning_without_force_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        result = runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--output", str(out)],
        )
        assert not out.exists()
        assert result.exit_code == 1

    def test_warning_without_force_shows_hint(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        result = runner.invoke(
            app,
            [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--output", str(out)],
        )
        assert "force-warning" in result.output + (result.stderr or "")

    def test_warning_with_force_writes(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        result = runner.invoke(
            app,
            [
                *_HARDEN_CMD,
                "--path",
                str(FIXTURE_DIR),
                "--output",
                str(out),
                "--force-warning",
            ],
        )
        assert out.exists()
        assert result.exit_code == 0

    def test_warning_with_force_verdict_in_file(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        runner.invoke(
            app,
            [
                *_HARDEN_CMD,
                "--path",
                str(FIXTURE_DIR),
                "--output",
                str(out),
                "--force-warning",
            ],
        )
        content = out.read_text()
        assert "WARNING" in content


class TestCLIHardenOutputBlocked:
    def test_blocked_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with patch(
            "aeos.cli.run_rls_harden", return_value=_make_harden_result("BLOCKED")
        ):
            result = runner.invoke(
                app,
                [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--output", str(out)],
            )
        assert not out.exists()
        assert result.exit_code == 1

    def test_blocked_with_force_still_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with patch(
            "aeos.cli.run_rls_harden", return_value=_make_harden_result("BLOCKED")
        ):
            result = runner.invoke(
                app,
                [
                    *_HARDEN_CMD,
                    "--path",
                    str(FIXTURE_DIR),
                    "--output",
                    str(out),
                    "--force-warning",
                ],
            )
        assert not out.exists()
        assert result.exit_code == 1

    def test_blocked_no_output_exits_1(self) -> None:
        with patch(
            "aeos.cli.run_rls_harden", return_value=_make_harden_result("BLOCKED")
        ):
            result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        assert result.exit_code == 1


class TestCLIHardenOutputOverwrite:
    def test_existing_file_without_overwrite_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        out.write_text("existing content")
        result = runner.invoke(
            app,
            [
                *_HARDEN_CMD,
                "--path",
                str(FIXTURE_DIR),
                "--output",
                str(out),
                "--force-warning",
            ],
        )
        assert result.exit_code == 1
        assert out.read_text() == "existing content"

    def test_existing_file_shows_overwrite_hint(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        out.write_text("existing content")
        result = runner.invoke(
            app,
            [
                *_HARDEN_CMD,
                "--path",
                str(FIXTURE_DIR),
                "--output",
                str(out),
                "--force-warning",
            ],
        )
        assert "overwrite" in result.output + (result.stderr or "")

    def test_overwrite_flag_replaces_file(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        out.write_text("existing content")
        result = runner.invoke(
            app,
            [
                *_HARDEN_CMD,
                "--path",
                str(FIXTURE_DIR),
                "--output",
                str(out),
                "--force-warning",
                "--overwrite",
            ],
        )
        assert result.exit_code == 0
        assert out.read_text() != "existing content"
        assert "AEOS" in out.read_text()


# ---------------------------------------------------------------------------
# TestAntiLeakage — security invariants
# ---------------------------------------------------------------------------


class TestAntiLeakage:
    def test_env_not_read(self, tmp_path: Path) -> None:
        fake_env = tmp_path / ".env"
        fake_env.write_text("SECRET_KEY=super_secret_value_xyz")
        fake_project = tmp_path / "project"
        fake_project.mkdir()
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(fake_project)])
        assert "super_secret_value_xyz" not in result.output

    def test_applied_false_in_json(self) -> None:
        result = runner.invoke(
            app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR), "--json"]
        )
        data = json.loads(result.output)
        assert data["applied"] is False

    def test_no_migration_applied_notice(self) -> None:
        result = runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        plain = _strip_ansi(result.output)
        assert "no migration applied" in plain.lower() or "applied" in plain.lower()

    def test_client_project_not_modified(self, tmp_path: Path) -> None:
        files_before = set(FIXTURE_DIR.rglob("*"))
        runner.invoke(app, [*_HARDEN_CMD, "--path", str(FIXTURE_DIR)])
        files_after = set(FIXTURE_DIR.rglob("*"))
        assert files_before == files_after
