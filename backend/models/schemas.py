from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    id: str
    name: str
    role: str  # "admin" or "user"


class ExtractedField(BaseModel):
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    original_text: str | None = None


class ExtractionResult(BaseModel):
    header_fields: dict[str, ExtractedField] = Field(default_factory=dict)
    line_items: list[dict[str, ExtractedField]] = Field(default_factory=list)
    summary_fields: dict[str, ExtractedField] = Field(default_factory=dict)
    raw_text: str | None = None
    extraction_notes: list[str] = Field(default_factory=list)


class ValidationRule(BaseModel):
    rule_name: str
    passed: bool
    severity: str = "info"  # info, warning, error
    message: str


class ValidationResult(BaseModel):
    rules: list[ValidationRule] = Field(default_factory=list)
    overall_recommendation: str = "pending"  # approve, reject, review
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_notes: list[str] = Field(default_factory=list)


class InvoiceResponse(BaseModel):
    id: str
    file_name: str
    status: str
    uploaded_by: str
    extraction_result: ExtractionResult | None = None
    validation_result: ValidationResult | None = None
    overall_confidence: float | None = None
    page_count: int = 0
    extraction_prompt_version: int | None = None
    validation_prompt_version: int | None = None
    created_at: str
    updated_at: str


class InvoiceListItem(BaseModel):
    id: str
    file_name: str
    status: str
    uploaded_by: str
    overall_confidence: float | None = None
    vendor_name: str | None = None
    invoice_number: str | None = None
    total_amount: float | None = None
    created_at: str


class ApprovalRequestCreate(BaseModel):
    invoice_id: str
    proposed_changes: dict[str, Any]


class ApprovalRequestResponse(BaseModel):
    id: str
    invoice_id: str
    request_type: str
    requested_by: str
    proposed_changes: dict[str, Any]
    status: str
    reviewed_by: str | None = None
    admin_notes: str | None = None
    final_changes: dict[str, Any] | None = None
    created_at: str
    updated_at: str


class ApprovalAction(BaseModel):
    status: Literal["approved", "rejected", "modified"]
    admin_notes: str | None = Field(default=None, max_length=2048)
    final_changes: dict[str, Any] | None = None


class FeedbackCreate(BaseModel):
    invoice_id: str = Field(max_length=64)
    vendor_name: str | None = Field(default=None, max_length=256)
    field_name: str | None = Field(default=None, max_length=128)
    original_value: str | None = Field(default=None, max_length=2048)
    corrected_value: str | None = Field(default=None, max_length=2048)
    feedback_text: str = Field(max_length=5000)


class FeedbackResponse(BaseModel):
    id: str
    invoice_id: str | None = None
    vendor_name: str | None = None
    field_name: str | None = None
    original_value: str | None = None
    corrected_value: str | None = None
    feedback_text: str
    submitted_by: str
    status: str
    reviewed_by: str | None = None
    created_at: str


class InvoiceActionRequest(BaseModel):
    action: Literal["submit", "approve", "reject", "reprocess"]


class ExtractionFieldUpdates(BaseModel):
    """Partial updates to extracted fields made by the user before submission."""
    header_fields: dict[str, Any] | None = None   # key -> new value
    summary_fields: dict[str, Any] | None = None  # key -> new value
    line_items: list[dict[str, Any]] | None = None  # full row replacement list
