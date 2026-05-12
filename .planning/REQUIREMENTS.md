# Requirements: ApiFuse

**Defined:** 2026-05-12
**Core Value:** Dynamic provider aggregation — add any OpenAPI-compatible service via YAML config and ApiFuse exposes it immediately as routable FastAPI endpoints.

## v1 Requirements

### Foundation

- [ ] **FOUND-01**: Project environment configured with uv, pyproject.toml, pydantic-settings, and .env support
- [ ] **FOUND-02**: Structured logging via structlog — zero `print()` calls enforced, uniform `apifuse_` prefix
- [ ] **FOUND-03**: FastAPI application with lifespan startup/shutdown, CORSMiddleware, and ErrorHandlingMiddleware

### Provider System

- [ ] **PROV-01**: `BaseProvider` abstract class defining the provider interface (`execute_operation()`)
- [ ] **PROV-02**: `ProviderRegistry` — central registry for registering and looking up providers by name
- [ ] **PROV-03**: `CustomClient` — async httpx HTTP client with auth header preparation (`_prepare_request()`)
- [ ] **PROV-04**: `ProviderLoader` — autodiscovery of providers from `config/providers/*.yaml` at startup
- [ ] **PROV-05**: `env_mapping` support — environment variable substitution in provider YAML configs

### Dynamic Router

- [ ] **ROUT-01**: `DynamicRouterGenerator` — reads OpenAPI YAML spec and generates FastAPI routes at startup
- [ ] **ROUT-02**: Full parameter handling — path, query, and body parameters mapped from OpenAPI spec
- [ ] **ROUT-03**: Dynamic Pydantic model generation — request/response models derived from OpenAPI schemas
- [ ] **ROUT-04**: Swagger UI integration — auto-generated documentation for all dynamic endpoints

### Production Providers

- [ ] **IMPL-01**: `OpenAPIProvider` — generic provider driven by OpenAPI YAML spec (`operations{}`, `execute_operation()`)
- [ ] **IMPL-02**: `CompositeProvider` — multi-provider aggregation using `x-aggregates` in OpenAPI spec

### System & Debug Endpoints

- [ ] **SYS-01**: `GET /api/v1/` — API info endpoint
- [ ] **SYS-02**: `GET /api/v1/health` — basic health check
- [ ] **SYS-03**: `GET /api/v1/health/detailed` — detailed system status (dev-only)
- [ ] **SYS-04**: Debug providers module — HTTPBin and JSONPlaceholder providers (`providers/debug/`), dev-only

### Developer Tooling

- [ ] **TOOL-01**: `scripts/resolve_openapi.py` — resolves OpenAPI spec references into single flat file
- [ ] **TOOL-02**: `scripts/validate_openapi.py` — validates OpenAPI spec files
- [ ] **TOOL-03**: `Makefile` (or shell scripts) — dev and prod workflow commands

## v2 Requirements

### Response Models

- **MOD-01**: Base response models `APIResponse` and `ErrorResponse` with unified schema
- **MOD-02**: Standardized error envelope across all endpoints

### Testing Suite

- **TEST-01**: pytest configuration with shared `conftest.py` and common fixtures
- **TEST-02**: Unit tests — config, provider registry, dynamic router
- **TEST-03**: Integration tests — provider execution with `httpx.MockTransport` (no real external calls)

### Docker Provider

- **DOCKER-01**: Docker provider config (`config/openapi/docker-resolved.yaml`) wired and tested

## Out of Scope

| Feature | Reason |
|---------|--------|
| Authentication / authorization | Not in v1 plan — gateway is open by design in v1 |
| Rate limiting | Not in v1 plan |
| Persistent storage / database | Gateway is stateless by design |
| gRPC or GraphQL | HTTP/REST only in v1 |
| OAuth / API key management | Out of scope for v1 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Pending |
| FOUND-03 | Phase 1 | Pending |
| PROV-01 | Phase 2 | Pending |
| PROV-02 | Phase 2 | Pending |
| PROV-03 | Phase 2 | Pending |
| PROV-04 | Phase 2 | Pending |
| PROV-05 | Phase 2 | Pending |
| ROUT-01 | Phase 3 | Pending |
| ROUT-02 | Phase 3 | Pending |
| ROUT-03 | Phase 3 | Pending |
| ROUT-04 | Phase 3 | Pending |
| IMPL-01 | Phase 4 | Pending |
| IMPL-02 | Phase 4 | Pending |
| SYS-01 | Phase 5 | Pending |
| SYS-02 | Phase 5 | Pending |
| SYS-03 | Phase 5 | Pending |
| SYS-04 | Phase 5 | Pending |
| TOOL-01 | Phase 6 | Pending |
| TOOL-02 | Phase 6 | Pending |
| TOOL-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-12*
*Last updated: 2026-05-12 — traceability confirmed against ROADMAP.md*
