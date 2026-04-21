"""
OpenRouter client utilities — friendlier, documented, and a little human.

This module provides a tiny helper to call the OpenRouter chat completion endpoint
and a small list of suggested model names. The code aims to be forgiving and to
return streaming chunks when requested so TUI code can display text as it arrives.

Written by Natalie Spiva <natalie@acreetionos.org>
"""

import json
import requests
from typing import Iterable

# The chat completions endpoint used by OpenRouter's public API.
OPENROUTER_URL = "https://api.openrouter.ai/v1/chat/completions"

# A short, user-facing list of common/sane models to choose from. This is
# opinionated and can be edited by the user. The TUI displays these choices.
MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4o-mini-512",
    "gpt-4o-mini-instruct",
]


class OpenRouterError(RuntimeError):
    """Raised when the OpenRouter API returns an error or can't be reached."""


def _parse_stream_line(raw_line: str) -> str:
    """Turn a raw streaming line into a user-facing chunk of text.

    The API may prefix lines with "data:" and typically sends JSON blobs that
    contain the incremental "delta" content. This helper extracts that text and
    falls back to a best-effort string if parsing fails.
    """
    if not raw_line:
        return ""
    text = raw_line
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except Exception:
            text = raw_line
    if text.startswith("data:"):
        text = text[len("data:") :].strip()
    if not text or text == "[DONE]":
        return ""

    try:
        obj = json.loads(text)
        choice = obj.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        chunk = delta.get("content") or choice.get("text") or ""
    except Exception:
        # If the payload isn't JSON (or is unexpected), return the raw text.
        chunk = text
    return chunk or ""


def create_chat(
    api_key: str,
    messages: list,
    model: str = "gpt-4o-mini",
    stream: bool = False,
    max_tokens: int = 512,
    timeout: int = 60,
) -> Iterable[str] | list:
    """Call the OpenRouter chat completions endpoint.

    Parameters
    - api_key: your OpenRouter API key (kept as a string)
    - messages: list of message dicts following the OpenAI-style schema
    - model: model name (string). See MODELS above for suggestions.
    - stream: if True yields incremental strings as the API streams them.
    - max_tokens, timeout: forwarded to the HTTP request.

    Returns
    - If stream=True: a generator that yields string chunks as they arrive.
    - If stream=False: a list containing one string with the full assistant reply.

    The function raises OpenRouterError for HTTP or API-level failures.
    """
    if not api_key:
        raise OpenRouterError("Missing OpenRouter API key — set OPENROUTER_API_KEY.")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": stream,
    }

    try:
        if stream:
            # Stream mode: yield chunks as they arrive so callers can render them.
            with requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeout,
            ) as r:
                try:
                    r.raise_for_status()
                except Exception as exc:  # HTTP error
                    raise OpenRouterError(f"OpenRouter HTTP error: {exc}") from exc

                for raw in r.iter_lines(decode_unicode=True):
                    chunk = _parse_stream_line(raw)
                    if chunk:
                        yield chunk
            return

        # Non-streaming: return the assembled assistant text as a single-element list
        r = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=timeout
        )
        try:
            r.raise_for_status()
        except Exception as exc:
            raise OpenRouterError(
                f"OpenRouter HTTP error: {exc} — response: {r.text}"
            ) from exc

        j = r.json()
        # Common shapes: try to extract message content, fall back to choices[].text
        content = ""
        try:
            content = j["choices"][0]["message"]["content"]
        except Exception:
            try:
                content = j.get("choices", [])[0].get("text", "")
            except Exception:
                content = json.dumps(j)
        return [content]

    except requests.exceptions.RequestException as exc:
        # Network-level or timeout errors
        raise OpenRouterError(f"Network error when calling OpenRouter: {exc}") from exc
