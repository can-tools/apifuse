# ApiFuse

## What This Is

ApiFuse is a FastAPI-based API gateway that dynamically generates HTTP endpoints from OpenAPI YAML specifications. It aggregates multiple external providers (Docker, composite, and custom) into a unified API surface, allowing new providers to be added purely through configuration without code changes.

## Core Value

Dynamic provider aggregation — add any OpenAPI-compatible service as a provider via YAML config and ApiFuse exposes it immediately as a routable FastAPI endpoint.

## Requirements

### Validated

- ✓ Python 3.12 + FastAPI stack established — existing (pyproject.toml, uv lockfile, main.py stub)
- ✓ Project structure defined — existing (app/, config/, docs/, tests/ layout from docs/plan.md)
- ✓ Core dependencies declared — existing (FastAPI 0.136.1, Pydantic 2.x, httpx, structlog, pytest)

### Active

- [ ] FastAPI application with lifespan, CORS middleware, error handling
- [ ] Structured logging (structlog, zero print() calls)
- [ ] Base response models: `APIResponse`, `ErrorResponse`
- [ ] `BaseProvider` abstract class + `ProviderRegistry`
- [ ] `CustomClient` async HTTP client (httpx)
- [ ] `ProviderLoader` — autodiscovery from `config/providers/*.yaml`
- [ ] Provider types: `openapi`, `composite`, `custom`
- [ ] Environment variable mapping (`env_mapping`)
- [ ] `DynamicRouterGenerator` — generate FastAPI routes from OpenAPI spec
- [ ] Path, query, body parameter handling
- [ ] Dynamic Pydantic model generation from OpenAPI schemas
- [ ] Swagger UI integration
- [ ] `OpenAPIProvider` — YAML spec-driven provider
- [ ] `CompositeProvider` — multi-provider aggregation (`x-aggregates`)
- [ ] Docker provider config (`config/openapi/docker-resolved.yaml`)
- [ ] System endpoints: `/api/v1/`, `/api/v1/health`, `/api/v1/health/detailed`
- [ ] Debug providers: HTTPBin, JSONPlaceholder (dev-only)
- [ ] pytest suite: unit + integration (httpx MockTransport)
- [ ] OpenAPI resolver/validator scripts
- [ ] Makefile / dev scripts

### Out of Scope

- Authentication/authorization middleware — not in v1 plan
- Rate limiting — not in v1 plan
- Persistent storage / database — gateway is stateless by design
- gRPC or GraphQL — HTTP/REST only

## Context

Brownfield project — `main.py` stub and `pyproject.toml` with dependencies exist. No `app/` package, no `tests/` directory yet. Architecture is clearly specified in `docs/architecture.md`. Provider system follows a registry pattern: `ProviderLoader` → `ProviderRegistry` → `BaseProvider` subclasses → `CustomClient` (httpx).

Key naming rule: uniform `apifuse_` prefix throughout. Structured logging only (structlog). Single shared `conftest.py`. No dead code from the start.

## Constraints

- **Tech stack**: Python 3.12 + FastAPI + Pydantic v2 + httpx + structlog — fixed per docs/plan.md
- **Package manager**: uv (not pip/poetry)
- **Logging**: structlog only — zero `print()` calls enforced from day one
- **Naming**: `apifuse_` prefix on all internal identifiers
- **Testing**: pytest + httpx MockTransport for integration tests; no real external calls in tests

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI dynamic routing | OpenAPI YAML → FastAPI routes at startup without code changes | — Pending |
| ProviderRegistry pattern | Central registry decouples route generation from provider impl | — Pending |
| httpx AsyncClient | Async-first, testable with MockTransport | — Pending |
| uv package manager | Fast, deterministic, lockfile-first | — Pending |
| structlog | Structured JSON logs, no print() discipline | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-12 after initialization from docs/plan.md + docs/architecture.md*
