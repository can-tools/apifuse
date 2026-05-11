# ApiFuse — Plan projektu

## Kontekst

ApiFuse to API gateway zbudowany na FastAPI, który:
- dynamicznie generuje endpointy z plików OpenAPI YAML
- agreguje wielu zewnętrznych providerów (Docker, composite i inne)
- wspiera trzy typy providerów: `openapi`, `composite`, `custom`

---

## Fazy

### Faza 1 — Fundament
- [ ] Inicjalizacja projektu `apifuse` (pyproject.toml, struktura folderów)
- [ ] Konfiguracja środowiska (uv, zależności, .env)
- [ ] Bazowa aplikacja FastAPI z lifespan
- [ ] Middleware: CORS, error handling
- [ ] System logowania (strukturalne logi)
- [ ] Modele bazowe: `APIResponse`, `ErrorResponse`

### Faza 2 — System providerów
- [ ] `BaseProvider` — abstrakcyjna klasa bazowa
- [ ] `ProviderRegistry` — centralny rejestr providerów
- [ ] `CustomClient` — async HTTP client (httpx)
- [ ] `ProviderLoader` — autodiscovery z `config/providers/*.yaml`
- [ ] Obsługa typów: `openapi`, `composite`, `custom`
- [ ] Mapowanie zmiennych środowiskowych (`env_mapping`)

### Faza 3 — Dynamic Router
- [ ] `DynamicRouterGenerator` — generowanie FastAPI routes z OpenAPI spec
- [ ] Obsługa parametrów: path, query, body
- [ ] Generowanie dynamicznych modeli Pydantic z schematu
- [ ] Mapowanie odpowiedzi (success + error codes)
- [ ] Integracja ze Swagger UI

### Faza 4 — Providery produkcyjne
- [ ] `OpenAPIProvider` — provider oparty na YAML spec
- [ ] `CompositeProvider` — agregacja wielu providerów (`x-aggregates`)
- [ ] Konfiguracja Docker (`config/openapi/docker-resolved.yaml`)
- [ ] Struktura gotowa na dodawanie kolejnych konfiguracji OpenAPI

### Faza 5 — Endpointy systemowe
- [ ] `GET /api/v1/` — info o API
- [ ] `GET /api/v1/health` — basic health check
- [ ] `GET /api/v1/health/detailed` — szczegółowy status (tylko dev)
- [ ] Debug providers: HTTPBin, JSONPlaceholder (tylko dev)

### Faza 6 — Testy
- [ ] Konfiguracja pytest + conftest
- [ ] Testy unit: config, provider registry, dynamic router
- [ ] Testy integracyjne: Docker i inne providery (z mockowanym httpx)

### Faza 7 — Narzędzia i dokumentacja
- [ ] Skrypty: `resolve_openapi.py`, `validate_openapi.py`
- [ ] Makefile / skrypty dev/prod
- [ ] Aktualizacja `docs/architecture.md`
- [ ] `API_ENDPOINTS.md` — lista dynamicznych endpointów

---

## Struktura docelowa

```
apifuse/
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── openapi.py
│   │   └── debug.py
│   ├── core/
│   │   ├── client.py        # BaseProvider, ProviderRegistry, CustomClient
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   ├── dynamic_router.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── models/
│   └── providers/
│       ├── openapi_provider.py
│       ├── composite_provider.py
│       ├── provider_loader.py
│       └── debug/
├── config/
│   ├── providers/           # YAML definicje providerów
│   └── openapi/             # Rozwiązane specyfikacje OpenAPI
├── docs/
│   ├── plan.md
│   └── architecture.md
├── tests/
├── scripts/
├── main.py
└── pyproject.toml
```

---

## Cele jakościowe

| Obszar | Założenie |
|---|---|
| Debug providers | jeden moduł `providers/debug/` |
| Logowanie | wyłącznie strukturalny logger, zero `print()` |
| Nazewnictwo | jednolity prefix `apifuse_` |
| Legacy endpoints | brak martwego kodu od startu |
| Testy | wspólny conftest, jasne fixtures, brak duplikatów |
