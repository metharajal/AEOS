from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from aeos.cli import REQUIRED_TOOLS, app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_doctor_all_present() -> None:
    with patch("aeos.cli.shutil.which", return_value="/usr/bin/tool"):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    for tool in REQUIRED_TOOLS:
        assert tool in result.output
    assert "MISSING" not in result.output


def test_doctor_some_missing() -> None:
    def _which(cmd: str) -> str | None:
        return None if cmd in ("docker", "pnpm") else "/usr/bin/tool"

    with patch("aeos.cli.shutil.which", side_effect=_which):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "docker" in result.output
    assert "pnpm" in result.output
    assert "MISSING" in result.output


def test_init_creates_project(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-project"])
    mp.undo()
    assert result.exit_code == 0
    project = tmp_path / "my-project"
    assert project.is_dir()
    assert (
        project / "README.md"
    ).read_text() == "# my-project\n\nGenerated with AEOS.\n"
    assert (project / "aeos.toml").read_text() == (
        '[project]\nname = "my-project"\naeos_version = "0.1.0"\n'
    )
    assert ".venv/" in (project / ".gitignore").read_text()
    for sub in [
        "governance/adr",
        "governance/rfc",
        "governance/dec",
        "governance/standards",
        "governance/playbooks",
        "docs",
        "src",
        "tests",
    ]:
        assert (project / sub).is_dir()


def test_init_fails_if_exists(tmp_path: Path) -> None:
    import pytest

    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    (tmp_path / "existing-project").mkdir()
    result = runner.invoke(app, ["init", "existing-project"])
    mp.undo()
    assert result.exit_code == 1
    assert "already exists" in result.output
