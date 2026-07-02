"""Unit tests for AEOS Verify — spec parsing and check runner (CAP-VERIFY-1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.verify.runner import run_check, run_verification
from aeos.verify.spec import Check, VerificationSpec, load_spec

runner = CliRunner()

# ---------------------------------------------------------------------------
# Spec parsing
# ---------------------------------------------------------------------------


def _write_spec(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.verify.toml"
    p.write_text(content, encoding="utf-8")
    return p


class TestLoadSpec:
    def test_parses_valid_spec(self, tmp_path: Path) -> None:
        p = _write_spec(
            tmp_path,
            '[sprint]\nid = "S-1"\ndescription = "test sprint"\n'
            '[[checks]]\nname = "check one"\n'
            'command = ["python", "-c", "pass"]\nexpect_exit = 0\ntimeout = 10\n',
        )
        spec = load_spec(p)
        assert spec.sprint_id == "S-1"
        assert spec.description == "test sprint"
        assert len(spec.checks) == 1
        assert spec.checks[0].name == "check one"
        assert spec.checks[0].command == ["python", "-c", "pass"]
        assert spec.checks[0].expect_exit == 0
        assert spec.checks[0].timeout == 10

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_spec(tmp_path / "nonexistent.verify.toml")

    def test_raises_on_missing_sprint_section(self, tmp_path: Path) -> None:
        p = _write_spec(tmp_path, '[other]\nkey = "value"\n')
        with pytest.raises(ValueError, match="Missing \\[sprint\\] section"):
            load_spec(p)

    def test_raises_on_missing_sprint_id(self, tmp_path: Path) -> None:
        p = _write_spec(tmp_path, '[sprint]\ndescription = "no id"\n')
        with pytest.raises(ValueError, match="sprint\\.id"):
            load_spec(p)

    def test_raises_when_command_is_string(self, tmp_path: Path) -> None:
        p = _write_spec(
            tmp_path,
            '[sprint]\nid = "S-1"\n'
            '[[checks]]\nname = "bad"\ncommand = "grep foo bar"\n',
        )
        with pytest.raises(ValueError, match="must be a list"):
            load_spec(p)

    def test_raises_on_empty_command_list(self, tmp_path: Path) -> None:
        p = _write_spec(
            tmp_path,
            '[sprint]\nid = "S-1"\n'
            '[[checks]]\nname = "empty"\ncommand = []\n',
        )
        with pytest.raises(ValueError, match="non-empty list"):
            load_spec(p)

    def test_defaults_applied_when_optional_fields_absent(
        self, tmp_path: Path
    ) -> None:
        p = _write_spec(
            tmp_path,
            '[sprint]\nid = "S-1"\n'
            '[[checks]]\nname = "minimal"\ncommand = ["python", "--version"]\n',
        )
        spec = load_spec(p)
        check = spec.checks[0]
        assert check.expect_exit == 0
        assert check.timeout > 0
        assert check.output_lines > 0

    def test_empty_checks_list_is_valid(self, tmp_path: Path) -> None:
        p = _write_spec(tmp_path, '[sprint]\nid = "S-1"\ndescription = "empty"\n')
        spec = load_spec(p)
        assert spec.checks == []

    def test_invalid_toml_raises_value_error(self, tmp_path: Path) -> None:
        p = _write_spec(tmp_path, "not valid toml ][[[")
        with pytest.raises(ValueError, match="Invalid TOML"):
            load_spec(p)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

_PY = sys.executable


def _make_check(
    command: list[str],
    expect_exit: int = 0,
    timeout: int = 10,
    output_lines: int = 20,
) -> Check:
    return Check(
        name="test-check",
        command=command,
        expect_exit=expect_exit,
        timeout=timeout,
        output_lines=output_lines,
    )


class TestRunCheck:
    def test_pass_when_exit_matches_expected(self) -> None:
        check = _make_check([_PY, "-c", "import sys; sys.exit(0)"], expect_exit=0)
        result = run_check(check)
        assert result.passed is True
        assert result.actual_exit == 0
        assert result.error == ""

    def test_fail_when_exit_does_not_match(self) -> None:
        check = _make_check([_PY, "-c", "import sys; sys.exit(1)"], expect_exit=0)
        result = run_check(check)
        assert result.passed is False
        assert result.actual_exit == 1

    def test_pass_when_expect_exit_1_and_command_returns_1(self) -> None:
        # exit=1 expected means "pattern absent" — this is a PASS
        check = _make_check([_PY, "-c", "import sys; sys.exit(1)"], expect_exit=1)
        result = run_check(check)
        assert result.passed is True

    def test_captures_stdout(self) -> None:
        check = _make_check([_PY, "-c", 'print("hello verify")'])
        result = run_check(check)
        assert "hello verify" in result.output

    def test_captures_stderr(self) -> None:
        check = _make_check(
            [_PY, "-c", "import sys; print('err', file=sys.stderr)"]
        )
        result = run_check(check)
        assert "err" in result.output

    def test_output_truncated_to_output_lines(self) -> None:
        # Print 50 lines, limit to 5
        check = _make_check(
            [_PY, "-c", "for i in range(50): print(i)"],
            output_lines=5,
        )
        result = run_check(check)
        lines = result.output.splitlines()
        assert len(lines) <= 6  # 5 content lines + 1 truncation notice
        assert "more lines" in result.output

    def test_timeout_produces_fail_with_error(self) -> None:
        check = _make_check(
            [_PY, "-c", "import time; time.sleep(60)"],
            timeout=1,
        )
        result = run_check(check)
        assert result.passed is False
        assert "timeout" in result.error

    def test_command_not_found_produces_fail_with_error(self) -> None:
        check = _make_check(["definitely-not-a-real-binary-xyz-aeos"])
        result = run_check(check)
        assert result.passed is False
        assert "command not found" in result.error or result.error != ""

    def test_result_stores_command(self) -> None:
        cmd = [_PY, "-c", "pass"]
        check = _make_check(cmd)
        result = run_check(check)
        assert result.command == cmd

    def test_result_stores_expect_exit(self) -> None:
        check = _make_check([_PY, "-c", "pass"], expect_exit=0)
        result = run_check(check)
        assert result.expect_exit == 0


class TestRunVerification:
    def test_all_checks_run_even_if_one_fails(self) -> None:
        spec = VerificationSpec(
            sprint_id="T",
            description="",
            checks=[
                Check(
                    name="fail",
                    command=[_PY, "-c", "import sys; sys.exit(1)"],
                    expect_exit=0,
                    timeout=10,
                ),
                Check(
                    name="pass",
                    command=[_PY, "-c", "pass"],
                    expect_exit=0,
                    timeout=10,
                ),
            ],
        )
        results = run_verification(spec)
        assert len(results) == 2
        assert results[0].passed is False
        assert results[1].passed is True

    def test_returns_one_result_per_check(self) -> None:
        spec = VerificationSpec(
            sprint_id="T",
            description="",
            checks=[
                Check(name=f"c{i}", command=[_PY, "-c", "pass"], timeout=10)
                for i in range(3)
            ],
        )
        results = run_verification(spec)
        assert len(results) == 3

    def test_empty_spec_returns_empty_results(self) -> None:
        spec = VerificationSpec(sprint_id="T", description="")
        results = run_verification(spec)
        assert results == []


# ---------------------------------------------------------------------------
# CLI — aeos verify sprint
# ---------------------------------------------------------------------------


def _write_passing_spec(tmp_path: Path) -> Path:
    p = tmp_path / "passing.verify.toml"
    p.write_text(
        f'[sprint]\nid = "T-PASS"\ndescription = "passing"\n'
        f'[[checks]]\nname = "ok"\ncommand = ["{_PY}", "-c", "pass"]\n'
        f"expect_exit = 0\ntimeout = 10\n",
        encoding="utf-8",
    )
    return p


def _write_failing_spec(tmp_path: Path) -> Path:
    p = tmp_path / "failing.verify.toml"
    p.write_text(
        f'[sprint]\nid = "T-FAIL"\ndescription = "failing"\n'
        f'[[checks]]\nname = "fail"\n'
        f'command = ["{_PY}", "-c", "import sys; sys.exit(1)"]\n'
        f"expect_exit = 0\ntimeout = 10\n",
        encoding="utf-8",
    )
    return p


class TestVerifySprintCli:
    def test_cli_exits_0_when_all_pass(self, tmp_path: Path) -> None:
        from aeos.cli import app

        spec = _write_passing_spec(tmp_path)
        result = runner.invoke(app, ["verify", "sprint", "T-PASS", "--spec", str(spec)])
        assert result.exit_code == 0

    def test_cli_exits_1_when_any_fail(self, tmp_path: Path) -> None:
        from aeos.cli import app

        spec = _write_failing_spec(tmp_path)
        result = runner.invoke(app, ["verify", "sprint", "T-FAIL", "--spec", str(spec)])
        assert result.exit_code == 1

    def test_cli_output_shows_pass(self, tmp_path: Path) -> None:
        from aeos.cli import app

        spec = _write_passing_spec(tmp_path)
        result = runner.invoke(app, ["verify", "sprint", "T-PASS", "--spec", str(spec)])
        assert "PASS" in result.output

    def test_cli_output_shows_fail(self, tmp_path: Path) -> None:
        from aeos.cli import app

        spec = _write_failing_spec(tmp_path)
        result = runner.invoke(app, ["verify", "sprint", "T-FAIL", "--spec", str(spec)])
        assert "FAIL" in result.output

    def test_cli_json_output_is_valid_json(self, tmp_path: Path) -> None:
        from aeos.cli import app

        spec = _write_passing_spec(tmp_path)
        result = runner.invoke(
            app, ["verify", "sprint", "T-PASS", "--spec", str(spec), "--json"]
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_cli_json_contains_required_keys(self, tmp_path: Path) -> None:
        from aeos.cli import app

        spec = _write_passing_spec(tmp_path)
        result = runner.invoke(
            app, ["verify", "sprint", "T-PASS", "--spec", str(spec), "--json"]
        )
        parsed = json.loads(result.output)
        required = (
            "sprint_id", "description", "passed", "total", "all_passed", "checks"
        )
        for key in required:
            assert key in parsed

    def test_cli_json_checks_contain_evidence(self, tmp_path: Path) -> None:
        from aeos.cli import app

        spec = _write_passing_spec(tmp_path)
        result = runner.invoke(
            app, ["verify", "sprint", "T-PASS", "--spec", str(spec), "--json"]
        )
        parsed = json.loads(result.output)
        assert len(parsed["checks"]) == 1
        check = parsed["checks"][0]
        required = (
            "name", "command", "expect_exit", "actual_exit", "passed", "output", "error"
        )
        for key in required:
            assert key in check

    def test_cli_exits_1_when_spec_not_found(self, tmp_path: Path) -> None:
        from aeos.cli import app

        ghost_spec = str(tmp_path / "ghost.verify.toml")
        result = runner.invoke(
            app,
            ["verify", "sprint", "ghost", "--spec", ghost_spec],
        )
        assert result.exit_code == 1
