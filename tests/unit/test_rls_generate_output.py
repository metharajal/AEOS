"""
Unit tests for aeos supabase rls generate --output (Sprint 2Y).
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from aeos.cli import _build_export_content, app
from aeos.providers.supabase.rls.generator import (
    RLSGenerateResult,
    RLSGenerateSummary,
)
from aeos.providers.supabase.rls.reviewer import (
    ReviewBlock,
    ReviewSummary,
    RLSReviewResult,
)

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _gen_result(
    auto: int = 2,
    todos: int = 0,
    sql: str = "BEGIN;\n-- [FIX] test\nCOMMIT;",
    warnings: list[str] | None = None,
) -> RLSGenerateResult:
    return RLSGenerateResult(
        path=Path("/projects/my-app"),
        status="OK",
        migrations_scanned=1,
        summary=RLSGenerateSummary(
            total_blocks=auto + todos,
            auto_generated=auto,
            manual_todos=todos,
            by_priority={"HIGH": auto + todos},
            include_medium=False,
        ),
        blocks=[],
        generated_sql=sql,
        warnings=warnings or [],
        test_plan=[],
        read_only=True,
        applied=False,
    )


def _review_result(
    verdict: str = "PASS",
    safe: int = 2,
    todos: int = 0,
    blocked: int = 0,
    block_reasons: list[str] | None = None,
    warnings: list[str] | None = None,
) -> RLSReviewResult:
    safe_blocks = [
        ReviewBlock(
            priority="HIGH",
            table="t",
            policy="p",
            risk_type="UPDATE_NO_WITH_CHECK",
            sql="-- fix",
            is_todo=False,
            classification="safe",
        )
        for _ in range(safe)
    ]
    todo_blocks = [
        ReviewBlock(
            priority="CRITICAL",
            table="t2",
            policy="p2",
            risk_type="SELECT_TOO_PERMISSIVE",
            sql="-- todo",
            is_todo=True,
            classification="todo",
        )
        for _ in range(todos)
    ]
    blocked_blocks = [
        ReviewBlock(
            priority="HIGH",
            table="t3",
            policy="p3",
            risk_type="NO_RLS",
            sql="DROP TABLE public.t3;",
            is_todo=False,
            classification="blocked",
            reasons=["Dangerous operation detected: DROP TABLE"],
        )
        for _ in range(blocked)
    ]
    summary = ReviewSummary(
        total_blocks=safe + todos + blocked,
        safe_executable_blocks=safe,
        manual_todo_blocks=todos,
        blocked_blocks=blocked,
        warnings_count=len(warnings or []),
        tables_affected=[],
        block_reasons=block_reasons or [],
    )
    return RLSReviewResult(
        path=Path("/projects/my-app"),
        status="OK",
        verdict=verdict,
        migrations_scanned=1,
        summary=summary,
        safe_blocks=safe_blocks,
        todo_blocks=todo_blocks,
        blocked_blocks=blocked_blocks,
        warnings=warnings or [],
        read_only=True,
        applied=False,
    )


def _cmd(out: Path, *extra: str) -> list[str]:
    """Build a generate --output invocation args list."""
    return [
        "supabase",
        "rls",
        "generate",
        "--path",
        str(FIXTURE_DIR),
        "--output",
        str(out),
        *extra,
    ]


# ---------------------------------------------------------------------------
# TestBuildExportContent
# ---------------------------------------------------------------------------


class TestBuildExportContent:
    def _make(
        self,
        verdict: str = "PASS",
        todos: int = 0,
        warnings: list[str] | None = None,
    ) -> str:
        gen = _gen_result(todos=todos, warnings=warnings or [])
        rev = _review_result(verdict=verdict, todos=todos, warnings=warnings or [])
        return _build_export_content(gen, rev)

    def test_contains_aeos_header(self) -> None:
        assert "AEOS RLS Migration Proposal" in self._make()

    def test_contains_read_only_true(self) -> None:
        assert "read_only:      true" in self._make()

    def test_contains_applied_false(self) -> None:
        assert "applied:        false" in self._make()

    def test_contains_verdict(self) -> None:
        assert "Verdict:        WARNING" in self._make(verdict="WARNING", todos=1)

    def test_contains_sql(self) -> None:
        content = self._make()
        assert "BEGIN;" in content
        assert "COMMIT;" in content

    def test_contains_not_applied_warning(self) -> None:
        assert "NOT been applied" in self._make()

    def test_warnings_section_present(self) -> None:
        assert "Check profiles table." in self._make(warnings=["Check profiles table."])

    def test_todo_section_present(self) -> None:
        content = self._make(verdict="WARNING", todos=1)
        assert "Manual TODOs" in content
        assert "SELECT_TOO_PERMISSIVE" in content

    def test_no_secret_in_content(self) -> None:
        content = self._make().lower()
        for pattern in _SECRET_PATTERNS:
            assert pattern.lower() not in content

    def test_date_present(self) -> None:
        today = datetime.date.today().isoformat()
        assert today in self._make()


# ---------------------------------------------------------------------------
# TestCLIGenerateWithoutOutput
# ---------------------------------------------------------------------------


class TestCLIGenerateWithoutOutput:
    def test_no_output_option_writes_no_file(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["supabase", "rls", "generate", "--path", str(FIXTURE_DIR)]
        )
        assert result.exit_code in (0, 1)
        assert not any(tmp_path.iterdir())

    def test_help_shows_output_option(self) -> None:
        result = runner.invoke(app, ["supabase", "rls", "generate", "--help"])
        plain = _strip_ansi(result.output)
        assert "--output" in plain
        assert "--force-warning" in plain
        assert "--overwrite" in plain


# ---------------------------------------------------------------------------
# TestCLIGenerateOutputPass
# ---------------------------------------------------------------------------


class TestCLIGenerateOutputPass:
    def _patch(self, todos: int = 0, verdict: str = "PASS") -> tuple[object, object]:
        return (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result(todos=todos)),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict=verdict, todos=todos),
            ),
        )

    def test_writes_file_on_pass(self, tmp_path: Path) -> None:
        out = tmp_path / "rls_proposal.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_output_contains_read_only(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            runner.invoke(app, _cmd(out))
        assert "read_only:      true" in out.read_text()

    def test_output_contains_applied_false(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            runner.invoke(app, _cmd(out))
        assert "applied:        false" in out.read_text()

    def test_output_no_secrets(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            runner.invoke(app, _cmd(out))
        content = out.read_text().lower()
        for secret in _SECRET_PATTERNS:
            assert secret.lower() not in content

    def test_stdout_shows_exported_path(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert "Exported:" in result.output

    def test_no_migration_applied_notice_in_file(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            runner.invoke(app, _cmd(out))
        assert "NOT been applied" in out.read_text()


# ---------------------------------------------------------------------------
# TestCLIGenerateOutputWarning
# ---------------------------------------------------------------------------


class TestCLIGenerateOutputWarning:
    def test_warning_without_force_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result(todos=1)),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="WARNING", todos=1),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert result.exit_code == 1
        assert not out.exists()

    def test_warning_without_force_shows_hint(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result(todos=1)),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="WARNING", todos=1),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert "--force-warning" in result.output

    def test_warning_with_force_writes_file(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result(todos=1)),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="WARNING", todos=1),
            ),
        ):
            result = runner.invoke(app, _cmd(out, "--force-warning"))
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_warning_force_file_contains_verdict(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result(todos=1)),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="WARNING", todos=1),
            ),
        ):
            runner.invoke(app, _cmd(out, "--force-warning"))
        assert "Verdict:        WARNING" in out.read_text()


# ---------------------------------------------------------------------------
# TestCLIGenerateOutputBlocked
# ---------------------------------------------------------------------------


class TestCLIGenerateOutputBlocked:
    def test_blocked_refuses_always(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(
                    verdict="BLOCKED",
                    blocked=1,
                    block_reasons=["Dangerous: DROP TABLE"],
                ),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert result.exit_code == 1
        assert not out.exists()

    def test_blocked_with_force_warning_still_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="BLOCKED", blocked=1),
            ),
        ):
            result = runner.invoke(app, _cmd(out, "--force-warning"))
        assert result.exit_code == 1
        assert not out.exists()

    def test_blocked_shows_block_reasons(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(
                    verdict="BLOCKED",
                    blocked=1,
                    block_reasons=["[t3] Dangerous: DROP TABLE"],
                ),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert "DROP TABLE" in result.output


# ---------------------------------------------------------------------------
# TestCLIGenerateOutputOverwrite
# ---------------------------------------------------------------------------


class TestCLIGenerateOutputOverwrite:
    def test_existing_file_without_overwrite_refuses(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        out.write_text("old content")
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert result.exit_code == 1
        assert out.read_text() == "old content"

    def test_existing_file_without_overwrite_shows_hint(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        out.write_text("old content")
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            result = runner.invoke(app, _cmd(out))
        assert "--overwrite" in result.output

    def test_existing_file_with_overwrite_succeeds(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        out.write_text("old content")
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            result = runner.invoke(app, _cmd(out, "--overwrite"))
        assert result.exit_code == 0
        assert out.read_text() != "old content"
        assert "AEOS RLS Migration Proposal" in out.read_text()


# ---------------------------------------------------------------------------
# TestAntiLeakage
# ---------------------------------------------------------------------------


class TestAntiLeakage:
    def test_env_file_not_read(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("SUPABASE_URL=https://secret.supabase.co")
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            runner.invoke(app, _cmd(out))
        if out.exists():
            assert "https://secret.supabase.co" not in out.read_text()

    def test_applied_always_false_in_output(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            runner.invoke(app, _cmd(out))
        assert "applied:        false" in out.read_text()

    def test_no_migration_applied_to_database(self, tmp_path: Path) -> None:
        out = tmp_path / "rls.sql"
        with (
            patch("aeos.cli.run_rls_generate", return_value=_gen_result()),
            patch(
                "aeos.cli.run_rls_review_from_result",
                return_value=_review_result(verdict="PASS"),
            ),
        ):
            runner.invoke(app, _cmd(out))
        assert "NOT been applied" in out.read_text()


# ---------------------------------------------------------------------------
# TestCLIGenerateOutputOnFixture (real fixtures, no mocks)
# ---------------------------------------------------------------------------


class TestCLIGenerateOutputOnFixture:
    def test_lovable_pass_verdict_writes_file(self, tmp_path: Path) -> None:
        out = tmp_path / "rls_lovable.sql"
        result = runner.invoke(
            app,
            [
                "supabase",
                "rls",
                "generate",
                "--path",
                str(LOVABLE_DIR),
                "--output",
                str(out),
            ],
        )
        # lovable fixture has only safe blocks → PASS → writes file
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text()
        assert "AEOS RLS Migration Proposal" in content
        assert "read_only:      true" in content
        assert "applied:        false" in content

    def test_lovable_output_no_secrets(self, tmp_path: Path) -> None:
        out = tmp_path / "rls_lovable.sql"
        runner.invoke(
            app,
            [
                "supabase",
                "rls",
                "generate",
                "--path",
                str(LOVABLE_DIR),
                "--output",
                str(out),
            ],
        )
        if out.exists():
            content = out.read_text().lower()
            for secret in _SECRET_PATTERNS:
                assert secret.lower() not in content

    def test_supabase_rls_fixture_warning_refuses_without_force(
        self, tmp_path: Path
    ) -> None:
        out = tmp_path / "rls_fixture.sql"
        result = runner.invoke(app, _cmd(out))
        # supabase_rls fixture has TODO blocks → WARNING → refused
        assert result.exit_code == 1
        assert not out.exists()

    def test_supabase_rls_fixture_warning_with_force_writes(
        self, tmp_path: Path
    ) -> None:
        out = tmp_path / "rls_fixture.sql"
        result = runner.invoke(app, _cmd(out, "--force-warning"))
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text()
        assert "AEOS RLS Migration Proposal" in content
        assert "read_only:      true" in content
        assert "applied:        false" in content
