"""FOUND-01 — configuration tests."""

import os

import pytest

from app.core.config import ApifuseSettings


def test_settings_load_with_no_env_file():
    result = ApifuseSettings()
    assert isinstance(result, ApifuseSettings)


def test_settings_default_app_env():
    assert ApifuseSettings().app_env == "development"


def test_settings_default_app_name():
    assert ApifuseSettings().app_name == "apifuse"


def test_settings_default_app_version():
    assert ApifuseSettings().app_version == "0.1.0"


def test_settings_is_dev_true_in_development():
    assert ApifuseSettings().is_dev is True


def test_settings_extra_env_vars_ignored():
    key = "SOME_UNKNOWN_VAR_XYZ"
    old = os.environ.get(key)
    try:
        os.environ[key] = "1"
        s = ApifuseSettings()
        assert isinstance(s, ApifuseSettings)
    finally:
        if old is None:
            del os.environ[key]
        else:
            os.environ[key] = old
