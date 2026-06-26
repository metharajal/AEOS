import json
from pathlib import Path
from unittest.mock import patch

import pytest
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


def test_init_creates_project(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-project"])
    mp.undo()
    assert result.exit_code == 0
    project = tmp_path / "my-project"
    assert project.is_dir()
    readme = (project / "README.md").read_text()
    assert readme == "# my-project\n\nGenerated with AEOS.\n"
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


def test_init_with_type_basic(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-project", "--type", "basic"])
    mp.undo()
    assert result.exit_code == 0
    assert (tmp_path / "my-project").is_dir()
    assert "my-project" in result.output


def test_init_with_unknown_type(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-project", "--type", "unknown"])
    mp.undo()
    assert result.exit_code == 1
    assert "unknown" in result.output


def test_init_fails_if_exists(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    (tmp_path / "existing-project").mkdir()
    result = runner.invoke(app, ["init", "existing-project"])
    mp.undo()
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_init_with_type_python(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["init", "demo-api", "--type", "python"])
    mp.undo()
    assert result.exit_code == 0
    assert (tmp_path / "demo-api" / "pyproject.toml").exists()
    assert (tmp_path / "demo-api" / "src" / "demo_api" / "version.py").exists()


def test_init_with_absolute_path(tmp_path: Path) -> None:
    dest = tmp_path / "my-project"
    result = runner.invoke(app, ["init", str(dest)])
    assert result.exit_code == 0
    assert dest.is_dir()
    assert (dest / "README.md").read_text() == "# my-project\n\nGenerated with AEOS.\n"
    assert 'name = "my-project"' in (dest / "aeos.toml").read_text()
    assert "my-project" in result.output
    assert str(dest) not in result.output


def test_init_python_with_absolute_path(tmp_path: Path) -> None:
    dest = tmp_path / "demo-api"
    result = runner.invoke(app, ["init", str(dest), "--type", "python"])
    assert result.exit_code == 0
    assert dest.is_dir()
    assert (dest / "src" / "demo_api" / "version.py").exists()
    content = (dest / "pyproject.toml").read_text()
    assert 'name = "demo-api"' in content
    assert str(tmp_path) not in content


def test_onboard_check_all_present(tmp_path: Path) -> None:
    from aeos.onboarding.checker import REQUIRED_ITEMS

    for item, kind in REQUIRED_ITEMS:
        target = tmp_path / item
        if kind == "file":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("")
        else:
            target.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["onboard", str(tmp_path), "--check"])
    assert result.exit_code == 0
    assert "MISSING" not in result.output
    assert "OK" in result.output


def test_onboard_check_some_missing(tmp_path: Path) -> None:
    result = runner.invoke(app, ["onboard", str(tmp_path), "--check"])
    assert result.exit_code == 1
    assert "MISSING" in result.output


def test_onboard_missing_path() -> None:
    result = runner.invoke(app, ["onboard", "missing-project", "--check"])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_onboard_check_default_path(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["onboard", "--check"])
    mp.undo()
    assert result.exit_code == 1
    assert "MISSING" in result.output
    assert "does not exist" not in result.output


def test_onboard_json_all_present(tmp_path: Path) -> None:
    from aeos.onboarding.checker import REQUIRED_ITEMS

    for item, kind in REQUIRED_ITEMS:
        target = tmp_path / item
        if kind == "file":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("")
        else:
            target.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["onboard", str(tmp_path), "--check", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["missing"] == []
    assert "README.md" in data["items"]
    assert data["items"]["README.md"] is True


def test_onboard_json_some_missing(tmp_path: Path) -> None:
    result = runner.invoke(app, ["onboard", str(tmp_path), "--check", "--json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert "README.md" in data["missing"]
    assert data["items"]["README.md"] is False


def test_onboard_json_path_field(tmp_path: Path) -> None:
    result = runner.invoke(app, ["onboard", str(tmp_path), "--check", "--json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["path"] == str(tmp_path.resolve())


def test_onboard_no_check_flag(tmp_path: Path) -> None:
    result = runner.invoke(app, ["onboard", str(tmp_path)])
    assert result.exit_code == 1
    assert "--check" in result.output


def test_project_inspect_current_dir(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["project", "inspect"])
    mp.undo()
    assert result.exit_code == 0
    assert "Project:" in result.output


def test_project_inspect_with_path(tmp_path: Path) -> None:
    result = runner.invoke(app, ["project", "inspect", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "Project:" in result.output
    assert "(unknown)" in result.output


def test_project_inspect_json_output(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["project", "inspect", "--json", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "project" in data
    assert "checks" in data
    assert data["project"]["name"] == "(unknown)"
    assert data["checks"]["configuration"]["aeos.toml"] is False
    assert "repository" in data["checks"]["git"]
    assert "remote_origin" in data["checks"]["git"]


def test_project_inspect_json_with_aeos_toml(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text('[project]\nname = "my-proj"\n')
    result = runner.invoke(
        app, ["project", "inspect", "--json", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["project"]["name"] == "my-proj"
    assert data["checks"]["configuration"]["aeos.toml"] is True


def test_ai_config_from_toml(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text(
        "\n".join(
            [
                "[ai]",
                'mode = "local-first"',
                "frontier_allowed = true",
                "require_human_approval = true",
                "",
                "[ai.local]",
                'provider = "ollama"',
                'base_url = "http://localhost:11434"',
                'default_model = "llama3.2"',
                "",
                "[ai.frontier]",
                'provider = "openai-compatible"',
                'base_url_env = "AEOS_FRONTIER_BASE_URL"',
                'api_key_env = "AEOS_FRONTIER_API_KEY"',
                'default_model_env = "AEOS_FRONTIER_MODEL"',
            ]
        )
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "config"])
    mp.undo()
    assert result.exit_code == 0
    assert "AI Configuration" in result.output
    assert "Source: aeos.toml" in result.output
    assert "local-first" in result.output
    assert "ollama" in result.output
    assert "AEOS_FRONTIER_API_KEY" in result.output


def test_ai_config_defaults(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text('[project]\nname = "test"\n')
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "config"])
    mp.undo()
    assert result.exit_code == 0
    assert "Source: (defaults)" in result.output
    assert "local-first" in result.output
    assert "ollama" in result.output
    assert "AEOS_FRONTIER_API_KEY" in result.output


def test_ai_config_missing_toml(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "config"])
    mp.undo()
    assert result.exit_code == 1
    assert "aeos.toml" in result.output


def test_ai_doctor_missing_toml(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "doctor"])
    mp.undo()
    assert result.exit_code == 1
    assert "ERROR" in result.output


def test_ai_doctor_displays_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "aeos.toml").write_text(
        "\n".join(
            [
                "[ai]",
                'mode = "local-first"',
                "frontier_allowed = true",
                "require_human_approval = true",
                "",
                "[ai.local]",
                'provider = "ollama"',
                'base_url = "http://localhost:11434"',
                'default_model = "llama3.2"',
                "",
                "[ai.frontier]",
                'provider = "openai-compatible"',
                'base_url_env = "AEOS_FRONTIER_BASE_URL"',
                'api_key_env = "AEOS_FRONTIER_API_KEY"',
                'default_model_env = "AEOS_FRONTIER_MODEL"',
            ]
        )
    )
    monkeypatch.setattr(
        "aeos.ai.doctor._check_endpoint", lambda url, timeout: (True, "")
    )
    monkeypatch.delenv("AEOS_FRONTIER_BASE_URL", raising=False)
    monkeypatch.delenv("AEOS_FRONTIER_API_KEY", raising=False)
    monkeypatch.delenv("AEOS_FRONTIER_MODEL", raising=False)
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "doctor"])
    mp.undo()
    assert result.exit_code == 0
    assert "--- Configuration ---" in result.output
    assert "--- Local AI ---" in result.output
    assert "--- Frontier AI ---" in result.output
    assert "--- Result ---" in result.output
    assert "ollama" in result.output
    assert "AEOS_FRONTIER_API_KEY" in result.output


def test_ai_doctor_never_displays_api_key_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "aeos.toml").write_text('[project]\nname = "test"\n')
    monkeypatch.setattr(
        "aeos.ai.doctor._check_endpoint", lambda url, timeout: (True, "")
    )
    monkeypatch.setenv("AEOS_FRONTIER_API_KEY", "sk-super-secret-key")
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "doctor"])
    mp.undo()
    assert "sk-super-secret-key" not in result.output


def _write_minimal_ai_toml_for_cli(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text(
        "\n".join(
            [
                "[ai]",
                'mode = "local-first"',
                "frontier_allowed = true",
                "require_human_approval = true",
                "",
                "[ai.local]",
                'provider = "ollama"',
                'base_url = "http://localhost:11434"',
                'default_model = "llama3.2"',
                "",
                "[ai.frontier]",
                'provider = "openai-compatible"',
                'base_url_env = "AEOS_FRONTIER_BASE_URL"',
                'api_key_env = "AEOS_FRONTIER_API_KEY"',
                'default_model_env = "AEOS_FRONTIER_MODEL"',
            ]
        )
    )


def test_ai_ask_local_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_minimal_ai_toml_for_cli(tmp_path)
    monkeypatch.setattr(
        "aeos.cli.ask_local_ai",
        lambda prompt, config, timeout: __import__(
            "aeos.ai.local", fromlist=["LocalAiResponse"]
        ).LocalAiResponse(text="AEOS est un système."),
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "Explique AEOS", "--provider", "local"])
    mp.undo()
    assert result.exit_code == 0
    assert "AEOS est un système." in result.output


def test_ai_ask_local_ollama_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml_for_cli(tmp_path)
    from aeos.ai.local import LocalAiError

    monkeypatch.setattr(
        "aeos.cli.ask_local_ai",
        lambda prompt, config, timeout: (_ for _ in ()).throw(
            LocalAiError("Ollama unreachable: Connection refused")
        ),
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "test", "--provider", "local"])
    mp.undo()
    assert result.exit_code == 1


def test_ai_ask_missing_toml(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "test", "--provider", "local"])
    mp.undo()
    assert result.exit_code == 1
    assert "aeos.toml" in result.output


def test_ai_ask_never_displays_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml_for_cli(tmp_path)
    monkeypatch.setenv("AEOS_FRONTIER_API_KEY", "sk-should-not-appear")
    monkeypatch.setattr(
        "aeos.cli.ask_local_ai",
        lambda prompt, config, timeout: __import__(
            "aeos.ai.local", fromlist=["LocalAiResponse"]
        ).LocalAiResponse(text="OK"),
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "test", "--provider", "local"])
    mp.undo()
    assert "sk-should-not-appear" not in result.output


def test_ai_ask_frontier_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml_for_cli(tmp_path)
    monkeypatch.setattr(
        "aeos.cli.ask_frontier_ai",
        lambda prompt, config, timeout: __import__(
            "aeos.ai.frontier", fromlist=["FrontierAiResponse"]
        ).FrontierAiResponse(text="AEOS est un OS IA."),
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(
        app, ["ai", "ask", "Explique AEOS", "--provider", "frontier"]
    )
    mp.undo()
    assert result.exit_code == 0
    assert "AEOS est un OS IA." in result.output


def test_ai_ask_frontier_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_minimal_ai_toml_for_cli(tmp_path)
    from aeos.ai.frontier import FrontierAiError

    monkeypatch.setattr(
        "aeos.cli.ask_frontier_ai",
        lambda prompt, config, timeout: (_ for _ in ()).throw(
            FrontierAiError("frontier unreachable: Connection refused")
        ),
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "test", "--provider", "frontier"])
    mp.undo()
    assert result.exit_code == 1


def test_ai_ask_frontier_missing_toml(tmp_path: Path) -> None:
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "test", "--provider", "frontier"])
    mp.undo()
    assert result.exit_code == 1
    assert "aeos.toml" in result.output


def test_ai_ask_frontier_never_displays_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml_for_cli(tmp_path)
    monkeypatch.setenv("AEOS_FRONTIER_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("AEOS_FRONTIER_API_KEY", "sk-ultra-secret-frontier-key")
    monkeypatch.setenv("AEOS_FRONTIER_MODEL", "gpt-4o")
    monkeypatch.setattr(
        "aeos.cli.ask_frontier_ai",
        lambda prompt, config, timeout: __import__(
            "aeos.ai.frontier", fromlist=["FrontierAiResponse"]
        ).FrontierAiResponse(text="OK"),
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "test", "--provider", "frontier"])
    mp.undo()
    assert "sk-ultra-secret-frontier-key" not in result.output


def test_ai_ask_local_still_works_after_frontier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml_for_cli(tmp_path)
    monkeypatch.setattr(
        "aeos.cli.ask_local_ai",
        lambda prompt, config, timeout: __import__(
            "aeos.ai.local", fromlist=["LocalAiResponse"]
        ).LocalAiResponse(text="local still works"),
    )
    mp = pytest.MonkeyPatch()
    mp.chdir(tmp_path)
    result = runner.invoke(app, ["ai", "ask", "test", "--provider", "local"])
    mp.undo()
    assert result.exit_code == 0
    assert "local still works" in result.output
