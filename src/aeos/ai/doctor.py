import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from aeos.ai.config import read_ai_config


@dataclass
class LocalCheckResult:
    provider: str
    base_url: str
    default_model: str
    endpoint_ok: bool
    endpoint_error: str


@dataclass
class FrontierCheckResult:
    provider: str
    base_url_env: str
    base_url_env_present: bool
    api_key_env: str
    api_key_env_present: bool
    default_model_env: str
    default_model_env_present: bool


@dataclass
class AiDoctorResult:
    config_ok: bool
    mode: str
    frontier_allowed: bool
    require_human_approval: bool
    local: LocalCheckResult
    frontier: FrontierCheckResult
    status: str


def _check_endpoint(url: str, timeout: int) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, f"unsupported scheme: {parsed.scheme}"
    req = urllib.request.Request(url)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=timeout):  # noqa: S310
            return True, ""
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except OSError as e:
        return False, str(e)


def _check_env(var: str) -> bool:
    return os.environ.get(var) is not None


def _make_error_result() -> AiDoctorResult:
    return AiDoctorResult(
        config_ok=False,
        mode="",
        frontier_allowed=False,
        require_human_approval=False,
        local=LocalCheckResult(
            provider="",
            base_url="",
            default_model="",
            endpoint_ok=False,
            endpoint_error="aeos.toml not found or invalid",
        ),
        frontier=FrontierCheckResult(
            provider="",
            base_url_env="",
            base_url_env_present=False,
            api_key_env="",
            api_key_env_present=False,
            default_model_env="",
            default_model_env_present=False,
        ),
        status="ERROR",
    )


def run_ai_doctor(path: Path) -> AiDoctorResult:
    config = read_ai_config(path)
    if config is None:
        return _make_error_result()

    if config.local.provider == "ollama":
        endpoint_url = config.local.base_url.rstrip("/") + "/api/tags"
        endpoint_ok, endpoint_error = _check_endpoint(endpoint_url, timeout=1)
    else:
        endpoint_ok, endpoint_error = False, "provider not checked"

    local = LocalCheckResult(
        provider=config.local.provider,
        base_url=config.local.base_url,
        default_model=config.local.default_model,
        endpoint_ok=endpoint_ok,
        endpoint_error=endpoint_error,
    )

    frontier = FrontierCheckResult(
        provider=config.frontier.provider,
        base_url_env=config.frontier.base_url_env,
        base_url_env_present=_check_env(config.frontier.base_url_env),
        api_key_env=config.frontier.api_key_env,
        api_key_env_present=_check_env(config.frontier.api_key_env),
        default_model_env=config.frontier.default_model_env,
        default_model_env_present=_check_env(config.frontier.default_model_env),
    )

    frontier_ready = (
        frontier.base_url_env_present
        and frontier.api_key_env_present
        and frontier.default_model_env_present
    )

    if endpoint_ok or frontier_ready:
        status = "OK"
    elif not endpoint_ok and not frontier_ready:
        status = "WARNING"
    else:
        status = "WARNING"

    return AiDoctorResult(
        config_ok=True,
        mode=config.mode,
        frontier_allowed=config.frontier_allowed,
        require_human_approval=config.require_human_approval,
        local=local,
        frontier=frontier,
        status=status,
    )
