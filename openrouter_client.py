"""
OpenRouter Client Module

This module provides utilities to interact with the OpenRouter API, supporting
both standard and streaming chat completions. It includes a pre-defined list
of high-performing models and robust error handling.

Features:
- Streaming response parsing.
- Automatic model fallback using 'super-model'.
- Support for multiple model slugs.
- Increased timeouts for complex reasoning models.

Written by Natalie Spiva <natalie@acreetionos.org>
"""

import json
from typing import Any, Iterable, Optional, TypedDict, Union

import requests

# The chat completions endpoint used by OpenRouter's public API.
OPENROUTER_URL = "https://api.openrouter.ai/v1/chat/completions"

# Top 20 models for programming and engineering tasks (as of April 2026).
# These are selected for SWE-bench performance, context window, and logic.
MODELS = [
    "openai/gpt-5.4",  # Latest OpenAI frontier model
    "openai/gpt-5.2-codex",  # Optimized specifically for agentic coding
    "anthropic/claude-4.6-sonnet",  # 1M context, elite reasoning & coding
    "anthropic/claude-4.6-opus",  # Maximum intelligence for complex architecture
    "google/gemini-3-pro",  # Leader in LiveCodeBench (91.7% score)
    "google/gemini-3-flash",  # High-speed agentic coding with 1M context
    "mistralai/devstral-2-2512",  # Mistral's 123B agentic coding specialist
    "mistralai/codestral-latest",  # The industry standard for fill-in-the-middle
    "deepseek/deepseek-v3.2",  # SOTA cost-to-performance coding logic
    "deepseek/deepseek-v3",  # High-efficiency GPT-4 class coder
    "minimax/minimax-m2.7",  # Built for multi-agent repo orchestration
    "minimax/minimax-m2.5",  # 80%+ SWE-Bench Verified efficiency
    "qwen/qwen3-coder-480b",  # Alibaba's massive MoE coding specialist
    "qwen/qwen3-coder-next",  # Budget-friendly coding for simple scripts
    "kuaishou/kwaipilot-kat-coder-pro",  # High accuracy for real-world engineering
    "xiaomi/mimo-v2-pro",  # 1T parameter agentic brain
    "meta-llama/llama-4-maverick",  # Meta's 400B MoE model
    "meta-llama/llama-4-scout",  # Meta's high-speed 109B model
    "z-ai/glm-5.1",  # Top-tier reasoning and programming logic
    "nvidia/nemotron-3-super",  # Optimized for hybrid Mamba-Transformer coding
]


class Message(TypedDict):
    """Schema for a single chat message."""

    role: str
    content: str


class Usage(TypedDict, total=False):
    """Schema for API usage metrics."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(TypedDict):
    """Schema for a full chat response."""

    content: str
    usage: Optional[Usage]


class OpenRouterError(RuntimeError):
    """Raised when the OpenRouter API returns an error or can't be reached."""


def _parse_stream_line(raw_line: Union[str, bytes]) -> tuple[str, Optional[Usage]]:
    """Turn a raw streaming line into a user-facing chunk of text and usage info."""
    if not raw_line:
        return "", None
    text = raw_line
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except Exception:
            text = str(raw_line)
    if text.startswith("data:"):
        text = text[len("data:") :].strip()
    if not text or text == "[DONE]":
        return "", None

    try:
        obj = json.loads(text)
        # Usage can sometimes be in the last chunk
        usage: Optional[Usage] = obj.get("usage")
        choice = obj.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        chunk = delta.get("content") or choice.get("text") or ""
        return chunk, usage
    except Exception:
        return str(text), None


def create_chat(
    api_key: str,
    messages: list[Message],
    model: Union[str, list[str]] = "openai/gpt-5.4",
    stream: bool = False,
    max_tokens: int = 1024,
    timeout: int = 120,
) -> Union[Iterable[tuple[str, Optional[Usage]]], ChatResponse]:
    """Call the OpenRouter chat completions endpoint."""
    if not api_key:
        raise OpenRouterError("Missing OpenRouter API key — set OPENROUTER_API_KEY.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://acreetionos.org",  # Optional but helpful for OpenRouter
        "X-Title": "Natalie-TUI",
    }

    payload: dict[str, Any] = {
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if model == "super-model":
        payload["models"] = MODELS
    elif isinstance(model, list):
        payload["models"] = model
    else:
        payload["model"] = model

    try:
        if stream:

            def stream_gen() -> Iterable[tuple[str, Optional[Usage]]]:
                with requests.post(
                    OPENROUTER_URL,
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=timeout,
                ) as r:
                    try:
                        r.raise_for_status()
                    except Exception as exc:
                        raise OpenRouterError(f"OpenRouter HTTP error: {exc}") from exc

                    for raw in r.iter_lines(decode_unicode=True):
                        chunk, usage = _parse_stream_line(raw)
                        if chunk or usage:
                            yield chunk, usage

            return stream_gen()

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
        usage_data = j.get("usage")
        content = ""
        try:
            content = j["choices"][0]["message"]["content"]
        except Exception:
            try:
                content = j.get("choices", [])[0].get("text", "")
            except Exception:
                content = json.dumps(j)

        return {"content": content, "usage": usage_data}

    except requests.exceptions.RequestException as exc:
        raise OpenRouterError(f"Network error when calling OpenRouter: {exc}") from exc
