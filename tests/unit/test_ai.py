import json
import urllib.error
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aeos.ai.config import AiConfig, AiFrontierConfig, AiLocalConfig, read_ai_config
from aeos.ai.doctor import run_ai_doctor
from aeos.ai.frontier import FrontierAiError, ask_frontier_ai
from aeos.ai.local import LocalAiError, ask_local_ai


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


def _make_ollama_config() -> AiConfig:
    return AiConfig(
        mode="local-first",
        frontier_allowed=True,
        require_human_approval=True,
        local=AiLocalConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            default_model="llama3.2",
        ),
        frontier=AiFrontierConfig(
            provider="openai-compatible",
            base_url_env="AEOS_FRONTIER_BASE_URL",
            api_key_env="AEOS_FRONTIER_API_KEY",
            default_model_env="AEOS_FRONTIER_MODEL",
        ),
        source="aeos.toml",
    )


def _fake_urlopen(
    response_dict: dict[str, object],
) -> Callable[..., MagicMock]:
    def _open(_req: object, **_kwargs: object) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_dict).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    return _open


def test_ask_local_ai_returns_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "aeos.ai.local.urllib.request.urlopen",
        _fake_urlopen({"response": "AEOS est un système.", "done": True}),
    )
    result = ask_local_ai("Explique AEOS", _make_ollama_config())
    assert result.text == "AEOS est un système."


def test_ask_local_ai_ollama_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_req: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("aeos.ai.local.urllib.request.urlopen", _raise)
    with pytest.raises(LocalAiError, match="Ollama unreachable"):
        ask_local_ai("test", _make_ollama_config())


def test_ask_local_ai_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "aeos.ai.local.urllib.request.urlopen",
        _fake_urlopen({"response": "", "done": True}),
    )
    with pytest.raises(LocalAiError, match="empty or invalid"):
        ask_local_ai("test", _make_ollama_config())


def test_ask_local_ai_unsupported_provider() -> None:
    config = _make_ollama_config()
    config.local.provider = "lm-studio"
    with pytest.raises(LocalAiError, match="unsupported local provider"):
        ask_local_ai("test", config)


def _make_frontier_config() -> AiConfig:
    return AiConfig(
        mode="local-first",
        frontier_allowed=True,
        require_human_approval=True,
        local=AiLocalConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            default_model="llama3.2",
        ),
        frontier=AiFrontierConfig(
            provider="openai-compatible",
            base_url_env="AEOS_FRONTIER_BASE_URL",
            api_key_env="AEOS_FRONTIER_API_KEY",
            default_model_env="AEOS_FRONTIER_MODEL",
        ),
        source="aeos.toml",
    )


def _fake_frontier_urlopen(
    response_dict: dict[str, object],
) -> Callable[..., MagicMock]:
    def _open(_req: object, **_kwargs: object) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_dict).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    return _open


def test_ask_frontier_ai_returns_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEOS_FRONTIER_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("AEOS_FRONTIER_API_KEY", "sk-test")
    monkeypatch.setenv("AEOS_FRONTIER_MODEL", "gpt-4o")
    monkeypatch.setattr(
        "aeos.ai.frontier.urllib.request.urlopen",
        _fake_frontier_urlopen(
            {"choices": [{"message": {"content": "AEOS est un OS IA."}}]}
        ),
    )
    result = ask_frontier_ai("Explique AEOS", _make_frontier_config())
    assert result.text == "AEOS est un OS IA."


def test_ask_frontier_ai_missing_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AEOS_FRONTIER_BASE_URL", raising=False)
    monkeypatch.delenv("AEOS_FRONTIER_API_KEY", raising=False)
    monkeypatch.delenv("AEOS_FRONTIER_MODEL", raising=False)
    with pytest.raises(FrontierAiError, match="missing environment variables"):
        ask_frontier_ai("test", _make_frontier_config())


def test_ask_frontier_ai_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEOS_FRONTIER_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("AEOS_FRONTIER_API_KEY", "sk-test")
    monkeypatch.setenv("AEOS_FRONTIER_MODEL", "gpt-4o")

    def _raise(_req: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("aeos.ai.frontier.urllib.request.urlopen", _raise)
    with pytest.raises(FrontierAiError, match="frontier unreachable"):
        ask_frontier_ai("test", _make_frontier_config())


def test_ask_frontier_ai_empty_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEOS_FRONTIER_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("AEOS_FRONTIER_API_KEY", "sk-test")
    monkeypatch.setenv("AEOS_FRONTIER_MODEL", "gpt-4o")
    monkeypatch.setattr(
        "aeos.ai.frontier.urllib.request.urlopen",
        _fake_frontier_urlopen({"choices": []}),
    )
    with pytest.raises(FrontierAiError, match="empty or invalid"):
        ask_frontier_ai("test", _make_frontier_config())


def test_ask_frontier_ai_unsupported_provider() -> None:
    config = _make_frontier_config()
    config.frontier.provider = "anthropic"
    with pytest.raises(FrontierAiError, match="unsupported frontier provider"):
        ask_frontier_ai("test", config)
