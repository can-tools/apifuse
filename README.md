# ApiFuse

API gateway zbudowany na FastAPI z dynamicznym generowaniem endpointów z OpenAPI spec.

## Setup

### 1. Zainstaluj uv

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Zainicjalizuj projekt

```bash
uv init --no-readme
uv python pin 3.12
```

### 3. Zainstaluj zależności

```bash
uv add fastapi uvicorn httpx pydantic-settings pyyaml structlog python-dotenv
```

```bash
uv add --dev pytest pytest-asyncio httpx pytest-playwright
```

### 4. Sync środowiska

```bash
uv sync
```

### 5. Uruchom

```bash
uv run uvicorn main:app --reload
```
