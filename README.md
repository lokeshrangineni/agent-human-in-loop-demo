# Invoice Agent — Human-in-the-Loop Multi-Agent Demo

A full-stack demo application showcasing a **human-in-the-loop multi-agent system** for invoice processing. Two AI agents (extraction and validation) collaborate to process uploaded invoices, while humans review, correct, and approve the results through a structured workflow.

## Features

### Multi-Agent Processing
- **Extraction Agent** — uses a vision LLM to read invoice images/PDFs and produce structured data (vendor, line items, amounts, dates, etc.) with per-field confidence scores.
- **Validation Agent** — cross-references extracted data against configurable business rules (budget limits, approved vendor list, duplicate detection) and produces an overall recommendation.
- Agents use **configurable system prompts** stored as versioned markdown, editable by admins at runtime.

### Human-in-the-Loop Workflow
1. **User uploads** an invoice (PDF or image, up to 30 MB).
2. **Agents process** — extraction + validation run automatically.
3. **User reviews** — inspects extracted fields, confidence scores, and validation results. Can **inline-edit** any field before submitting.
4. **User submits** for admin approval and optionally provides **prompt feedback** suggesting how the agent prompts could be improved.
5. **Admin approves or deletes** the invoice as a final decision.

### Prompt Management
- System prompts are versioned — every edit creates a new version.
- Admins can **edit the active prompt**, **activate any previous version**, and **review user suggestions** from a dedicated Prompts editor page.
- Each processed invoice records which prompt versions were used, with clickable links back to the Prompts editor.

### Confidence Visualization
- Every extracted field carries a confidence score (0–1).
- Color-coded badges (green / amber / red) let users quickly spot low-confidence fields that need attention.
- User-edited fields are highlighted with a blue "edited" badge and set to 1.0 confidence.

### Roles & Permissions
| Capability | User | Admin |
|---|:---:|:---:|
| Upload & process invoices | Yes | Yes |
| Edit extracted fields | Own invoices | All |
| Submit for approval | Own invoices | All |
| Final approve / delete | — | Yes |
| Submit prompt feedback | Yes | Yes |
| Edit agent prompts | — | Yes |
| View prompt versions & history | — | Yes |

### Security
- Ownership checks on all invoice endpoints (users can only access their own invoices).
- Admin-only guards on approval, prompt management, and prompt viewing APIs.
- Path traversal protection on file storage and document serving.
- Input validation with `Literal` types and `max_length` constraints.
- Internal error details suppressed from API responses.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Database | SQLite (with migration support) |
| Agent framework | LangGraph (planned Phase 2 orchestration) |
| LLM providers | Anthropic Claude (direct or Vertex AI), Ollama (local) |
| Document processing | PyMuPDF (PDF to images), Pillow |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4 |
| Icons | Lucide React |

## Project Structure

```
├── backend/
│   ├── agents/              # Extraction & validation agent logic
│   │   ├── extraction.py
│   │   ├── validation.py
│   │   └── orchestrator.py  # Coordinates the agent pipeline
│   ├── models/
│   │   ├── database.py      # SQLite schema, migrations, connection
│   │   └── schemas.py       # Pydantic request/response models
│   ├── routers/
│   │   ├── auth.py          # User identity (header-based for demo)
│   │   ├── invoices.py      # Upload, process, edit, approve, delete
│   │   ├── feedback.py      # Prompt feedback CRUD
│   │   ├── prompts.py       # Prompt version management (admin)
│   │   └── approvals.py     # Data correction approvals
│   ├── services/
│   │   ├── llm/             # Swappable LLM providers
│   │   │   ├── base.py      # Abstract VisionLLM interface
│   │   │   ├── claude_provider.py
│   │   │   ├── ollama_provider.py
│   │   │   └── factory.py   # get_llm() factory
│   │   ├── pdf_converter.py # PDF/image → base64 for vision LLMs
│   │   ├── prompt_manager.py# Prompt versioning & storage
│   │   └── business_rules.py
│   ├── storage/
│   │   ├── base.py          # Abstract DocumentStore interface
│   │   └── local.py         # Local filesystem (S3-ready abstraction)
│   ├── prompts/             # Default prompt markdown files
│   │   ├── extraction_system.md
│   │   └── validation_system.md
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Invoices, Detail, Feedback, Prompts
│       ├── components/      # Layout, StatusBadge, ConfidenceBadge, UserSwitcher
│       ├── services/api.ts  # Backend API client
│       ├── types/index.ts   # TypeScript interfaces
│       └── hooks/           # useCurrentUser
├── sample-invoices/         # 10 test PDFs (clean, scanned, low-res, noisy)
├── generate_sample_invoices.py
├── Makefile
├── .env.example
└── project-requirements.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- One of:
  - [Ollama](https://ollama.ai) with a vision model (default: `llama3.2-vision`)
  - Anthropic Claude API key
  - Google Cloud project with Claude on Vertex AI

### 1. Clone and configure

```bash
git clone <repo-url>
cd agent-human-in-loop-demo
cp .env.example .env
# Edit .env to configure your LLM provider (see below)
```

### 2. Install dependencies

```bash
make setup
```

Or manually:

```bash
pip install -r backend/requirements.txt
cd frontend && npm install
```

### 3. Start the servers

In two separate terminals:

```bash
make backend    # FastAPI on http://localhost:8000
make frontend   # Vite dev server on http://localhost:5173
```

Then open **http://localhost:5173** in your browser.

### 4. Generate sample invoices (optional)

```bash
make generate-invoices
```

Creates 10 diverse test PDFs in `sample-invoices/`.

## LLM Configuration

Configure via `.env` (copy from `.env.example`):

### Ollama (local, default)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2-vision
```

