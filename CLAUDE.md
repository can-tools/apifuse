# ApiFuse — Project Guide

## Project

**ApiFuse** — FastAPI-based API gateway with dynamic OpenAPI-driven routing and multi-provider aggregation.

- Project: `.planning/PROJECT.md`
- Roadmap: `.planning/ROADMAP.md`
- Requirements: `.planning/REQUIREMENTS.md`
- State: `.planning/STATE.md`

## GSD Workflow

This project uses Get Shit Done (GSD) for structured phase-based execution.

**Current phase:** See `.planning/STATE.md`

**Workflow commands:**
- `/gsd-progress` — check current status and next step
- `/gsd-discuss-phase <N>` — gather context before planning
- `/gsd-plan-phase <N>` — create execution plan for a phase
- `/gsd-execute-phase <N>` — execute the plan
- `/gsd-verify-work <N>` — verify phase deliverables

## Code Quality Rules

These are enforced from Phase 1 and must not be violated:

- **Zero `print()` calls** — use `structlog` exclusively
- **`apifuse_` prefix** — uniform naming on all internal identifiers
- **No dead code** — no unused imports, variables, or commented-out blocks
- **Single `conftest.py`** — shared fixtures only, no duplication
- **uv** — package manager; never use pip or poetry directly

## Stack

- Python 3.12 + FastAPI + Pydantic v2 + httpx + structlog
- uv (package manager), uvicorn (ASGI server)
- pytest + pytest-asyncio + httpx.MockTransport (tests)

## Architecture

Provider system: `ProviderLoader` → `ProviderRegistry` → `BaseProvider` subclasses → `CustomClient` (httpx)

Dynamic routing: OpenAPI YAML → `DynamicRouterGenerator` → FastAPI routes at startup

See `docs/architecture.md` for full diagram.
