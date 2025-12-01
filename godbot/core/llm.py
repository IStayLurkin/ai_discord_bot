# Part of the GodBot core LLM interface

from typing import AsyncIterator, Optional, Dict, Any

from ollama_client import stream_ollama


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

