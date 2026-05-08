import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from backend.config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                page_count INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'uploaded',
                -- status: uploaded, processing, extracted, validated, 
                --         approved, rejected, pending_review
                uploaded_by TEXT NOT NULL,
                extraction_result TEXT,   -- JSON
                validation_result TEXT,   -- JSON
                overall_confidence REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approval_requests (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                request_type TEXT NOT NULL,
                -- request_type: data_correction, feedback
                requested_by TEXT NOT NULL,
                proposed_changes TEXT NOT NULL,  -- JSON
                status TEXT NOT NULL DEFAULT 'pending',
                -- status: pending, approved, rejected, modified
                reviewed_by TEXT,
                admin_notes TEXT,
                final_changes TEXT,  -- JSON: what admin actually approved
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            );

            CREATE TABLE IF NOT EXISTS feedback_memory (
                id TEXT PRIMARY KEY,
                invoice_id TEXT,
                vendor_name TEXT,
                invoice_format TEXT,
                field_name TEXT,
                original_value TEXT,
                corrected_value TEXT,
                feedback_text TEXT,
                submitted_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                -- status: pending, approved, rejected
                reviewed_by TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            );

            CREATE INDEX IF NOT EXISTS idx_invoices_status 
                ON invoices(status);
            CREATE INDEX IF NOT EXISTS idx_invoices_uploaded_by 
                ON invoices(uploaded_by);
            CREATE INDEX IF NOT EXISTS idx_invoices_created_at 
                ON invoices(created_at);
            CREATE INDEX IF NOT EXISTS idx_approval_requests_status 
                ON approval_requests(status);
            CREATE INDEX IF NOT EXISTS idx_approval_requests_invoice 
                ON approval_requests(invoice_id);
            CREATE INDEX IF NOT EXISTS idx_feedback_memory_vendor 
                ON feedback_memory(vendor_name);
            CREATE INDEX IF NOT EXISTS idx_feedback_memory_status 
                ON feedback_memory(status);

            CREATE TABLE IF NOT EXISTS prompt_versions (
                id TEXT PRIMARY KEY,
                prompt_key TEXT NOT NULL,
                -- prompt_key: extraction_system, validation_system
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                change_summary TEXT,
                created_by TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(prompt_key, version)
            );

            CREATE INDEX IF NOT EXISTS idx_prompt_versions_key
                ON prompt_versions(prompt_key);
            CREATE INDEX IF NOT EXISTS idx_prompt_versions_active
                ON prompt_versions(prompt_key, is_active);
        """)


def migrate_db():
    """Apply incremental schema migrations for columns added after initial release."""
    migrations = [
        "ALTER TABLE invoices ADD COLUMN extraction_prompt_version INTEGER",
        "ALTER TABLE invoices ADD COLUMN validation_prompt_version INTEGER",
    ]
    with get_db() as conn:
        for sql in migrations:
            try:
                conn.execute(sql)
            except Exception:
                pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
