# Coding Conventions

**Analysis Date:** 2026-05-12

> **Note:** This project is in early initialization. Only `main.py` exists as a stub.
> Conventions below are derived from `docs/plan.md`, `docs/architecture.md`, and the
> declared dependency stack in `pyproject.toml`. They represent the intended patterns
> the project has committed to — not yet fully implemented code.

## Language & Runtime

- **Python 3.12** (pinned via `.python-version` / `uv python pin`)
- **Package manager:** `uv` — use `uv add`, `uv sync`, `uv run` exclusively
- **No `pip` commands** in this project; all tooling runs through `uv run`

## Naming Patterns

**Modules and files:**
- `snake_case` for all Python files: `base_provider.py`, `dynamic_router.py`, `provider_loader.py`
- Module prefix `apifuse_` for shared/utility identifiers where disambiguation is needed (per `docs/plan.md` quality goals)
- Debug-only modules grouped under `providers/debug/` subpackage

**Classes:**
- `PascalCase`: `BaseProvider`, `ProviderRegistry`, `CustomClient`, `DynamicRouterGenerator`, `APIResponse`, `ErrorResponse`

**Functions and variables:**
- `snake_case`: `execute_operation()`, `initialize_providers()`, `register_dynamic_routes()`, `_prepare_request()`
- Private/internal methods prefixed with `_`: `_prepare_request()`

**Configuration keys:**
- YAML config keys use `snake_case` (e.g., `env_mapping`, `x-aggregates`)
- Environment variables use `UPPER_SNAKE_CASE`

**URL paths:**
- Versioned under `/api/v1/`
- Resource segments use `snake_case` or kebab-case: `/api/v1/health/detailed`

## Code Style

**Formatting:**
- No formatter config detected in `pyproject.toml` — not yet configured
- Intended style: standard Python (PEP 8)
- Recommendation when adding formatter: `ruff format` (compatible with `uv` toolchain)

**Linting:**
- No linter config detected — not yet configured
- Recommendation: `ruff check` in `pyproject.toml` `[tool.ruff]` section

**Type hints:**
- Pydantic models used for all request/response shapes (`pydantic-settings`, Pydantic v2)
- Type annotations expected on all public function signatures (inferred from FastAPI + Pydantic usage)

## Import Organization

**Expected order (PEP 8 / isort convention):**
1. Standard library (`asyncio`, `os`, `typing`, etc.)
2. Third-party packages (`fastapi`, `httpx`, `pydantic`, `structlog`, `yaml`)
3. Local application imports (`app.core`, `app.providers`, `app.models`)

**No path aliases detected** — standard Python module imports only.

## Error Handling

**Pattern:**
- Dedicated `exceptions.py` module in `app/core/` (planned: `docs/plan.md` Phase 1)
- Response models: `APIResponse` for success, `ErrorResponse` for failures
- Middleware-level error handling: `ErrorHandlingMiddleware` (planned in architecture)
- HTTP errors from upstream providers propagated via `APIResponse(status_code, data, ...)`
- No bare `except:` clauses — use specific exception types

**FastAPI error responses:**
- Use `HTTPException` for client errors (4xx)
- `ErrorHandlingMiddleware` catches unhandled exceptions for 5xx responses

## Logging

**Framework:** `structlog` 25.5.0

**Rules (from `docs/plan.md` quality goals):**
- **Zero `print()` calls** — structured logger exclusively
- All log calls go through the `structlog` logger configured in `app/core/logging.py`
- Structured fields (key=value pairs) preferred over f-string interpolation in log messages

**Pattern (intended):**
```python
import structlog
log = structlog.get_logger()

log.info("provider_registered", provider_id="docker", provider_type="openapi")
log.error("request_failed", status_code=502, provider_id="docker")
```

## Comments

**When to comment:**
- Public classes and functions that form the provider/router API surface get docstrings
- Internal implementation details use inline comments sparingly
- No JSDoc-style decorators — plain Python docstrings

**Docstring style:**
- One-line docstring for simple functions
- Multi-line Google-style or plain description for complex classes

## Function Design

**Async-first:**
- All I/O-bound functions (HTTP calls, provider execution) must be `async def`
- `httpx.AsyncClient` used exclusively — no synchronous `requests` calls
- FastAPI route handlers are `async def`

**Parameters:**
- Pydantic models or `dataclass` for structured inputs, not raw dicts
- FastAPI dependency injection (`Depends()`) for shared resources (registry, config)

**Return values:**
- Route handlers return Pydantic model instances or `APIResponse`
- Provider methods return `APIResponse(status_code, data, ...)`

## Module Design

**Package structure (target from `docs/plan.md`):**
```
app/
├── api/          # Route handlers: health.py, openapi.py, debug.py
├── core/         # client.py, config.py, dynamic_router.py, exceptions.py, logging.py
├── models/       # Pydantic request/response models
└── providers/    # openapi_provider.py, composite_provider.py, provider_loader.py, debug/
config/
├── providers/    # YAML provider definitions (*.yaml)
└── openapi/      # Resolved OpenAPI specs (*.yaml)
tests/            # pytest test suites
scripts/          # Dev/prod utility scripts
```

**Exports:**
- Each subpackage exposes its public API via `__init__.py`
- No barrel re-exports of private internals

**Separation of concerns:**
- `app/core/client.py`: `BaseProvider`, `ProviderRegistry`, `CustomClient`
- `app/core/config.py`: `Settings` via `pydantic-settings`
- `app/core/dynamic_router.py`: `DynamicRouterGenerator`
- `app/providers/`: Provider implementations, loaded from YAML config

## Configuration

**Settings class:**
- `pydantic-settings` with `BaseSettings` in `app/core/config.py`
- Environment variables loaded from `.env` via `python-dotenv`
- Provider-specific env vars mapped via `env_mapping` in YAML configs

**YAML config files:**
- Provider definitions: `config/providers/*.yaml`
- Resolved OpenAPI specs: `config/openapi/*-resolved.yaml`
- YAML parsed with `pyyaml`

## Provider Pattern

**Three provider types (from architecture):**
- `openapi`: YAML-spec-driven, builds `operations{}` dict, calls `execute_operation()`
- `composite`: Orchestrates multiple providers via `x-aggregates` field in YAML spec
- `custom`: Manually written Python class (e.g., debug providers)

**Lifecycle:**
1. `ProviderLoader` scans `config/providers/*.yaml` at startup (`lifespan`)
2. Creates provider instances, registers in `ProviderRegistry`
3. `DynamicRouterGenerator` reads OpenAPI YAML → creates FastAPI routes
4. Requests: middleware → route handler → registry → `BaseProvider` → httpx → `APIResponse`

---

*Convention analysis: 2026-05-12*
