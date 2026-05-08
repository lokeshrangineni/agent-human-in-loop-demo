import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.database import init_db, migrate_db
from backend.routers import auth, invoices, approvals, feedback, prompts
from backend.services.prompt_manager import init_prompts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Invoice Processing Agent",
    description="Human-in-the-loop multi-agent invoice processing and approval workflow",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(approvals.router)
app.include_router(feedback.router)
app.include_router(prompts.router)


@app.on_event("startup")
async def startup():
    init_db()
    migrate_db()
    init_prompts()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
