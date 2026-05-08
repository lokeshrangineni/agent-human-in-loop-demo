"""
Invoice processing orchestrator — coordinates the Extraction and Validation agents.

Phase 1: Simple sequential orchestration.
Phase 2: Will be replaced with a LangGraph StateGraph with interrupt()
for human-in-the-loop checkpoints.
"""

import logging
from pathlib import Path

from backend.agents.extraction import extract_invoice
from backend.agents.validation import validate_extraction
from backend.models.database import get_db, now_iso
from backend.services.pdf_converter import document_to_images_b64
from backend.services.prompt_manager import get_active_prompt_with_version

logger = logging.getLogger(__name__)


async def run_invoice_workflow(invoice_id: str) -> dict:
    """Run the full extraction + validation workflow for an invoice."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    if not row:
        raise ValueError(f"Invoice {invoice_id} not found")

    now = now_iso()
    with get_db() as conn:
        conn.execute(
            "UPDATE invoices SET status = ?, updated_at = ? WHERE id = ?",
            ("processing", now, invoice_id),
        )

    # Step 1: Convert document to images for the vision LLM
    from backend.config import UPLOAD_DIR
    file_path = Path(row["file_path"]).resolve()
    upload_root = Path(UPLOAD_DIR).resolve()
    if not str(file_path).startswith(str(upload_root)):
        raise ValueError("Invalid document path")
    logger.info("Converting document to images: %s", file_path)
    try:
        images_b64 = document_to_images_b64(file_path)
    except Exception as e:
        logger.error("Document conversion failed: %s", e)
        now = now_iso()
        with get_db() as conn:
            conn.execute(
                "UPDATE invoices SET status = ?, updated_at = ? WHERE id = ?",
                ("uploaded", now, invoice_id),
            )
        return {
            "invoice_id": invoice_id,
            "status": "error",
            "error": "Document processing failed. Please check the file and try again.",
        }

    page_count = len(images_b64)

    # Capture active prompt versions before running agents
    _, ext_prompt_version = get_active_prompt_with_version("extraction_system")
    _, val_prompt_version = get_active_prompt_with_version("validation_system")

    # Step 2: Extract
    logger.info("Starting extraction for invoice %s (%d pages)", invoice_id, page_count)
    extraction = await extract_invoice(
        image_data=images_b64,
        vendor_hint=None,
    )

    now = now_iso()
    with get_db() as conn:
        conn.execute(
            """UPDATE invoices 
               SET extraction_result = ?, status = ?, page_count = ?,
                   extraction_prompt_version = ?, updated_at = ?
               WHERE id = ?""",
            (extraction.model_dump_json(), "extracted", page_count,
             ext_prompt_version, now, invoice_id),
        )

    # Step 3: Validate
    logger.info("Starting validation for invoice %s", invoice_id)
    validation = await validate_extraction(extraction)

    status = "pending_review"
    if validation.overall_recommendation == "approve":
        status = "validated"

    now = now_iso()
    with get_db() as conn:
        conn.execute(
            """UPDATE invoices 
               SET validation_result = ?, overall_confidence = ?,
                   validation_prompt_version = ?, status = ?, updated_at = ?
               WHERE id = ?""",
            (
                validation.model_dump_json(),
                validation.overall_confidence,
                val_prompt_version,
                status,
                now,
                invoice_id,
            ),
        )

    logger.info(
        "Workflow complete for invoice %s: status=%s, confidence=%.2f",
        invoice_id, status, validation.overall_confidence,
    )

    return {
        "invoice_id": invoice_id,
        "status": status,
        "overall_confidence": validation.overall_confidence,
        "recommendation": validation.overall_recommendation,
    }
