# Part of the GodBot core LLM interface

from typing import AsyncIterator, Optional, Dict, Any

# Phase 11.1 logging
from godbot.core.logging import get_logger
from ollama_client import stream_ollama

log = get_logger(__name__)


async def stream_response(
    prompt: str,
    model: str,
    tools: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Core streaming interface for all LLM calls.

    - Wraps stream_ollama so we have a single place to adjust behavior
    - tools: optional tool schemas passed through to Ollama
    """
    if tools is not None:
        async for chunk in stream_ollama(prompt, model, tools=tools):
            yield chunk
    else:
        async for chunk in stream_ollama(prompt, model):
            yield chunk

