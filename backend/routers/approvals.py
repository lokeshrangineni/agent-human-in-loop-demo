import json
import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.models.database import get_db, now_iso
from backend.models.schemas import (
    ApprovalAction,
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    UserInfo,
)
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.post("", response_model=ApprovalRequestResponse, status_code=201)
async def create_approval_request(
    req: ApprovalRequestCreate,
    user: UserInfo = Depends(get_current_user),
):
    """User submits data corrections for admin approval (Workflow 1)."""
    approval_id = str(uuid.uuid4())
    now = now_iso()

    with get_db() as conn:
        invoice = conn.execute(
            "SELECT id FROM invoices WHERE id = ?", (req.invoice_id,)
        ).fetchone()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        conn.execute(
            """
            INSERT INTO approval_requests 
                (id, invoice_id, request_type, requested_by, proposed_changes, 
                 status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval_id,
                req.invoice_id,
                "data_correction",
                user.id,
                json.dumps(req.proposed_changes),
                "pending",
                now,
                now,
            ),
        )

    return ApprovalRequestResponse(
        id=approval_id,
        invoice_id=req.invoice_id,
        request_type="data_correction",
        requested_by=user.id,
        proposed_changes=req.proposed_changes,
        status="pending",
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=list[ApprovalRequestResponse])
async def list_approval_requests(
    status: str | None = None,
    user: UserInfo = Depends(get_current_user),
):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM approval_requests ORDER BY created_at DESC"
            ).fetchall()

    return [
        ApprovalRequestResponse(
            id=row["id"],
            invoice_id=row["invoice_id"],
            request_type=row["request_type"],
            requested_by=row["requested_by"],
            proposed_changes=json.loads(row["proposed_changes"]),
            status=row["status"],
            reviewed_by=row["reviewed_by"],
            admin_notes=row["admin_notes"],
            final_changes=json.loads(row["final_changes"]) if row["final_changes"] else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.post("/{approval_id}/review", response_model=ApprovalRequestResponse)
async def review_approval(
    approval_id: str,
    action: ApprovalAction,
    user: UserInfo = Depends(get_current_user),
):
    """Admin reviews and acts on an approval request."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can review approvals")

    if action.status not in ("approved", "rejected", "modified"):
        raise HTTPException(status_code=400, detail="Invalid status")

    now = now_iso()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM approval_requests WHERE id = ?", (approval_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Approval request not found")
        if row["status"] != "pending":
            raise HTTPException(status_code=400, detail="Request already reviewed")

        conn.execute(
            """
            UPDATE approval_requests 
            SET status = ?, reviewed_by = ?, admin_notes = ?, 
                final_changes = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                action.status,
                user.id,
                action.admin_notes,
                json.dumps(action.final_changes) if action.final_changes else None,
                now,
                approval_id,
            ),
        )

        if action.status in ("approved", "modified"):
            changes = action.final_changes or json.loads(row["proposed_changes"])
            invoice_row = conn.execute(
                "SELECT extraction_result FROM invoices WHERE id = ?",
                (row["invoice_id"],),
            ).fetchone()

            if invoice_row and invoice_row["extraction_result"]:
                extraction = json.loads(invoice_row["extraction_result"])
                for key, val in changes.items():
                    if key == "header_fields":
                        extraction.setdefault("header_fields", {}).update(val)
                    elif key == "line_items":
                        extraction["line_items"] = val
                    elif key == "summary_fields":
                        extraction.setdefault("summary_fields", {}).update(val)

                conn.execute(
                    "UPDATE invoices SET extraction_result = ?, updated_at = ? WHERE id = ?",
                    (json.dumps(extraction), now, row["invoice_id"]),
                )

        updated = conn.execute(
            "SELECT * FROM approval_requests WHERE id = ?", (approval_id,)
        ).fetchone()

    return ApprovalRequestResponse(
        id=updated["id"],
        invoice_id=updated["invoice_id"],
        request_type=updated["request_type"],
        requested_by=updated["requested_by"],
        proposed_changes=json.loads(updated["proposed_changes"]),
        status=updated["status"],
        reviewed_by=updated["reviewed_by"],
        admin_notes=updated["admin_notes"],
        final_changes=json.loads(updated["final_changes"]) if updated["final_changes"] else None,
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )
