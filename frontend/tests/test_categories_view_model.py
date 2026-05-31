"""Tests for CategoriesViewModel — Commit 4."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from frontend.categories.categories_view_model import CategoriesViewModel


SAMPLE_CATEGORIES = [
    {"id": "cat-1", "name": "Architecture", "description": ""},
    {"id": "cat-2", "name": "Nature", "description": ""},
    {"id": "cat-3", "name": "Portrait", "description": ""},
]


def _vm(fetcher=None):
    return CategoriesViewModel(
        categories_fetcher=fetcher or (lambda: SAMPLE_CATEGORIES)
    )


def _wait_for_state(vm, target: str, timeout_ms: int = 2000) -> None:
    if vm.loadingState == target:
        return
    loop = QEventLoop()

    def check(name: str):
        if name == target:
            loop.quit()

    vm.loadingStateChanged.connect(check)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


def _spin(ms: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _load(vm):
    vm.load()
    _wait_for_state(vm, "Ready")
    _spin()


def _load_error(vm):
    vm.load()
    _wait_for_state(vm, "Error")
    _spin()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_categories_defaults_to_empty(qapp):
    assert _vm().categories == []


def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_active_filters_empty_when_no_categories_loaded(qapp):
    assert _vm().activeFilters == {}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def test_load_populates_categories(qapp):
    vm = _vm()
    _load(vm)
    assert len(vm.categories) == 3


def test_load_sets_state_to_ready(qapp):
    vm = _vm()
    _load(vm)
    assert vm.loadingState == "Ready"


def test_load_sets_state_to_error_on_failure(qapp):
    vm = _vm(fetcher=lambda: None)
    _load_error(vm)
    assert vm.loadingState == "Error"


def test_categories_sorted_alphabetically(qapp):
    vm = _vm()
    _load(vm)
    names = [c["name"] for c in vm.categories]
    assert names == sorted(names)


def test_categories_include_filter_state(qapp):
    vm = _vm()
    _load(vm)
    for cat in vm.categories:
        assert "filterState" in cat
        assert cat["filterState"] == "off"


# ---------------------------------------------------------------------------
# Tri-state cycling
# ---------------------------------------------------------------------------

def test_cycle_filter_off_to_include(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-1")
    cat = next(c for c in vm.categories if c["id"] == "cat-1")
    assert cat["filterState"] == "include"


def test_cycle_filter_include_to_exclude(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-1")
    vm.cycleFilter("cat-1")
    cat = next(c for c in vm.categories if c["id"] == "cat-1")
    assert cat["filterState"] == "exclude"


def test_cycle_filter_exclude_to_off(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-1")
    vm.cycleFilter("cat-1")
    vm.cycleFilter("cat-1")
    cat = next(c for c in vm.categories if c["id"] == "cat-1")
    assert cat["filterState"] == "off"


def test_cycle_filter_emits_filter_changed(qapp):
    vm = _vm()
    _load(vm)
    received = []
    vm.filterChanged.connect(lambda: received.append(1))
    vm.cycleFilter("cat-1")
    assert len(received) == 1


def test_cycle_filter_emits_categories_changed(qapp):
    vm = _vm()
    _load(vm)
    received = []
    vm.categoriesChanged.connect(lambda: received.append(1))
    vm.cycleFilter("cat-1")
    assert len(received) == 1


# ---------------------------------------------------------------------------
# Active filters
# ---------------------------------------------------------------------------

def test_active_filters_empty_when_all_off(qapp):
    vm = _vm()
    _load(vm)
    assert vm.activeFilters == {}


def test_active_filters_contains_include(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-1")
    assert vm.activeFilters == {"cat-1": "include"}


def test_active_filters_contains_exclude(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-2")
    vm.cycleFilter("cat-2")
    assert vm.activeFilters == {"cat-2": "exclude"}


def test_active_filters_excludes_off_categories(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-1")           # include
    vm.cycleFilter("cat-2")           # include
    vm.cycleFilter("cat-2")           # exclude
    assert "cat-3" not in vm.activeFilters
    assert vm.activeFilters["cat-1"] == "include"
    assert vm.activeFilters["cat-2"] == "exclude"


# ---------------------------------------------------------------------------
# Clear filters
# ---------------------------------------------------------------------------

def test_clear_filters_resets_all_to_off(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-1")
    vm.cycleFilter("cat-2")
    vm.clearFilters()
    assert vm.activeFilters == {}
    for cat in vm.categories:
        assert cat["filterState"] == "off"


def test_clear_filters_emits_filter_changed(qapp):
    vm = _vm()
    _load(vm)
    vm.cycleFilter("cat-1")
    received = []
    vm.filterChanged.connect(lambda: received.append(1))
    vm.clearFilters()
    assert len(received) == 1
