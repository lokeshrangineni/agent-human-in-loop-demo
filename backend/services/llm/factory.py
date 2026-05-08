import logging
import os

from backend.services.llm.base import VisionLLM

logger = logging.getLogger(__name__)

_instance: VisionLLM | None = None


def get_llm() -> VisionLLM:
    """
    Factory that returns a configured VisionLLM based on environment settings.

    Configuration via environment variables:
      LLM_PROVIDER    — "claude", "claude-vertex", or "ollama" (default: "ollama")

    For Claude (direct API):
      ANTHROPIC_API_KEY    — API key (required)
      CLAUDE_MODEL         — Model name (default: "claude-sonnet-4-20250514")
      CLAUDE_BASE_URL      — Custom base URL for proxy deployments

    For Claude on Vertex AI (enterprise):
      VERTEX_PROJECT_ID    — Google Cloud project ID (required)
      VERTEX_REGION        — GCP region (default: "us-east5")
      CLAUDE_MODEL         — Model name (default: "claude-sonnet-4@20250514")
      Auth: uses Application Default Credentials (gcloud auth or service account)

    For Ollama (local):
      OLLAMA_BASE_URL      — Ollama server URL (default: "http://localhost:11434")
      OLLAMA_MODEL         — Model name (default: "llama3.2-vision")
    """
    global _instance
    if _instance is not None:
        return _instance

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "claude":
        from backend.services.llm.claude_provider import ClaudeLLM

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required for Claude provider. "
                "Set it in your .env file or environment."
            )

        _instance = ClaudeLLM(
            api_key=api_key,
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            base_url=os.getenv("CLAUDE_BASE_URL"),
        )

    elif provider == "claude-vertex":
        from backend.services.llm.claude_provider import ClaudeVertexLLM

        project_id = os.getenv("VERTEX_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "VERTEX_PROJECT_ID is required for Claude Vertex provider. "
                "Set it in your .env file or environment."
            )

        _instance = ClaudeVertexLLM(
            project_id=project_id,
            region=os.getenv("VERTEX_REGION", "us-east5"),
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4@20250514"),
        )

    elif provider == "ollama":
        from backend.services.llm.ollama_provider import OllamaLLM

        _instance = OllamaLLM(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2-vision"),
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. "
            "Supported: 'claude', 'claude-vertex', 'ollama'"
        )

    logger.info("LLM provider initialized: %s", _instance.provider_name())
    return _instance


def reset_llm():
    """Reset the singleton (useful for testing or config changes)."""
    global _instance
    _instance = None
