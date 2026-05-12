# Phase 1: Foundation - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the FastAPI application skeleton: app instantiation, middleware stack (CORS + error handling), structured logging configuration via structlog, and pydantic-settings-based environment config. This is the infrastructure layer every subsequent phase depends on. No provider logic, no dynamic routing. **Wave 0** adds a minimal pytest harness and stubs for FOUND-* only (not the full v2 TEST-01/02/03 program).

</domain>

<decisions>
## Implementation Decisions

### Logging

- **D-01:** Use **human-readable ConsoleRenderer in dev, JSONRenderer in prod** — switched by `APP_ENV` setting. The two formats are structurally different so the switch must live in `app/core/logging.py` setup, not at call sites.
- **D-02:** Log level: **DEBUG when `APP_ENV=development`, INFO otherwise**. No separate `LOG_LEVEL` env var needed in Phase 1.

### Settings / Environment Configuration

- **D-03:** **No required env vars** — application starts without any `.env` file. All settings have sensible defaults. `APP_ENV` defaults to `development`.
- **D-04:** Startup behavior: use pydantic-settings `BaseSettings` with default values. Missing optional vars do not block startup. Hard-fail remains available via pydantic validation if a future phase adds a required field.
- **D-05:** Security restrictions (allowlists, key requirements) are **deferred to a later phase** — Phase 1 is local-first.

### CORS

- **D-06:** **`allow_origins=["*"]`** (open) by default. No `CORS_ORIGINS` env var needed in Phase 1. CORS restriction is a future concern.

### Error Response Format

- **D-07:** `ErrorHandlingMiddleware` returns **full exception details (`message` + `type`) in dev mode, minimal in prod**. Dev vs prod is determined by `APP_ENV`.
- **D-08:** Error JSON format: `{"error": "<message>", "status_code": <code>}` (flat, simple). All HTTP errors use this envelope consistently.

### Claude's Discretion

- Specific structlog processor chain (e.g., which processors to include before the renderer) — planner can follow standard structlog FastAPI patterns.
- Whether `app/core/logging.py` exposes a `configure_logging()` function or uses module-level setup — either is fine.
- Lifespan handler structure inside `main.py` — can be inline or delegated to a helper.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and Goals

- `.planning/ROADMAP.md` §Phase 1 — goal, success criteria (what must be TRUE), deferred items
- `.planning/REQUIREMENTS.md` §Foundation — FOUND-01, FOUND-02, FOUND-03 definitions
- `.planning/PROJECT.md` — tech stack constraints, naming rules, key decisions

### Architecture and Conventions

- `.planning/codebase/ARCHITECTURE.md` — planned file locations (`app/core/config.py`, `app/core/logging.py`, `app/core/exceptions.py`), middleware stack order, component responsibilities
- `.planning/codebase/CONVENTIONS.md` — naming patterns (`apifuse_` prefix rule, `snake_case` files, `PascalCase` classes), logging rules (zero `print()`)

### Existing Source

- `main.py` — current stub (has a `print()` call that violates quality rules; this file gets replaced)
- `pyproject.toml` — all dependencies declared (FastAPI, pydantic-settings, structlog, httpx, etc.)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `pyproject.toml` — all Phase 1 deps already declared: `fastapi`, `pydantic-settings`, `structlog`, `python-dotenv`, `uvicorn`. No `uv add` calls needed for Phase 1.
- `uv.lock` + `.python-version` — environment already pinned and reproducible.

### Established Patterns

- **apifuse_ prefix** — all internal identifiers (log event names, function names exposed in the apifuse namespace) must carry this prefix. Example: `apifuse_provider_registered`, not `provider_registered`.
- **Zero print()** — enforced from day one. The existing `main.py` stub has a `print()` call that must be removed.
- **Async-first** — all I/O functions are `async def`; route handlers are `async def`.
- **uv toolchain** — use `uv run`, `uv add`; never `pip` or `poetry`.

### Integration Points

- `main.py` is the entry point — it creates the FastAPI app, registers middleware, and defines the lifespan. Phase 1 fully rewrites this file.
- Phase 2 will call `initialize_providers()` inside the lifespan — leave a stub hook or comment in the lifespan for this.
- `app/core/` is the layer Phase 2+ depends on — `config.py`, `logging.py`, `exceptions.py` must be importable and stable after Phase 1.

</code_context>

<specifics>
## Specific Ideas

- API should work locally out of the box — no `.env` required, no configuration ceremony for first `uvicorn main:app` run.
- Dev mode is the primary experience for Phase 1; prod hardening (CORS restrictions, auth, rate limiting) is explicitly deferred.

</specifics>

<deferred>
## Deferred Ideas

- CORS allowlist / origin restriction — deferred to a later phase (security hardening)
- Authentication / authorization middleware — explicitly out of scope for v1 (see PROJECT.md Out of Scope)
- Rate limiting — out of scope for v1
- `APIResponse` / `ErrorResponse` base models (MOD-01, MOD-02) — deferred to v2 per ROADMAP.md
- pytest suite (TEST-01/02/03) — deferred to v2 per ROADMAP.md

</deferred>

---

*Phase: 1-Foundation*
*Context gathered: 2026-05-12*
