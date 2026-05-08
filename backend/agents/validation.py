"""
Validation Agent — cross-references extracted invoice data against 
business rules and produces a validation report.
"""

import logging

from backend.models.schemas import ExtractionResult, ValidationResult
from backend.services.business_rules import validate_invoice

logger = logging.getLogger(__name__)


async def validate_extraction(
    extraction: ExtractionResult,
) -> ValidationResult:
    """
    Validate extracted invoice data against business rules.
    
    Returns a validation report with per-rule results and an 
    overall recommendation.
    """
    result = validate_invoice(extraction)
    logger.info(
        "Validation complete: recommendation=%s, confidence=%.2f, rules=%d",
        result.overall_recommendation,
        result.overall_confidence,
        len(result.rules),
    )
    return result


async def request_re_extraction(
    extraction: ExtractionResult,
    low_confidence_fields: list[str],
) -> list[str]:
    """
    Determine which fields should be re-extracted based on validation results.
    Returns a list of field names that need clarification.
    """
    fields_to_retry = []
    threshold = 0.5

    for name, field in extraction.header_fields.items():
        if name in low_confidence_fields and field.confidence < threshold:
            fields_to_retry.append(name)

    for name, field in extraction.summary_fields.items():
        if name in low_confidence_fields and field.confidence < threshold:
            fields_to_retry.append(name)

    return fields_to_retry
