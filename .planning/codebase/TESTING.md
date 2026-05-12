# Testing Patterns

**Analysis Date:** 2026-05-12

> **Note:** This project is in early initialization. No test files exist yet (`tests/`
> directory not created, no `conftest.py`). Patterns below are derived from installed
> dev dependencies in `pyproject.toml` and the testing plan in `docs/plan.md` (Phase 6).
> This document captures the intended testing setup to guide implementation.

## Test Framework

**Runner:**
- `pytest` 9.0.3
- Config: `pyproject.toml` `[tool.pytest.ini_options]` section (not yet added)

**Async support:**
- `pytest-asyncio` 1.3.0 — required for all `async def` test functions
- Mode should be set to `asyncio_mode = "auto"` in pytest config to avoid per-test decoration

**E2E / Browser:**
- `pytest-playwright` 0.7.2 — installed but no E2E tests planned in early phases

**HTTP testing:**
- `httpx` 0.28.1 — listed in both runtime and dev dependencies
- FastAPI's `TestClient` (sync) or `httpx.AsyncClient` with `ASGITransport` for async integration tests

**Assertion Library:**
- Built-in `pytest` assertions (no additional library)

**Run Commands:**
```bash
uv run pytest                          # Run all tests
uv run pytest -v                       # Verbose output
uv run pytest tests/unit/              # Unit tests only
uv run pytest tests/integration/       # Integration tests only
uv run pytest --cov=app --cov-report=term-missing  # Coverage (requires pytest-cov)
uv run pytest -x                       # Stop on first failure
uv run pytest -k "test_provider"       # Run tests matching pattern
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root (not co-located with source)
- Mirrors `app/` package structure inside `tests/`

**Target structure (from `docs/plan.md`):**
```
tests/
├── conftest.py              # Shared fixtures, app setup
├── unit/
│   ├── test_config.py       # Settings, env loading
│   ├── test_provider_registry.py
│   └── test_dynamic_router.py
└── integration/
    ├── test_health.py       # /api/v1/health endpoints
    ├── test_docker_provider.py   # with mocked httpx
    └── test_composite_provider.py
```

**Naming:**
- Test files: `test_<module_name>.py`
- Test functions: `test_<behavior_description>` in snake_case
- Test classes: `Test<ComponentName>` (optional, for grouping related tests)

## Test Structure

**Suite Organization:**
```python
# tests/unit/test_provider_registry.py
import pytest
from app.core.client import ProviderRegistry

class TestProviderRegistry:
    def test_register_provider_adds_to_registry(self):
        registry = ProviderRegistry()
        # ...

    def test_get_unknown_provider_raises(self):
        registry = ProviderRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

# Async test example
@pytest.mark.asyncio
async def test_execute_operation_returns_api_response(mock_provider):
    response = await mock_provider.execute_operation("list_containers", {})
    assert response.status_code == 200
```

**Patterns:**
- Arrange / Act / Assert structure (no special markers needed)
- One behavior per test function — no multi-assertion omnibus tests
- `conftest.py` holds all shared fixtures; no fixture duplication across test files (quality goal from `docs/plan.md`)

## Mocking

**Framework:**
- `unittest.mock` from stdlib (`MagicMock`, `AsyncMock`, `patch`)
- `httpx` mock transport for HTTP interception (no external mock server needed)

**HTTP mocking pattern (planned):**
```python
import httpx
import pytest

@pytest.fixture
def mock_http_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"containers": []})
    return httpx.MockTransport(handler)

@pytest.fixture
async def provider_with_mock_http(mock_http_transport):
    async with httpx.AsyncClient(transport=mock_http_transport) as client:
        yield client
```

**Provider mocking:**
```python
from unittest.mock import AsyncMock, patch

@patch("app.providers.openapi_provider.OpenAPIProvider.execute_operation")
async def test_route_calls_provider(mock_execute):
    mock_execute.return_value = APIResponse(status_code=200, data={})
    # ...
```

**What to mock:**
- All outbound HTTP calls via `httpx.AsyncClient` — use `httpx.MockTransport`
- External service dependencies (Docker daemon, remote APIs)
- File system reads for YAML configs in unit tests (use `tmp_path` fixture or in-memory dicts)

**What NOT to mock:**
- Internal business logic (provider registry, routing logic)
- Pydantic model validation
- FastAPI dependency injection wiring in integration tests

## Fixtures and Factories

**Shared fixtures in `conftest.py`:**
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app  # when app/ is implemented

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def async_client():
    # For async route testing
    from httpx import AsyncClient, ASGITransport
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

@pytest.fixture
def sample_provider_config():
    return {
        "id": "test_provider",
        "type": "openapi",
        "base_url": "http://localhost:9999",
        "spec": "config/openapi/test-resolved.yaml",
    }
```

**Location:**
- Shared fixtures: `tests/conftest.py` (one conftest — no duplicates per quality goals)
- YAML test fixtures: `tests/fixtures/` (for sample provider configs, OpenAPI specs)

## Coverage

**Requirements:** Not yet enforced (no `pytest-cov` in `pyproject.toml`)

**Planned addition:**
```toml
# pyproject.toml
[dependency-groups]
dev = [
    "pytest-cov>=6.0.0",
]

[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing"
```

**View Coverage:**
```bash
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Types

**Unit Tests (`tests/unit/`):**
- Scope: Individual classes and functions in isolation
- Covers: `Settings` loading, `ProviderRegistry` operations, `DynamicRouterGenerator` route building
- No HTTP calls, no file I/O — all dependencies mocked or injected
- Fast: < 1s per test

**Integration Tests (`tests/integration/`):**
- Scope: Full FastAPI request/response cycle using `TestClient` or `AsyncClient`
- Covers: Health endpoints, dynamic routes generated from OpenAPI spec, provider orchestration
- HTTP to external services mocked via `httpx.MockTransport`
- Tests YAML config loading with real files (or `tmp_path` copies)

**E2E Tests:**
- `pytest-playwright` 0.7.2 installed
- Scope: Browser-driven testing of any web UI (not yet planned)
- Not applicable to current API-gateway use cases unless an admin UI is added

## Pytest Configuration (Recommended)

Add to `pyproject.toml` when tests are implemented:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
```

## Common Patterns

**Async Testing:**
```python
import pytest

# With asyncio_mode = "auto" in pyproject.toml, no decorator needed:
async def test_provider_executes_async():
    provider = OpenAPIProvider(config)
    result = await provider.execute_operation("list", {})
    assert result.status_code == 200

# Otherwise use explicit mark:
@pytest.mark.asyncio
async def test_provider_executes_async():
    ...
```

**Error Testing:**
```python
import pytest
from fastapi.testclient import TestClient

def test_unknown_provider_returns_404(client: TestClient):
    response = client.get("/api/v1/nonexistent/endpoint")
    assert response.status_code == 404

def test_upstream_error_returns_502(client: TestClient, mock_http_transport):
    # Mock transport returns 500
    response = client.get("/api/v1/docker/containers/json")
    assert response.status_code == 502

async def test_invalid_config_raises_value_error():
    with pytest.raises(ValueError, match="provider type"):
        ProviderLoader.load({"type": "unknown"})
```

**YAML Config Testing:**
```python
def test_provider_loader_discovers_yaml(tmp_path):
    config_dir = tmp_path / "providers"
    config_dir.mkdir()
    (config_dir / "test.yaml").write_text("id: test\ntype: custom\n")

    providers = ProviderLoader.load_all(config_dir)
    assert len(providers) == 1
    assert providers[0].id == "test"
```

---

*Testing analysis: 2026-05-12*
