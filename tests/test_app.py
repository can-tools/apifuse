"""FOUND-03 — app + ErrorHandlingMiddleware tests."""

import pytest
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.config import apifuse_settings
from app.core.exceptions import ErrorHandlingMiddleware


async def apifuse_route_always_boom(_):
    raise RuntimeError("boom")


async def apifuse_route_not_found(_):
    exc = Exception("missing")
    exc.status_code = 404  # type: ignore[attr-defined]
    raise exc


def test_middleware_dev_returns_exception_detail():
    """ErrorHandling must live inside Starlette's stack so ServerErrorMiddleware does not reply first."""
    app = Starlette(routes=[Route("/", apifuse_route_always_boom)])
    app.add_middleware(ErrorHandlingMiddleware, app_env="development")
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 500
    body = r.json()
    assert body["status_code"] == 500
    assert "RuntimeError" in body["error"]


def test_middleware_prod_masks_internal_server_error():
    app = Starlette(routes=[Route("/", apifuse_route_always_boom)])
    app.add_middleware(ErrorHandlingMiddleware, app_env="production")
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 500
    assert r.json() == {"error": "Internal server error", "status_code": 500}


def test_middleware_prod_non_500_uses_str_exc():
    app = Starlette(routes=[Route("/", apifuse_route_not_found)])
    app.add_middleware(ErrorHandlingMiddleware, app_env="production")
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 404
    assert r.json()["error"] == "missing"


@pytest.mark.asyncio
async def test_middleware_websocket_scope_propagates():
    async def inner(scope, receive, send):
        raise ValueError("ws boom")

    mw = ErrorHandlingMiddleware(inner, app_env="development")

    async def receive():
        return {"type": "websocket.connect"}

    async def send(_):
        pass

    scope = {"type": "websocket", "path": "/ws", "headers": []}

    with pytest.raises(ValueError, match="ws boom"):
        await mw(scope, receive, send)


@pytest.mark.asyncio
async def test_unknown_route_returns_json_error_envelope(async_client):
    r = await async_client.get("/nonexistent-route-xyz")
    assert r.status_code == 404
    data = r.json()
    assert "error" in data
    assert "status_code" in data
    assert data["status_code"] == 404


@pytest.mark.asyncio
async def test_cors_headers_on_options_request(async_client):
    r = await async_client.options(
        "/",
        headers={"Origin": "http://localhost:3000"},
    )
    assert r.headers.get("access-control-allow-origin") == "*"


@pytest.mark.asyncio
async def test_app_starts_and_root_returns_response(async_client):
    r = await async_client.get("/")
    assert r is not None


@pytest.mark.asyncio
async def test_openapi_json_version_matches_settings(async_client):
    r = await async_client.get("/openapi.json")
    assert r.status_code == 200
    payload = r.json()
    assert payload["info"]["version"] == apifuse_settings.app_version
