import structlog
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

log = structlog.get_logger()


class ErrorHandlingMiddleware:
    """Pure ASGI middleware (not BaseHTTPMiddleware) for reliable exception handling."""

    def __init__(self, app: ASGIApp, app_env: str = "development") -> None:
        self.app = app
        self.is_dev = app_env == "development"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            status_code = getattr(exc, "status_code", 500)
            if self.is_dev:
                error_message = f"{type(exc).__name__}: {exc}"
            else:
                error_message = "Internal server error" if status_code == 500 else str(exc)
            log.error(
                "apifuse_unhandled_exception",
                exc_type=type(exc).__name__,
                status_code=status_code,
                exc_info=exc,
            )
            response = JSONResponse(
                status_code=status_code,
                content={"error": error_message, "status_code": status_code},
            )
            await response(scope, receive, send)
