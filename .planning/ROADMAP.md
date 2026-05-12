# Roadmap: ApiFuse

## Overview

ApiFuse is built in six sequential phases, each delivering a coherent, verifiable capability. Phase 1 establishes the FastAPI application skeleton and development discipline. Phase 2 builds the provider infrastructure — the registry, loader, and HTTP client — that everything else depends on. Phase 3 adds the dynamic router that generates FastAPI routes from OpenAPI YAML at startup, which is the project's core capability. Phase 4 implements the two production provider types (OpenAPIProvider and CompositeProvider) that make the gateway useful with real specs. Phase 5 adds the system and debug endpoints that make the gateway operable. Phase 6 delivers the developer tooling that makes it maintainable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - FastAPI application skeleton with structured logging, CORS, and error handling
- [ ] **Phase 2: Provider System** - BaseProvider, ProviderRegistry, CustomClient, ProviderLoader, and env_mapping
- [ ] **Phase 3: Dynamic Router** - DynamicRouterGenerator producing FastAPI routes from OpenAPI YAML at startup
- [ ] **Phase 4: Production Providers** - OpenAPIProvider and CompositeProvider wired into the registry
- [ ] **Phase 5: System & Debug Endpoints** - Health endpoints, API info, and dev-only debug providers
- [ ] **Phase 6: Developer Tooling** - OpenAPI resolver/validator scripts and Makefile workflow commands

## Phase Details

### Phase 1: Foundation
**Goal**: A running FastAPI application that enforces all code-quality constraints from day one
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03
**Success Criteria** (what must be TRUE):
  1. `uvicorn main:app` starts without errors and serves requests
  2. All imports use `apifuse_` prefix; zero `print()` calls exist in the codebase
  3. Structured JSON log lines appear in the console for application lifecycle events (startup, shutdown) via structlog — per-request access logging middleware is deferred to Phase 2 (aligns with RESEARCH.md Open Question 1)
  4. CORS and error-handling middleware intercept malformed requests and return JSON error responses
  5. Settings load via pydantic-settings with an optional `.env` file; **no env vars are required** in Phase 1 — defaults apply when `.env` is absent (aligns with CONTEXT D-03/D-04; a future phase may introduce required secrets)
**Deferred to v2** (not approved for this phase):
  - `APIResponse` and `ErrorResponse` base models (MOD-01, MOD-02) — unified response envelope
**Plans**: 5 plans

Plans:
- [ ] 01-01-PLAN.md — Wave 0: Test infrastructure (pyproject.toml pytest config, tests/__init__.py, conftest.py, stub test files)
- [ ] 01-02-PLAN.md — Wave 1: Package init files + ApifuseSettings config module (FOUND-01)
- [ ] 01-03-PLAN.md — Wave 2: configure_logging() with structlog processor chain, dev/prod renderer switching (FOUND-02)
- [ ] 01-04-PLAN.md — Wave 2: ErrorHandlingMiddleware pure ASGI class with D-07/D-08 error envelope (FOUND-03 partial)
- [ ] 01-05-PLAN.md — Wave 3: main.py rewrite — FastAPI app, lifespan, middleware stack, integration tests (FOUND-03 complete)

### Phase 2: Provider System
**Goal**: Providers can be declared in YAML, autodiscovered at startup, and invoked via a central registry
**Depends on**: Phase 1
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05
**Success Criteria** (what must be TRUE):
  1. `BaseProvider` is an abstract class; instantiating it directly raises `TypeError`
  2. Dropping a YAML file into `config/providers/` causes ProviderLoader to register it automatically at next startup — no code change required
  3. `ProviderRegistry.get("name")` returns the correct provider instance or raises a typed `ProviderNotFound` error
  4. `CustomClient` executes an async HTTP request and returns a structured response; auth headers from `env_mapping` are substituted correctly
  5. An env variable referenced in a provider YAML (`${MY_TOKEN}`) is resolved from the environment at startup
