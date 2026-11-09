# Run from the repo root. Needs uv (Python 3.12) and Node 22 (see frontend/.nvmrc).

.PHONY: install dev backend frontend widget widget-watch widget-host kb test lint check

install:
	cd backend && uv sync
	cd widget && npm ci
	cd frontend && npm ci

# Backend on 8010, the widget rebuilding on save, and the sample site on 3010.
dev:
	@echo "Backend on http://localhost:8010, sample site on http://localhost:3010"
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && uv run uvicorn app.main:app --reload --port 8010) & \
	(cd widget && npm run watch) & \
	(cd frontend && npm run dev) & \
	wait

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8010

frontend:
	cd frontend && npm run dev

# Build widget.js (with the size check) and copy it into frontend/public/embed/.
widget:
	cd widget && npm run build

widget-watch:
	cd widget && npm run watch

# The hostile-CSS isolation page, at http://localhost:8099/test/host.html (needs the backend).
widget-host: widget
	cd widget && python3 -m http.server 8099 --bind 127.0.0.1

# Regenerate the help center PDFs and the sample site data (Northwind from sample/northwind-facts.md).
kb:
	cd backend && uv run python sample/generate_kb.py
	cd backend && uv run python -m sample.generate_kingsway_kb

test:
	cd backend && uv run pytest
	cd widget && npm test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd widget && npm run typecheck
	cd frontend && npm run lint

check: lint test widget
	cd frontend && npm run build
