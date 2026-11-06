import json
import logging
import re
from typing import Any
from typing import Dict

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)


def parse_json_object(text: str) -> Dict[str, Any]:
    """Parse the first JSON object in a model reply (tolerates code fences and preambles)."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {}


class LLMClient:
    model_name = "stub"

    def generate(self, prompt: str, system: str | None = None) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str, system: str | None = None) -> Dict[str, Any]:
        instruction = "Respond with a single JSON object only, no prose and no code fences."
        text = self.generate(prompt, system=f"{system}\n\n{instruction}" if system else instruction)
        return parse_json_object(text)


class StubLLMClient(LLMClient):
    """Offline placeholder so the pipeline runs without an LLM (tests, local dev)."""

    def generate(self, prompt: str, system: str | None = None) -> str:
        return "This is a stubbed LLM response. Set LLM_PROVIDER to use a real model."

    def generate_json(self, prompt: str, system: str | None = None) -> Dict[str, Any]:
        return {}


class OpenAICompatibleClient(LLMClient):
    """Chat Completions client for any OpenAI-compatible endpoint (Groq, OpenAI, Ollama /v1, vLLM...)."""

    def __init__(self, base_url: str, model: str, api_key: str | None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self.api_key = api_key

    def _chat(self, prompt: str, system: str | None, json_mode: bool) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: Dict[str, Any] = {"model": self.model_name, "messages": messages, "temperature": 0.2}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=90)
        if response.status_code == 400 and json_mode:
            # Some models/providers reject response_format; retry with prompt-only JSON instructions.
            payload.pop("response_format")
            response = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=90)
        response.raise_for_status()
        return response.json()["choices"][0]["message"].get("content") or ""

    def generate(self, prompt: str, system: str | None = None) -> str:
        return self._chat(prompt, system, json_mode=False)

    def generate_json(self, prompt: str, system: str | None = None) -> Dict[str, Any]:
        instruction = "Respond with a single JSON object only, no prose and no code fences."
        full_system = f"{system}\n\n{instruction}" if system else instruction
        return parse_json_object(self._chat(prompt, full_system, json_mode=True))


class LlamaOllamaClient(LLMClient):
    """Native Ollama API (e.g. a local Llama 3.2)."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model

    def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "openai":
        return OpenAICompatibleClient(settings.llm_base_url, settings.llm_model, settings.llm_api_key)
    if settings.llm_provider == "ollama-llama":
        return LlamaOllamaClient(base_url=settings.llm_base_url, model=settings.llm_model)
    return StubLLMClient()
