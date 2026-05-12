# Phase 1: Foundation - Pattern Map

**Mapped:** 2026-05-12
**Files analyzed:** 6 new/modified files
**Analogs found:** 0 / 6 (greenfield — no existing app code)

> This is a greenfield phase. `main.py` is a 6-line stub with a `print()` call; no
> `app/` package exists yet. All patterns are sourced from RESEARCH.md verified
> code examples and the project's committed conventions in CONVENTIONS.md and
> ARCHITECTURE.md. The planner MUST copy these patterns verbatim — they encode
> locked decisions D-01 through D-08.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `main.py` | config / entrypoint | request-response | `main.py` stub (rewrite) | no match — stub only |
| `app/__init__.py` | package marker | — | none | no match |
| `app/core/__init__.py` | package marker | — | none | no match |
| `app/core/config.py` | config | — | none | no match |
| `app/core/logging.py` | utility | — | none | no match |
| `app/core/exceptions.py` | middleware | request-response | none | no match |

---

## Pattern Assignments

### `main.py` (entrypoint, request-response)

**Analog:** none — full rewrite of 6-line stub
**Constraint violations to fix:** line 2 — `print("Hello from apifuse!")` must be removed (FOUND-02)

**Imports pattern:**
```python
# Standard library first, then third-party, then local (PEP 8 / CONVENTIONS.md)
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import apifuse_settings
from app.core.exceptions import ErrorHandlingMiddleware
from app.core.logging import configure_logging
```

**Lifespan pattern (D-01, D-02, RESEARCH.md Pattern 3):**
```python
log = structlog.get_logger()

@asynccontextmanager
async def apifuse_lifespan(app: FastAPI):
    # configure_logging MUST be called before any log.* call (Pitfall 2)
    configure_logging(apifuse_settings.app_env)
    log.info("apifuse_startup", app_env=apifuse_settings.app_env, version=apifuse_settings.app_version)
    # Phase 2 hook: initialize_providers() goes here
    yield
    log.info("apifuse_shutdown")
```

**App instantiation and middleware ordering (D-06, RESEARCH.md Pattern 4):**
```python
app = FastAPI(
    title=apifuse_settings.app_name,
    version=apifuse_settings.app_version,
    lifespan=apifuse_lifespan,
)

# Middleware insertion order is REVERSED — last added = outermost (Pitfall 1)
# Add ErrorHandlingMiddleware FIRST → it becomes innermost
app.add_middleware(ErrorHandlingMiddleware, app_env=apifuse_settings.app_env)

# Add CORSMiddleware LAST → it becomes outermost (runs first on every request)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # D-06: open by default; restrict in security phase
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**HTTPException handler (D-07, D-08, RESEARCH.md Pattern 5 alternative):**
```python
@app.exception_handler(HTTPException)
async def apifuse_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},  # D-08
    )
```

**No `if __name__ == "__main__"` block required** — uvicorn is invoked directly via
`uv run uvicorn main:app`. Remove the legacy stub's `main()` function and `print()`.

---

### `app/__init__.py` (package marker)

**Pattern:** Empty file — no imports, no code. Marks `app/` as a Python package.

```python
# intentionally empty
```

---

### `app/core/__init__.py` (package marker)

**Pattern:** Empty file — no imports, no code. Marks `app/core/` as a Python package.

```python
# intentionally empty
```

---

### `app/core/config.py` (config, pydantic-settings)

**Analog:** none — first settings module in the project
**Locks:** D-03 (no required env vars), D-04 (all defaults), RESEARCH.md Pattern 1

**Imports pattern:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
```

**Core pattern (D-03, D-04):**
```python
class ApifuseSettings(BaseSettings):
    """Application settings loaded from environment variables and optional .env file.

    All fields have defaults — application starts with zero environment configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",            # silently ignored if absent (D-03)
        env_file_encoding="utf-8",
        extra="ignore",             # unknown env vars do not raise ValidationError (Pitfall 5)
    )

    app_env: str = "development"   # D-03: default; switch to "production" via APP_ENV
    app_name: str = "apifuse"
    app_version: str = "0.1.0"

    @property
    def is_dev(self) -> bool:
        """True when running in development mode."""
        return self.app_env == "development"


# Module-level singleton — imported by logging.py and main.py
apifuse_settings = ApifuseSettings()
```

