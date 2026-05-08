import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pathlib import Path

from backend.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR
from backend.models.database import get_db, now_iso
from backend.models.schemas import (
    ExtractionFieldUpdates,
    InvoiceActionRequest,
    InvoiceListItem,
    InvoiceResponse,
    ExtractionResult,
    ValidationResult,
    UserInfo,
)
from backend.routers.auth import get_current_user
from backend.storage.local import LocalDocumentStore

router = APIRouter(prefix="/api/invoices", tags=["invoices"])
store = LocalDocumentStore()


@router.post("", response_model=InvoiceResponse, status_code=201)
async def upload_invoice(
    file: UploadFile = File(...),
    user: UserInfo = Depends(get_current_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{suffix}' not allowed. Allowed: {ALLOWED_EXTENSIONS}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max: {MAX_FILE_SIZE_MB}MB",
        )

    invoice_id = str(uuid.uuid4())
    file_path = await store.upload(invoice_id, content, file.filename or "document.pdf")
    now = now_iso()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO invoices (id, file_name, file_path, file_size, mime_type, 
                                  status, uploaded_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice_id,
                file.filename,
                file_path,
                len(content),
                file.content_type,
                "uploaded",
                user.id,
                now,
                now,
            ),
        )

    return InvoiceResponse(
        id=invoice_id,
        file_name=file.filename or "",
        status="uploaded",
        uploaded_by=user.id,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=list[InvoiceListItem])
async def list_invoices(user: UserInfo = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM invoices ORDER BY created_at DESC"
        ).fetchall()

    items = []
    for row in rows:
        vendor_name = None
        invoice_number = None
        total_amount = None

        if row["extraction_result"]:
            ext = json.loads(row["extraction_result"])
            header = ext.get("header_fields", {})
            summary = ext.get("summary_fields", {})
            if "vendor_name" in header:
                vendor_name = header["vendor_name"].get("value")
            if "invoice_number" in header:
                invoice_number = header["invoice_number"].get("value")
            for key in ("grand_total", "total", "total_amount"):
                if key in summary:
                    total_amount = summary[key].get("value")
                    break

        items.append(
            InvoiceListItem(
                id=row["id"],
                file_name=row["file_name"],
                status=row["status"],
                uploaded_by=row["uploaded_by"],
                overall_confidence=row["overall_confidence"],
                vendor_name=vendor_name,
                invoice_number=invoice_number,
                total_amount=total_amount,
                created_at=row["created_at"],
            )
        )
    return items


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    user: UserInfo = Depends(get_current_user),
):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if user.role != "admin" and row["uploaded_by"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    extraction = None
    if row["extraction_result"]:
        extraction = ExtractionResult(**json.loads(row["extraction_result"]))

    validation = None
    if row["validation_result"]:
        validation = ValidationResult(**json.loads(row["validation_result"]))

    return InvoiceResponse(
        id=row["id"],
        file_name=row["file_name"],
        status=row["status"],
        uploaded_by=row["uploaded_by"],
        extraction_result=extraction,
        validation_result=validation,
        overall_confidence=row["overall_confidence"],
        page_count=row["page_count"] or 0,
        extraction_prompt_version=row["extraction_prompt_version"],
        validation_prompt_version=row["validation_prompt_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/{invoice_id}/document")
async def download_document(
    invoice_id: str,
    user: UserInfo = Depends(get_current_user),
):
    from fastapi.responses import FileResponse

    with get_db() as conn:
        row = conn.execute(
            "SELECT file_path, file_name, mime_type, uploaded_by FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if user.role != "admin" and row["uploaded_by"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    file_path = Path(row["file_path"]).resolve()
    upload_root = Path(UPLOAD_DIR).resolve()
    if not str(file_path).startswith(str(upload_root)):
        raise HTTPException(status_code=403, detail="Invalid file path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found")

    MIME_MAP = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".tiff": "image/tiff", ".bmp": "image/bmp"}
    safe_media_type = MIME_MAP.get(file_path.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=row["file_name"],
        media_type=safe_media_type,
    )


@router.post("/{invoice_id}/process")
async def process_invoice(
    invoice_id: str,
    user: UserInfo = Depends(get_current_user),
):
    """Trigger extraction + validation workflow for an uploaded invoice."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if user.role != "admin" and row["uploaded_by"] != user.id:
        raise HTTPException(status_code=403, detail="Only the uploader or an admin can process this invoice")

    from backend.agents.orchestrator import run_invoice_workflow

    result = await run_invoice_workflow(invoice_id)
    return result


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: str,
    user: UserInfo = Depends(get_current_user),
):
    """Delete an invoice. Admins can delete any invoice; uploaders can delete their own."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, uploaded_by FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if user.role != "admin" and row["uploaded_by"] != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own invoices")

    # Remove DB records (cascade via foreign keys or explicit deletes)
    with get_db() as conn:
        conn.execute("DELETE FROM approval_requests WHERE invoice_id = ?", (invoice_id,))
        conn.execute("DELETE FROM feedback_memory WHERE invoice_id = ?", (invoice_id,))
        conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))

    # Remove uploaded files from storage
    await store.delete(invoice_id)


