from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict | None = None


class VisionLLM(ABC):
    """Abstract base for vision-capable LLM providers."""

    @abstractmethod
    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        images_b64: list[str],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Send a vision request to the LLM.

        Args:
            system_prompt: System-level instructions.
            user_prompt: The user message / task description.
            images_b64: List of base64-encoded images (PNG/JPEG).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.

        Returns:
            LLMResponse with the model's text output.
        """
        ...

    @abstractmethod
    async def invoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a text-only request (no images)."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'claude', 'ollama')."""
        ...
