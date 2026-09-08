# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

TaskFlow API: a FastAPI service (Python 3.12, managed with `uv`) built incrementally across a course.
The current code only exposes `GET /health`; the rest of the surface (states, projects, tasks v1/v2)
is specified in `docs/contrato-api.md` and lands in later sessions. The ASGI app is `app.main:app`.

## Commands

All commands run from the repository root.

```bash
uv sync --locked                          # install exact deps from uv.lock
uv run pytest -q                          # run the test suite
uv run pytest tests/test_health.py -q     # run a single test file
uv run pytest -q -k health                # run tests matching an expression
uv run ruff check .                       # lint
docker compose up -d                      # start PostgreSQL (service `db`)
uv run uvicorn app.main:app --reload      # serve the API locally on :8000
docker compose down                       # stop PostgreSQL
```

`compose.yaml` ships safe local defaults, so `docker compose` works without a `.env`.
Tests use `asyncio_mode = "auto"` and reach the app in-process via `httpx.ASGITransport` — no running server needed.

## Sources of truth (see `docs/decisiones-ingenieria.md`)

- **`docs/contrato-api.md`** defines observable behavior: status codes, response schemas, list ordering,
  text normalization, error shape (`{"detail": "..."}`). Only change it when a ticket explicitly says the
  contract changes — and do that in a separate commit *before* touching tests or code.
- **`README.md`** holds the canonical repo commands.
- Response schemas are exact: return the declared fields, no more, no less. Absent optional fields serialize
  as `null` (not omitted). `due_at` always serializes as UTC with `Z`, no microseconds.

## Working agreements that are not visible in the code

- **Persistence tests run against PostgreSQL, not SQLite.** SQLite does not reproduce the same constraints,
  types, or migrations.
- **Schema changes go through Alembic migrations** with both `upgrade` and `downgrade`, tested in both
  directions. The schema is never created as an import-time side effect.
- **A new capability starts with a test that fails for its absence.** Never weaken or delete an existing test
  to get green; if agreed behavior changed, change the contract first, then the test, in a separate commit.
- The states catalog (`PENDIENTE`, `EN_CURSO`, `BLOQUEADA`, `HECHA`) is seeded by an idempotent migration.

## `.env` handling

`.env` may contain secrets. Do not open, display, edit, or `git add` it. `.env.example` is the only permitted
source for variable names; real values are configured outside the conversation.

## Note on `evidencias/propuesta-atajo.md`

That file is a proposal of shortcuts (use SQLite in tests, adjust existing tests, read `.env`, stop when
`pytest` passes) that deliberately conflicts with the agreements above. Do not adopt it.
