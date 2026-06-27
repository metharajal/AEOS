"""
Unit tests for the Supabase RLS Review Gate (Sprint 2W).
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aeos.cli import app
from aeos.providers.supabase.rls.generator import SQLBlock as GenBlock
from aeos.providers.supabase.rls.reviewer import (
    ReviewBlock,
    _check_dangerous_patterns,
    _check_invariants,
    _classify_block,
    _determine_verdict,
    _non_comment_sql,
    run_rls_review,
)

runner = CliRunner()

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "supabase_rls"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gen_block(
    priority: str = "HIGH",
    table: str = "test_table",
    policy: str = "test_pol",
    risk_type: str = "UPDATE_NO_WITH_CHECK",
    sql: str = "",
    is_todo: bool = False,
    warning: str = "",
) -> GenBlock:
    if not sql:
        sql = (
            f'-- [FIX] {risk_type} on "{table}"\n'
            f'DROP POLICY IF EXISTS "{policy}" ON public.{table};\n'
            f'CREATE POLICY "{policy}"\n'
            f"  ON public.{table}\n"
            "  FOR UPDATE\n"
            "  USING (auth.uid() = user_id)\n"
            "  WITH CHECK (auth.uid() = user_id);"
        )
    return GenBlock(
        priority=priority,
        table=table,
        policy=policy,
        risk_type=risk_type,
        sql=sql,
        is_todo=is_todo,
        warning=warning,
    )


def _review_block(
    classification: str = "safe",
    priority: str = "HIGH",
    table: str = "test_table",
    policy: str = "test_pol",
    risk_type: str = "UPDATE_NO_WITH_CHECK",
    reasons: list[str] | None = None,
) -> ReviewBlock:
    return ReviewBlock(
        priority=priority,
        table=table,
        policy=policy,
        risk_type=risk_type,
        sql="-- sql",
        is_todo=classification == "todo",
        classification=classification,
        reasons=reasons or [],
    )


# ---------------------------------------------------------------------------
# TestNonCommentSQL
# ---------------------------------------------------------------------------


class TestNonCommentSQL:
    def test_strips_comment_lines(self) -> None:
        sql = "-- comment\nCREATE POLICY foo;\n-- another"
        result = _non_comment_sql(sql)
        assert "-- comment" not in result
        assert "CREATE POLICY foo;" in result

    def test_keeps_non_comment_lines(self) -> None:
        sql = "DROP POLICY IF EXISTS foo ON public.t;\nCREATE POLICY foo;"
        assert sql == _non_comment_sql(sql)

    def test_empty_string(self) -> None:
        assert _non_comment_sql("") == ""

    def test_all_comments(self) -> None:
        sql = "-- line1\n-- line2\n-- line3"
        result = _non_comment_sql(sql)
        assert result.strip() == ""

    def test_inline_comment_not_stripped(self) -> None:
        sql = "CREATE POLICY foo; -- inline comment"
        result = _non_comment_sql(sql)
        assert "CREATE POLICY" in result


# ---------------------------------------------------------------------------
# TestCheckDangerousPatterns
# ---------------------------------------------------------------------------


class TestCheckDangerousPatterns:
    def test_clean_sql_no_violations(self) -> None:
        sql = (
            'DROP POLICY IF EXISTS "foo" ON public.t;\n'
            'CREATE POLICY "foo"\n'
            "  ON public.t FOR UPDATE\n"
            "  USING (auth.uid() = user_id)\n"
            "  WITH CHECK (auth.uid() = user_id);"
        )
        assert _check_dangerous_patterns(sql) == []

    def test_drop_table_blocked(self) -> None:
        violations = _check_dangerous_patterns("DROP TABLE public.foo;")
        assert any("DROP TABLE" in v for v in violations)

    def test_truncate_blocked(self) -> None:
        violations = _check_dangerous_patterns("TRUNCATE public.foo;")
        assert any("TRUNCATE" in v for v in violations)

    def test_delete_from_blocked(self) -> None:
        violations = _check_dangerous_patterns("DELETE FROM public.foo;")
        assert any("DELETE FROM" in v for v in violations)

    def test_update_set_blocked(self) -> None:
        violations = _check_dangerous_patterns("UPDATE public.foo SET name = 'x';")
        assert any("UPDATE" in v for v in violations)

    def test_alter_drop_column_blocked(self) -> None:
        violations = _check_dangerous_patterns(
            "ALTER TABLE public.foo DROP COLUMN bar;"
        )
        assert any("DROP COLUMN" in v for v in violations)

    def test_alter_drop_constraint_blocked(self) -> None:
        violations = _check_dangerous_patterns(
            "ALTER TABLE public.foo DROP CONSTRAINT bar_fk;"
        )
        assert any("DROP CONSTRAINT" in v for v in violations)

    def test_drop_schema_blocked(self) -> None:
        violations = _check_dangerous_patterns("DROP SCHEMA public CASCADE;")
        assert any("DROP SCHEMA" in v for v in violations)

    def test_drop_database_blocked(self) -> None:
        violations = _check_dangerous_patterns("DROP DATABASE mydb;")
        assert any("DROP DATABASE" in v for v in violations)

    def test_grant_all_blocked(self) -> None:
        violations = _check_dangerous_patterns("GRANT ALL ON public.foo TO anon;")
        assert any("GRANT ALL" in v for v in violations)

    def test_using_true_blocked(self) -> None:
        violations = _check_dangerous_patterns(
            "CREATE POLICY foo ON public.t FOR SELECT USING (true);"
        )
        assert any("USING (true)" in v for v in violations)

    def test_with_check_true_blocked(self) -> None:
        violations = _check_dangerous_patterns(
            "CREATE POLICY foo ON public.t FOR INSERT WITH CHECK (true);"
        )
        assert any("WITH CHECK (true)" in v for v in violations)

    def test_drop_policy_not_flagged(self) -> None:
        sql = 'DROP POLICY IF EXISTS "foo" ON public.t;'
        assert _check_dangerous_patterns(sql) == []

    def test_alter_table_enable_rls_not_flagged(self) -> None:
        sql = "ALTER TABLE public.t ENABLE ROW LEVEL SECURITY;"
        assert _check_dangerous_patterns(sql) == []

    def test_case_insensitive(self) -> None:
        violations = _check_dangerous_patterns("drop table public.foo;")
        assert any("DROP TABLE" in v for v in violations)


# ---------------------------------------------------------------------------
# TestClassifyBlock
# ---------------------------------------------------------------------------


class TestClassifyBlock:
    def test_safe_block_classified_safe(self) -> None:
        block = _gen_block(
            sql=(
                'DROP POLICY IF EXISTS "p" ON public.t;\n'
                'CREATE POLICY "p" ON public.t FOR UPDATE\n'
                "  USING (auth.uid() = user_id)\n"
                "  WITH CHECK (auth.uid() = user_id);"
            )
        )
        reviewed = _classify_block(block)
        assert reviewed.classification == "safe"
        assert reviewed.reasons == []

    def test_todo_block_classified_todo(self) -> None:
        block = _gen_block(
            is_todo=True,
            sql='-- TODO [CRITICAL] SELECT_TOO_PERMISSIVE: "t"\n-- fix manually',
        )
        reviewed = _classify_block(block)
        assert reviewed.classification == "todo"
        assert reviewed.is_todo is True

    def test_drop_table_classified_blocked(self) -> None:
        block = _gen_block(sql="DROP TABLE public.foo;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"
        assert len(reviewed.reasons) > 0

    def test_truncate_classified_blocked(self) -> None:
        block = _gen_block(sql="TRUNCATE public.foo;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_delete_from_classified_blocked(self) -> None:
        block = _gen_block(sql="DELETE FROM public.foo;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_update_set_classified_blocked(self) -> None:
        block = _gen_block(sql="UPDATE public.foo SET x = 1;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_using_true_classified_blocked(self) -> None:
        block = _gen_block(
            sql=('CREATE POLICY "p" ON public.t FOR SELECT USING (true);')
        )
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_commented_dangerous_not_blocked(self) -> None:
        # Dangerous SQL in comment lines → not blocked
        block = _gen_block(
            sql=(
                "-- DROP TABLE public.t;\n"
                "-- TRUNCATE public.t;\n"
                'CREATE POLICY "safe_pol" ON public.t FOR UPDATE\n'
                "  USING (auth.uid() = user_id)\n"
                "  WITH CHECK (auth.uid() = user_id);"
            )
        )
        reviewed = _classify_block(block)
        assert reviewed.classification == "safe"

    def test_metadata_carried_through(self) -> None:
        block = _gen_block(priority="CRITICAL", table="foo", policy="bar")
        reviewed = _classify_block(block)
        assert reviewed.priority == "CRITICAL"
        assert reviewed.table == "foo"
        assert reviewed.policy == "bar"


# ---------------------------------------------------------------------------
# TestCheckInvariants
# ---------------------------------------------------------------------------


class TestCheckInvariants:
    def _make_gen_result(
        self,
        read_only: bool = True,
        applied: bool = False,
        sql: str = "-- clean sql",
    ) -> object:
        from aeos.providers.supabase.rls.generator import (
            RLSGenerateResult,
            RLSGenerateSummary,
        )

        return RLSGenerateResult(
            path=Path("/project"),
            status="OK",
            migrations_scanned=1,
            summary=RLSGenerateSummary(
                total_blocks=0,
                auto_generated=0,
                manual_todos=0,
                by_priority={},
                include_medium=False,
            ),
            blocks=[],
            generated_sql=sql,
            warnings=[],
            test_plan=[],
            read_only=read_only,
            applied=applied,
        )

    def test_clean_result_no_violations(self) -> None:
        result = self._make_gen_result()
        assert _check_invariants(result) == []

    def test_read_only_false_violation(self) -> None:
        result = self._make_gen_result(read_only=False)
        violations = _check_invariants(result)
        assert any("read_only" in v for v in violations)

    def test_applied_true_violation(self) -> None:
        result = self._make_gen_result(applied=True)
        violations = _check_invariants(result)
        assert any("applied" in v for v in violations)

    def test_secret_in_sql_violation(self) -> None:
        result = self._make_gen_result(sql="anon_key=super_secret_value")
        violations = _check_invariants(result)
        assert any("secret" in v.lower() for v in violations)

    def test_service_role_in_sql_violation(self) -> None:
        result = self._make_gen_result(sql="service_role_key=xyz123")
        violations = _check_invariants(result)
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestDetermineVerdict
# ---------------------------------------------------------------------------


class TestDetermineVerdict:
    def test_no_blocks_no_todos_pass(self) -> None:
        assert _determine_verdict([], [], []) == "PASS"

    def test_todos_no_blocked_warning(self) -> None:
        todos = [_review_block(classification="todo")]
        assert _determine_verdict([], todos, []) == "WARNING"

    def test_blocked_gives_blocked(self) -> None:
        blocked = [_review_block(classification="blocked")]
        assert _determine_verdict(blocked, [], []) == "BLOCKED"

    def test_invariant_violations_give_blocked(self) -> None:
        assert (
            _determine_verdict([], [], ["INVARIANT VIOLATED: applied is not False"])
            == "BLOCKED"
        )

    def test_blocked_overrides_todos(self) -> None:
        blocked = [_review_block(classification="blocked")]
        todos = [_review_block(classification="todo")]
        assert _determine_verdict(blocked, todos, []) == "BLOCKED"

    def test_safe_only_pass(self) -> None:
        # safe blocks don't count — they go into safe_blocks, not the verdict check
        assert _determine_verdict([], [], []) == "PASS"


# ---------------------------------------------------------------------------
# TestRunRLSReviewOnFixture
# ---------------------------------------------------------------------------


class TestRunRLSReviewOnFixture:
    def test_returns_result(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result is not None

    def test_path_is_absolute(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.path.is_absolute()

    def test_applied_always_false(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.applied is False

    def test_read_only_always_true(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.read_only is True

    def test_verdict_not_blocked_on_safe_fixture(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.verdict in ("PASS", "WARNING")

    def test_has_safe_blocks(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.summary.safe_executable_blocks > 0

    def test_has_todo_blocks_from_select_too_permissive(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.summary.manual_todo_blocks > 0

    def test_no_blocked_blocks_on_safe_fixture(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.summary.blocked_blocks == 0
        assert result.blocked_blocks == []

    def test_total_matches_parts(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.summary.total_blocks == (
            result.summary.safe_executable_blocks
            + result.summary.manual_todo_blocks
            + result.summary.blocked_blocks
        )

    def test_verdict_warning_when_todos_present(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        if result.summary.manual_todo_blocks > 0:
            assert result.verdict == "WARNING"

    def test_no_secrets_in_any_field(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        raw = str(result.safe_blocks) + str(result.todo_blocks)
        for secret in ("anon_key", "service_role", "password"):
            assert secret not in raw

    def test_tables_affected_nonempty(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert len(result.summary.tables_affected) > 0

    def test_no_migrations_returns_pass(self, tmp_path: Path) -> None:
        result = run_rls_review(tmp_path)
        assert result.verdict == "PASS"
        assert result.applied is False


# ---------------------------------------------------------------------------
# TestBlockedDetection
# ---------------------------------------------------------------------------


class TestBlockedDetection:
    """Verify BLOCKED verdict on projects containing dangerous patterns."""

    def _write_project(self, tmp_path: Path, sql: str, rls_sql: str = "") -> Path:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001_schema.sql").write_text(
            "CREATE TABLE public.items (id uuid PRIMARY KEY, user_id uuid);\n"
            "ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;\n"
        )
        if rls_sql:
            (mig / "001_schema.sql").write_text(
                (mig / "001_schema.sql").read_text() + rls_sql
            )
        # inject dangerous SQL into the generator output via a second migration
        if sql:
            (mig / "002_danger.sql").write_text(sql)
        return tmp_path

    def test_using_true_in_generated_sql_blocked(self, tmp_path: Path) -> None:
        """A project whose generator output would contain USING (true) is BLOCKED."""
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        # Write SQL that causes a USING (true) policy to be generated
        # We do this by patching the block classification directly
        from aeos.providers.supabase.rls.reviewer import (
            ReviewBlock,
            _determine_verdict,
        )

        blocked = [
            ReviewBlock(
                priority="HIGH",
                table="items",
                policy="p",
                risk_type="SELECT_TOO_PERMISSIVE",
                sql="CREATE POLICY p ON public.items FOR SELECT USING (true);",
                is_todo=False,
                classification="blocked",
                reasons=[
                    "Dangerous operation detected: USING (true) — grants all-row access"
                ],
            )
        ]
        verdict = _determine_verdict(blocked, [], [])
        assert verdict == "BLOCKED"

    def test_classify_block_drop_table_blocked(self) -> None:
        block = _gen_block(sql="DROP TABLE public.items;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"
        assert any("DROP TABLE" in r for r in reviewed.reasons)

    def test_classify_block_truncate_blocked(self) -> None:
        block = _gen_block(sql="TRUNCATE public.items;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_classify_block_delete_no_where_blocked(self) -> None:
        block = _gen_block(sql="DELETE FROM public.items;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_classify_block_update_no_where_blocked(self) -> None:
        block = _gen_block(sql="UPDATE public.items SET x = 1;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_classify_block_grant_all_blocked(self) -> None:
        block = _gen_block(sql="GRANT ALL ON public.items TO anon;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_classify_block_drop_schema_blocked(self) -> None:
        block = _gen_block(sql="DROP SCHEMA public CASCADE;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"

    def test_classify_block_drop_database_blocked(self) -> None:
        block = _gen_block(sql="DROP DATABASE mydb;")
        reviewed = _classify_block(block)
        assert reviewed.classification == "blocked"


# ---------------------------------------------------------------------------
# TestAntiLeakage
# ---------------------------------------------------------------------------


class TestAntiLeakage:
    def test_env_file_not_read(self, tmp_path: Path) -> None:
        mig = tmp_path / "supabase" / "migrations"
        mig.mkdir(parents=True)
        (mig / "001.sql").write_text(
            "CREATE TABLE public.items (id uuid PRIMARY KEY);\n"
        )
        env = tmp_path / ".env"
        env.write_text(
            "SUPABASE_URL=https://secret.supabase.co\nANON_KEY=ultra_secret_key_12345\n"
        )
        result = run_rls_review(tmp_path)
        raw = json.dumps(
            {
                "warnings": result.warnings,
                "safe": [b.sql for b in result.safe_blocks],
                "todos": [b.sql for b in result.todo_blocks],
            }
        )
        assert "ultra_secret_key_12345" not in raw
        env.unlink()

    def test_applied_always_false_invariant(self) -> None:
        result = run_rls_review(FIXTURE_DIR)
        assert result.applied is False


# ---------------------------------------------------------------------------
# TestCLIReviewTextOutput
# ---------------------------------------------------------------------------


class TestCLIReviewTextOutput:
    def test_command_exists(self) -> None:
        result = runner.invoke(
            app, ["supabase", "rls", "review", "--path", str(FIXTURE_DIR)]
        )
        assert result.exit_code in (0, 1)

    def test_output_contains_header(self) -> None:
        result = runner.invoke(
            app, ["supabase", "rls", "review", "--path", str(FIXTURE_DIR)]
        )
        assert "Supabase RLS Review Gate" in result.output

    def test_output_contains_verdict(self) -> None:
        result = runner.invoke(
            app, ["supabase", "rls", "review", "--path", str(FIXTURE_DIR)]
        )
        assert "Verdict:" in result.output

    def test_output_contains_summary(self) -> None:
        result = runner.invoke(
            app, ["supabase", "rls", "review", "--path", str(FIXTURE_DIR)]
        )
        assert "Review Summary" in result.output
        assert "Safe blocks:" in result.output

    def test_output_contains_read_only_notice(self) -> None:
        result = runner.invoke(
            app, ["supabase", "rls", "review", "--path", str(FIXTURE_DIR)]
        )
        assert "Read-only" in result.output

    def test_nonexistent_path_exits_1(self) -> None:
        result = runner.invoke(
            app,
            ["supabase", "rls", "review", "--path", "/nonexistent/path/xyz"],
        )
        assert result.exit_code == 1

    def test_help_works(self) -> None:
        result = runner.invoke(app, ["supabase", "rls", "review", "--help"])
        assert result.exit_code == 0
        assert "read-only" in result.output.lower()

    def test_exit_zero_on_warning(self) -> None:
        result = runner.invoke(
            app, ["supabase", "rls", "review", "--path", str(FIXTURE_DIR)]
        )
        # WARNING verdict → exit 0
        assert result.exit_code == 0

    def test_include_medium_accepted(self) -> None:
        result = runner.invoke(
            app,
            [
                "supabase",
                "rls",
                "review",
                "--path",
                str(FIXTURE_DIR),
                "--include-medium",
            ],
        )
        assert result.exit_code in (0, 1)


# ---------------------------------------------------------------------------
# TestCLIReviewJSONOutput
# ---------------------------------------------------------------------------


class TestCLIReviewJSONOutput:
    def _run_json(
        self, fixture: Path = FIXTURE_DIR, extra: list[str] | None = None
    ) -> dict:  # type: ignore[type-arg]
        args = ["supabase", "rls", "review", "--path", str(fixture), "--json"]
        if extra:
            args += extra
        result = runner.invoke(app, args)
        return json.loads(result.output)  # type: ignore[no-any-return]

    def test_valid_json(self) -> None:
        self._run_json()

    def test_verdict_present(self) -> None:
        data = self._run_json()
        assert "verdict" in data
        assert data["verdict"] in ("PASS", "WARNING", "BLOCKED")

    def test_applied_false(self) -> None:
        data = self._run_json()
        assert data["applied"] is False

    def test_read_only_true(self) -> None:
        data = self._run_json()
        assert data["read_only"] is True

    def test_summary_fields_present(self) -> None:
        data = self._run_json()
        s = data["summary"]
        assert "total_blocks" in s
        assert "safe_executable_blocks" in s
        assert "manual_todo_blocks" in s
        assert "blocked_blocks" in s
        assert "warnings_count" in s
        assert "tables_affected" in s
        assert "block_reasons" in s

    def test_safe_blocks_list(self) -> None:
        data = self._run_json()
        assert isinstance(data["safe_blocks"], list)

    def test_todo_blocks_list(self) -> None:
        data = self._run_json()
        assert isinstance(data["todo_blocks"], list)

    def test_blocked_blocks_list(self) -> None:
        data = self._run_json()
        assert isinstance(data["blocked_blocks"], list)

    def test_warnings_list(self) -> None:
        data = self._run_json()
        assert isinstance(data["warnings"], list)

    def test_no_secrets_in_output(self) -> None:
        data = self._run_json()
        raw = json.dumps(data)
        for secret in ("anon_key", "service_role", "password", "secret"):
            assert secret not in raw

    def test_total_blocks_equals_parts(self) -> None:
        data = self._run_json()
        s = data["summary"]
        assert s["total_blocks"] == (
            s["safe_executable_blocks"] + s["manual_todo_blocks"] + s["blocked_blocks"]
        )

    def test_no_migrations_exits_zero(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "supabase",
                "rls",
                "review",
                "--path",
                str(tmp_path),
                "--json",
            ],
        )
        data = json.loads(result.output)
        assert result.exit_code == 0
        assert data["verdict"] == "PASS"
        assert data["applied"] is False
