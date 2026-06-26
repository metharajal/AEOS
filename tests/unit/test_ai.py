from pathlib import Path

from aeos.ai.config import read_ai_config


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
