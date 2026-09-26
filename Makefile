.DEFAULT_GOAL := help
SHELL := /bin/bash
BACKEND := backend
VENV := $(BACKEND)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --------------------------------------------------------------- bootstrap
.PHONY: env
env: ## Create .env from the template if missing
	@test -f .env || (cp .env.example .env && echo "Created .env — fill in POSTGRES_PASSWORD and LOCAL_API_TOKEN")

.PHONY: install
install: ## Create the backend virtualenv and install dev dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	cd $(BACKEND) && .venv/bin/pip install -e ".[dev]"

.PHONY: token
token: ## Generate a random LOCAL_API_TOKEN
	@python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# ------------------------------------------------------------------ docker
.PHONY: up
up: env ## Start the full stack (postgres, redis, ollama, backend)
	docker compose up -d --build
	@echo "API:    http://localhost:$${API_PORT:-8787}/docs"
	@echo "Health: http://localhost:$${API_PORT:-8787}/api/v1/health/deep"

.PHONY: down
down: ## Stop the stack
	docker compose down

.PHONY: reset
reset: ## Stop the stack and DELETE all data volumes
	docker compose down -v

.PHONY: logs
logs: ## Tail backend logs
	docker compose logs -f backend

.PHONY: infra
infra: env ## Start only postgres + redis (for local, non-container development)
	docker compose up -d postgres redis

.PHONY: pull-model
pull-model: ## Pull the configured Ollama model
	docker compose exec ollama ollama pull $${AI_MODEL:-qwen2.5:7b-instruct}

# --------------------------------------------------------------- database
.PHONY: migrate
migrate: ## Apply all migrations
	cd $(BACKEND) && .venv/bin/alembic upgrade head

.PHONY: downgrade
downgrade: ## Roll back one migration
	cd $(BACKEND) && .venv/bin/alembic downgrade -1

.PHONY: revision
revision: ## Autogenerate a migration (make revision m="add x")
	cd $(BACKEND) && .venv/bin/alembic revision --autogenerate -m "$(m)"

.PHONY: seed
seed: ## Seed exchanges, data sources, scoring profiles and the asset universe
	$(PY) scripts/seed_reference_data.py

# ------------------------------------------------------------------- run
.PHONY: dev
dev: ## Run the API locally with reload
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8787

# ---------------------------------------------------------------- quality
.PHONY: lint
lint: ## Ruff + Black check
	cd $(BACKEND) && .venv/bin/ruff check app ../scripts ../tests
	cd $(BACKEND) && .venv/bin/ruff format --check app ../scripts ../tests

.PHONY: format
format: ## Auto-format
	cd $(BACKEND) && .venv/bin/ruff check --fix app ../scripts ../tests
	cd $(BACKEND) && .venv/bin/ruff format app ../scripts ../tests

.PHONY: typecheck
typecheck: ## mypy --strict
	cd $(BACKEND) && .venv/bin/mypy app

.PHONY: arch
arch: ## Enforce the architecture invariants (I1..I12)
	$(PY) scripts/check_architecture.py

.PHONY: test
test: ## Run unit tests (no database required)
	cd $(BACKEND) && .venv/bin/pytest ../tests -m "not integration and not network" -q

.PHONY: test-all
test-all: ## Run every test, including integration (needs postgres)
	cd $(BACKEND) && .venv/bin/pytest ../tests -q

.PHONY: check
check: lint typecheck arch test ## Everything CI runs
