import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DATABASE_PATH = BASE_DIR / "data" / "invoices.db"
DATABASE_PATH.parent.mkdir(exist_ok=True)

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # "local" or "s3"

MAX_FILE_SIZE_MB = 30
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}

HARDCODED_USERS = [
    {"id": "admin-jane", "name": "Jane (Admin)", "role": "admin"},
    {"id": "admin-bob", "name": "Bob (Admin)", "role": "admin"},
    {"id": "user-john", "name": "John", "role": "user"},
    {"id": "user-sarah", "name": "Sarah", "role": "user"},
]

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

APPROVED_VENDORS = [
    "Acme Office Supplies Co.",
    "British Cloud Services Ltd.",
    "Martinez & Sons Construction",
    "Sakura Electronics Inc.",
    "LegalShield Consulting Group",
    "Cafe Minimal Roasters",
]

BUDGET_LIMIT = 50000.00
