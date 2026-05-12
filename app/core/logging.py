import logging
import sys

import structlog


def drop_color_message_key(_, __, event_dict: dict) -> dict:
    """Remove uvicorn's redundant 'color_message' key before rendering."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging(app_env: str = "development") -> None:
    """Configure structlog and bridge uvicorn stdlib logs. Must be called once at startup before any log calls."""
    is_dev = app_env == "development"
    log_level = logging.DEBUG if is_dev else logging.INFO

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        drop_color_message_key,
        timestamper,
        structlog.processors.StackInfoRenderer(),
    ]

    if is_dev:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for uvicorn_logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_log = logging.getLogger(uvicorn_logger_name)
        uvicorn_log.handlers.clear()
        uvicorn_log.propagate = True

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.propagate = False
