"""
Extraction Agent — parses invoice documents and extracts structured data
with confidence scores.

Uses a vision-capable LLM to analyze PDF pages and extract all invoice fields
dynamically (no fixed schema assumed).
"""

import json
import logging

from backend.models.schemas import ExtractionResult, ExtractedField
from backend.services.feedback_memory import build_feedback_prompt
from backend.services.llm import get_llm
from backend.services.prompt_manager import get_active_prompt

logger = logging.getLogger(__name__)

USER_PROMPT = "Extract all invoice data from this document. Return strict JSON matching the schema."


async def extract_invoice(
    image_data: list[str],
    vendor_hint: str | None = None,
) -> ExtractionResult:
    """
    Extract structured data from invoice page images.

    Args:
        image_data: List of base64-encoded page images.
        vendor_hint: Optional vendor name to retrieve relevant feedback.
    """
    if not image_data:
        logger.warning("No images provided for extraction")
        return _empty_result("No document images provided")

    feedback_context = build_feedback_prompt(vendor_hint)
    system_prompt = get_active_prompt("extraction_system")
    if feedback_context:
        system_prompt += feedback_context

    llm = get_llm()
    logger.info(
        "Running extraction via %s with %d page image(s)",
        llm.provider_name(), len(image_data),
    )

    try:
        response = await llm.invoke(
            system_prompt=system_prompt,
            user_prompt=USER_PROMPT,
            images_b64=image_data,
            temperature=0.0,
            max_tokens=4096,
        )
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return _empty_result(f"LLM call failed: {e}")

    return _parse_response(response.content)


def _parse_response(raw: str) -> ExtractionResult:
    """Parse the LLM's JSON response into an ExtractionResult."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM response as JSON: %s\nRaw: %s", e, raw[:500])
        return _empty_result(f"Failed to parse LLM response: {e}")

    try:
        header_fields = {
            k: ExtractedField(**v) if isinstance(v, dict) else ExtractedField(value=v, confidence=0.5)
            for k, v in data.get("header_fields", {}).items()
        }

        line_items = []
        for row in data.get("line_items", []):
            parsed_row = {
                k: ExtractedField(**v) if isinstance(v, dict) else ExtractedField(value=v, confidence=0.5)
                for k, v in row.items()
            }
            line_items.append(parsed_row)

        summary_fields = {
            k: ExtractedField(**v) if isinstance(v, dict) else ExtractedField(value=v, confidence=0.5)
            for k, v in data.get("summary_fields", {}).items()
        }

        return ExtractionResult(
            header_fields=header_fields,
            line_items=line_items,
            summary_fields=summary_fields,
            extraction_notes=data.get("extraction_notes", []),
        )

    except Exception as e:
        logger.error("Failed to build ExtractionResult: %s", e)
        return _empty_result(f"Failed to structure extraction: {e}")


def _empty_result(note: str) -> ExtractionResult:
    return ExtractionResult(
        header_fields={},
        line_items=[],
        summary_fields={},
        extraction_notes=[note],
    )
