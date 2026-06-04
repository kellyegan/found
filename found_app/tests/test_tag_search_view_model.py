"""Tests for TagSearchViewModel — Commit 10."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from found_app.tag_search.tag_search_view_model import TagSearchViewModel
from found_app.services.filter_state import FilterStateManager


SAMPLE_TAGS = [
    {"id": "tag-1", "name": "architecture"},
    {"id": "tag-2", "name": "nature"},
    {"id": "tag-3", "name": "portrait"},
]


def _vm(fetcher=None, filter_state=None):
    return TagSearchViewModel(
        tags_fetcher=fetcher or (lambda term: SAMPLE_TAGS),
        filter_state=filter_state,
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


def _search(vm, term="arch"):
    vm.search(term)
    _wait_for_state(vm, "Ready")
    _spin()


def _search_empty(vm, term="arch"):
    vm.search(term)
    _wait_for_state(vm, "Empty")
    _spin()


def _search_error(vm, term="arch"):
    vm.search(term)
    _wait_for_state(vm, "Error")
    _spin()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_suggestions_default_to_empty(qapp):
    assert _vm().suggestions == []


def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_tag_names_defaults_to_empty(qapp):
    assert _vm().tagNames == {}


# ---------------------------------------------------------------------------
# Search — no-op cases
# ---------------------------------------------------------------------------

def test_search_empty_string_is_noop(qapp):
    fetched = []
    vm = _vm(fetcher=lambda t: fetched.append(t) or SAMPLE_TAGS)
    vm.search("")
    _spin()
    assert fetched == []
    assert vm.loadingState == "Idle"


def test_search_whitespace_only_is_noop(qapp):
    fetched = []
    vm = _vm(fetcher=lambda t: fetched.append(t) or SAMPLE_TAGS)
    vm.search("   ")
    _spin()
    assert fetched == []
    assert vm.loadingState == "Idle"


# ---------------------------------------------------------------------------
# Search — success
# ---------------------------------------------------------------------------

def test_search_fetcher_receives_term(qapp):
    received = []
    vm = _vm(fetcher=lambda t: received.append(t) or SAMPLE_TAGS)
    _search(vm, "arch")
    assert received == ["arch"]


def test_search_strips_term_before_fetch(qapp):
    received = []
    vm = _vm(fetcher=lambda t: received.append(t) or SAMPLE_TAGS)
    _search(vm, "  arch  ")
    assert received == ["arch"]


def test_search_populates_suggestions(qapp):
    vm = _vm()
    _search(vm)
    assert len(vm.suggestions) == 3


def test_search_sets_state_to_ready(qapp):
    vm = _vm()
    _search(vm)
    assert vm.loadingState == "Ready"


def test_search_emits_suggestions_changed(qapp):
    vm = _vm()
    received = []
    vm.suggestionsChanged.connect(lambda: received.append(1))
    _search(vm)
    assert len(received) >= 1


# ---------------------------------------------------------------------------
# Search — empty / error
# ---------------------------------------------------------------------------

def test_search_sets_state_to_empty_on_no_results(qapp):
    vm = _vm(fetcher=lambda t: [])
    _search_empty(vm)
    assert vm.loadingState == "Empty"
    assert vm.suggestions == []


def test_search_sets_state_to_error_on_none(qapp):
    vm = _vm(fetcher=lambda t: None)
    _search_error(vm)
    assert vm.loadingState == "Error"


def test_search_sets_state_to_error_on_exception(qapp):
    def bad(t): raise RuntimeError("fail")
    vm = _vm(fetcher=bad)
    _search_error(vm)
    assert vm.loadingState == "Error"


def test_search_clears_suggestions_on_error(qapp):
    vm = _vm()
    _search(vm)
    assert len(vm.suggestions) == 3

    vm2 = _vm(fetcher=lambda t: None)
    _search_error(vm2)
    assert vm2.suggestions == []


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def test_clear_resets_suggestions(qapp):
    vm = _vm()
    _search(vm)
    vm.clear()
    assert vm.suggestions == []


def test_clear_sets_state_to_idle(qapp):
    vm = _vm()
    _search(vm)
    vm.clear()
    assert vm.loadingState == "Idle"


def test_clear_emits_suggestions_changed(qapp):
    vm = _vm()
    _search(vm)
    received = []
    vm.suggestionsChanged.connect(lambda: received.append(1))
    vm.clear()
    assert len(received) == 1


# ---------------------------------------------------------------------------
# selectTag
# ---------------------------------------------------------------------------

def test_select_tag_stores_name_in_tag_names(qapp):
    vm = _vm()
    vm.selectTag("tag-1", "architecture")
    assert vm.tagNames == {"tag-1": "architecture"}


def test_select_tag_emits_tag_names_changed(qapp):
    vm = _vm()
    received = []
    vm.tagNamesChanged.connect(lambda: received.append(1))
    vm.selectTag("tag-1", "architecture")
    assert len(received) == 1


def test_select_tag_calls_filter_state_set_tag_filter(qapp):
    filter_state = FilterStateManager()
    vm = _vm(filter_state=filter_state)
    vm.selectTag("tag-1", "architecture")
    assert filter_state.tagFilters == {"tag-1": "include"}


def test_select_tag_mode_is_include(qapp):
    filter_state = FilterStateManager()
    vm = _vm(filter_state=filter_state)
    vm.selectTag("tag-2", "nature")
    assert filter_state.tagFilters["tag-2"] == "include"


def test_select_tag_clears_suggestions(qapp):
    vm = _vm()
    _search(vm)
    assert len(vm.suggestions) > 0
    vm.selectTag("tag-1", "architecture")
    assert vm.suggestions == []


def test_select_tag_sets_state_to_idle(qapp):
    vm = _vm()
    _search(vm)
    vm.selectTag("tag-1", "architecture")
    assert vm.loadingState == "Idle"


def test_select_tag_noop_without_filter_state(qapp):
    vm = _vm()  # no filter_state
    vm.selectTag("tag-1", "architecture")  # must not raise
    assert vm.tagNames == {"tag-1": "architecture"}


# ---------------------------------------------------------------------------
# Active tag exclusion from suggestions
# ---------------------------------------------------------------------------

def test_suggestions_exclude_active_tag_filters(qapp):
    filter_state = FilterStateManager()
    filter_state.setTagFilter("tag-1", "include")
    vm = _vm(filter_state=filter_state)
    _search(vm)
    ids = [s["id"] for s in vm.suggestions]
    assert "tag-1" not in ids
    assert "tag-2" in ids
    assert "tag-3" in ids


def test_suggestions_include_all_when_no_active_filters(qapp):
    filter_state = FilterStateManager()
    vm = _vm(filter_state=filter_state)
    _search(vm)
    assert len(vm.suggestions) == 3


def test_state_is_empty_when_all_suggestions_filtered_out(qapp):
    filter_state = FilterStateManager()
    for tag in SAMPLE_TAGS:
        filter_state.setTagFilter(tag["id"], "include")
    vm = _vm(filter_state=filter_state)
    vm.search("arch")
    _wait_for_state(vm, "Empty")
    _spin()
    assert vm.loadingState == "Empty"
    assert vm.suggestions == []


# ---------------------------------------------------------------------------
# tagNames cleanup on filter clear
# ---------------------------------------------------------------------------

def test_tag_names_cleaned_when_tag_removed_from_filter(qapp):
    filter_state = FilterStateManager()
    vm = _vm(filter_state=filter_state)
    vm.selectTag("tag-1", "architecture")
    assert "tag-1" in vm.tagNames

    filter_state.setTagFilter("tag-1", "off")
    _spin()
    assert "tag-1" not in vm.tagNames


def test_multiple_tags_can_be_selected(qapp):
    filter_state = FilterStateManager()
    vm = _vm(filter_state=filter_state)
    vm.selectTag("tag-1", "architecture")
    vm.selectTag("tag-2", "nature")
    assert vm.tagNames == {"tag-1": "architecture", "tag-2": "nature"}
    assert filter_state.tagFilters == {"tag-1": "include", "tag-2": "include"}
