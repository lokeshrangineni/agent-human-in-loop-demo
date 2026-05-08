from backend.models.database import get_db


def get_vendor_feedback(vendor_name: str) -> list[dict]:
    """Retrieve approved feedback for a specific vendor to use as few-shot context."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT field_name, original_value, corrected_value, feedback_text
            FROM feedback_memory
            WHERE vendor_name = ? AND status = 'approved'
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (vendor_name,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_all_approved_feedback(limit: int = 50) -> list[dict]:
    """Retrieve all approved feedback for general agent context."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT vendor_name, field_name, original_value, corrected_value, feedback_text
            FROM feedback_memory
            WHERE status = 'approved'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def build_feedback_prompt(vendor_name: str | None = None) -> str:
    """Build a prompt section from accumulated feedback."""
    feedback_items = []

    if vendor_name:
        feedback_items = get_vendor_feedback(vendor_name)

    if not feedback_items:
        feedback_items = get_all_approved_feedback(limit=10)

    if not feedback_items:
        return ""

    lines = ["\n## Past Corrections and Feedback (use these to improve extraction accuracy):\n"]
    for item in feedback_items:
        if item.get("field_name") and item.get("corrected_value"):
            lines.append(
                f"- Field '{item['field_name']}': was extracted as '{item.get('original_value', '?')}', "
                f"corrected to '{item['corrected_value']}'"
            )
        if item.get("feedback_text"):
            lines.append(f"  Feedback: {item['feedback_text']}")

    return "\n".join(lines)