**Naming rule:** class name uses `PascalCase` (`ApifuseSettings`); singleton uses
`apifuse_` prefix (`apifuse_settings`) per CONVENTIONS.md.

---

### `app/core/logging.py` (utility, structlog setup)

**Analog:** none — first logging module in the project
**Locks:** D-01 (ConsoleRenderer dev / JSONRenderer prod), D-02 (DEBUG dev / INFO prod),
RESEARCH.md Pattern 2

**Imports pattern:**
```python
import logging
import sys

import structlog
```

**Helper processor (RESEARCH.md Pattern 2):**
```python
def drop_color_message_key(_, __, event_dict: dict) -> dict:
    """Remove uvicorn's redundant 'color_message' key before rendering."""
    event_dict.pop("color_message", None)
    return event_dict
```

**Core pattern — configure_logging (D-01, D-02):**
```python
def configure_logging(app_env: str = "development") -> None:
    """Configure structlog and bridge uvicorn's stdlib logs into the same chain.

    Must be called once at startup before any log calls are made (see Pitfall 2).
    """
    is_dev = app_env == "development"
    log_level = logging.DEBUG if is_dev else logging.INFO  # D-02

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

    # D-01: renderer chosen once at startup based on APP_ENV
    if is_dev:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    # structlog side: wrap_for_formatter MUST be the final processor
    structlog.configure(
        processors=shared_processors + [
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(log_level),  # zero-overhead filtering
        cache_logger_on_first_use=True,
    )

    # stdlib side: ProcessorFormatter routes ALL stdlib logs (uvicorn, httpx) through structlog
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

    # Route uvicorn error/startup logs through root logger (Pitfall 4 prevention)
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_log = logging.getLogger(uvicorn_logger_name)
        uvicorn_log.handlers.clear()
        uvicorn_log.propagate = True

    # Suppress uvicorn.access — suppress duplicate access lines (Pitfall 4)
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.propagate = False
```

**Usage pattern at call sites (CONVENTIONS.md Logging section):**
```python
# Any module that needs a logger:
import structlog

log = structlog.get_logger()

# Event names carry apifuse_ prefix (CONVENTIONS.md)
log.info("apifuse_startup", app_env="development", version="0.1.0")
log.error("apifuse_request_failed", status_code=502, provider_id="docker")
# NEVER: print("something")  — violates FOUND-02
```

---

### `app/core/exceptions.py` (middleware, request-response)

**Analog:** none — first middleware in the project
**Locks:** D-07 (full detail in dev, minimal in prod), D-08 (flat JSON envelope),
RESEARCH.md Pattern 5

**Imports pattern:**
```python
import structlog
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
```

**Core pattern — pure ASGI middleware (D-07, D-08):**
```python
log = structlog.get_logger()


class ErrorHandlingMiddleware:
    """Pure ASGI middleware that catches all unhandled exceptions and returns
    the standard error envelope: {"error": "...", "status_code": N}.

    Implemented as a pure ASGI callable (not BaseHTTPMiddleware) to reliably
    catch exceptions from all middleware layers, including streaming responses.
    """

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
            # D-07: full detail in dev, minimal in prod
            if self.is_dev:
                error_message = f"{type(exc).__name__}: {exc}"
            else:
                error_message = "Internal server error" if status_code == 500 else str(exc)
            log.error(
                "apifuse_unhandled_exception",
                exc_type=type(exc).__name__,
                status_code=status_code,
                exc_info=exc,
            )
            # D-08: flat envelope {"error": "...", "status_code": N}
            response = JSONResponse(
                status_code=status_code,
                content={"error": error_message, "status_code": status_code},
            )
            await response(scope, receive, send)
```