**Plans**: TBD

### Phase 3: Dynamic Router
**Goal**: FastAPI routes are generated automatically from any OpenAPI YAML spec at startup, with full parameter handling and Swagger UI
**Depends on**: Phase 2
**Requirements**: ROUT-01, ROUT-02, ROUT-03, ROUT-04
**Success Criteria** (what must be TRUE):
  1. Pointing `DynamicRouterGenerator` at an OpenAPI YAML produces live FastAPI routes (GET, POST, etc.) without any manual route registration
  2. Path parameters, query parameters, and request bodies declared in the OpenAPI spec are correctly validated on incoming requests
  3. Pydantic models generated from OpenAPI schemas reject payloads that violate the schema (wrong types, missing required fields)
  4. Swagger UI at `/docs` lists all dynamically registered endpoints with correct parameter docs
**Plans**: TBD

### Phase 4: Production Providers
**Goal**: OpenAPI-spec-driven providers and composite multi-provider aggregation work end-to-end
**Depends on**: Phase 3
**Requirements**: IMPL-01, IMPL-02
**Success Criteria** (what must be TRUE):
  1. An `openapi`-type provider YAML wired to a real OpenAPI spec (e.g., Docker) proxies a live request through the gateway and returns data
  2. `OpenAPIProvider.execute_operation("operationId", params)` selects the correct HTTP method and path from the parsed spec
  3. A `composite`-type provider using `x-aggregates` calls multiple sub-providers and returns a merged response in a single gateway response
  4. Adding a new OpenAPI provider requires only a YAML file in `config/providers/` — no Python code changes
**Deferred to v2** (not approved for this phase):
  - Docker provider config (`config/openapi/docker-resolved.yaml`) (DOCKER-01) — real Docker spec wiring
**Plans**: TBD

### Phase 5: System & Debug Endpoints
**Goal**: The gateway exposes health, info, and dev-mode debug endpoints that make it operable and explorable
**Depends on**: Phase 4
**Requirements**: SYS-01, SYS-02, SYS-03, SYS-04
**Success Criteria** (what must be TRUE):
  1. `GET /api/v1/` returns API name, version, and provider count as JSON
  2. `GET /api/v1/health` returns `{"status": "ok"}` with HTTP 200 in under 50 ms
  3. `GET /api/v1/health/detailed` returns per-provider status and is only reachable in dev mode (returns 404 or 403 in production)
  4. Debug providers (HTTPBin, JSONPlaceholder) are registered and reachable under `/api/v1/debug/` in dev mode; they do not appear in production
**Plans**: TBD
**UI hint**: yes

### Phase 6: Developer Tooling
**Goal**: Developers can resolve, validate, and work with OpenAPI specs via CLI scripts and a Makefile
**Depends on**: Phase 5
**Requirements**: TOOL-01, TOOL-02, TOOL-03
**Success Criteria** (what must be TRUE):
  1. `python scripts/resolve_openapi.py <input.yaml>` produces a single flat OpenAPI file with all `$ref`s inlined
  2. `python scripts/validate_openapi.py <file.yaml>` exits 0 for a valid spec and exits non-zero with a human-readable error for an invalid one
  3. `make dev` starts the development server; `make lint` runs linting; `make test` runs the test suite — all from the project root
**Deferred to v2** (not approved for this phase):
  - pytest suite — unit tests (config, registry, dynamic router) (TEST-01, TEST-02)
  - Integration tests with `httpx.MockTransport` (TEST-03)
  - `docs/architecture.md` update and `API_ENDPOINTS.md` — documentation update pass
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/5 | Not started | - |
| 2. Provider System | 0/TBD | Not started | - |
| 3. Dynamic Router | 0/TBD | Not started | - |
| 4. Production Providers | 0/TBD | Not started | - |
| 5. System & Debug Endpoints | 0/TBD | Not started | - |
| 6. Developer Tooling | 0/TBD | Not started | - |
