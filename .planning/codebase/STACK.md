# Technology Stack

**Analysis Date:** 2026-05-12

## Languages

**Primary:**
- Python 3.12 - All application and test code

## Runtime

**Environment:**
- Python 3.12.2 (pinned via `.python-version`)

**Package Manager:**
- uv 0.11.11
- Lockfile: `uv.lock` (present, committed)

## Frameworks

**Core:**
- FastAPI 0.136.1 - HTTP API framework, dynamic route registration, OpenAPI/Swagger UI generation
- Starlette 1.0.0 - ASGI foundation underlying FastAPI (middleware, routing)
- Uvicorn 0.46.0 - ASGI server for running the FastAPI application

**Data Validation:**
- Pydantic 2.13.4 - Request/response model validation, dynamic model generation from OpenAPI schemas
- pydantic-settings 2.14.1 - Environment-based configuration management (`Settings` class)

**HTTP Client:**
- httpx 0.28.1 - Async HTTP client for outbound provider calls (`BaseProvider` / `CustomClient`)

**Configuration:**
- pyyaml 6.0.3 - Parses provider definition YAML and OpenAPI spec YAML files
- python-dotenv 1.2.2 - Loads `.env` file into environment for local development

**Logging:**
- structlog 25.5.0 - Structured logging; zero `print()` policy enforced by project conventions

**Testing:**
- pytest 9.0.3 - Test runner
- pytest-asyncio 1.3.0 - Async test support for FastAPI/httpx async code
- pytest-playwright 0.7.2 - End-to-end browser tests (Playwright 1.59.0)
- httpx 0.28.1 - Also used in tests for async HTTP assertions

**Build/Dev:**
- uv - Dependency resolution, virtual environment management, script runner

## Key Dependencies

**Critical:**
- `fastapi>=0.136.1` - Core web framework; all routing, middleware, and Swagger UI depend on it
- `httpx>=0.28.1` - All outbound API calls via `BaseProvider`/`CustomClient`; also used in tests
- `pydantic-settings>=2.14.1` - Settings loaded from env vars at startup; misconfiguration crashes boot
- `pyyaml>=6.0.3` - YAML config parsing; `config/providers/*.yaml` and `config/openapi/*.yaml` parsed at startup
- `structlog>=25.5.0` - Structured logging throughout; must remain zero-`print()` per conventions

**Infrastructure:**
- `uvicorn>=0.46.0` - Production ASGI server
- `python-dotenv>=1.2.2` - Local `.env` loading
- `anyio 4.13.0` - Async I/O primitives (transitive; used by httpx and FastAPI internally)
- `starlette 1.0.0` - ASGI middleware stack (CORSMiddleware, error handling)

## Configuration

**Environment:**
- Configuration managed via `pydantic-settings` (`Settings` class, location TBD at `app/core/config.py`)
- `.env` file for local development (no `.env` file present yet — early-stage project)
- Key configs expected: provider base URLs, API credentials via `env_mapping` in provider YAML

**Build:**
- `pyproject.toml` - Project metadata, dependency declarations, Python version constraint (`>=3.12`)
- `uv.lock` - Fully pinned lockfile for reproducible installs
- `.python-version` - Pins Python to `3.12` for uv/pyenv compatibility

## Platform Requirements

**Development:**
- Python 3.12+
- uv 0.11.x for dependency management
- `.env` file (not yet present; must be created from future `.env.example`)

**Production:**
- ASGI-compatible host (Uvicorn process)
- No database or file storage required (stateless API gateway)
- External provider APIs must be reachable from the deployment environment

---

*Stack analysis: 2026-05-12*
