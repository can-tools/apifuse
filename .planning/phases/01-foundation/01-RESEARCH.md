# Phase 1: Foundation - Research

**Researched:** 2026-05-12
**Domain:** FastAPI skeleton — structlog, pydantic-settings, middleware stack
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use **human-readable ConsoleRenderer in dev, JSONRenderer in prod** — switched by `APP_ENV` setting. The two formats are structurally different so the switch must live in `app/core/logging.py` setup, not at call sites.
- **D-02:** Log level: **DEBUG when `APP_ENV=development`, INFO otherwise**. No separate `LOG_LEVEL` env var needed in Phase 1.
- **D-03:** **No required env vars** — application starts without any `.env` file. All settings have sensible defaults. `APP_ENV` defaults to `development`.
- **D-04:** Startup behavior: use pydantic-settings `BaseSettings` with default values. Missing optional vars do not block startup. Hard-fail remains available via pydantic validation if a future phase adds a required field.
- **D-05:** Security restrictions (allowlists, key requirements) are **deferred to a later phase** — Phase 1 is local-first.
- **D-06:** **`allow_origins=["*"]`** (open) by default. No `CORS_ORIGINS` env var needed in Phase 1. CORS restriction is a future concern.
- **D-07:** `ErrorHandlingMiddleware` returns **full exception details (`message` + `type`) in dev mode, minimal in prod**. Dev vs prod is determined by `APP_ENV`.
- **D-08:** Error JSON format: `{"error": "<message>", "status_code": <code>}` (flat, simple). All HTTP errors use this envelope consistently.

### Claude's Discretion

- Specific structlog processor chain (e.g., which processors to include before the renderer) — planner can follow standard structlog FastAPI patterns.
- Whether `app/core/logging.py` exposes a `configure_logging()` function or uses module-level setup — either is fine.
- Lifespan handler structure inside `main.py` — can be inline or delegated to a helper.

### Deferred Ideas (OUT OF SCOPE)

- CORS allowlist / origin restriction — deferred to a later phase (security hardening)
- Authentication / authorization middleware — explicitly out of scope for v1
- Rate limiting — out of scope for v1
- `APIResponse` / `ErrorResponse` base models (MOD-01, MOD-02) — deferred to v2
- pytest suite (TEST-01/02/03) — deferred to v2 per ROADMAP.md
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOUND-01 | Project environment configured with uv, pyproject.toml, pydantic-settings, and .env support | All deps already in pyproject.toml (VERIFIED: uv.lock). pydantic-settings v2 BaseSettings pattern documented. |
| FOUND-02 | Structured logging via structlog — zero `print()` calls enforced, uniform `apifuse_` prefix | Full structlog processor chain + uvicorn bridging pattern documented. `apifuse_` prefix scoped to event names and module-level identifiers. |
| FOUND-03 | FastAPI application with lifespan startup/shutdown, CORSMiddleware, and ErrorHandlingMiddleware | FastAPI lifespan pattern (asynccontextmanager), CORS ordering, exception-safe middleware pattern documented. |
</phase_requirements>

---

## Summary

Phase 1 builds the application skeleton that every subsequent phase depends on: FastAPI app instantiation, structured logging via structlog, environment configuration via pydantic-settings, and a two-middleware stack (CORS + error handling). All dependencies are already declared in `pyproject.toml` and installed — no `uv add` calls are needed for this phase.

The key technical challenge is wiring structlog so that uvicorn's own stdlib-based loggers (uvicorn, uvicorn.error, uvicorn.access) also emit through structlog's processor chain, giving a single consistent log format regardless of log origin. This is accomplished via `structlog.stdlib.ProcessorFormatter` attached to the Python root logger, with uvicorn's native handlers cleared and propagation enabled. The renderer (ConsoleRenderer vs JSONRenderer) is chosen once at startup based on `APP_ENV`.

The `ErrorHandlingMiddleware` must be implemented as a pure ASGI middleware (not `BaseHTTPMiddleware`) to reliably catch all exceptions, including those from other middleware layers, and return the `{"error": ..., "status_code": ...}` envelope defined in D-08.

