"""
Tests for ThumbnailGridModel — Commit 2.

Covers:
- Initial rowCount is 0
- appendPage adds items and updates rowCount
- data() returns expected role values
- thumbnailUrl role returns image://thumbnails/<id> URI
- hasMore and cursor are updated after appendPage
- appendPage on empty list is a no-op
- clear() resets all state
- countChanged signal fires after appendPage
- hasMoreChanged signal fires after appendPage
"""

import pytest
from PySide6.QtCore import QModelIndex, Qt

from found_app.models.thumbnail_grid_model import ThumbnailGridModel


SAMPLE_ITEMS = [
    {"id": "aaaa-1111", "filename": "dog.jpg", "width": 200, "height": 150, "file_status": "available"},
    {"id": "bbbb-2222", "filename": "cat.jpg", "width": 100, "height": 100, "file_status": "missing"},
]


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_row_count_is_zero(qapp):
    model = ThumbnailGridModel()
    assert model.rowCount(QModelIndex()) == 0


def test_initial_has_more_is_false(qapp):
    model = ThumbnailGridModel()
    assert model.hasMore is False


def test_initial_cursor_is_empty(qapp):
    model = ThumbnailGridModel()
    assert model.cursor == ""


def test_initial_count_property_is_zero(qapp):
    model = ThumbnailGridModel()
    assert model.count == 0


# ---------------------------------------------------------------------------
# appendPage
# ---------------------------------------------------------------------------


