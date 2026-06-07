"""Tests for the ConfirmDialog QML component.

Covers:
- ConfirmDialog.qml exists and loads cleanly
- Exposes open, message, confirmLabel, cancelLabel, checkboxLabel, checkboxChecked
- Exposes confirmed and cancelled signals
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent

import found_app
from found_app.theme.theme import ThemeManager

QML_DIR = Path(found_app.__file__).parent / "qml"


@pytest.fixture
def engine(qapp):
    """Minimal engine — ConfirmDialog only depends on Theme."""
    theme = ThemeManager()
    e = QQmlEngine()
    e.rootContext().setContextProperty("Theme", theme)
    theme.setParent(e)
    yield e
    e.clearComponentCache()


def load_component(engine, filename: str):
    path = QML_DIR / filename
    assert path.exists(), f"{filename} not found at {path}"
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
    errors = [err.toString() for err in component.errors()]
    assert not errors, f"{filename} load errors: {errors}"
    assert component.status() == QQmlComponent.Status.Ready, (
        f"{filename} status: {component.status()}"
    )
    obj = component.create(engine.rootContext())
    assert obj is not None, f"{filename} create() returned None"
    obj.setParent(engine)
    return obj


# ---------------------------------------------------------------------------
# Loads
# ---------------------------------------------------------------------------


def test_confirm_dialog_qml_exists():
    assert (QML_DIR / "components/ConfirmDialog.qml").exists()


def test_confirm_dialog_loads(engine):
    load_component(engine, "components/ConfirmDialog.qml")


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_open_defaults_to_false(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    assert obj.property("open") is False


def test_open_is_writable(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_message_defaults_to_empty(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    assert obj.property("message") == ""


def test_message_is_writable(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    obj.setProperty("message", "Are you sure you want to remove photo.jpg from the library?")
    assert obj.property("message") == "Are you sure you want to remove photo.jpg from the library?"


def test_confirm_label_defaults_to_confirm(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    assert obj.property("confirmLabel") == "Confirm"


def test_confirm_label_is_writable(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    obj.setProperty("confirmLabel", "Remove")
    assert obj.property("confirmLabel") == "Remove"


def test_cancel_label_defaults_to_cancel(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    assert obj.property("cancelLabel") == "Cancel"


def test_checkbox_label_defaults_to_empty(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    assert obj.property("checkboxLabel") == ""


def test_checkbox_label_is_writable(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    obj.setProperty("checkboxLabel", "Also remove from library")
    assert obj.property("checkboxLabel") == "Also remove from library"


def test_checkbox_checked_defaults_to_false(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    assert obj.property("checkboxChecked") is False


def test_checkbox_checked_is_writable(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    obj.setProperty("checkboxChecked", True)
    assert obj.property("checkboxChecked") is True


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


def test_has_confirmed_signal(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    received = []
    obj.confirmed.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_has_cancelled_signal(engine):
    obj = load_component(engine, "components/ConfirmDialog.qml")
    received = []
    obj.cancelled.connect(lambda: received.append(1))
    assert isinstance(received, list)