**Primary recommendation:** Use the `ProcessorFormatter` bridging pattern to unify structlog + uvicorn logs. Use `make_filtering_bound_logger` for performant level filtering. Gate dev vs prod rendering in `configure_logging(app_env: str)`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Settings loading | API / Backend (`app/core/config.py`) | — | pydantic-settings reads env vars/`.env` at import time |
| Logging configuration | API / Backend (`app/core/logging.py`) | — | One-time startup call; structlog is process-global |
| CORS enforcement | API / Backend middleware | — | Starlette CORSMiddleware processes HTTP headers |
| Error formatting | API / Backend middleware | — | ErrorHandlingMiddleware wraps the ASGI call chain |
| App instantiation | Application Layer (`main.py`) | — | FastAPI() + middleware registration + lifespan |
| Lifespan hooks | Application Layer (`main.py`) | — | asynccontextmanager pattern; Phase 2 will add provider init |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.136.1 | HTTP framework, routing, OpenAPI | Already installed; chosen by project |
| structlog | 25.5.0 | Structured logging | Already installed; zero-`print()` rule |
| pydantic-settings | 2.14.1 | Environment-backed BaseSettings | Already installed; pydantic v2-native |
| uvicorn | 0.46.0 | ASGI server | Already installed |
| python-dotenv | 1.2.2 | `.env` file loading (used by pydantic-settings) | Already installed |
| pydantic | 2.13.4 | Data validation (transitive dep of FastAPI + settings) | Already installed |

**Version verification:** All versions confirmed via `uv run python -c "import X; print(X.__version__)"` against the active virtual environment. [VERIFIED: uv.lock]

### Supporting (dev-only)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3 | Test runner | Phase 2+ (TEST-01 deferred) |
| pytest-asyncio | 1.3.0 | Async test support | Phase 2+ |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| structlog ConsoleRenderer | Rich directly | structlog integrates processor chain; Rich alone doesn't |
| ProcessorFormatter bridge | `logging.basicConfig` only | ProcessorFormatter captures uvicorn logs into structlog chain |
| `make_filtering_bound_logger` | `filter_by_level` processor | `make_filtering_bound_logger` filters at class-build time — zero overhead for dropped levels |

**Installation:** No new installs needed. All Phase 1 dependencies are already in `pyproject.toml` and `uv.lock`. [VERIFIED: pyproject.toml]

---

## Architecture Patterns

### System Architecture Diagram

```
HTTP Request
    │
    ▼
uvicorn (ASGI server)  ─── stdlib logging ──► root logger
    │                                              │
    ▼                                              ▼
FastAPI app (main.py)                  ProcessorFormatter (structlog)
    │                                              │
    ├─► CORSMiddleware (outermost — added last)    ├─► ConsoleRenderer (APP_ENV=development)
    │                                              └─► JSONRenderer (APP_ENV=production)
    ├─► ErrorHandlingMiddleware (added first)
    │       │ catches all exceptions
    │       └─► {"error": "...", "status_code": N}
    │
    ▼
Route handlers
    │
    └─► structlog.get_logger() ──► same ProcessorFormatter chain
```

Data flow note: `add_middleware` stacks in reverse — the **last** `add_middleware` call produces the **outermost** (first-to-run) middleware. CORSMiddleware must be outermost; therefore it must be added last.

### Recommended Project Structure

```
app/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py        # ApifuseSettings(BaseSettings)
│   ├── logging.py       # configure_logging(), apifuse_get_logger()
│   └── exceptions.py    # ErrorHandlingMiddleware, ApifuseError base
main.py                  # FastAPI app, lifespan, middleware registration
```

### Pattern 1: pydantic-settings BaseSettings with all defaults

**What:** `BaseSettings` subclass where every field has a default — app starts with zero `.env` file (D-03, D-04).

**When to use:** Phase 1 startup; settings singleton imported by `logging.py` and `main.py`.

```python
# app/core/config.py
# Source: Context7 /pydantic/pydantic-settings [VERIFIED: Context7]
from pydantic_settings import BaseSettings, SettingsConfigDict

class ApifuseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # unknown env vars silently ignored
    )

    app_env: str = "development"
    app_name: str = "apifuse"
    app_version: str = "0.1.0"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

# Module-level singleton — imported elsewhere
apifuse_settings = ApifuseSettings()
```

