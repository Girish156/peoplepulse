# PeoplePulse Makefile
SHELL := /bin/bash
.PHONY: help setup up down migrate seed generate-data validate evaluate test lint format clean

PYTHON := python
PIP := pip
PNPM := pnpm

help: ## Show this help message
	@echo "PeoplePulse - Evidence-Based Performance Review Platform"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Environment ───────────────────────────────────────────────
setup: ## Install all dependencies (backend + frontend)
	@echo "Setting up backend..."
	cd backend && $(PIP) install -e ".[dev]" || $(PIP) install -r requirements.txt
	@echo "Setting up frontend..."
	cd frontend && $(PNPM) install
	@echo "Setup complete! Copy .env.example to .env and configure."

# ── Docker ────────────────────────────────────────────────────
up: ## Start all services with Docker Compose
	docker compose up -d
	@echo "Services started:"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://localhost:8000/docs"

down: ## Stop all Docker services
	docker compose down

up-db: ## Start only the PostgreSQL database
	docker compose up -d db
	@echo "PostgreSQL started on port 5432"

# ── Database ──────────────────────────────────────────────────
migrate: ## Run Alembic database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

seed: ## Seed reference data (competencies, review cycles)
	$(PYTHON) database/seed_reference_data.py

# ── Data Generation ───────────────────────────────────────────
generate-small: ## Generate small dataset (100 employees, 300 goals)
	$(PYTHON) scripts/generate_data.py --seed 20261022 --mode small

generate-full: ## Generate full dataset (3000 employees, 10000 goals) — may take minutes
	$(PYTHON) scripts/generate_data.py --seed 20261022 --mode full

generate-data: generate-small ## Alias for generate-small

validate: ## Validate generated data
	$(PYTHON) scripts/validate_data.py
	@echo "Validation report: data/reports/validation_report.md"

evaluate: ## Evaluate anomaly detection against ground truth
	$(PYTHON) scripts/evaluate_anomalies.py
	@echo "Evaluation report: data/reports/evaluation_report.md"

compare: ## Compare two deterministic runs for reproducibility
	$(PYTHON) scripts/compare_runs.py --seed 20261022 --mode small

# ── Testing ───────────────────────────────────────────────────
test: ## Run all backend tests
	cd backend && $(PYTHON) -m pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	cd backend && $(PYTHON) -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	cd backend && $(PYTHON) -m pytest tests/integration/ -v

test-cov: ## Run tests with coverage report
	cd backend && $(PYTHON) -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# ── Frontend ──────────────────────────────────────────────────
frontend-dev: ## Start frontend development server
	cd frontend && $(PNPM) dev

frontend-build: ## Build frontend for production
	cd frontend && $(PNPM) build

frontend-start: ## Start production frontend
	cd frontend && $(PNPM) start

lint: ## Run frontend linting
	cd frontend && $(PNPM) lint

typecheck: ## Run TypeScript type checking
	cd frontend && $(PNPM) tsc --noEmit

format: ## Format code (frontend)
	cd frontend && $(PNPM) prettier --write "src/**/*.{ts,tsx}"

# ── Backend Dev ───────────────────────────────────────────────
backend-dev: ## Start backend development server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-lint: ## Lint backend Python code
	cd backend && $(PYTHON) -m ruff check app/ || echo "Install ruff: pip install ruff"

# ── Full Workflow ─────────────────────────────────────────────
workflow-check: validate evaluate test ## Run full data + test workflow

# ── Cleanup ───────────────────────────────────────────────────
clean: ## Clean generated data files (preserve ground truth)
	find data/generated -type f -name "*.csv" -delete 2>/dev/null || true
	find data/generated -type f -name "*.json" -delete 2>/dev/null || true
	find data/reports -type f -name "*.json" -delete 2>/dev/null || true
	find data/reports -type f -name "*.md" -delete 2>/dev/null || true
	@echo "Cleaned generated files"

clean-all: down clean ## Stop services and clean all generated files

# ── Info ──────────────────────────────────────────────────────
status: ## Show service status
	docker compose ps

logs: ## Show all service logs
	docker compose logs -f

logs-backend: ## Show backend logs
	docker compose logs -f backend

logs-db: ## Show database logs
	docker compose logs -f db

