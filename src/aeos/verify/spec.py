"""
AEOS Verify Spec — parse .verify.toml specs written before sprint code.
Pure parsing: no I/O beyond file reads, no subprocess, no AI, no network.
Commands are always lists (shell=False): no free shell execution.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TIMEOUT = 30
DEFAULT_OUTPUT_LINES = 20


@dataclass
class Check:
    name: str
    command: list[str]
    expect_exit: int = 0
    timeout: int = DEFAULT_TIMEOUT
    output_lines: int = DEFAULT_OUTPUT_LINES


@dataclass
class VerificationSpec:
    sprint_id: str
    description: str
    checks: list[Check] = field(default_factory=list)


def load_spec(path: Path) -> VerificationSpec:
    """Parse a .verify.toml file into a VerificationSpec.

    Raises:
        FileNotFoundError: path does not exist.
        ValueError: TOML is invalid or required fields are missing.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Spec not found: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML in {path}: {e}") from e

    sprint = data.get("sprint")
    if not isinstance(sprint, dict):
        raise ValueError(f"Missing [sprint] section in {path}")

    sprint_id = sprint.get("id")
    if not isinstance(sprint_id, str) or not sprint_id.strip():
        raise ValueError(f"Missing or empty sprint.id in {path}")

    description = sprint.get("description", "")
    if not isinstance(description, str):
        description = ""

    raw_checks = data.get("checks", [])
    if not isinstance(raw_checks, list):
        raise ValueError(f"'checks' must be a TOML array in {path}")

    checks: list[Check] = []
    for i, raw in enumerate(raw_checks):
        if not isinstance(raw, dict):
            raise ValueError(f"Check #{i} must be a TOML table in {path}")

        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Check #{i}: missing or empty 'name' in {path}")

        command = raw.get("command")
        if isinstance(command, str):
            raise ValueError(
                f"Check '{name}': 'command' must be a list, not a string "
                f"(use command = [\"prog\", \"arg\"]). Shell-free execution required."
            )
        if not isinstance(command, list) or not command:
            raise ValueError(
                f"Check '{name}': 'command' must be a non-empty list in {path}"
            )
        if not all(isinstance(a, str) for a in command):
            raise ValueError(
                f"Check '{name}': all command arguments must be strings in {path}"
            )

        expect_exit = raw.get("expect_exit", 0)
        if not isinstance(expect_exit, int):
            raise ValueError(
                f"Check '{name}': 'expect_exit' must be an integer in {path}"
            )

        timeout = raw.get("timeout", DEFAULT_TIMEOUT)
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError(
                f"Check '{name}': 'timeout' must be a positive integer in {path}"
            )

        output_lines = raw.get("output_lines", DEFAULT_OUTPUT_LINES)
        if not isinstance(output_lines, int) or output_lines <= 0:
            raise ValueError(
                f"Check '{name}': 'output_lines' must be a positive integer in {path}"
            )

        checks.append(
            Check(
                name=name,
                command=command,
                expect_exit=expect_exit,
                timeout=timeout,
                output_lines=output_lines,
            )
        )

    return VerificationSpec(
        sprint_id=sprint_id.strip(),
        description=description,
        checks=checks,
    )
