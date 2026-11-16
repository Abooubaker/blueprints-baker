# RoboCraft developer commands. Run `make` or `make help` for the list.
SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

API_DIR := apps/api
WEB_DIR := apps/web
COMPOSE := docker compose

.PHONY: help install install-api install-web db-up db-down db-reset migrate revision \
	dev-api dev-web test test-api test-web lint format typecheck build contracts check \
	api-check web-check clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "; printf "\nRoboCraft commands:\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2} END {printf "\n"}' $(MAKEFILE_LIST)

install: install-api install-web ## Install backend and frontend dependencies

install-api: ## Sync Python dependencies with uv
	cd $(API_DIR) && uv sync

install-web: ## Install Node dependencies from the lockfile
	cd $(WEB_DIR) && npm ci

db-up: ## Start local PostgreSQL
	$(COMPOSE) up -d db

db-down: ## Stop local PostgreSQL
	$(COMPOSE) down

db-reset: ## Delete the local database volume and recreate it (destructive)
	$(COMPOSE) down -v
	$(COMPOSE) up -d db

migrate: ## Apply all Alembic migrations
	cd $(API_DIR) && uv run alembic upgrade head

revision: ## Autogenerate a migration: make revision m="add table"
	@test -n "$(m)" || (echo 'Usage: make revision m="describe change"' && exit 1)
	cd $(API_DIR) && uv run alembic revision --autogenerate -m "$(m)"

dev-api: ## Run the API with reload on :8000
	cd $(API_DIR) && uv run uvicorn app.main:app --reload --port 8000

dev-web: ## Run the Next.js dev server on :3000
	cd $(WEB_DIR) && npm run dev

test: test-api test-web ## Run backend and frontend tests

test-api: ## Run backend tests (SQLite, no PostgreSQL required)
	cd $(API_DIR) && uv run pytest

test-web: ## Run frontend checks that act as the test suite
	cd $(WEB_DIR) && npm run typecheck

lint: ## Lint backend and frontend
	cd $(API_DIR) && uv run ruff check .
	cd $(WEB_DIR) && npm run lint

format: ## Format backend and frontend
	cd $(API_DIR) && uv run ruff format .
	cd $(WEB_DIR) && npm run format

typecheck: ## Run mypy and TypeScript checks
	cd $(API_DIR) && uv run mypy app
	cd $(WEB_DIR) && npm run typecheck

build: ## Build the production frontend bundle
	cd $(WEB_DIR) && npm run build

contracts: ## Regenerate OpenAPI, agent schemas, and frontend API types
	cd $(API_DIR) && uv run python ../../scripts/export_contracts.py
	cd $(WEB_DIR) && npm run codegen

api-check: ## Full backend quality gate
	cd $(API_DIR) && uv run ruff check .
	cd $(API_DIR) && uv run ruff format --check .
	cd $(API_DIR) && uv run mypy app
	cd $(API_DIR) && uv run pytest

web-check: ## Full frontend quality gate
	cd $(WEB_DIR) && npm run lint
	cd $(WEB_DIR) && npm run typecheck
	cd $(WEB_DIR) && npm run format:check
	cd $(WEB_DIR) && npm run build

check: api-check web-check ## Run every quality gate

clean: ## Remove local build caches and artifacts
	rm -rf $(WEB_DIR)/.next $(WEB_DIR)/out $(WEB_DIR)/coverage $(WEB_DIR)/*.tsbuildinfo
	find $(API_DIR) -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf $(API_DIR)/.pytest_cache $(API_DIR)/.mypy_cache $(API_DIR)/.ruff_cache $(API_DIR)/htmlcov
