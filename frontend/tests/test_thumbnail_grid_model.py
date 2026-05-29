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

from frontend.library.thumbnail_grid_model import ThumbnailGridModel


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