Make sure the model is pulled: `ollama pull llama3.2-vision`

### Claude (direct Anthropic API)

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-api-key
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### Claude on Vertex AI (enterprise)

```env
LLM_PROVIDER=claude-vertex
VERTEX_PROJECT_ID=your-gcp-project-id
VERTEX_REGION=us-east5
CLAUDE_MODEL=claude-sonnet-4@20250514
```

Requires Google Application Default Credentials:

```bash
gcloud auth application-default login
```

## Demo Users

The app uses hardcoded users selectable from a dropdown (no login required):

| User | Role | ID |
|---|---|---|
| Jane (Admin) | admin | `admin-jane` |
| Bob (Admin) | admin | `admin-bob` |
| John | user | `user-john` |
| Sarah | user | `user-sarah` |

Switch users using the dropdown in the top-right corner of the UI.

## Makefile Targets

| Command | Description |
|---|---|
| `make setup` | Install all dependencies |
| `make backend` | Start FastAPI server (port 8000) |
| `make frontend` | Start Vite dev server (port 5173) |
| `make reset-db` | Delete and recreate the SQLite database |
| `make generate-invoices` | Generate sample test invoice PDFs |
| `make clean` | Remove build artifacts and caches |
| `make lint` | Run frontend linters |
| `make help` | Show all available targets |

## API Overview

All endpoints are under `/api`. Authentication is via the `X-User-Id` header.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/auth/users` | List available users |
| `POST` | `/api/invoices` | Upload an invoice |
| `GET` | `/api/invoices` | List all invoices |
| `GET` | `/api/invoices/:id` | Get invoice details |
| `POST` | `/api/invoices/:id/process` | Run extraction + validation |
| `PATCH` | `/api/invoices/:id/fields` | Edit extracted fields |
| `POST` | `/api/invoices/:id/action` | Submit / approve / reject |
| `DELETE` | `/api/invoices/:id` | Delete an invoice |
| `GET` | `/api/invoices/:id/document` | Download original document |
| `GET` | `/api/feedback` | List feedback |
| `POST` | `/api/feedback` | Submit prompt feedback |
| `POST` | `/api/feedback/:id/review` | Review feedback (admin) |
| `GET` | `/api/prompts` | List prompts (admin) |
| `GET` | `/api/prompts/:key` | Get prompt + version history (admin) |
| `POST` | `/api/prompts/:key` | Create new prompt version (admin) |
| `POST` | `/api/prompts/:key/activate` | Activate a prompt version (admin) |

## Design Decisions

- **Flexible schema**: Extraction results are stored as JSON blobs — no fixed column per field. This lets the extraction agent discover whatever fields exist on each invoice.
- **Document storage abstraction**: `DocumentStore` interface with a `LocalDocumentStore` implementation. Ready to swap in S3 without changing application code.
- **LLM provider abstraction**: `VisionLLM` interface with Claude and Ollama implementations behind a `get_llm()` factory, switchable via environment variable.
- **Prompt versioning**: Every prompt edit creates a new version. Each processed invoice records the prompt versions used, providing full traceability.
- **SQLite for demo**: Lightweight, zero-config. Schema designed to migrate to PostgreSQL when needed.

## License

This is a demo/reference application for educational purposes.
