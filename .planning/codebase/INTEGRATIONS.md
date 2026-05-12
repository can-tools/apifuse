# External Integrations

**Analysis Date:** 2026-05-12

## APIs & External Services

ApiFuse is an API gateway whose entire purpose is proxying to external providers. Providers are declared
in `config/providers/*.yaml` (not yet created — planned in Phase 4). The resolved OpenAPI specs live
in `config/openapi/*.yaml`.

**Docker API (planned):**
- Purpose: Proxy Docker daemon HTTP API through ApiFuse
- Provider type: `openapi` (driven by `config/openapi/docker-resolved.yaml`)
- Provider config: `config/providers/docker.yaml` (planned)
- Auth: Not yet specified; expected via `env_mapping` in provider YAML

**Composite Provider (planned):**
- Purpose: Aggregate responses from multiple providers in a single request
- Provider config: `config/providers/composite.yaml` (planned)
- OpenAPI spec: `config/openapi/composite-resolved.yaml` (planned)
- Mechanism: `x-aggregates` extension in provider YAML spec

**Debug Providers (dev-only, planned):**
- HTTPBin - Used for request inspection and debugging in dev mode; custom Python provider class
- JSONPlaceholder - Fake REST API for testing provider wiring; custom Python provider class
- Both exposed under `/api/v1/debug/*` (only available when `ENV=development`)

**Generic OpenAPI Providers:**
- Any API that has an OpenAPI 3.x spec can be registered by adding a YAML file to `config/providers/`
- Provider class: `OpenAPIProvider` (`app/providers/openapi_provider.py`, planned)
- Auth injected via `_prepare_request()` in `BaseProvider` (`app/core/client.py`, planned)

## Data Storage

**Databases:**
- None — ApiFuse is a stateless API gateway; no database is used or planned

**File Storage:**
- Local filesystem only — YAML provider configs (`config/providers/`) and OpenAPI specs (`config/openapi/`) read at startup

**Caching:**
- Cache-control headers emitted via `CacheHeaders` middleware (described in `docs/architecture.md`)
- No in-memory or external cache store (Redis, Memcached, etc.) detected or planned

## Authentication & Identity

**Auth Provider:**
- No user-facing authentication layer detected or planned
- Per-provider auth: injected by `BaseProvider._prepare_request()` using credentials sourced from env vars declared in `env_mapping` section of each provider's YAML config
- Auth schemes vary per provider (API key headers, Bearer tokens, etc.) — abstracted by provider layer

## Monitoring & Observability

**Error Tracking:**
- No external error tracking service (Sentry, Rollbar, etc.) detected or planned

**Logs:**
- structlog 25.5.0 for structured (JSON-compatible) logging
- Structured logs emitted to stdout; collection depends on deployment environment

**Health Checks:**
- `GET /api/v1/health` — basic health endpoint
- `GET /api/v1/health/detailed` — detailed provider status (dev-only per architecture notes)

## CI/CD & Deployment

**Hosting:**
- Not yet specified — project is in early phase (only `main.py` stub exists)
- Target: any ASGI-compatible host (Uvicorn process, Docker container)

**CI Pipeline:**
- No CI configuration files detected (no `.github/workflows/`, no `Dockerfile`)

## Environment Configuration

**Required env vars (planned, per architecture):**
- Provider-specific credentials declared under `env_mapping` in each `config/providers/*.yaml` file
- Specific variable names not yet determined (provider configs not yet created)

**Secrets location:**
- No `.env` file present yet
- Pattern: `.env` for local dev, loaded via `python-dotenv`; pydantic-settings reads into `Settings` object

## Webhooks & Callbacks

**Incoming:**
- None — ApiFuse is a request-driven gateway, no webhook receiver endpoints planned

**Outgoing:**
- None — ApiFuse makes synchronous HTTP calls to provider APIs per request; no async callbacks

---

*Integration audit: 2026-05-12*
