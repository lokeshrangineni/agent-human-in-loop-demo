import logging

import httpx

from backend.services.llm.base import VisionLLM, LLMResponse

logger = logging.getLogger(__name__)


class OllamaLLM(VisionLLM):
    """
    Ollama provider — connects to a locally running Ollama instance.

    Supports vision models like LLaVA, Llama 3.2 Vision, etc.
    Uses the Ollama REST API (OpenAI-compatible /v1/chat/completions
    is also available, but the native API gives better control).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2-vision",
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        logger.info("Ollama LLM initialized: model=%s, base_url=%s", model, base_url)

    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        images_b64: list[str],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt,
                "images": images_b64,
            },
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        response = await self._client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("message", {}).get("content", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_duration_ms": data.get("total_duration", 0) / 1_000_000,
        }

        logger.info(
            "Ollama response: model=%s, eval_count=%s, duration=%.0fms",
            data.get("model", self.model),
            usage["completion_tokens"],
            usage["total_duration_ms"],
        )
        return LLMResponse(content=text, model=data.get("model", self.model), usage=usage)

    async def invoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        response = await self._client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("message", {}).get("content", "")
        return LLMResponse(content=text, model=data.get("model", self.model))

    def provider_name(self) -> str:
        return "ollama"