Key points confirmed by Context7 docs:
- `env_file` is optional — if `.env` is absent, pydantic-settings silently ignores it and uses defaults. [VERIFIED: Context7 /pydantic/pydantic-settings]
- `extra="ignore"` prevents `ValidationError` if the environment contains unrecognized variables. [VERIFIED: Context7 /pydantic/pydantic-settings]
- Field defaults satisfy D-03: `app_env` defaults to `"development"` without any env var.

### Pattern 2: structlog processor chain — dev/prod switching

**What:** `configure_logging()` function called once at startup. Builds separate shared processor lists and switches the renderer based on `APP_ENV`. Uses `ProcessorFormatter` to capture uvicorn's stdlib logs into the same chain.

**When to use:** Called at the top of the FastAPI lifespan before anything else logs.

```python
# app/core/logging.py
# Sources: Context7 /hynek/structlog, gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e
# [VERIFIED: Context7 /hynek/structlog], [CITED: github.com/nymous/f138c7f06062b7c43c060bf03759c29e]
import logging
import sys
import structlog

def drop_color_message_key(_, __, event_dict: dict) -> dict:
    """Remove uvicorn's redundant 'color_message' key before rendering."""
    event_dict.pop("color_message", None)
    return event_dict

def configure_logging(app_env: str = "development") -> None:
    is_dev = app_env == "development"
    log_level = logging.DEBUG if is_dev else logging.INFO

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        drop_color_message_key,
        timestamper,
        structlog.processors.StackInfoRenderer(),
    ]

    if is_dev:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    # structlog side: hand off to ProcessorFormatter
    structlog.configure(
        processors=shared_processors + [
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )

    # stdlib side: ProcessorFormatter routes ALL stdlib logs (including uvicorn) through structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Route uvicorn loggers through root (disable their native handlers)
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_log = logging.getLogger(uvicorn_logger_name)
        uvicorn_log.handlers.clear()
        uvicorn_log.propagate = True  # let root handler format it

    # Suppress uvicorn.access — access logging reimplemented in middleware
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.propagate = False
```

**Key facts about `make_filtering_bound_logger`:** [VERIFIED: Context7 /hynek/structlog]
- Filters below `min_level` at **class-build time** — filtered levels become no-ops with zero runtime overhead.
- Accepts `logging.DEBUG`, `logging.INFO`, etc. (integer constants).
- This is the recommended approach over the `filter_by_level` processor for performance.

**Key facts about `ProcessorFormatter`:** [VERIFIED: Context7 /hynek/structlog]
- `foreign_pre_chain` processes stdlib log records (from uvicorn, httpx, etc.) before the final `processors` list.
- `remove_processors_meta` strips the internal `_record` and `_from_structlog` keys before rendering.
- `wrap_for_formatter` must be the **last** processor on the structlog side — it serializes the event dict into a format `ProcessorFormatter` can read.

### Pattern 3: FastAPI lifespan (asynccontextmanager)

**What:** Single `@asynccontextmanager` function passed to `FastAPI(lifespan=...)`. Startup logic runs before `yield`; shutdown logic runs after. Replaces deprecated `on_startup`/`on_shutdown` events.

**When to use:** This is the only supported pattern in FastAPI ≥ 0.93.0. [VERIFIED: Context7 /fastapi/fastapi]

```python
# main.py
# Source: Context7 /fastapi/fastapi [VERIFIED: Context7]
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import apifuse_settings
from app.core.logging import configure_logging
import structlog

log = structlog.get_logger()

@asynccontextmanager
async def apifuse_lifespan(app: FastAPI):
    configure_logging(apifuse_settings.app_env)
    log.info("apifuse_startup", app_env=apifuse_settings.app_env, version=apifuse_settings.app_version)
    # Phase 2 hook: initialize_providers() goes here
    yield
    log.info("apifuse_shutdown")

app = FastAPI(
    title=apifuse_settings.app_name,
    version=apifuse_settings.app_version,
    lifespan=apifuse_lifespan,
)
```

### Pattern 4: Middleware ordering (CORSMiddleware outermost)

**What:** FastAPI's `add_middleware` stacks in **reverse insertion order** — the last-added middleware becomes the outermost (first to process requests, last to process responses). To make CORSMiddleware the outermost:

