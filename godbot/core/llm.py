"""
Unified LLM Engine — Phase 11.4
Supports:
    - OpenAI (GPT-4.1, GPT-5, GPT-o models)
    - Ollama (local inference)
    - HuggingFace Transformers (local GPU/CPU)

Central interface:
    llm.chat(text or messages)
    llm.complete(prompt)
    llm.embed(text)
    llm.info()
"""

from __future__ import annotations

import os
import json
import time
import requests
import traceback

from typing import Any, Dict, List, Optional

from godbot.core.logging import get_logger

log = get_logger(__name__)


# -------------------------------------------------------------------------
# Environment Config
# -------------------------------------------------------------------------

LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "dolphin-llama3:latest")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3-8B-Instruct")
HF_DEVICE = os.getenv("HF_DEVICE", "cpu")

LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))


# -------------------------------------------------------------------------
# Lazy-loaded HuggingFace objects
# -------------------------------------------------------------------------

hf_tokenizer = None
hf_model_obj = None


def load_hf():
    """Load HuggingFace model + tokenizer lazily."""
    global hf_tokenizer, hf_model_obj

    if hf_model_obj is not None:
        return

    log.info(f"Loading HuggingFace model: {HF_MODEL} on {HF_DEVICE}")

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM

        hf_tokenizer = AutoTokenizer.from_pretrained(HF_MODEL)
        hf_model_obj = AutoModelForCausalLM.from_pretrained(
            HF_MODEL,
            device_map=HF_DEVICE,
            torch_dtype="auto",
        )

    except Exception as e:
        log.error(f"Failed to load HuggingFace model: {e}", exc_info=True)
        raise e


# -------------------------------------------------------------------------
# OpenAI Engine
# -------------------------------------------------------------------------

def _openai_chat(messages: List[Dict[str, str]]) -> str:
    try:
        import openai

        client = openai.OpenAI()

        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            timeout=LLM_TIMEOUT,
        )

        return resp.choices[0].message.content

    except Exception as e:
        log.error("OpenAI chat error:", exc_info=True)
        raise e


def _openai_complete(prompt: str) -> str:
    return _openai_chat([{"role": "user", "content": prompt}])


def _openai_embed(text: str) -> List[float]:
    import openai
    client = openai.OpenAI()
    try:
        resp = client.embeddings.create(
            model="text-embedding-3-large",
            input=text,
        )
        return resp.data[0].embedding
    except Exception:
        log.error("OpenAI embedding error", exc_info=True)
        raise


# -------------------------------------------------------------------------
# Ollama Engine
# -------------------------------------------------------------------------

def _ollama_chat(messages: List[Dict[str, str]]) -> str:
    """Call local Ollama model."""
    url = f"{OLLAMA_URL}/api/chat"
    body = {"model": LLM_MODEL, "messages": messages}

    try:
        r = requests.post(url, json=body, timeout=LLM_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return data["message"]["content"]
    except Exception:
        log.error("Ollama chat error", exc_info=True)
        raise


def _ollama_complete(prompt: str) -> str:
    return _ollama_chat([{"role": "user", "content": prompt}])


def _ollama_embed(text: str) -> List[float]:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": LLM_MODEL, "prompt": text},
            timeout=LLM_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["embedding"]

    except Exception:
        log.error("Ollama embedding error", exc_info=True)
        raise


# -------------------------------------------------------------------------
# HuggingFace Engine
# -------------------------------------------------------------------------

def _hf_chat(messages: List[Dict[str, str]]) -> str:
    """Simple conversation stitching."""
    load_hf()

    full_prompt = ""
    for m in messages:
        if m["role"] == "user":
            full_prompt += f"User: {m['content']}\n"
        else:
            full_prompt += f"Assistant: {m['content']}\n"
    full_prompt += "Assistant:"

    try:
        inputs = hf_tokenizer(full_prompt, return_tensors="pt").to(HF_DEVICE)
        outputs = hf_model_obj.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
        )

        text = hf_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return text.split("Assistant:", 1)[-1].strip()

    except Exception:
        log.error("HF chat error", exc_info=True)
        raise


def _hf_complete(prompt: str) -> str:
    return _hf_chat([{"role": "user", "content": prompt}])


def _hf_embed(text: str) -> List[float]:
    load_hf()
    from transformers import AutoModel
    import torch

    try:
        tok = hf_tokenizer(text, return_tensors="pt").to(HF_DEVICE)
        model = hf_model_obj
        with torch.no_grad():
            out = model(**tok, output_hidden_states=True)
        return out.hidden_states[-1][0][0].cpu().numpy().tolist()
    except Exception:
        log.error("HF embed error", exc_info=True)
        raise


# -------------------------------------------------------------------------
# Unified Interface (llm)
# -------------------------------------------------------------------------

class LLMEngine:
    def __init__(self):
        self.backend = LLM_BACKEND
        log.info(f"LLM backend set to: {self.backend}")

    # -----------------------
    # Chat
    # -----------------------
    def chat(self, messages_or_text: Any) -> str:
        """Accept raw string or list of chat messages."""

        if isinstance(messages_or_text, str):
            messages = [{"role": "user", "content": messages_or_text}]
        else:
            messages = messages_or_text

        log.info(f"LLM.chat({self.backend}) called")

        if self.backend == "openai":
            return _openai_chat(messages)

        if self.backend == "ollama":
            return _ollama_chat(messages)

        if self.backend == "huggingface":
            return _hf_chat(messages)

        raise ValueError(f"Unknown backend: {self.backend}")

    # -----------------------
    # Completion
    # -----------------------
    def complete(self, prompt: str) -> str:
        log.info(f"LLM.complete({self.backend}) called")

        if self.backend == "openai":
            return _openai_complete(prompt)

        if self.backend == "ollama":
            return _ollama_complete(prompt)

        if self.backend == "huggingface":
            return _hf_complete(prompt)

        raise ValueError(f"Unknown backend: {self.backend}")

    # -----------------------
    # Embeddings
    # -----------------------
    def embed(self, text: str) -> List[float]:
        log.info(f"LLM.embed({self.backend}) called")

        if self.backend == "openai":
            return _openai_embed(text)

        if self.backend == "ollama":
            return _ollama_embed(text)

        if self.backend == "huggingface":
            return _hf_embed(text)

        raise ValueError(f"Unknown backend: {self.backend}")

    # -----------------------
    # Info
    # -----------------------
    def info(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "model": LLM_MODEL,
            "hf_model": HF_MODEL,
            "ollama_url": OLLAMA_URL,
        }


# Global LLM instance
llm = LLMEngine()
