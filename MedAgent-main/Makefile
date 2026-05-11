.PHONY: dev up down build reset
.PHONY: seed-kb test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend migrate

# ── Docker lifecycle ────────────────────────────────────

dev:
	docker compose up

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

reset:
	docker compose down -v
	docker compose up -d

# ── Knowledge base ──────────────────────────────────────

seed-kb:
	docker compose exec backend /app/.venv/bin/python -u /app/scripts/seed_kb.py

verify-kb:
	docker compose exec backend /app/.venv/bin/python -u /app/scripts/seed_kb.py --verify

# ── Testing ─────────────────────────────────────────────

test: test-backend test-frontend

test-backend:
	cd backend && uv run python -m pytest tests/ -v --tb=short --timeout=30

test-frontend:
	cd frontend && (pnpm test --run || corepack pnpm test --run)

# ── Linting ─────────────────────────────────────────────

lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check .

typecheck-backend:
	cd backend && uv run mypy app --ignore-missing-imports || echo "Type check completed with issues (see above)"

lint-frontend:
	cd frontend && (pnpm lint || corepack pnpm lint)

# ── Formatting ──────────────────────────────────────────

format: format-backend format-frontend

format-backend:
	cd backend && uv run ruff format .
	cd backend && uv run ruff check . --fix

format-frontend:
	cd frontend && (pnpm format || corepack pnpm format)

# ── Database ────────────────────────────────────────────

migrate:
	cd backend && uv run alembic upgrade head

migrate-down:
	cd backend && uv run alembic downgrade -1

# ── Audit / Safety ──────────────────────────────────────

audit-verify:
	cd backend && uv run python ../scripts/audit_verify.py