.PHONY: help setup setup-backend setup-frontend backend frontend dev clean reset-db lint

PYTHON := python
PIP := pip
NPM := npm

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ──────────────────────────────────────────────────────

setup: setup-backend setup-frontend ## Install all dependencies

setup-backend: ## Install backend Python dependencies
	$(PIP) install -r backend/requirements.txt

setup-frontend: ## Install frontend Node dependencies
	cd frontend && $(NPM) install

# ─── Run ────────────────────────────────────────────────────────

backend: ## Start the FastAPI backend server (port 8000)
	$(PYTHON) -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start the Vite frontend dev server (port 5173)
	cd frontend && $(NPM) run dev

dev: ## Start both backend and frontend (requires two terminals)
	@echo "Run these in separate terminals:"
	@echo "  make backend"
	@echo "  make frontend"

# ─── Database ───────────────────────────────────────────────────

reset-db: ## Delete and recreate the SQLite database
	rm -f data/invoices.db
	$(PYTHON) -c "from backend.models.database import init_db; init_db()"
	@echo "Database reset complete."

# ─── Utilities ──────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	rm -rf frontend/dist frontend/node_modules/.vite
	rm -rf __pycache__ backend/__pycache__ backend/**/__pycache__
	rm -rf uploads/*
	@echo "Clean complete."

generate-invoices: ## Generate sample test invoices
	$(PYTHON) generate_sample_invoices.py

lint: ## Run linters
	cd frontend && $(NPM) run lint
