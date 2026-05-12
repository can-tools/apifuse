# Codebase Concerns

**Analysis Date:** 2026-05-12

## Tech Debt

**Project is a stub — no application code exists:**
- Issue: The entire application described in `docs/architecture.md` and `docs/plan.md` has not been implemented. The only Python source file is a 7-line placeholder.
- Files: `main.py`
- Impact: `main.py` exports `main()` which prints "Hello from apifuse!" — it is not a FastAPI `app` object. The README instructs running `uvicorn main:app --reload` which will crash immediately because `app` does not exist in `main.py`.
- Fix approach: Implement Faza 1 from `docs/plan.md` — create `app/` directory structure, real FastAPI lifespan, middleware stack, and base models as specified.

**No `app/` directory structure:**
- Issue: The planned module layout (`app/api/`, `app/core/`, `app/models/`, `app/providers/`) is entirely absent.
- Files: All paths listed in `docs/plan.md` under "Struktura docelowa"
- Impact: Any code added without this structure will land in the root, making future refactoring expensive and deviating from the intended architecture.
- Fix approach: Create the directory scaffold as a first implementation step before any logic is added.

**`pyproject.toml` description is the uv scaffold placeholder:**
- Issue: `description = "Add your description here"` — the default `uv init` placeholder text was never replaced.
- Files: `pyproject.toml` line 4
- Impact: Low — cosmetic, but signals the project has not progressed past scaffold stage.
- Fix approach: Set a meaningful description matching the README ("API gateway built on FastAPI with dynamic endpoint generation from OpenAPI spec").

**`config/` directory is absent:**
- Issue: The architecture requires `config/providers/*.yaml` and `config/openapi/*.yaml` for provider autodiscovery, but neither the directory nor any YAML files exist.
- Files: `docs/architecture.md`, `docs/plan.md` — referenced paths do not exist on disk.
- Impact: `ProviderLoader` cannot function; the dynamic router has nothing to read. The system as designed cannot start.
- Fix approach: Create `config/providers/` and `config/openapi/` with at least placeholder YAML files as part of Faza 4.

## Known Bugs

**`uvicorn main:app` will fail at startup:**
- Symptoms: `ImportError: cannot import name 'app' from 'main'` when running the command documented in the README.
- Files: `main.py`, `README.md`
- Trigger: Running `uv run uvicorn main:app --reload` as instructed.
- Workaround: None until the FastAPI `app` instance is created in `main.py`.

## Security Considerations

**No authentication or authorization layer defined:**
- Risk: The architecture diagram shows no auth layer between the client and the FastAPI gateway. The dynamic router will proxy requests to external APIs (Docker, etc.) without any authentication on the gateway itself.
- Files: `docs/architecture.md`
- Current mitigation: None — the application does not exist yet.
- Recommendations: Design an auth strategy (API key, JWT, or OAuth2) before implementing production providers. The `_prepare_request()` method stub in the architecture implies per-provider auth headers but gateway-level auth is unspecified.

**Debug endpoints intended to be dev-only have no enforcement mechanism defined:**
- Risk: `GET /api/v1/debug/*` and `GET /api/v1/health/detailed` are described as "tylko dev" (dev only), but no mechanism (environment flag check, middleware guard) is specified or implemented.
- Files: `docs/architecture.md`, `docs/plan.md` (Faza 5)
- Current mitigation: None — endpoints do not exist yet.
- Recommendations: Implement an `APP_ENV` or `DEBUG` settings guard that disables debug router registration in production at startup.

**No `.env.example` file:**
- Risk: Developers cloning the repo have no reference for required environment variables. Secrets may be inlined into config files or committed accidentally.
- Files: Root directory — `.env.example` absent.
- Current mitigation: `.gitignore` correctly excludes `.env`.
- Recommendations: Add `.env.example` with all required variable names (no values) before the first env-dependent code is committed.

**CORS middleware configuration unspecified:**
- Risk: The architecture lists `CORSMiddleware` but `allowed_origins` is not defined. Default FastAPI CORS allows nothing or everything depending on configuration — both are problematic.
- Files: `docs/architecture.md`
- Current mitigation: Not applicable — middleware not implemented yet.
- Recommendations: Define `CORS_ALLOWED_ORIGINS` as a settings field (pydantic-settings) and configure it explicitly before any frontend integration.

## Performance Bottlenecks

**No caching strategy defined for proxied API responses:**
- Problem: The architecture mentions `CacheHeaders` middleware but provides no specification for cache duration, cache key strategy, or cache storage backend.
- Files: `docs/architecture.md`
- Cause: The design is incomplete at this stage — caching is named but not designed.
- Improvement path: Define cache policy per provider in provider YAML config before implementing the middleware. Consider in-memory (via `cachetools`) for local dev and Redis for production.

**`pytest-playwright` included without async test mode configured:**
- Problem: `pytest-playwright` is a heavyweight dependency (installs Chromium/Firefox/WebKit browsers) included in dev dependencies but there is no `[tool.pytest.ini_options]` section configuring `asyncio_mode` for `pytest-asyncio` or a `conftest.py`.
- Files: `pyproject.toml`
- Cause: Dependencies were added speculatively without configuring the test runner.
- Improvement path: Add `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` to `pyproject.toml`. Evaluate whether Playwright is actually needed — it is expensive for an API gateway project with no browser UI.

