import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from aeos.ai.config import AiConfig


@dataclass
class LocalAiResponse:
    text: str


class LocalAiError(Exception):
    pass


def ask_local_ai(prompt: str, config: AiConfig, timeout: int = 30) -> LocalAiResponse:
    if config.local.provider != "ollama":
        raise LocalAiError(f"unsupported local provider: {config.local.provider}")
    url = config.local.base_url.rstrip("/") + "/api/generate"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise LocalAiError(f"unsupported scheme: {parsed.scheme}")
    payload = json.dumps(
        {
            "model": config.local.default_model,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise LocalAiError(f"Ollama unreachable: {e.reason}") from e
    except OSError as e:
        raise LocalAiError(str(e)) from e
    text = body.get("response", "")
    if not isinstance(text, str) or not text:
        raise LocalAiError("empty or invalid response from Ollama")
    return LocalAiResponse(text=text)