```python
# Source: Context7 /fastapi/fastapi [VERIFIED: Context7]
# Add ErrorHandlingMiddleware FIRST (it will be innermost)
app.add_middleware(ErrorHandlingMiddleware)

# Add CORSMiddleware LAST (it will be outermost — runs first on request)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # D-06
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why CORSMiddleware must be outermost:** CORS preflight (`OPTIONS`) requests must receive CORS headers before hitting any auth or error middleware. If ErrorHandlingMiddleware is outermost and raises on a preflight, the browser gets no CORS headers.

### Pattern 5: ErrorHandlingMiddleware — pure ASGI

**What:** Implement as a pure ASGI callable (not `BaseHTTPMiddleware`) for reliable exception catching. `BaseHTTPMiddleware` has known edge cases where exceptions from background tasks or streaming responses escape. For Phase 1's purposes either works, but the pure ASGI pattern is safer.

```python
# app/core/exceptions.py
# Source: FastAPI/Starlette docs pattern [CITED: fastapi.tiangolo.com/tutorial/middleware]
# [ASSUMED: pure ASGI is safer than BaseHTTPMiddleware for all-exception catching]
import json
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse

class ErrorHandlingMiddleware:
    def __init__(self, app: ASGIApp, app_env: str = "development") -> None:
        self.app = app
        self.is_dev = app_env == "development"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            status_code = getattr(exc, "status_code", 500)
            if self.is_dev:
                error_message = str(exc)
            else:
                error_message = "Internal server error" if status_code == 500 else str(exc)
            response = JSONResponse(
                status_code=status_code,
                content={"error": error_message, "status_code": status_code},  # D-08
            )
            await response(scope, receive, send)
```

**Alternative — `@app.exception_handler`:** For `HTTPException` specifically, FastAPI's `exception_handler` decorator is simpler and fully supported. Use the middleware for catching unhandled Python exceptions (500s); use `exception_handler` for formatting `HTTPException` (4xx). Both can coexist. [VERIFIED: Context7 /fastapi/fastapi]

```python
# Exception handler for HTTPException (complements middleware)
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from starlette.responses import JSONResponse

