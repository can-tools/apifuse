"""FOUND-02 — logging tests."""

import logging
from pathlib import Path

import pytest
import structlog
from structlog import stdlib as structlog_stdlib

from app.core.logging import configure_logging


@pytest.fixture(autouse=True)
def apifuse_reset_structlog():
    structlog.reset_defaults()
    yield
    structlog.reset_defaults()


def test_configure_logging_does_not_raise():
    configure_logging("development")
    structlog.reset_defaults()
    configure_logging("production")


def test_configure_logging_production_uses_json_renderer():
    configure_logging("production")
    assert structlog.is_configured()
    assert structlog.get_config()["wrapper_class"] is not None
    fmt = logging.getLogger().handlers[0].formatter
    assert isinstance(fmt, structlog_stdlib.ProcessorFormatter)
    assert any(type(p).__name__ == "JSONRenderer" for p in fmt.processors)
    assert logging.getLogger().level == logging.INFO


def test_no_print_calls_in_source():
    roots = list(Path("app").rglob("*.py")) + [Path("main.py")]
    violations = []
    for path in roots:
        if path.is_file() and "print(" in path.read_text(encoding="utf-8"):
            violations.append(str(path))
    assert violations == [], f"print() found in: {violations}"
