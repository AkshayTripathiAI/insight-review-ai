import json
from typing import Any
from typing import Dict

import requests

from app.config import get_settings


class LLMClient:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError


class StubLLMClient(LLMClient):
    def generate(self, prompt: str) -> str:
        return "This is a stubbed LLM response. Replace StubLLMClient with a real provider."

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        return {"aspects": [], "sentiment": "neutral"}


class LlamaOllamaClient(LLMClient):
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        instruction = (
            "Return a JSON object only, with keys aspects and sentiment. "
            "Do not include any explanation."
        )
        full_prompt = f"{instruction}\n\n{prompt}"
        text = self.generate(full_prompt)
        try:
            return json.loads(text)
        except Exception:
            return {"aspects": [], "sentiment": "neutral"}


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "ollama-llama":
        return LlamaOllamaClient(base_url=settings.llm_base_url, model=settings.llm_model)
    return StubLLMClient()