## Fragile Areas

**Dynamic route generation from YAML spec is high-risk:**
- Files: `docs/architecture.md` — `DynamicRouterGenerator` (not yet implemented)
- Why fragile: Generating FastAPI routes at runtime from YAML means type errors, missing parameters, and invalid schemas will surface at startup rather than at import time. A malformed YAML will crash the entire gateway.
- Safe modification: Implement strict Pydantic validation of provider YAML schemas before route generation. Add startup-time validation with clear error messages identifying which provider and which field caused the failure.
- Test coverage: No tests exist; this component needs comprehensive unit tests with both valid and malformed YAML fixtures before implementation is considered complete.

**`CompositeProvider` `x-aggregates` semantics are undefined:**
- Files: `docs/architecture.md` — `x-aggregates` field in YAML spec
- Why fragile: OpenAPI extensions (`x-*`) are custom — no schema validation exists. A typo in `x-aggregates` will silently produce incorrect aggregation rather than failing loudly.
- Safe modification: Define and document the exact `x-aggregates` schema. Validate it at provider load time with explicit error messages.
- Test coverage: None — this feature does not exist yet.

## Scaling Limits

**Single-process uvicorn:**
- Current capacity: One uvicorn worker process.
- Limit: CPU-bound operations (YAML parsing, dynamic route generation) block the event loop. High concurrency to proxied APIs will saturate a single worker.
- Scaling path: Document use of `uvicorn --workers N` or switch to gunicorn + uvicorn workers for production. Note that in-memory provider registry is not safe to share across processes without redesign.

## Dependencies at Risk

**`pytest-asyncio` version `1.3.0` is unusually high (likely a pre-release or typo):**
- Risk: As of early 2026, pytest-asyncio's production releases are in the `0.x` series. Version `1.3.0` specified in `pyproject.toml` may be a pre-release or a version that introduces breaking API changes.
- Impact: Test suite may fail to collect or run if the version is incompatible with `pytest >= 9.0.3`.
- Files: `pyproject.toml` line 19, `uv.lock`
- Migration plan: Verify the actual release history for `pytest-asyncio`. If `1.x` is stable, ensure `asyncio_mode` configuration matches the new API. If it is a typo, downgrade to `>=0.23`.

**`annotated-doc 0.0.4` appears in `uv.lock` but not in `pyproject.toml`:**
- Risk: An unlisted transitive or phantom dependency (`annotated-doc`) appears in the lockfile and is installed into `.venv`. This package is obscure (version `0.0.4`, small codebase) and its origin is unclear.
- Impact: Supply chain risk — an unvetted package is installed silently.
- Files: `uv.lock` — `annotated-doc` entry
- Migration plan: Audit where this dependency is pulled from. Run `uv tree` to trace which direct dependency requires it, or remove it if it is unused.

**All runtime dependencies use `>=` version constraints with no upper bound:**
- Risk: `fastapi>=0.136.1`, `uvicorn>=0.46.0`, etc. — no upper bounds means a future breaking release of any dependency will be automatically pulled by `uv sync` if the lockfile is regenerated.
- Impact: Silent breakage when upstream packages release major versions.
- Files: `pyproject.toml` lines 6-14
- Migration plan: For production stability, consider `~=` (compatible release) constraints or regularly audited upper bounds. The `uv.lock` file pins exact versions for day-to-day use, but CI without the lockfile will pick up latest.

## Missing Critical Features

**No tests exist:**
- Problem: `tests/` directory does not exist. `pyproject.toml` includes `pytest`, `pytest-asyncio`, and `pytest-playwright` but there is no test code, no `conftest.py`, and no pytest configuration.
- Blocks: Cannot verify any implementation correctness. CI cannot be added without a passing test baseline.
- Priority: High — required before any Phase 2+ implementation is considered complete.

**No linting or formatting tooling configured:**
- Problem: No `ruff`, `black`, `flake8`, `mypy`, or any other linter/formatter is listed in dev dependencies or configured in `pyproject.toml`.
- Blocks: Code style will diverge as more contributors add code. Type errors will go undetected.
- Priority: Medium — add `ruff` and `mypy` to `[dependency-groups]` dev and configure `[tool.ruff]` and `[tool.mypy]` sections in `pyproject.toml` before significant implementation begins.

**No CI/CD pipeline:**
- Problem: `.github/workflows/` is empty. No automated test, lint, or build step runs on push.
- Blocks: No safety net for contributions. Changes that break the app (e.g., the `uvicorn main:app` crash) cannot be caught automatically.
- Priority: High — add a minimal GitHub Actions workflow running `uv sync && uv run pytest` before implementation phases begin.

## Test Coverage Gaps

**Entire codebase is untested:**
- What's not tested: Everything — there is no application code and no test code.
- Files: All future `app/` modules, `main.py`
- Risk: Any implementation can break silently. The dynamic router generator is the highest-risk component (runtime code generation from YAML) and needs test-first development.
- Priority: High — establish `tests/` structure, `conftest.py`, and at minimum a smoke test that the FastAPI app starts before implementation of each subsequent phase.

---

*Concerns audit: 2026-05-12*
