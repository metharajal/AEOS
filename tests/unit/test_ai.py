from pathlib import Path

import pytest

from aeos.ai.config import read_ai_config
from aeos.ai.doctor import run_ai_doctor


def test_read_ai_config_returns_none_if_no_toml(tmp_path: Path) -> None:
    result = read_ai_config(tmp_path)
    assert result is None


def test_read_ai_config_returns_none_if_invalid_toml(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text("not valid toml ][")
    result = read_ai_config(tmp_path)
    assert result is None


def test_read_ai_config_defaults_when_no_ai_section(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text('[project]\nname = "test"\n')
    result = read_ai_config(tmp_path)
    assert result is not None
    assert result.mode == "local-first"
    assert result.frontier_allowed is True
    assert result.require_human_approval is True
    assert result.local.provider == "ollama"
    assert result.local.base_url == "http://localhost:11434"
    assert result.local.default_model == "llama3.2"
    assert result.frontier.provider == "openai-compatible"
    assert result.frontier.base_url_env == "AEOS_FRONTIER_BASE_URL"
    assert result.frontier.api_key_env == "AEOS_FRONTIER_API_KEY"
    assert result.frontier.default_model_env == "AEOS_FRONTIER_MODEL"
    assert result.source == "(defaults)"


def test_read_ai_config_reads_explicit_values(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text(
        "\n".join(
            [
                "[ai]",
                'mode = "hybrid"',
                "frontier_allowed = false",
                "require_human_approval = false",
                "",
                "[ai.local]",
                'provider = "lm-studio"',
                'base_url = "http://localhost:1234"',
                'default_model = "mistral"',
                "",
                "[ai.frontier]",
                'provider = "anthropic-compatible"',
                'base_url_env = "MY_BASE_URL"',
                'api_key_env = "MY_API_KEY"',
                'default_model_env = "MY_MODEL"',
            ]
        )
    )
    result = read_ai_config(tmp_path)
    assert result is not None
    assert result.mode == "hybrid"
    assert result.frontier_allowed is False
    assert result.require_human_approval is False
    assert result.local.provider == "lm-studio"
    assert result.local.base_url == "http://localhost:1234"
    assert result.local.default_model == "mistral"
    assert result.frontier.provider == "anthropic-compatible"
    assert result.frontier.base_url_env == "MY_BASE_URL"
    assert result.frontier.api_key_env == "MY_API_KEY"
    assert result.frontier.default_model_env == "MY_MODEL"
    assert result.source == "aeos.toml"


def _write_minimal_ai_toml(tmp_path: Path) -> None:
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


def test_run_ai_doctor_no_toml(tmp_path: Path) -> None:
    result = run_ai_doctor(tmp_path)
    assert result.config_ok is False
    assert result.status == "ERROR"


def test_run_ai_doctor_endpoint_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml(tmp_path)
    monkeypatch.setattr(
        "aeos.ai.doctor._check_endpoint", lambda url, timeout: (True, "")
    )
    result = run_ai_doctor(tmp_path)
    assert result.config_ok is True
    assert result.local.endpoint_ok is True
    assert result.status == "OK"


def test_run_ai_doctor_endpoint_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml(tmp_path)
    monkeypatch.setattr(
        "aeos.ai.doctor._check_endpoint",
        lambda url, timeout: (False, "Connection refused"),
    )
    result = run_ai_doctor(tmp_path)
    assert result.local.endpoint_ok is False
    assert result.local.endpoint_error == "Connection refused"


def test_run_ai_doctor_frontier_env_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml(tmp_path)
    monkeypatch.setattr(
        "aeos.ai.doctor._check_endpoint",
        lambda url, timeout: (False, "Connection refused"),
    )
    monkeypatch.setenv("AEOS_FRONTIER_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("AEOS_FRONTIER_API_KEY", "sk-test")
    monkeypatch.setenv("AEOS_FRONTIER_MODEL", "gpt-4o")
    result = run_ai_doctor(tmp_path)
    assert result.frontier.base_url_env_present is True
    assert result.frontier.api_key_env_present is True
    assert result.frontier.default_model_env_present is True
    assert result.status == "OK"


def test_run_ai_doctor_frontier_env_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_minimal_ai_toml(tmp_path)
    monkeypatch.setattr(
        "aeos.ai.doctor._check_endpoint",
        lambda url, timeout: (False, "Connection refused"),
    )
    monkeypatch.delenv("AEOS_FRONTIER_BASE_URL", raising=False)
    monkeypatch.delenv("AEOS_FRONTIER_API_KEY", raising=False)
    monkeypatch.delenv("AEOS_FRONTIER_MODEL", raising=False)
    result = run_ai_doctor(tmp_path)
    assert result.frontier.api_key_env_present is False
    assert result.status == "WARNING"
