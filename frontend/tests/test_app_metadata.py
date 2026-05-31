"""Tests for app metadata reading via importlib.metadata."""

import pytest


def test_get_app_metadata_returns_version():
    from frontend.version import get_app_metadata
    metadata = get_app_metadata()
    assert isinstance(metadata["version"], str)
    assert len(metadata["version"]) > 0


def test_get_app_metadata_returns_license():
    from frontend.version import get_app_metadata
    metadata = get_app_metadata()
    assert isinstance(metadata["license"], str)
    assert len(metadata["license"]) > 0


def test_get_app_metadata_version_format():
    from frontend.version import get_app_metadata
    metadata = get_app_metadata()
    parts = metadata["version"].split(".")
    assert len(parts) >= 2