@app.exception_handler(HTTPException)
async def apifuse_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )
```

### Pattern 6: apifuse_ prefix convention

**What it applies to** (from CONVENTIONS.md and CONTEXT.md): [VERIFIED: .planning/codebase/CONVENTIONS.md]
- **Log event names:** `log.info("apifuse_startup", ...)`, `log.info("apifuse_request_received", ...)` — all structlog event strings use the prefix.
- **Module-level identifiers exposed in the apifuse namespace:** `apifuse_settings`, `apifuse_lifespan`, named public functions that form the package API surface.
- **NOT applied to:** class names (PascalCase: `ErrorHandlingMiddleware`, `ApifuseSettings`), private helpers (`_prepare_request`), route path strings, or local variables.
- **In summary:** The prefix is a namespace guard on event strings and singleton/public identifiers — not a universal rule for every Python identifier.

### Anti-Patterns to Avoid

- **`print()` anywhere:** Violates FOUND-02. Replace every debug print with `structlog.get_logger().debug("apifuse_debug_...", ...)`.
- **`on_startup`/`on_shutdown` events:** Deprecated in FastAPI 0.93+. Use `lifespan` parameter. [VERIFIED: Context7 /fastapi/fastapi]
- **`BaseHTTPMiddleware` for top-level error catching:** Known issues with streaming responses and background tasks — use pure ASGI middleware or `exception_handler` decorators.
- **Calling `configure_logging()` at module import time:** Import order is not guaranteed in FastAPI. Call inside lifespan startup, or at the top of `main.py` before `FastAPI()` is instantiated.
- **Leaving uvicorn's `uvicorn.access` logger active:** It emits duplicate access lines alongside any middleware-level access logging. Disable propagation for `uvicorn.access` and reimplement access logging in middleware.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| `.env` loading | Custom file parser | `pydantic-settings` with `env_file=".env"` | Handles type coercion, missing file, precedence |
| Log level filtering | Custom `if level < threshold` guards | `make_filtering_bound_logger(logging.INFO)` | Zero-overhead class-level filtering |
| Uvicorn log bridging | Custom log interceptor | `ProcessorFormatter` + `propagate=True` | ProcessorFormatter is the canonical bridge; custom interceptors break on version updates |
| CORS header injection | Custom middleware | `fastapi.middleware.cors.CORSMiddleware` | Handles OPTIONS preflight, varies, credentials, correct header set |
| Exception serialization | Custom JSON error formatter | `starlette.responses.JSONResponse` | Handles charset, content-type header |

**Key insight:** pydantic-settings + structlog's ProcessorFormatter + FastAPI's CORSMiddleware handle every infrastructure concern in Phase 1. There is nothing to invent.

---

## Common Pitfalls

### Pitfall 1: Middleware insertion order is reversed

**What goes wrong:** Developer adds CORSMiddleware first and ErrorHandlingMiddleware second, expecting CORS to be outermost. Result: CORS runs innermost — preflight requests get no CORS headers if ErrorHandlingMiddleware raises.

**Why it happens:** FastAPI wraps each `add_middleware` call around the previous stack — last-added = outermost.

**How to avoid:** Always add ErrorHandlingMiddleware before CORSMiddleware in code. Comment the order explicitly.

**Warning signs:** Browser preflight `OPTIONS` requests returning 500 or no `Access-Control-Allow-Origin` header.

### Pitfall 2: structlog not configured before first log call

**What goes wrong:** `structlog.get_logger().info("...")` is called at module import time, before `configure_logging()` runs. structlog uses its default (no-processor) configuration and emits unformatted output.

**Why it happens:** Python imports execute module bodies immediately. If `log = structlog.get_logger()` is in a module that's imported early, the first log before lifespan runs uses default config.

**How to avoid:** Call `configure_logging()` at the very top of `main.py` (before `FastAPI()`) OR as the very first thing in the lifespan. Avoid logging at module import time.

**Warning signs:** Mixed formatted/unformatted log lines at startup.

### Pitfall 3: `cache_logger_on_first_use=True` after reconfiguration

**What goes wrong:** `structlog.configure(cache_logger_on_first_use=True)` is set, then `configure_logging()` is called a second time (e.g., in tests). Cached loggers still use the old config.

**Why it happens:** Caching freezes the processor chain at first use. Reconfiguration doesn't invalidate the cache.

**How to avoid:** Call `structlog.configure(cache_logger_on_first_use=True)` only once at startup. In tests, call `structlog.reset_defaults()` before reconfiguring. [VERIFIED: Context7 /hynek/structlog]

### Pitfall 4: `uvicorn.access` propagation left enabled

**What goes wrong:** Both the custom access log middleware and uvicorn's built-in access logger emit a line per request — duplicate log output.

**Why it happens:** `uvicorn.access` propagates to root logger by default.

**How to avoid:** Set `logging.getLogger("uvicorn.access").propagate = False` in `configure_logging()`.

### Pitfall 5: Missing `extra="ignore"` in BaseSettings

**What goes wrong:** Any environment variable in the shell that doesn't match a Settings field name causes `ValidationError` at startup — e.g., `TERM`, `PATH`, `HOME`.

**Why it happens:** pydantic-settings v2 defaults to `extra="ignore"` but some configurations override it. Confirm `extra="ignore"` is explicit.

**How to avoid:** Set `extra="ignore"` in `model_config`. [VERIFIED: Context7 /pydantic/pydantic-settings]

---

## Code Examples

### Getting a logger in any module

```python
# Source: Context7 /hynek/structlog [VERIFIED: Context7]
import structlog

log = structlog.get_logger()

# All event names use apifuse_ prefix per CONVENTIONS.md
log.info("apifuse_provider_registered", provider_id="docker", provider_type="openapi")
log.error("apifuse_request_failed", status_code=502, provider_id="docker")
```

### Per-request context binding (middleware pattern)

```python
# Source: Context7 /hynek/structlog contextvars docs [VERIFIED: Context7]
import uuid
import structlog
from structlog.contextvars import clear_contextvars, bind_contextvars

async def logging_middleware(request, call_next):
    clear_contextvars()
    bind_contextvars(
        request_id=str(uuid.uuid4()),
        method=request.method,
        path=request.url.path,
    )
    response = await call_next(request)
    return response
