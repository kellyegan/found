"""Tests for AppContainer (core/app_container.py)."""

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtQml import QQmlEngine

from found_app.core.app_settings import AppSettings


@pytest.fixture
def container(qapp):
    from found_app.core.app_container import AppContainer
    return AppContainer()


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


def test_app_container_is_importable():
    from found_app.core.app_container import AppContainer  # noqa: F401


def test_app_container_can_be_instantiated(qapp):
    from found_app.core.app_container import AppContainer
    container = AppContainer()
    assert container is not None


def test_app_container_theme_uses_provided_app_settings(qapp, tmp_path):
    from found_app.core.app_container import AppContainer

    settings_file = tmp_path / "settings.ini"
    settings = AppSettings(QSettings(str(settings_file), QSettings.Format.IniFormat))
    container = AppContainer(settings=settings)

    container._theme.setThemeName("Found")

    restored = AppSettings(QSettings(str(settings_file), QSettings.Format.IniFormat))
    assert restored.get("theme/name") == "Found"


# ---------------------------------------------------------------------------
# Lifecycle methods
# ---------------------------------------------------------------------------


def test_app_container_has_start_method(container):
    assert callable(container.start)


def test_app_container_has_shutdown_method(container):
    assert callable(container.shutdown)


# ---------------------------------------------------------------------------
# wire_engine
# ---------------------------------------------------------------------------


def test_app_container_has_wire_engine_method(container):
    assert callable(container.wire_engine)


def test_wire_engine_registers_all_context_properties(container, qapp):
    engine = QQmlEngine()
    container.wire_engine(engine)
    ctx = engine.rootContext()
    expected_keys = [
        "AppState",
        "BackendConnection",
        "LibraryState",
        "SelectionManager",
        "NavigationManager",
        "CollectionsState",
        "ImportState",
        "FilterState",
        "MetadataState",
        "TagSearchState",
        "TagEditorSearchState",
        "TagEditorState",
        "CollectionEditorState",
        "baseUrl",
        "foundVersion",
        "foundLicense",
    ]
    for key in expected_keys:
        assert ctx.contextProperty(key) is not None, f"Missing context property: {key}"


def test_wire_engine_registers_thumbnail_provider(container, qapp):
    engine = QQmlEngine()
    container.wire_engine(engine)
    assert container.thumbnail_provider is not None


def test_wire_engine_base_url_is_string(container, qapp):
    engine = QQmlEngine()
    container.wire_engine(engine)
    base_url = engine.rootContext().contextProperty("baseUrl")
    assert isinstance(base_url, str)
    assert base_url.startswith("http://")


def test_wire_engine_found_version_is_string(container, qapp):
    engine = QQmlEngine()
    container.wire_engine(engine)
    version = engine.rootContext().contextProperty("foundVersion")
    assert isinstance(version, str)


# ---------------------------------------------------------------------------
# LibraryState relocation callables
# ---------------------------------------------------------------------------


def test_library_state_has_path_patcher_wired(container):
    assert container._library_state._path_patcher is not None


def test_library_state_has_prefix_relocator_wired(container):
    assert container._library_state._prefix_relocator is not None


def test_library_state_has_image_fetcher_wired(container):
    assert container._library_state._image_fetcher is not None


def test_library_state_has_preview_relocator_wired(container):
    assert container._library_state._preview_relocator is not None


def test_library_state_has_batch_verifier_wired(container):
    assert container._library_state._batch_verifier is not None


def test_library_state_has_missing_id_fetcher_wired(container):
    assert container._library_state._missing_id_fetcher is not None
