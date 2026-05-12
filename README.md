# ApiFuse

A **FastAPI**-based API gateway with **dynamic route generation** from **OpenAPI (YAML)** specs and **multi-provider aggregation** through configuration—add integrations without hand-writing a new route module for each service.

## What this project is

One HTTP surface connects external OpenAPI-compatible services. A new provider is primarily a YAML file under config; ApiFuse exposes it as FastAPI endpoints.

## Repository status (today)

The project is **under active construction**. Dependencies are already declared in `pyproject.toml` (FastAPI, Pydantic Settings, structlog, httpx, PyYAML, uvicorn, etc.). **Phase 1 (Foundation)** is planned in GSD (**five plans**: test harness, `app/core`, logging, middleware, `main.py` rewrite). The **final application layout is not fully implemented yet**—current `main.py` is a short stub to be replaced per the phase plans.

Details: **`.planning/STATE.md`**, roadmap: **`.planning/ROADMAP.md`**, requirements: **`.planning/REQUIREMENTS.md`**.

## Roadmap at a glance (6 phases)

1. **Foundation** — app skeleton, structlog, CORS, error handling, settings.
2. **Provider System** — registry, loader, HTTP client, env mapping.
3. **Dynamic Router** — generate FastAPI routes from OpenAPI at startup.
4. **Production Providers** — e.g. OpenAPIProvider and CompositeProvider.
5. **System & Debug** — health, info, developer endpoints.
6. **Developer Tooling** — OpenAPI scripts, Makefile.

## Planning workflow (GSD)

This repo uses **Get Shit Done**—phase-based work with artifacts in **`.planning/`**. When your AI/IDE has GSD skills wired up, typical commands include progress, discuss-phase, plan-phase, execute-phase, and verify-work.

Conventions: **`CLAUDE.md`**. Product context: **`.planning/PROJECT.md`**.

## Code quality (from Phase 1 onward)

- **No `print()`** — use **structlog** only.
- **`apifuse_` prefix** on internal identifiers (project convention).
- **No dead code** (no unused imports/variables, no commented-out blocks).
- **Single shared `tests/conftest.py`** — no duplicated fixtures.
- **Package manager: `uv` only** — do not use `pip` or `poetry` directly on this project.

## Target architecture

Provider pipeline: **ProviderLoader** → **ProviderRegistry** → **BaseProvider** subclasses → **CustomClient** (httpx).

Routing: **OpenAPI YAML** → **DynamicRouterGenerator** → FastAPI routes at startup.

Diagram: **`docs/architecture.md`**. Legacy planning notes: **`docs/plan.md`**.

## Requirements

- **Python 3.12+**
- **uv** (toolchain and package manager)

## Setup

### 1. Install uv

**Linux / macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Initialize the project

For a **new** empty directory (greenfield). If you **cloned this repo**, `pyproject.toml` and `uv.lock` already exist—skip to **§4 Sync** (or run only `uv sync` after step 1).

```bash
uv init --no-readme
uv python pin 3.12
```

### 3. Add dependencies

Production:

```bash
uv add fastapi uvicorn httpx pydantic-settings pyyaml structlog python-dotenv
```

Development:

```bash
uv add --dev pytest pytest-asyncio httpx pytest-playwright
```

### 4. Sync the environment

```bash
uv sync
```

### 5. Run the dev server

```bash
uv run uvicorn main:app --reload
```

Until **Phase 1** is executed in code, `main:app` may still behave as a **temporary stub**; the target app is defined in **`.planning/phases/01-foundation/`**.

### 6. Tests (after Phase 1 Wave 0+ lands in the tree)

```bash
uv run pytest tests/ -q
```

The `tests/` tree and pytest config are introduced by the Phase 1 plan set.

## Contributor shortcut

**Clone of this repository:** install `uv`, then **`uv sync`** from the repo root. You do not need to re-run `uv init` or the `uv add` lines unless you are reproducing the stack from scratch or intentionally resetting the project metadata.