```

Note: This pattern should be implemented as an `@app.middleware("http")` decorator or a lightweight Starlette middleware — separate from `ErrorHandlingMiddleware`.

### pydantic-settings optional env file

```python
# Source: Context7 /pydantic/pydantic-settings [VERIFIED: Context7]
from pydantic_settings import BaseSettings, SettingsConfigDict

class ApifuseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # silently ignored if file doesn't exist
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_env: str = "development"  # D-03: works with zero env vars
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` / `on_event("shutdown")` | `lifespan` asynccontextmanager | FastAPI 0.93.0 (2023) | Deprecated events still work but emit deprecation warning in current FastAPI |
| `filter_by_level` processor (runtime check) | `make_filtering_bound_logger(level)` | structlog 21.2.0 | Filtered levels become zero-cost no-ops |
| `structlog.configure(processors=[..., JSONRenderer()])` alone | `ProcessorFormatter` bridge | structlog ~20.x | Bridge is required to capture third-party (uvicorn) logs into structlog chain |

**Deprecated/outdated:**
- `@app.on_event("startup")`: Still functional but deprecated in favor of `lifespan`. [VERIFIED: Context7 /fastapi/fastapi]
- `structlog.stdlib.filter_by_level` as a chain processor: Functional but slower than `make_filtering_bound_logger`. [VERIFIED: Context7 /hynek/structlog]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pure ASGI middleware is safer than `BaseHTTPMiddleware` for all-exception catching in this use case | Pattern 5: ErrorHandlingMiddleware | If wrong, `BaseHTTPMiddleware` works fine for Phase 1's non-streaming use case — low impact, easy swap |
| A2 | `uvicorn.access` log suppression is correct for Phase 1 (no per-request access log in middleware yet) | Pattern 2: structlog config | If Phase 1 needs access logging, the middleware pattern in Pattern 6 can be added — missing it is a minor gap, not a breakage |

---

## Open Questions

1. **Should Phase 1 include a per-request logging middleware?**
   - What we know: The structlog contextvars pattern supports per-request binding (`request_id`, `method`, `path`)
   - What's unclear: CONTEXT.md doesn't mention it; success criteria don't require `request_id` in logs
   - Recommendation: Include a minimal `@app.middleware("http")` that calls `clear_contextvars()` + `bind_contextvars(request_id=uuid4())` to unblock Phase 2+ logging — adds ~10 lines, no dependencies

2. **Should `ApifuseSettings` be a module-level singleton or instantiated via `Depends()`?**
   - What we know: Claude's Discretion allows either; singleton is simpler for Phase 1
   - What's unclear: Phase 2 may want `Depends(get_settings)` for testability
   - Recommendation: Module-level singleton `apifuse_settings = ApifuseSettings()` for Phase 1; leave `get_settings()` helper as a thin wrapper for future `Depends()` injection

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All | ✓ | 3.12.2 | — |
| uv | Package management | ✓ | (active) | — |
| FastAPI | HTTP framework | ✓ | 0.136.1 | — |
| structlog | Logging | ✓ | 25.5.0 | — |
| pydantic-settings | Config | ✓ | 2.14.1 | — |
| uvicorn | ASGI server | ✓ | 0.46.0 | — |
| python-dotenv | .env loading | ✓ | 1.2.2 | — |

All dependencies present. No missing items. [VERIFIED: uv run python -c "import X; print(X.__version__)"]

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| Config file | None — Wave 0 must create `pyproject.toml [tool.pytest.ini_options]` section |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOUND-01 | Settings load with zero env vars; `app_env` defaults to "development" | unit | `uv run pytest tests/test_config.py -x` | ❌ Wave 0 |
| FOUND-01 | `.env` file absent → no ValidationError | unit | `uv run pytest tests/test_config.py::test_no_env_file -x` | ❌ Wave 0 |
| FOUND-02 | No `print()` call anywhere in `app/` or `main.py` | static (grep) | `grep -r "print(" app/ main.py` → exit 1 if any found | ❌ Wave 0 |
| FOUND-02 | structlog emits JSON when `APP_ENV=production` | unit | `uv run pytest tests/test_logging.py -x` | ❌ Wave 0 |
| FOUND-03 | `uvicorn main:app` starts without errors | smoke | `uv run uvicorn main:app --port 8765 &; sleep 1; curl -s http://localhost:8765/` | ❌ Wave 0 |
| FOUND-03 | Unknown route returns JSON error envelope `{"error":..., "status_code":404}` | integration | `uv run pytest tests/test_app.py::test_error_envelope -x` | ❌ Wave 0 |
| FOUND-03 | CORS headers present on `OPTIONS /` | integration | `uv run pytest tests/test_app.py::test_cors_headers -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/conftest.py` — shared `TestClient` fixture using `httpx.AsyncClient(app=app, base_url="http://test")`
- [ ] `tests/test_config.py` — covers FOUND-01
- [ ] `tests/test_logging.py` — covers FOUND-02
- [ ] `tests/test_app.py` — covers FOUND-03 (CORS headers, error envelope, smoke start)
- [ ] `pyproject.toml [tool.pytest.ini_options]` — asyncio_mode = "auto", testpaths = ["tests"]

