import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from aeos.ai.config import AiConfig


@dataclass
class FrontierAiResponse:
    text: str


class FrontierAiError(Exception):
    pass


def ask_frontier_ai(
    prompt: str, config: AiConfig, timeout: int = 30
) -> FrontierAiResponse:
    if config.frontier.provider != "openai-compatible":
        raise FrontierAiError(
            f"unsupported frontier provider: {config.frontier.provider}"
        )

    missing = [
        name
        for name in [
            config.frontier.base_url_env,
            config.frontier.api_key_env,
            config.frontier.default_model_env,
        ]
        if os.environ.get(name) is None
    ]
    if missing:
        raise FrontierAiError(f"missing environment variables: {', '.join(missing)}")

    base_url = os.environ[config.frontier.base_url_env]
    api_key = os.environ[config.frontier.api_key_env]
    model = os.environ[config.frontier.default_model_env]

    url = base_url.rstrip("/") + "/chat/completions"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise FrontierAiError(f"unsupported scheme: {parsed.scheme}")

    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise FrontierAiError(f"frontier unreachable: {e.reason}") from e
    except OSError as e:
        raise FrontierAiError(str(e)) from e

    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise FrontierAiError("empty or invalid response from frontier provider") from e

    if not isinstance(text, str) or not text:
        raise FrontierAiError("empty response content from frontier provider")

    return FrontierAiResponse(text=text)
