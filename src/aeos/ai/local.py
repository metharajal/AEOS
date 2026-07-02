import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from aeos.ai.config import AiConfig

_LOCAL_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1"})


@dataclass
class LocalAiResponse:
    text: str


class LocalAiError(Exception):
    pass


def ask_local_ai(prompt: str, config: AiConfig, timeout: int = 30) -> LocalAiResponse:
    base = config.local.base_url.rstrip("/")
    parsed_base = urllib.parse.urlparse(base)
    if parsed_base.scheme not in ("http", "https"):
        raise LocalAiError(f"unsupported scheme: {parsed_base.scheme}")
    hostname = parsed_base.hostname or ""
    if hostname not in _LOCAL_HOSTNAMES:
        raise LocalAiError(
            f"local AI runtime must use a local endpoint "
            f"(got: {hostname!r}). Allowed: localhost, 127.0.0.1, ::1"
        )
    url = base + "/v1/chat/completions"
    payload = json.dumps(
        {
            "model": config.local.default_model,
            "messages": [{"role": "user", "content": prompt}],
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
        raise LocalAiError(f"local AI runtime unreachable: {e.reason}") from e
    except OSError as e:
        raise LocalAiError(str(e)) from e
    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LocalAiError("empty or invalid response from local AI runtime") from e
    if not isinstance(text, str) or not text:
        raise LocalAiError("empty response from local AI runtime")
    return LocalAiResponse(text=text)
