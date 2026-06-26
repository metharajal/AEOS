import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_MODE = "local-first"
_DEFAULT_FRONTIER_ALLOWED = True
_DEFAULT_REQUIRE_HUMAN_APPROVAL = True

_DEFAULT_LOCAL_PROVIDER = "ollama"
_DEFAULT_LOCAL_BASE_URL = "http://localhost:11434"
_DEFAULT_LOCAL_MODEL = "llama3.2"

_DEFAULT_FRONTIER_PROVIDER = "openai-compatible"
_DEFAULT_FRONTIER_BASE_URL_ENV = "AEOS_FRONTIER_BASE_URL"
_DEFAULT_FRONTIER_API_KEY_ENV = "AEOS_FRONTIER_API_KEY"
_DEFAULT_FRONTIER_MODEL_ENV = "AEOS_FRONTIER_MODEL"


@dataclass
class AiLocalConfig:
    provider: str
    base_url: str
    default_model: str


@dataclass
class AiFrontierConfig:
    provider: str
    base_url_env: str
    api_key_env: str
    default_model_env: str


@dataclass
class AiConfig:
    mode: str
    frontier_allowed: bool
    require_human_approval: bool
    local: AiLocalConfig
    frontier: AiFrontierConfig
    source: str


def _default_local() -> AiLocalConfig:
    return AiLocalConfig(
        provider=_DEFAULT_LOCAL_PROVIDER,
        base_url=_DEFAULT_LOCAL_BASE_URL,
        default_model=_DEFAULT_LOCAL_MODEL,
    )


def _default_frontier() -> AiFrontierConfig:
    return AiFrontierConfig(
        provider=_DEFAULT_FRONTIER_PROVIDER,
        base_url_env=_DEFAULT_FRONTIER_BASE_URL_ENV,
        api_key_env=_DEFAULT_FRONTIER_API_KEY_ENV,
        default_model_env=_DEFAULT_FRONTIER_MODEL_ENV,
    )


def _default_config(source: str) -> AiConfig:
    return AiConfig(
        mode=_DEFAULT_MODE,
        frontier_allowed=_DEFAULT_FRONTIER_ALLOWED,
        require_human_approval=_DEFAULT_REQUIRE_HUMAN_APPROVAL,
        local=_default_local(),
        frontier=_default_frontier(),
        source=source,
    )


def read_ai_config(path: Path) -> AiConfig | None:
    toml_path = path / "aeos.toml"
    if not toml_path.is_file():
        return None
    try:
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return None

    ai = data.get("ai")
    if not isinstance(ai, dict):
        return _default_config("(defaults)")

    local_raw = ai.get("local", {})
    local_raw = local_raw if isinstance(local_raw, dict) else {}
    frontier_raw = ai.get("frontier", {})
    frontier_raw = frontier_raw if isinstance(frontier_raw, dict) else {}

    mode = ai.get("mode", _DEFAULT_MODE)
    mode = mode if isinstance(mode, str) else _DEFAULT_MODE

    frontier_allowed = ai.get("frontier_allowed", _DEFAULT_FRONTIER_ALLOWED)
    if not isinstance(frontier_allowed, bool):
        frontier_allowed = _DEFAULT_FRONTIER_ALLOWED

    require_human_approval = ai.get(
        "require_human_approval", _DEFAULT_REQUIRE_HUMAN_APPROVAL
    )
    if not isinstance(require_human_approval, bool):
        require_human_approval = _DEFAULT_REQUIRE_HUMAN_APPROVAL

    def _str(raw: dict[str, object], key: str, default: str) -> str:
        val = raw.get(key, default)
        return val if isinstance(val, str) else default

    local = AiLocalConfig(
        provider=_str(local_raw, "provider", _DEFAULT_LOCAL_PROVIDER),
        base_url=_str(local_raw, "base_url", _DEFAULT_LOCAL_BASE_URL),
        default_model=_str(local_raw, "default_model", _DEFAULT_LOCAL_MODEL),
    )

    frontier = AiFrontierConfig(
        provider=_str(frontier_raw, "provider", _DEFAULT_FRONTIER_PROVIDER),
        base_url_env=_str(frontier_raw, "base_url_env", _DEFAULT_FRONTIER_BASE_URL_ENV),
        api_key_env=_str(frontier_raw, "api_key_env", _DEFAULT_FRONTIER_API_KEY_ENV),
        default_model_env=_str(
            frontier_raw, "default_model_env", _DEFAULT_FRONTIER_MODEL_ENV
        ),
    )

    return AiConfig(
        mode=mode,
        frontier_allowed=frontier_allowed,
        require_human_approval=require_human_approval,
        local=local,
        frontier=frontier,
        source="aeos.toml",
    )
