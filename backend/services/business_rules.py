from backend.config import APPROVED_VENDORS, BUDGET_LIMIT
from backend.models.schemas import ExtractionResult, ValidationResult, ValidationRule


def validate_invoice(extraction: ExtractionResult) -> ValidationResult:
    """Run business rules against extracted invoice data."""
    rules: list[ValidationRule] = []

    vendor_name = _get_header_value(extraction, "vendor_name")
    if vendor_name:
        is_approved = any(
            vendor_name.lower() in v.lower() or v.lower() in vendor_name.lower()
            for v in APPROVED_VENDORS
        )
        rules.append(
            ValidationRule(
                rule_name="approved_vendor",
                passed=is_approved,
                severity="error" if not is_approved else "info",
                message=f"Vendor '{vendor_name}' is {'on' if is_approved else 'NOT on'} the approved vendor list.",
            )
        )
    else:
        rules.append(
            ValidationRule(
                rule_name="approved_vendor",
                passed=False,
                severity="warning",
                message="Vendor name could not be extracted — unable to verify against approved list.",
            )
        )

    total = _get_summary_value(extraction, ["grand_total", "total", "total_amount"])
    if total is not None:
        try:
            amount = float(total)
            within_budget = amount <= BUDGET_LIMIT
            rules.append(
                ValidationRule(
                    rule_name="budget_limit",
                    passed=within_budget,
                    severity="error" if not within_budget else "info",
                    message=f"Invoice total ${amount:,.2f} is {'within' if within_budget else 'OVER'} the ${BUDGET_LIMIT:,.2f} budget limit.",
                )
            )
        except (ValueError, TypeError):
            rules.append(
                ValidationRule(
                    rule_name="budget_limit",
                    passed=False,
                    severity="warning",
                    message=f"Could not parse total amount '{total}' for budget check.",
                )
            )

    required_fields = ["invoice_number", "vendor_name", "due_date"]
    missing = []
    for field in required_fields:
        val = _get_header_value(extraction, field)
        if not val:
            missing.append(field)

    rules.append(
        ValidationRule(
            rule_name="required_fields",
            passed=len(missing) == 0,
            severity="warning" if missing else "info",
            message=f"Missing required fields: {', '.join(missing)}" if missing else "All required fields present.",
        )
    )

    if extraction.line_items:
        rules.append(
            ValidationRule(
                rule_name="line_items_present",
                passed=True,
                severity="info",
                message=f"{len(extraction.line_items)} line item(s) extracted.",
            )
        )
    else:
        rules.append(
            ValidationRule(
                rule_name="line_items_present",
                passed=False,
                severity="warning",
                message="No line items found in invoice.",
            )
        )

    low_confidence_fields = _find_low_confidence(extraction)
    if low_confidence_fields:
        rules.append(
            ValidationRule(
                rule_name="confidence_check",
                passed=False,
                severity="warning",
                message=f"Low confidence on {len(low_confidence_fields)} field(s): {', '.join(low_confidence_fields)}",
            )
        )

    errors = sum(1 for r in rules if not r.passed and r.severity == "error")
    warnings = sum(1 for r in rules if not r.passed and r.severity == "warning")

    if errors > 0:
        recommendation = "reject"
    elif warnings > 0:
        recommendation = "review"
    else:
        recommendation = "approve"

    all_confidences = _collect_confidences(extraction)
    overall = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    pass_ratio = sum(1 for r in rules if r.passed) / len(rules) if rules else 0.0
    combined_confidence = (overall * 0.7) + (pass_ratio * 0.3)

    return ValidationResult(
        rules=rules,
        overall_recommendation=recommendation,
        overall_confidence=round(combined_confidence, 3),
    )


def _get_header_value(ext: ExtractionResult, field: str):
    f = ext.header_fields.get(field)
    return f.value if f else None


def _get_summary_value(ext: ExtractionResult, fields: list[str]):
    for field in fields:
        f = ext.summary_fields.get(field)
        if f and f.value is not None:
            return f.value
    return None


def _find_low_confidence(ext: ExtractionResult, threshold: float = 0.6) -> list[str]:
    low = []
    for name, field in ext.header_fields.items():
        if field.confidence < threshold:
            low.append(name)
    for name, field in ext.summary_fields.items():
        if field.confidence < threshold:
            low.append(name)
    for i, item in enumerate(ext.line_items):
        for name, field in item.items():
            if field.confidence < threshold:
                low.append(f"line_item[{i}].{name}")
    return low


def _collect_confidences(ext: ExtractionResult) -> list[float]:
    confs = []
    for f in ext.header_fields.values():
        confs.append(f.confidence)
    for f in ext.summary_fields.values():
        confs.append(f.confidence)
    for item in ext.line_items:
        for f in item.values():
            confs.append(f.confidence)
    return confs
