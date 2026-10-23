"""LLM provider abstraction.

- mock       : offline canned responses (default) — exercises the whole pipeline
               without any API key. Responses are clearly marked [MOCK].
- groq       : Groq API (free tier). Needs GROQ_API_KEY.
- bedrock    : AWS Bedrock Converse API (ap-south-1). Needs AWS creds + a model
               ID enabled in the Bedrock console (BEDROCK_MODEL_ID).
- gemini     : Google AI Studio free tier (no credit card, just a Google
               account). Needs GEMINI_API_KEY. Generous limits.
- openrouter : OpenRouter :free models (no card). Needs OPENROUTER_API_KEY.

Switch with the LLM_PROVIDER env var.
"""
from __future__ import annotations

import time

import httpx

from . import config


def _post_with_retry(url: str, *, headers: dict, payload: dict,
                     timeout: float = 60.0) -> httpx.Response:
    """POST with one retry on 429 (free tiers rate-limit — the demo must not die)."""
    last: httpx.Response | None = None
    for attempt in range(2):
        resp = httpx.Client(timeout=timeout).post(url, headers=headers, json=payload)
        last = resp
        if resp.status_code != 429:
            return resp
        time.sleep(5)
    assert last is not None
    return last


class BaseLLM:
    name = "base"

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class MockLLM(BaseLLM):
    """Deterministic stand-in so the RAG + MCP + web stack is testable offline."""

    name = "mock"

    def complete(self, system: str, user: str) -> str:
        excerpt = user[:600].replace("\n", " ")
        return (
            "[MOCK — set LLM_PROVIDER=groq or bedrock for real answers]\n\n"
            "Arre, bahut badhiya question hai! Main abhi mock mode mein hoon, "
            "isliye poora Hinglish jawab nahi de sakta. Lekin dekho, tumhare "
            "notes mein is topic par yeh mila:\n\n"
            f"…{excerpt}…\n\n"
            "Real LLM connect karne ke baad main isko simple Hinglish mein "
            "samjhaunga, examples ke saath. [1]"
        )


class GroqLLM(BaseLLM):
    name = "groq"

    def __init__(self) -> None:
        from groq import Groq

        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set (LLM_PROVIDER=groq)")
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def complete(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.6,
            max_tokens=800,
        )
        return (resp.choices[0].message.content or "").strip()


class BedrockLLM(BaseLLM):
    """AWS Bedrock via the Converse API — this is the AWS Builder integration."""

    name = "bedrock"

    def __init__(self) -> None:
        import boto3

        self.client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)

    def complete(self, system: str, user: str) -> str:
        resp = self.client.converse(
            modelId=config.BEDROCK_MODEL_ID,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"maxTokens": 800, "temperature": 0.6},
        )
        blocks = resp["output"]["message"]["content"]
        return "".join(b.get("text", "") for b in blocks).strip()


class GeminiLLM(BaseLLM):
    """Google AI Studio free tier — no credit card, just a Google account."""

    name = "gemini"

    def __init__(self) -> None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set (LLM_PROVIDER=gemini)")

    def complete(self, system: str, user: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{config.GEMINI_MODEL}:generateContent"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 800},
        }
        resp = _post_with_retry(
            url,
            headers={"x-goog-api-key": config.GEMINI_API_KEY,
                     "Content-Type": "application/json"},
            payload=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()


class OpenRouterLLM(BaseLLM):
    """OpenRouter :free models — one key, many models, OpenAI-compatible."""

    name = "openrouter"

    def __init__(self) -> None:
        if not config.OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not set (LLM_PROVIDER=openrouter)")

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.6,
            "max_tokens": 800,
        }
        resp = _post_with_retry(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/vckshood",
                     "X-Title": "PadhaiPal"},
            payload=payload,
        )
        resp.raise_for_status()
        return (resp.json()["choices"][0]["message"]["content"] or "").strip()


_llm: BaseLLM | None = None


def get_llm() -> BaseLLM:
    global _llm
    if _llm is None:
        if config.LLM_PROVIDER == "groq":
            _llm = GroqLLM()
        elif config.LLM_PROVIDER == "bedrock":
            _llm = BedrockLLM()
        elif config.LLM_PROVIDER == "gemini":
            _llm = GeminiLLM()
        elif config.LLM_PROVIDER == "openrouter":
            _llm = OpenRouterLLM()
        else:
            _llm = MockLLM()
        print(f"[llm] provider: {_llm.name}")
    return _llm


def reset_llm() -> None:
    """For tests: drop the cached provider so env changes take effect."""
    global _llm
    _llm = None
