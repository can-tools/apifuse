<!-- refreshed: 2026-05-12 -->
# Architecture

**Analysis Date:** 2026-05-12

## System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT (HTTP Request)                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                          │
│                         `main.py`                                │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  MIDDLEWARE STACK                                          │   │
│  │  CORSMiddleware → ErrorHandlingMiddleware → CacheHeaders  │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Static endpoints:                                               │
│  GET /api/v1/                  → API info                        │
│  GET /api/v1/health            → basic health check              │
│  GET /api/v1/health/detailed   → detailed status (dev only)      │
│  /api/v1/openapi/*             → OpenAPI meta-router             │
│  /api/v1/debug/*               → debug providers (dev only)      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
           ┌───────────┴────────────┐
           │    STARTUP (lifespan)   │
           │  1. initialize_providers│
           │  2. register_dynamic_  │
           │     routes()           │
           └───────────┬────────────┘
                       │
       ┌───────────────┼───────────────────┐
       ▼               ▼                   ▼
┌─────────────┐ ┌──────────────┐ ┌────────────────────┐
│  PROVIDER   │ │  DYNAMIC     │ │  CONFIG            │
│  LOADER     │ │  ROUTER      │ │                    │
│             │ │  GENERATOR   │ │  config/providers/ │
│ config/     │ │              │ │    docker.yaml     │
│ providers/  │ │  Reads       │ │    composite.yaml  │
│ *.yaml      │ │  OpenAPI     │ │    *.yaml          │
│             │ │  spec →      │ │                    │
│ Registers   │ │  creates     │ │  config/openapi/   │
│ providers   │ │  FastAPI     │ │    docker-         │
│ in registry │ │  routes      │ │      resolved.yaml │
│             │ │  dynamically │ │    composite-      │
│             │ │              │ │      resolved.yaml │
└──────┬──────┘ └──────────────┘ └────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                    PROVIDER REGISTRY                          │
│              `app/core/client.py` (planned)                  │
│                                                              │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐     │
│  │  OpenAPI     │  │  Composite    │  │  Custom       │     │
│  │  Provider    │  │  Provider     │  │  Provider     │     │
│  │              │  │               │  │               │     │
│  │  Reads YAML  │  │  Aggregates   │  │  Manually     │     │
│  │  spec, builds│  │  multiple     │  │  written      │     │
│  │  operations{}│  │  providers    │  │  Python class │     │
│  │  execute_    │  │  x-aggregates │  │  (debug,      │     │
│  │  operation() │  │  from spec    │  │  legacy)      │     │
│  └──────┬───────┘  └──────┬────────┘  └──────┬────────┘     │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                   │
          └─────────────────┬───────────────────┘
                            ▼
          ┌─────────────────────────────────────────────┐
          │        BaseProvider / CustomClient           │
          │        (httpx async HTTP client)             │
          │                                              │
          │  _prepare_request() → auth headers           │
          │  execute_operation() → HTTP call             │
          │  APIResponse(status_code, data, ...)         │
          └──────────────┬───────────────────────────────┘
                         │
         ┌───────────────┼────────────────────┐
         ▼               ▼                    ▼
 ┌──────────────┐ ┌─────────────┐  ┌──────────────────┐
 │  Docker API  │ │  External   │  │  JSONPlaceholder  │
 │  (external)  │ │  API n      │  │  HTTPBin (debug)  │
 └──────────────┘ └─────────────┘  └──────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File (planned) |
|-----------|----------------|----------------|
| FastAPI App | HTTP entrypoint, middleware stack, lifespan | `main.py` |
| ProviderLoader | Auto-discovers `config/providers/*.yaml`, instantiates providers | `app/providers/provider_loader.py` |
| ProviderRegistry | Central registry for all provider instances | `app/core/client.py` |
| DynamicRouterGenerator | Parses OpenAPI YAML → generates FastAPI routes at startup | `app/core/dynamic_router.py` |
| BaseProvider | Abstract base with `execute_operation()` and `_prepare_request()` | `app/core/client.py` |
| CustomClient | Async HTTP client using httpx | `app/core/client.py` |
| OpenAPIProvider | Reads OpenAPI YAML spec, builds operations dict | `app/providers/openapi_provider.py` |
| CompositeProvider | Orchestrates multiple providers, merges results via `x-aggregates` | `app/providers/composite_provider.py` |
| Settings | Environment-backed configuration via pydantic-settings | `app/core/config.py` |
| Health router | `/api/v1/health` and `/api/v1/health/detailed` endpoints | `app/api/health.py` |
| OpenAPI meta-router | `/api/v1/openapi/*` endpoints for OpenAPI spec introspection | `app/api/openapi.py` |
| Debug router | `/api/v1/debug/*` endpoints (dev-only: HTTPBin, JSONPlaceholder) | `app/api/debug.py` |

## Pattern Overview

**Overall:** Provider-Registry Gateway with Dynamic Routing

**Key Characteristics:**
- API gateway that proxies and aggregates external APIs via YAML-configured providers
- Routes are registered dynamically at startup from OpenAPI spec YAML files — no hardcoded proxy routes
- Three provider types: `openapi` (YAML-driven), `composite` (aggregates other providers), `custom` (manually coded)
- All provider instances managed centrally by `ProviderRegistry`
- Async-first: FastAPI + httpx throughout

## Layers

**Application Layer:**
- Purpose: HTTP entrypoint, middleware, static system endpoints
- Location: `main.py`, `app/api/`
- Contains: FastAPI app instance, lifespan handler, CORS/error middleware, health/debug/OpenAPI routers
- Depends on: Core layer, Providers layer
- Used by: External HTTP clients

**Core Layer:**
- Purpose: Shared infrastructure — config, HTTP client, registry, dynamic router, logging
- Location: `app/core/`
- Contains: `config.py` (Settings), `client.py` (BaseProvider, ProviderRegistry, CustomClient), `dynamic_router.py`, `exceptions.py`, `logging.py`
- Depends on: Config files, external httpx library
- Used by: Application layer, Providers layer

**Providers Layer:**
- Purpose: Provider implementations that know how to call specific external APIs
- Location: `app/providers/`
- Contains: `openapi_provider.py`, `composite_provider.py`, `provider_loader.py`, `debug/`
- Depends on: Core layer (BaseProvider, CustomClient)
- Used by: Application layer via ProviderRegistry

**Config Layer:**
- Purpose: YAML-based configuration for provider definitions and resolved OpenAPI specs
- Location: `config/`
- Contains: `config/providers/*.yaml` (provider definitions), `config/openapi/*.yaml` (resolved OpenAPI specs)
- Depends on: Nothing (static files)
- Used by: ProviderLoader, DynamicRouterGenerator

**Models Layer:**
- Purpose: Pydantic models for requests, responses, and errors
- Location: `app/models/`
- Contains: `APIResponse`, `ErrorResponse`, dynamically generated Pydantic models from OpenAPI schema
- Depends on: Nothing
- Used by: All layers

## Data Flow

### Primary Request Path

1. HTTP request arrives at FastAPI app (`main.py`)
2. Middleware stack processes request: CORS → ErrorHandling → CacheHeaders
3. Dynamically registered route handler matches the path (e.g., `/api/v1/docker/containers`)
4. Route handler calls `provider_registry.get_provider(name)` (`app/core/client.py`)
5. Provider's `execute_operation()` is called with path/query/body params
6. `BaseProvider._prepare_request()` adds auth headers from env mapping
7. `CustomClient` makes async httpx HTTP call to external API
8. Response wrapped in `APIResponse(status_code, data, ...)` and returned

### Startup / Dynamic Route Registration

1. FastAPI lifespan starts (`main.py`)
2. `ProviderLoader` scans `config/providers/*.yaml`, instantiates providers
3. Each provider registered in `ProviderRegistry`
4. `DynamicRouterGenerator` reads `config/openapi/*.yaml` files
5. For each OpenAPI path/method, a FastAPI route is created and attached to the app
6. Dynamic routes available at `/api/v1/{provider}/{...paths}`

### Composite Provider Flow

1. Request arrives at a composite provider route
2. `CompositeProvider.execute_operation()` reads `x-aggregates` from its OpenAPI spec
3. Calls each referenced sub-provider's `execute_operation()` in sequence or parallel
4. Aggregates and merges results into single response
5. Returns combined `APIResponse`

**State Management:**
- No persistent in-process state; `ProviderRegistry` holds provider instances as module-level singleton
- All external state lives in upstream APIs or environment variables

## Key Abstractions

**BaseProvider:**
- Purpose: Abstract base class all providers inherit from; defines `execute_operation()` and `_prepare_request()` contracts
- Examples: `app/providers/openapi_provider.py`, `app/providers/composite_provider.py`
- Pattern: Template Method — subclasses override `execute_operation()`, share `_prepare_request()` auth logic

**ProviderRegistry:**
- Purpose: Central dictionary of named provider instances; lookup by provider name string
- Examples: `app/core/client.py`
- Pattern: Registry / Service Locator

**DynamicRouterGenerator:**
- Purpose: Reads OpenAPI YAML at startup and emits FastAPI `APIRouter` with generated route handlers
- Examples: `app/core/dynamic_router.py`
- Pattern: Code generation at startup from data-driven config

**Provider YAML config:**
- Purpose: Declarative definition of a provider — type, base_url, auth strategy, env_mapping
- Examples: `config/providers/docker.yaml`, `config/providers/composite.yaml`
- Pattern: Data-driven configuration

## Entry Points

**HTTP Server:**
- Location: `main.py`
- Triggers: `uvicorn main:app --reload`
- Responsibilities: Creates FastAPI app, registers middleware, attaches static routers, runs lifespan

**Lifespan (startup):**
- Location: `main.py` (lifespan context manager)
- Triggers: Application startup
- Responsibilities: Calls `initialize_providers()` and `register_dynamic_routes()`

**CLI stub:**
- Location: `main.py` (`if __name__ == "__main__": main()`)
- Triggers: Direct `python main.py` execution (currently placeholder only)
- Responsibilities: Placeholder `print()` — not yet wired to FastAPI

## Architectural Constraints

- **Threading:** Single-threaded async event loop (uvicorn + FastAPI + httpx async)
- **Global state:** `ProviderRegistry` is a module-level singleton in `app/core/client.py`
- **Circular imports:** Not yet applicable (app layer not yet implemented)
- **Dynamic routes:** All proxy routes are generated at startup; adding a new provider requires a YAML file + app restart, not code changes
- **Dev-only features:** Debug providers and `/api/v1/health/detailed` are gated behind a `dev` mode setting

## Anti-Patterns

### Hardcoded proxy route handlers

**What happens:** Writing `@app.get("/api/v1/docker/containers")` directly in application code
**Why it's wrong:** Defeats the purpose of the dynamic router — every new API requires a code change and redeployment
**Do this instead:** Define the provider in `config/providers/docker.yaml` and add its OpenAPI spec to `config/openapi/`; `DynamicRouterGenerator` will create the route automatically

### Using `print()` for logging

**What happens:** Using `print()` statements for debug output
**Why it's wrong:** Violates the structural logging requirement; `print()` output is not machine-parseable and loses context
**Do this instead:** Use the shared `structlog` logger from `app/core/logging.py` with named fields

### Custom provider for standard APIs

**What happens:** Writing a full `custom` provider class for an API that has an OpenAPI spec
**Why it's wrong:** Requires Python code for something that can be driven from YAML
**Do this instead:** Use `openapi` provider type with a resolved YAML spec in `config/openapi/`

## Error Handling

**Strategy:** Centralized via `ErrorHandlingMiddleware` in the middleware stack; all unhandled exceptions caught and formatted as `ErrorResponse`

**Patterns:**
- `ErrorResponse` model for all error payloads (consistent JSON shape)
- `exceptions.py` defines custom exception types for provider errors, config errors
- Provider-level errors from httpx calls wrapped before propagating up

## Cross-Cutting Concerns

**Logging:** Structured logging via `structlog` (`app/core/logging.py`); no `print()` allowed; uniform `apifuse_` prefix on log event names
**Validation:** Pydantic models for all API responses; dynamically generated Pydantic models from OpenAPI JSON Schema for request bodies
**Authentication:** Per-provider auth via `env_mapping` in YAML config; `_prepare_request()` injects auth headers from resolved environment variables

---

*Architecture analysis: 2026-05-12*