**Naming rule:** `ErrorHandlingMiddleware` uses `PascalCase` (no `apifuse_` prefix) per
CONVENTIONS.md — the prefix applies to log event names and module-level public
identifiers, not class names.

---

## Shared Patterns

### Zero `print()` rule
**Source:** CLAUDE.md, CONVENTIONS.md, FOUND-02
**Apply to:** All files — `main.py`, `app/core/config.py`, `app/core/logging.py`, `app/core/exceptions.py`
**Enforcement:** Replace every `print()` with a structlog call. The existing `main.py` stub
has `print("Hello from apifuse!")` on line 2 — this is the only violation in the codebase
and must be deleted with the function that contains it.

### `apifuse_` prefix rule
**Source:** CONVENTIONS.md, CONTEXT.md code_context section
**Apply to:** Log event name strings, module-level public identifiers (singletons, public functions)
**Do NOT apply to:** Class names (`ErrorHandlingMiddleware`, `ApifuseSettings`), private helpers, local variables, route path strings
```python
# Correct usage:
apifuse_settings = ApifuseSettings()         # module-level singleton
log.info("apifuse_startup", ...)             # log event name
log.error("apifuse_unhandled_exception", ...)

# Not prefixed (PascalCase classes):
class ApifuseSettings(BaseSettings): ...
class ErrorHandlingMiddleware: ...
```

### Async-first
**Source:** CONVENTIONS.md Function Design section
**Apply to:** All I/O-bound functions and route handlers
```python
# All route handlers and lifecycle hooks must be async def
@asynccontextmanager
async def apifuse_lifespan(app: FastAPI): ...

async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None: ...
```

### Import ordering
**Source:** CONVENTIONS.md Import Organization section
**Apply to:** All files
```
1. Standard library (contextlib, logging, sys, typing, etc.)
2. Third-party (fastapi, pydantic_settings, structlog, starlette, etc.)
3. Local application (app.core.config, app.core.logging, app.core.exceptions)
```

### No `@app.on_event` (deprecated)
**Source:** RESEARCH.md Anti-Patterns, RESEARCH.md State of the Art
**Apply to:** `main.py`
**Rule:** Use `@asynccontextmanager` + `FastAPI(lifespan=...)` exclusively. Never use
`@app.on_event("startup")` or `@app.on_event("shutdown")`.

### uv toolchain
**Source:** CLAUDE.md, CONVENTIONS.md
**Apply to:** All task actions that install or run code
```bash
# Correct:
uv run uvicorn main:app --reload
uv run pytest tests/ -x -q
uv add <package>

# Never:
pip install ...
poetry run ...
python -m pytest ...  # use uv run pytest
```

---

## No Analog Found

All Phase 1 files have no codebase analog — this is a greenfield phase. Every file
listed below is the first of its kind in this repository.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `main.py` | entrypoint | request-response | Only a 6-line stub exists; no FastAPI app yet |
| `app/__init__.py` | package marker | — | `app/` package does not exist yet |
| `app/core/__init__.py` | package marker | — | `app/core/` package does not exist yet |
| `app/core/config.py` | config | — | No settings module exists yet |
| `app/core/logging.py` | utility | — | No logging module exists yet |
| `app/core/exceptions.py` | middleware | request-response | No middleware exists yet |

**Planner note:** Use the patterns extracted from RESEARCH.md (above) directly — they are
verified against Context7 official docs and are production-ready. Do not invent alternatives.

---

## Metadata

**Analog search scope:** `/c/Workspace/cursor/apifuse/**` — full repository
**Files scanned:** `main.py` (6 lines), `pyproject.toml` (23 lines), `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/phases/01-foundation/01-CONTEXT.md`, `.planning/phases/01-foundation/01-RESEARCH.md`
**Pattern extraction date:** 2026-05-12
**Source confidence:** HIGH — all patterns sourced from Context7-verified RESEARCH.md examples
