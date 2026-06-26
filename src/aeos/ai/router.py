from dataclasses import dataclass

from aeos.ai.config import AiConfig
from aeos.ai.frontier import FrontierAiError, ask_frontier_ai
from aeos.ai.local import LocalAiError, ask_local_ai

_VALID_PROVIDERS: tuple[str, ...] = ("auto", "frontier", "local")


@dataclass
class AiRouterResponse:
    text: str
    provider_used: str


class AiRouterError(Exception):
    pass


def _call_local(prompt: str, config: AiConfig, timeout: int) -> AiRouterResponse:
    try:
        resp = ask_local_ai(prompt, config, timeout=timeout)
    except LocalAiError as e:
        raise AiRouterError(str(e)) from e
    return AiRouterResponse(text=resp.text, provider_used="local")


def _call_frontier(prompt: str, config: AiConfig, timeout: int) -> AiRouterResponse:
    try:
        resp = ask_frontier_ai(prompt, config, timeout=timeout)
    except FrontierAiError as e:
        raise AiRouterError(str(e)) from e
    return AiRouterResponse(text=resp.text, provider_used="frontier")


def _call_auto(prompt: str, config: AiConfig, timeout: int) -> AiRouterResponse:
    try:
        return _call_local(prompt, config, timeout)
    except AiRouterError as local_err:
        if not config.frontier_allowed:
            raise AiRouterError(
                f"local failed and frontier is disabled: {local_err}"
            ) from local_err
        if config.require_human_approval:
            raise AiRouterError(
                "local failed; use --provider frontier to call frontier explicitly"
            ) from local_err
        try:
            return _call_frontier(prompt, config, timeout)
        except AiRouterError as frontier_err:
            raise AiRouterError(
                f"both local and frontier failed: {frontier_err}"
            ) from frontier_err


def ask_ai(
    prompt: str,
    config: AiConfig,
    provider: str = "local",
    timeout: int = 30,
) -> AiRouterResponse:
    if provider not in _VALID_PROVIDERS:
        raise AiRouterError(
            f"unknown provider '{provider}'."
            f" Use: {', '.join(sorted(_VALID_PROVIDERS))}."
        )
    if provider == "local":
        return _call_local(prompt, config, timeout)
    if provider == "frontier":
        return _call_frontier(prompt, config, timeout)
    return _call_auto(prompt, config, timeout)