def test_append_page_increases_row_count(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok1", True)
    assert model.rowCount(QModelIndex()) == 2


def test_append_page_empty_list_is_noop(qapp):
    model = ThumbnailGridModel()
    model.appendPage([], None, False)
    assert model.rowCount(QModelIndex()) == 0


def test_append_page_accumulates_across_calls(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok1", True)
    model.appendPage(SAMPLE_ITEMS, "tok2", False)
    assert model.rowCount(QModelIndex()) == 4


def test_append_page_updates_has_more(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok1", True)
    assert model.hasMore is True


def test_append_page_updates_cursor(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok99", False)
    assert model.cursor == "tok99"


def test_append_page_cursor_empty_string_when_none(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert model.cursor == ""


# ---------------------------------------------------------------------------
# data() roles
# ---------------------------------------------------------------------------


def _index(model, row):
    return model.index(row, 0, QModelIndex())


def test_data_image_id_role(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    val = model.data(_index(model, 0), ThumbnailGridModel.IdRole)
    assert val == "aaaa-1111"


def test_data_filename_role(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    val = model.data(_index(model, 0), ThumbnailGridModel.FilenameRole)
    assert val == "dog.jpg"


def test_data_thumbnail_url_uses_image_provider_scheme(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    val = model.data(_index(model, 0), ThumbnailGridModel.ThumbnailUrlRole)
    assert val == "image://thumbnails/aaaa-1111"


def test_data_file_status_role(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    missing_val = model.data(_index(model, 1), ThumbnailGridModel.FileStatusRole)
    assert missing_val == "missing"


def test_data_returns_none_for_invalid_index(qapp):
    model = ThumbnailGridModel()
    val = model.data(_index(model, 99), ThumbnailGridModel.IdRole)
    assert val is None


# ---------------------------------------------------------------------------
# roleNames
# ---------------------------------------------------------------------------


def test_role_names_include_expected_keys(qapp):
    model = ThumbnailGridModel()
    names = model.roleNames()
    values = list(names.values())
    assert b"imageId" in values
    assert b"thumbnailUrl" in values
    assert b"fileStatus" in values
    assert b"filename" in values


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------


def test_clear_resets_row_count(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok1", True)
    model.clear()
    assert model.rowCount(QModelIndex()) == 0


def test_clear_resets_cursor(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok1", True)
    model.clear()
    assert model.cursor == ""


def test_clear_resets_has_more(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok1", True)
    model.clear()
    assert model.hasMore is False


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


def test_count_changed_signal_fires_after_append(qapp):
    model = ThumbnailGridModel()
    received = []
    model.countChanged.connect(received.append)
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert 2 in received


def test_has_more_changed_signal_fires_after_append(qapp):
    model = ThumbnailGridModel()
    received = []
    model.hasMoreChanged.connect(received.append)
    model.appendPage(SAMPLE_ITEMS, "tok", True)
    assert True in received


def test_count_changed_signal_fires_after_clear(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    received = []
    model.countChanged.connect(received.append)
    model.clear()
    assert 0 in received


# ---------------------------------------------------------------------------
# allIds
# ---------------------------------------------------------------------------


def test_all_ids_initially_empty(qapp):
    model = ThumbnailGridModel()
    assert model.allIds == []


def test_all_ids_returns_ids_in_order(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert model.allIds == ["aaaa-1111", "bbbb-2222"]


def test_all_ids_updates_after_second_page(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok", True)
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert model.allIds == ["aaaa-1111", "bbbb-2222", "aaaa-1111", "bbbb-2222"]


def test_all_ids_empty_after_clear(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    model.clear()
    assert model.allIds == []


# ---------------------------------------------------------------------------
# filenameForId
# ---------------------------------------------------------------------------


def test_filename_for_id_returns_matching_filename(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert model.filenameForId("bbbb-2222") == "cat.jpg"


def test_filename_for_id_returns_empty_string_when_not_found(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert model.filenameForId("nope") == ""


# ---------------------------------------------------------------------------
# missingCount
# ---------------------------------------------------------------------------


def test_missing_count_defaults_to_zero(qapp):
    model = ThumbnailGridModel()
    assert model.missingCount == 0


def test_missing_count_counts_missing_items(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)  # one "missing" in SAMPLE_ITEMS
    assert model.missingCount == 1


def test_missing_count_accumulates_across_pages(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, "tok", True)
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert model.missingCount == 2


def test_missing_count_zero_when_no_missing(qapp):
    model = ThumbnailGridModel()
    available_only = [{"id": "x-1", "filename": "x.jpg", "file_status": "available"}]
    model.appendPage(available_only, None, False)
    assert model.missingCount == 0


def test_missing_count_resets_on_clear(qapp):
    model = ThumbnailGridModel()
    model.appendPage(SAMPLE_ITEMS, None, False)
    model.clear()
    assert model.missingCount == 0


def test_missing_count_changed_signal_fires(qapp):
    model = ThumbnailGridModel()
    received = []
    model.missingCountChanged.connect(received.append)
    model.appendPage(SAMPLE_ITEMS, None, False)
    assert 1 in received


# ---------------------------------------------------------------------------
# updateItemStatus
# ---------------------------------------------------------------------------


def test_update_item_status_changes_stored_value(qapp):
    model = ThumbnailGridModel()
    model.appendPage([{"id": "aaa-111", "file_status": "available"}], None, False)
    model.updateItemStatus("aaa-111", "missing")
    idx = model.index(0, 0)
    assert model.data(idx, ThumbnailGridModel.FileStatusRole) == "missing"


def test_update_item_status_available_to_missing_increases_count(qapp):
    model = ThumbnailGridModel()
    model.appendPage([{"id": "aaa-111", "file_status": "available"}], None, False)
    assert model.missingCount == 0
    model.updateItemStatus("aaa-111", "missing")
    assert model.missingCount == 1


def test_update_item_status_missing_to_available_decreases_count(qapp):
    model = ThumbnailGridModel()
    model.appendPage([{"id": "aaa-111", "file_status": "missing"}], None, False)
    assert model.missingCount == 1
    model.updateItemStatus("aaa-111", "available")
    assert model.missingCount == 0


def test_update_item_status_no_op_for_unknown_id(qapp):
    model = ThumbnailGridModel()
    model.appendPage([{"id": "aaa-111", "file_status": "available"}], None, False)
    model.updateItemStatus("not-in-model", "missing")
    assert model.missingCount == 0


def test_update_item_status_same_status_no_count_change(qapp):
    model = ThumbnailGridModel()
    model.appendPage([{"id": "aaa-111", "file_status": "available"}], None, False)
    model.updateItemStatus("aaa-111", "available")
    assert model.missingCount == 0


def test_update_item_status_emits_missing_count_changed(qapp):
    model = ThumbnailGridModel()
    model.appendPage([{"id": "aaa-111", "file_status": "available"}], None, False)
    received = []
    model.missingCountChanged.connect(received.append)
    model.updateItemStatus("aaa-111", "missing")
    assert 1 in received
