from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.config import apifuse_settings
from app.core.exceptions import ErrorHandlingMiddleware
from app.core.logging import configure_logging

log = structlog.get_logger()


@asynccontextmanager
async def apifuse_lifespan(app: FastAPI):
    configure_logging(apifuse_settings.app_env)
    log.info(
        "apifuse_startup",
        app_env=apifuse_settings.app_env,
        version=apifuse_settings.app_version,
    )
    # Phase 2 hook: initialize_providers() goes here
    yield
    log.info("apifuse_shutdown")


app = FastAPI(
    title=apifuse_settings.app_name,
    version=apifuse_settings.app_version,
    lifespan=apifuse_lifespan,
)


@app.exception_handler(StarletteHTTPException)
async def apifuse_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": message, "status_code": exc.status_code},
    )


# Innermost (added first): error handling
app.add_middleware(ErrorHandlingMiddleware, app_env=apifuse_settings.app_env)

# Outermost (added last): CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
