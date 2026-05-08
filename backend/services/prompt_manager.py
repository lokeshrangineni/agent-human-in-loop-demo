"""
Prompt management service — versioned prompt storage with file-based initial load.

On first startup, prompts are loaded from markdown files in backend/prompts/.
After that, the active version is always read from the database.
Admins can edit prompts via the UI; every edit creates a new version.
"""

import logging
import uuid
from pathlib import Path

from backend.config import BASE_DIR
from backend.models.database import get_db, now_iso

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

PROMPT_KEYS = {
    "extraction_system": {
        "file": "extraction_system.md",
        "description": "System prompt for the Extraction Agent (vision LLM)",
    },
    "validation_system": {
        "file": "validation_system.md",
        "description": "System prompt for the Validation Agent",
    },
}


def init_prompts():
    """
    Load prompts from files into the database if they don't exist yet.
    Called during application startup.
    """
    with get_db() as conn:
        for key, meta in PROMPT_KEYS.items():
            existing = conn.execute(
                "SELECT id FROM prompt_versions WHERE prompt_key = ?", (key,)
            ).fetchone()

            if existing:
                logger.info("Prompt '%s' already in DB, skipping file load", key)
                continue

            file_path = PROMPTS_DIR / meta["file"]
            if not file_path.exists():
                logger.warning("Prompt file not found: %s", file_path)
                continue

            content = file_path.read_text(encoding="utf-8")
            version_id = str(uuid.uuid4())
            now = now_iso()

            conn.execute(
                """
                INSERT INTO prompt_versions 
                    (id, prompt_key, version, content, change_summary, 
                     created_by, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id, key, 1, content,
                    "Initial version loaded from file",
                    "system", 1, now,
                ),
            )
            logger.info("Loaded prompt '%s' from %s (version 1)", key, file_path.name)


def get_active_prompt(prompt_key: str) -> str:
    """Get the currently active prompt content for a given key."""
    content, _ = get_active_prompt_with_version(prompt_key)
    return content


def get_active_prompt_with_version(prompt_key: str) -> tuple[str, int | None]:
    """Return (content, version_number) for the currently active prompt."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT content, version FROM prompt_versions WHERE prompt_key = ? AND is_active = 1",
            (prompt_key,),
        ).fetchone()

    if not row:
        logger.warning("No active prompt for '%s', falling back to file", prompt_key)
        return _load_from_file(prompt_key), None

    return row["content"], row["version"]


def get_prompt_history(prompt_key: str) -> list[dict]:
    """Get all versions of a prompt, newest first."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, prompt_key, version, content, change_summary,
                   created_by, is_active, created_at
            FROM prompt_versions
            WHERE prompt_key = ?
            ORDER BY version DESC
            """,
            (prompt_key,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_all_prompts_summary() -> list[dict]:
    """Get a summary of all prompt keys with their active version info."""
    results = []
    with get_db() as conn:
        for key, meta in PROMPT_KEYS.items():
            active = conn.execute(
                """
                SELECT id, version, change_summary, created_by, created_at, content
                FROM prompt_versions
                WHERE prompt_key = ? AND is_active = 1
                """,
                (key,),
            ).fetchone()

            total_versions = conn.execute(
                "SELECT COUNT(*) as cnt FROM prompt_versions WHERE prompt_key = ?",
                (key,),
            ).fetchone()["cnt"]

            results.append({
                "prompt_key": key,
                "description": meta["description"],
                "active_version": dict(active) if active else None,
                "total_versions": total_versions,
            })

    return results


def create_prompt_version(
    prompt_key: str,
    content: str,
    change_summary: str,
    created_by: str,
    activate: bool = True,
) -> dict:
    """
    Create a new version of a prompt. Optionally set it as the active version.
    """
    if prompt_key not in PROMPT_KEYS:
        raise ValueError(f"Unknown prompt key: '{prompt_key}'")

    with get_db() as conn:
        max_version = conn.execute(
            "SELECT COALESCE(MAX(version), 0) as mv FROM prompt_versions WHERE prompt_key = ?",
            (prompt_key,),
        ).fetchone()["mv"]

        new_version = max_version + 1
        version_id = str(uuid.uuid4())
        now = now_iso()

        if activate:
            conn.execute(
                "UPDATE prompt_versions SET is_active = 0 WHERE prompt_key = ?",
                (prompt_key,),
            )

        conn.execute(
            """
            INSERT INTO prompt_versions 
                (id, prompt_key, version, content, change_summary, 
                 created_by, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id, prompt_key, new_version, content,
                change_summary, created_by,
                1 if activate else 0, now,
            ),
        )

        row = conn.execute(
            "SELECT * FROM prompt_versions WHERE id = ?", (version_id,)
        ).fetchone()

    logger.info(
        "Created prompt version: key=%s, version=%d, by=%s, active=%s",
        prompt_key, new_version, created_by, activate,
    )
    return dict(row)


def activate_prompt_version(prompt_key: str, version_id: str) -> dict:
    """Set a specific version as the active prompt (revert)."""
    with get_db() as conn:
        target = conn.execute(
            "SELECT * FROM prompt_versions WHERE id = ? AND prompt_key = ?",
            (version_id, prompt_key),
        ).fetchone()

        if not target:
            raise ValueError(f"Version {version_id} not found for prompt '{prompt_key}'")

        conn.execute(
            "UPDATE prompt_versions SET is_active = 0 WHERE prompt_key = ?",
            (prompt_key,),
        )
        conn.execute(
            "UPDATE prompt_versions SET is_active = 1 WHERE id = ?",
            (version_id,),
        )

        updated = conn.execute(
            "SELECT * FROM prompt_versions WHERE id = ?", (version_id,)
        ).fetchone()

    logger.info(
        "Activated prompt version: key=%s, version=%d",
        prompt_key, target["version"],
    )
    return dict(updated)


def _load_from_file(prompt_key: str) -> str:
    """Fallback: load prompt content directly from the markdown file."""
    meta = PROMPT_KEYS.get(prompt_key)
    if not meta:
        return ""
    file_path = PROMPTS_DIR / meta["file"]
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return ""
