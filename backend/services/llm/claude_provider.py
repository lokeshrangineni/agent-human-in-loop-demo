import logging

import anthropic

from backend.services.llm.base import VisionLLM, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeLLM(VisionLLM):
    """
    Anthropic Claude provider — direct API.

    Uses an API key to authenticate with Anthropic's API (or a custom proxy).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        base_url: str | None = None,
        max_retries: int = 2,
    ):
        client_kwargs: dict = {
            "api_key": api_key,
            "max_retries": max_retries,
        }
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = anthropic.AsyncAnthropic(**client_kwargs)
        self.model = model
        logger.info("Claude LLM initialized: model=%s, base_url=%s", model, base_url or "default")

    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        images_b64: list[str],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        content_blocks = _build_content_blocks(images_b64, user_prompt)
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": content_blocks}],
        )
        return _parse_response(response)

    async def invoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return _parse_response(response)

    def provider_name(self) -> str:
        return "claude"


class ClaudeVertexLLM(VisionLLM):
    """
    Claude on Google Vertex AI — enterprise deployment.

    Authenticates via Google Cloud Application Default Credentials (ADC).
    Requires:
      - gcloud CLI authenticated (gcloud auth application-default login), OR
      - GOOGLE_APPLICATION_CREDENTIALS env var pointing to a service account key
    """

    def __init__(
        self,
        project_id: str,
        region: str = "us-east5",
        model: str = "claude-sonnet-4@20250514",
        max_retries: int = 2,
    ):
        from anthropic import AsyncAnthropicVertex

        self.client = AsyncAnthropicVertex(
            project_id=project_id,
            region=region,
            max_retries=max_retries,
        )
        self.model = model
        self._project_id = project_id
        self._region = region
        logger.info(
            "Claude Vertex LLM initialized: model=%s, project=%s, region=%s",
            model, project_id, region,
        )

    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        images_b64: list[str],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        content_blocks = _build_content_blocks(images_b64, user_prompt)
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": content_blocks}],
        )
        return _parse_response(response)

    async def invoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return _parse_response(response)

    def provider_name(self) -> str:
        return "claude-vertex"


# ─── Shared helpers ─────────────────────────────────────────────


def _build_content_blocks(images_b64: list[str], user_prompt: str) -> list[dict]:
    blocks: list[dict] = []
    for img_b64 in images_b64:
        media_type = _detect_media_type(img_b64)
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": img_b64,
            },
        })
    blocks.append({"type": "text", "text": user_prompt})
    return blocks


def _parse_response(response) -> LLMResponse:
    text = response.content[0].text if response.content else ""
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    logger.info("Claude response: model=%s, tokens=%s", response.model, usage)
    return LLMResponse(content=text, model=response.model, usage=usage)


def _detect_media_type(b64_data: str) -> str:
    if b64_data.startswith("/9j/"):
        return "image/jpeg"
    if b64_data.startswith("iVBOR"):
        return "image/png"
    if b64_data.startswith("R0lGOD"):
        return "image/gif"
    if b64_data.startswith("UklGR"):
        return "image/webp"
    return "image/png"
