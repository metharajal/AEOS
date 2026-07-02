"""
AEOS Verify Runner — execute checks and produce verifiable evidence.
No AI. No network. Local deterministic tools only.
subprocess shell=False: no free shell, no injection surface.
All checks run even if earlier ones fail — full evidence always collected.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from aeos.verify.spec import Check, VerificationSpec


@dataclass
class CheckResult:
    name: str
    command: list[str]
    expect_exit: int
    actual_exit: int
    output: str
    passed: bool
    error: str


def run_check(check: Check) -> CheckResult:
    """Execute one check. Never raises — execution errors are captured in .error."""
    try:
        proc = subprocess.run(  # noqa: S603
            check.command,
            capture_output=True,
            text=True,
            timeout=check.timeout,
            shell=False,
        )
        combined = proc.stdout + proc.stderr
        lines = combined.splitlines()
        truncated = "\n".join(lines[: check.output_lines])
        if len(lines) > check.output_lines:
            truncated += f"\n... ({len(lines) - check.output_lines} more lines)"
        return CheckResult(
            name=check.name,
            command=check.command,
            expect_exit=check.expect_exit,
            actual_exit=proc.returncode,
            output=truncated,
            passed=(proc.returncode == check.expect_exit),
            error="",
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=check.name,
            command=check.command,
            expect_exit=check.expect_exit,
            actual_exit=-1,
            output="",
            passed=False,
            error=f"timeout after {check.timeout}s",
        )
    except FileNotFoundError:
        return CheckResult(
            name=check.name,
            command=check.command,
            expect_exit=check.expect_exit,
            actual_exit=-1,
            output="",
            passed=False,
            error=f"command not found: {check.command[0]}",
        )
    except OSError as e:
        return CheckResult(
            name=check.name,
            command=check.command,
            expect_exit=check.expect_exit,
            actual_exit=-1,
            output="",
            passed=False,
            error=str(e),
        )


def run_verification(spec: VerificationSpec) -> list[CheckResult]:
    """Run all checks. All checks run regardless of individual failures."""
    return [run_check(check) for check in spec.checks]