@router.patch("/{invoice_id}/fields", response_model=InvoiceResponse)
async def update_fields(
    invoice_id: str,
    updates: ExtractionFieldUpdates,
    user: UserInfo = Depends(get_current_user),
):
    """User corrects individual extracted fields before submitting for approval."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if user.role != "admin" and row["uploaded_by"] != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own invoices")

    if not row["extraction_result"]:
        raise HTTPException(status_code=400, detail="No extraction result to update")

    extraction = json.loads(row["extraction_result"])

    # Apply header field updates — preserve confidence shape, mark as user-verified
    if updates.header_fields:
        for key, new_value in updates.header_fields.items():
            if key in extraction.get("header_fields", {}):
                extraction["header_fields"][key]["value"] = new_value
                extraction["header_fields"][key]["confidence"] = 1.0
                extraction["header_fields"][key]["user_edited"] = True
            else:
                extraction.setdefault("header_fields", {})[key] = {
                    "value": new_value, "confidence": 1.0, "user_edited": True
                }

    # Apply summary field updates
    if updates.summary_fields:
        for key, new_value in updates.summary_fields.items():
            if key in extraction.get("summary_fields", {}):
                extraction["summary_fields"][key]["value"] = new_value
                extraction["summary_fields"][key]["confidence"] = 1.0
                extraction["summary_fields"][key]["user_edited"] = True
            else:
                extraction.setdefault("summary_fields", {})[key] = {
                    "value": new_value, "confidence": 1.0, "user_edited": True
                }

    # Replace line items wholesale (each cell value updated, confidence set to 1.0)
    if updates.line_items is not None:
        updated_rows = []
        for row_data in updates.line_items:
            updated_row = {}
            for col, new_value in row_data.items():
                updated_row[col] = {"value": new_value, "confidence": 1.0, "user_edited": True}
            updated_rows.append(updated_row)
        extraction["line_items"] = updated_rows

    now = now_iso()
    with get_db() as conn:
        conn.execute(
            "UPDATE invoices SET extraction_result = ?, updated_at = ? WHERE id = ?",
            (json.dumps(extraction), now, invoice_id),
        )
        updated_row = conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    ext = ExtractionResult(**json.loads(updated_row["extraction_result"]))
    val = None
    if updated_row["validation_result"]:
        val = ValidationResult(**json.loads(updated_row["validation_result"]))

    return InvoiceResponse(
        id=updated_row["id"],
        file_name=updated_row["file_name"],
        status=updated_row["status"],
        uploaded_by=updated_row["uploaded_by"],
        extraction_result=ext,
        validation_result=val,
        overall_confidence=updated_row["overall_confidence"],
        page_count=updated_row["page_count"] or 0,
        extraction_prompt_version=updated_row["extraction_prompt_version"],
        validation_prompt_version=updated_row["validation_prompt_version"],
        created_at=updated_row["created_at"],
        updated_at=updated_row["updated_at"],
    )


@router.post("/{invoice_id}/action")
async def invoice_action(
    invoice_id: str,
    action: InvoiceActionRequest,
    user: UserInfo = Depends(get_current_user),
):
    """Approve, reject, or request reprocessing of an invoice."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Only admins may approve or reject
    if action.action in ("approve", "reject") and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can approve or reject invoices",
        )

    # Only the submitter (or admin) may submit or reprocess
    if action.action in ("submit", "reprocess") and user.role != "admin" and row["uploaded_by"] != user.id:
        raise HTTPException(status_code=403, detail="You can only submit/reprocess your own invoices")

    status_map = {
        "submit": "pending_approval",
        "approve": "approved",
        "reject": "rejected",
        "reprocess": "uploaded",
    }
    new_status = status_map.get(action.action)
    if not new_status:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action.action}")

    now = now_iso()
    with get_db() as conn:
        conn.execute(
            "UPDATE invoices SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, invoice_id),
        )

    if action.action == "reprocess":
        from backend.agents.orchestrator import run_invoice_workflow
        result = await run_invoice_workflow(invoice_id)
        return result

    return {"status": new_status, "invoice_id": invoice_id}