---

## Project Constraints (from CLAUDE.md)

| Directive | Applies To | Enforcement Point |
|-----------|-----------|-------------------|
| Zero `print()` calls — use `structlog` exclusively | All source files in `app/` and `main.py` | FOUND-02 requirement; grep check in Wave 0 tests |
| `apifuse_` prefix — uniform naming on all internal identifiers | Log event names; module-level public names | CONVENTIONS.md; code review |
| No dead code — no unused imports, variables, or commented-out blocks | All files written in Phase 1 | Code review per task |
| Single `conftest.py` — shared fixtures only, no duplication | `tests/conftest.py` | Test Wave 0 setup |
| uv — package manager; never use pip or poetry | All install/run commands | All task actions use `uv run` / `uv add` |

---

## Security Domain

> `security_enforcement` not explicitly set to `false` in config. Section included.
> D-05 defers security restrictions to a later phase — Phase 1 is local-first.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No (D-05 deferred) | — |
| V3 Session Management | No | — |
| V4 Access Control | No (D-05 deferred) | — |
| V5 Input Validation | Partial | Pydantic v2 validates Settings fields; FastAPI validates path/query params |
| V6 Cryptography | No | — |

### Known Threat Patterns for Phase 1 Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Env var injection in settings | Tampering | pydantic-settings type coercion + field validation |
| Unhandled exception leaks stack traces | Information disclosure | ErrorHandlingMiddleware: minimal error in prod (D-07) |
| CORS wildcard `allow_origins=["*"]` | Elevation of privilege | Acceptable for Phase 1 (D-06); restrict in security hardening phase |

---

## Sources

### Primary (HIGH confidence)

- Context7 `/hynek/structlog` — processor chain, ConsoleRenderer, JSONRenderer, ProcessorFormatter, make_filtering_bound_logger, contextvars patterns
- Context7 `/pydantic/pydantic-settings` — BaseSettings, model_config, env_file, extra="ignore", optional fields with defaults
- Context7 `/fastapi/fastapi` — lifespan asynccontextmanager, CORSMiddleware, add_middleware ordering, exception_handler decorator
- `pyproject.toml` + `uv run python -c "..."` — all installed package versions verified in active venv

### Secondary (MEDIUM confidence)

- [GitHub Gist: nymous — Logging setup for FastAPI, Uvicorn and Structlog](https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e) — ProcessorFormatter bridge pattern, uvicorn logger suppression, per-request middleware
- [ouassim.tech — Setting Up Structured Logging in FastAPI with structlog](https://ouassim.tech/notes/setting-up-structured-logging-in-fastapi-with-structlog/) — shared_processors pattern, drop_color_message_key, environment renderer switching

### Tertiary (LOW confidence)

- None — all claims are backed by Context7 (primary) or verified community patterns (secondary).

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against active virtual environment
- Architecture: HIGH — verified against Context7 official docs for all three libraries
- Pitfalls: MEDIUM-HIGH — processor chain pitfalls verified; middleware ordering verified; some pitfalls from community patterns cross-checked with official docs

**Research date:** 2026-05-12
**Valid until:** 2026-06-12 (stable libraries; structlog and pydantic-settings have slow-moving APIs)
