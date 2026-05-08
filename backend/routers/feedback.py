import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.models.database import get_db, now_iso
from backend.models.schemas import FeedbackCreate, FeedbackResponse, UserInfo
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    fb: FeedbackCreate,
    user: UserInfo = Depends(get_current_user),
):
    """User submits feedback to improve agent behavior (Workflow 2)."""
    feedback_id = str(uuid.uuid4())
    now = now_iso()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO feedback_memory 
                (id, invoice_id, vendor_name, invoice_format, field_name,
                 original_value, corrected_value, feedback_text, 
                 submitted_by, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                fb.invoice_id,
                fb.vendor_name,
                None,
                fb.field_name,
                fb.original_value,
                fb.corrected_value,
                fb.feedback_text,
                user.id,
                "pending",
                now,
            ),
        )

    return FeedbackResponse(
        id=feedback_id,
        invoice_id=fb.invoice_id,
        vendor_name=fb.vendor_name,
        field_name=fb.field_name,
        original_value=fb.original_value,
        corrected_value=fb.corrected_value,
        feedback_text=fb.feedback_text,
        submitted_by=user.id,
        status="pending",
        created_at=now,
    )


@router.get("", response_model=list[FeedbackResponse])
async def list_feedback(
    status: str | None = None,
    vendor: str | None = None,
    invoice_id: str | None = None,
    user: UserInfo = Depends(get_current_user),
):
    with get_db() as conn:
        query = "SELECT * FROM feedback_memory WHERE 1=1"
        params: list = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if vendor:
            query += " AND vendor_name = ?"
            params.append(vendor)
        if invoice_id:
            query += " AND invoice_id = ?"
            params.append(invoice_id)

        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()

    return [
        FeedbackResponse(
            id=row["id"],
            invoice_id=row["invoice_id"],
            vendor_name=row["vendor_name"],
            field_name=row["field_name"],
            original_value=row["original_value"],
            corrected_value=row["corrected_value"],
            feedback_text=row["feedback_text"],
            submitted_by=row["submitted_by"],
            status=row["status"],
            reviewed_by=row["reviewed_by"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@router.post("/{feedback_id}/review", response_model=FeedbackResponse)
async def review_feedback(
    feedback_id: str,
    action: dict,
    user: UserInfo = Depends(get_current_user),
):
    """Admin reviews feedback — approve or reject for agent learning."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can review feedback")

    new_status = action.get("status")
    if new_status not in ("approved", "rejected", "reviewed"):
        raise HTTPException(status_code=400, detail="Status must be 'approved', 'rejected', or 'reviewed'")

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM feedback_memory WHERE id = ?", (feedback_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Feedback not found")
        if row["status"] != "pending":
            raise HTTPException(status_code=400, detail="Feedback already reviewed")

        conn.execute(
            "UPDATE feedback_memory SET status = ?, reviewed_by = ? WHERE id = ?",
            (new_status, user.id, feedback_id),
        )

        updated = conn.execute(
            "SELECT * FROM feedback_memory WHERE id = ?", (feedback_id,)
        ).fetchone()

    return FeedbackResponse(
        id=updated["id"],
        invoice_id=updated["invoice_id"],
        vendor_name=updated["vendor_name"],
        field_name=updated["field_name"],
        original_value=updated["original_value"],
        corrected_value=updated["corrected_value"],
        feedback_text=updated["feedback_text"],
        submitted_by=updated["submitted_by"],
        status=updated["status"],
        reviewed_by=updated["reviewed_by"],
        created_at=updated["created_at"],
    )
