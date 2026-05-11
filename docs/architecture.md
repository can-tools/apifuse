# ApiFuse — Schemat architektury

## Diagram blokowy

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT                                 │
│                    (HTTP Request)                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI (main.py)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   MIDDLEWARE STACK                       │   │
│  │  CORSMiddleware → ErrorHandlingMiddleware → CacheHeaders │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Stałe endpointy:                                               │
│  GET /api/v1/                → info o API                      │
│  GET /api/v1/health          → basic health check              │
│  GET /api/v1/health/detailed → szczegółowy status              │
│  /api/v1/openapi/*           → OpenAPI meta-router             │
│  /api/v1/debug/*             → debug providers (tylko dev)     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
              ┌───────────┴────────────┐
              │    STARTUP (lifespan)  │
              │  1. initialize_providers()
              │  2. register_dynamic_routes()
              └───────────┬────────────┘
                          │
          ┌───────────────┼───────────────────┐
          ▼               ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────────┐
│ PROVIDER     │  │ DYNAMIC      │  │ CONFIG             │
│ LOADER       │  │ ROUTER       │  │                    │
│              │  │ GENERATOR    │  │ config/providers/  │
│ config/      │  │ Czyta OpenAPI│  │   docker.yaml      │
│ providers/   │  │ spec → tworzy│  │   composite.yaml   │
│ *.yaml       │  │ FastAPI      │  │   *.yaml           │
│              │  │ routes       │  │                    │
│ Rejestruje   │  │ dynamicznie  │  │ config/openapi/    │
│ providery    │  │              │  │   docker-          │
│ w registry   │  │ /api/v1/     │  │     resolved.yaml  │
│              │  │  {provider}/ │  │   composite-       │
│              │  │  {...paths}  │  │     resolved.yaml  │
└──────┬───────┘  └──────────────┘  │   *.yaml           │
       │                            └────────────────────┘
       ▼
┌──────────────────────────────────────────────────────────────┐
│                    PROVIDER REGISTRY                         │
│              (ProviderRegistry w client.py)                  │
│                                                              │
│   ┌────────────────┐  ┌───────────────┐  ┌───────────────┐  │
│   │ OpenAPI        │  │ Composite     │  │ Custom        │  │
│   │ Provider       │  │ Provider      │  │ Provider      │  │
│   │                │  │               │  │               │  │
│   │ - Wczytuje     │  │ - Agreguje    │  │ - Ręcznie     │  │
│   │   YAML spec    │  │   wiele       │  │   napisana    │  │
│   │ - Buduje       │  │   providerów  │  │   klasa       │  │
│   │   operations{} │  │ - x-aggregates│  │ (np. debug,   │  │
│   │ - execute_     │  │   z OpenAPI   │  │  legacy       │  │
│   │   operation()  │  │   spec        │  │  providers)   │  │
│   └───────┬────────┘  └──────┬────────┘  └──────┬────────┘  │
└───────────┼─────────────────┼─────────────────── ┼──────────┘
            │                 │                     │
            └────────────────┬┘                     │
                             ▼                      ▼
            ┌────────────────────────────────────────────────┐
            │           BaseProvider / CustomClient           │
            │           (httpx async HTTP client)             │
            │                                                 │
            │  _prepare_request() → auth headers              │
            │  execute_operation() → HTTP call                │
            │  APIResponse(status_code, data, ...)            │
            └──────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼────────────────────┐
           ▼               ▼                    ▼
   ┌──────────────┐ ┌─────────────┐  ┌──────────────────┐
   │ Docker API   │ │ External    │  │ JSONPlaceholder  │
   │ (external)   │ │ API n       │  │ HTTPBin (debug)  │
   └──────────────┘ └─────────────┘  └──────────────────┘
```

## Kluczowe przepływy

| Faza | Co się dzieje |
|---|---|
| **Startup** | `provider_loader` skanuje `config/providers/*.yaml`, tworzy instancje providerów, rejestruje w `provider_registry` |
| **Dynamic routing** | `DynamicRouterGenerator` czyta pliki OpenAPI YAML → generuje FastAPI routes automatycznie → dołącza do aplikacji |
| **Request** | Middleware → route handler → `provider_registry` → `BaseProvider` → HTTP call → `APIResponse` |
| **Composite** | Specjalny provider który wywołuje inne providery i agreguje wyniki z `x-aggregates` w YAML spec |

## Typy providerów

| Typ | Opis | Przykłady |
|---|---|---|
| `openapi` | Generyczny, napędzany YAML spec | Docker, dowolne API z OpenAPI spec |
| `composite` | Orkiestruje wiele providerów, zwraca zagregowaną odpowiedź | composite |
| `custom` | Ręcznie napisana klasa Python | HTTPBin, JSONPlaceholder (debug) |
