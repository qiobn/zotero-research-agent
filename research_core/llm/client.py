"""Thin LiteLLM wrapper with retry and logging."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import litellm
from loguru import logger

litellm.drop_params = True

DEFAULT_MODEL = "gpt-4o-mini"


async def llm_completion(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    tools: list[dict] | None = None,
    **kwargs: Any,
) -> dict:
    """Single-shot async completion. Returns the full response dict."""
    logger.debug(f"LLM call: model={model}, msgs={len(messages)}")
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        tools=tools,
        **kwargs,
    )
    return response


async def llm_completion_stream(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    **kwargs: Any,
) -> AsyncIterator[str]:
    """Streaming async completion. Yields content deltas."""
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
        **kwargs,
    )
    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
