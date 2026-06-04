"""Tests for FilterStateManager."""

import pytest

from found_app.services.filter_state import FilterStateManager


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_has_active_filters_defaults_to_false(qapp):
    fsm = FilterStateManager()
    assert fsm.hasActiveFilters is False


def test_category_filters_defaults_to_empty(qapp):
    fsm = FilterStateManager()
    assert fsm.categoryFilters == {}


def test_tag_filters_defaults_to_empty(qapp):
    fsm = FilterStateManager()
    assert fsm.tagFilters == {}


def test_show_missing_only_defaults_to_false(qapp):
    fsm = FilterStateManager()
    assert fsm.showMissingOnly is False


def test_import_job_id_defaults_to_empty_string(qapp):
    fsm = FilterStateManager()
    assert fsm.importJobId == ""


def test_query_params_empty_when_no_filters(qapp):
    fsm = FilterStateManager()
    assert fsm.queryParams == {}


# ---------------------------------------------------------------------------
# Category filters
# ---------------------------------------------------------------------------


def test_set_category_filter_include(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    assert fsm.categoryFilters == {"cat-1": "include"}


def test_set_category_filter_exclude(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "exclude")
    assert fsm.categoryFilters == {"cat-1": "exclude"}


def test_set_category_filter_off_removes_entry(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    fsm.setCategoryFilter("cat-1", "off")
    assert "cat-1" not in fsm.categoryFilters


def test_cycle_category_off_to_include(qapp):
    fsm = FilterStateManager()
    fsm.cycleCategoryFilter("cat-1")
    assert fsm.categoryFilters.get("cat-1") == "include"


def test_cycle_category_include_to_exclude(qapp):
    fsm = FilterStateManager()
    fsm.cycleCategoryFilter("cat-1")
    fsm.cycleCategoryFilter("cat-1")
    assert fsm.categoryFilters.get("cat-1") == "exclude"


def test_cycle_category_exclude_to_off(qapp):
    fsm = FilterStateManager()
    fsm.cycleCategoryFilter("cat-1")
    fsm.cycleCategoryFilter("cat-1")
    fsm.cycleCategoryFilter("cat-1")
    assert "cat-1" not in fsm.categoryFilters


def test_multiple_category_filters(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    fsm.setCategoryFilter("cat-2", "exclude")
    assert fsm.categoryFilters == {"cat-1": "include", "cat-2": "exclude"}


def test_category_include_sets_has_active_filters(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    assert fsm.hasActiveFilters is True


def test_category_include_appears_in_query_params(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    assert fsm.queryParams.get("category") == "cat-1"


def test_category_exclude_appears_in_query_params(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "exclude")
    assert fsm.queryParams.get("exclude_category") == "cat-1"
    assert "category" not in fsm.queryParams


def test_set_category_filter_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.setCategoryFilter("cat-1", "include")
    assert len(received) == 1


def test_cycle_category_filter_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.cycleCategoryFilter("cat-1")
    assert len(received) == 1


# ---------------------------------------------------------------------------
# Tag filters
# ---------------------------------------------------------------------------


def test_set_tag_filter_include(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "include")
    assert fsm.tagFilters == {"tag-1": "include"}


def test_set_tag_filter_exclude(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "exclude")
    assert fsm.tagFilters == {"tag-1": "exclude"}


def test_set_tag_filter_off_removes_entry(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "include")
    fsm.setTagFilter("tag-1", "off")
    assert "tag-1" not in fsm.tagFilters


def test_cycle_tag_off_to_include(qapp):
    fsm = FilterStateManager()
    fsm.cycleTagFilter("tag-1")
    assert fsm.tagFilters.get("tag-1") == "include"


def test_cycle_tag_include_to_exclude(qapp):
    fsm = FilterStateManager()
    fsm.cycleTagFilter("tag-1")
    fsm.cycleTagFilter("tag-1")
    assert fsm.tagFilters.get("tag-1") == "exclude"


def test_cycle_tag_exclude_to_off(qapp):
    fsm = FilterStateManager()
    fsm.cycleTagFilter("tag-1")
    fsm.cycleTagFilter("tag-1")
    fsm.cycleTagFilter("tag-1")
    assert "tag-1" not in fsm.tagFilters


def test_tag_include_sets_has_active_filters(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "include")
    assert fsm.hasActiveFilters is True


def test_tag_include_appears_in_query_params(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "include")
    assert fsm.queryParams.get("tag") == "tag-1"


def test_tag_exclude_appears_in_query_params(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "exclude")
    assert fsm.queryParams.get("exclude_tag") == "tag-1"
    assert "tag" not in fsm.queryParams


def test_set_tag_filter_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.setTagFilter("tag-1", "include")
    assert len(received) == 1


def test_cycle_tag_filter_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.cycleTagFilter("tag-1")
    assert len(received) == 1


# ---------------------------------------------------------------------------
# Missing image toggle
# ---------------------------------------------------------------------------


def test_set_show_missing_only_true(qapp):
    fsm = FilterStateManager()
    fsm.setShowMissingOnly(True)
    assert fsm.showMissingOnly is True


def test_set_show_missing_only_false(qapp):
    fsm = FilterStateManager()
    fsm.setShowMissingOnly(True)
    fsm.setShowMissingOnly(False)
    assert fsm.showMissingOnly is False


def test_missing_only_sets_has_active_filters(qapp):
    fsm = FilterStateManager()
    fsm.setShowMissingOnly(True)
    assert fsm.hasActiveFilters is True


def test_missing_only_in_query_params(qapp):
    fsm = FilterStateManager()
    fsm.setShowMissingOnly(True)
    assert fsm.queryParams.get("file_status") == "missing"


def test_missing_only_false_not_in_query_params(qapp):
    fsm = FilterStateManager()
    assert "file_status" not in fsm.queryParams


def test_set_missing_only_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.setShowMissingOnly(True)
    assert len(received) == 1


def test_set_missing_only_no_signal_when_unchanged(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.setShowMissingOnly(False)
    assert len(received) == 0


# ---------------------------------------------------------------------------
# Import job filter
# ---------------------------------------------------------------------------


def test_set_import_job_filter(qapp):
    fsm = FilterStateManager()
    fsm.setImportJobFilter("job-123")
    assert fsm.importJobId == "job-123"


def test_set_import_job_filter_empty_string_clears(qapp):
    fsm = FilterStateManager()
    fsm.setImportJobFilter("job-123")
    fsm.setImportJobFilter("")
    assert fsm.importJobId == ""


def test_import_job_sets_has_active_filters(qapp):
    fsm = FilterStateManager()
    fsm.setImportJobFilter("job-123")
    assert fsm.hasActiveFilters is True


def test_import_job_in_query_params(qapp):
    fsm = FilterStateManager()
    fsm.setImportJobFilter("job-123")
    assert fsm.queryParams.get("import_job") == "job-123"


def test_import_job_absent_from_query_params_when_cleared(qapp):
    fsm = FilterStateManager()
    assert "import_job" not in fsm.queryParams


def test_set_import_job_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.setImportJobFilter("job-123")
    assert len(received) == 1


def test_set_import_job_no_signal_when_unchanged(qapp):
    fsm = FilterStateManager()
    fsm.setImportJobFilter("job-123")
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.setImportJobFilter("job-123")
    assert len(received) == 0


# ---------------------------------------------------------------------------
# Combined query params
# ---------------------------------------------------------------------------


def test_combined_category_and_import_job(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    fsm.setImportJobFilter("job-123")
    params = fsm.queryParams
    assert params.get("category") == "cat-1"
    assert params.get("import_job") == "job-123"


def test_combined_tag_and_missing(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "include")
    fsm.setShowMissingOnly(True)
    params = fsm.queryParams
    assert params.get("tag") == "tag-1"
    assert params.get("file_status") == "missing"


def test_combined_all_filters(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    fsm.setTagFilter("tag-1", "include")
    fsm.setShowMissingOnly(True)
    fsm.setImportJobFilter("job-123")
    params = fsm.queryParams
    assert params.get("category") == "cat-1"
    assert params.get("tag") == "tag-1"
    assert params.get("file_status") == "missing"
    assert params.get("import_job") == "job-123"


def test_combined_include_and_exclude_category(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    fsm.setCategoryFilter("cat-2", "exclude")
    params = fsm.queryParams
    assert params.get("category") == "cat-1"
    assert params.get("exclude_category") == "cat-2"


def test_combined_include_and_exclude_tag(qapp):
    fsm = FilterStateManager()
    fsm.setTagFilter("tag-1", "include")
    fsm.setTagFilter("tag-2", "exclude")
    params = fsm.queryParams
    assert params.get("tag") == "tag-1"
    assert params.get("exclude_tag") == "tag-2"


# ---------------------------------------------------------------------------
# Clear all filters
# ---------------------------------------------------------------------------


def test_clear_all_filters_resets_everything(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    fsm.setTagFilter("tag-1", "include")
    fsm.setShowMissingOnly(True)
    fsm.setImportJobFilter("job-123")
    fsm.clearAllFilters()
    assert fsm.categoryFilters == {}
    assert fsm.tagFilters == {}
    assert fsm.showMissingOnly is False
    assert fsm.importJobId == ""
    assert fsm.hasActiveFilters is False
    assert fsm.queryParams == {}


def test_clear_all_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.clearAllFilters()
    assert len(received) == 1


def test_clear_all_no_signal_when_already_empty(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.clearAllFilters()
    assert len(received) == 0


def test_clear_category_filters_only_removes_categories(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    fsm.setImportJobFilter("job-123")
    fsm.clearCategoryFilters()
    assert fsm.categoryFilters == {}
    assert fsm.importJobId == "job-123"


def test_clear_category_filters_emits_filters_changed(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.clearCategoryFilters()
    assert len(received) == 1


def test_clear_category_filters_no_signal_when_empty(qapp):
    fsm = FilterStateManager()
    received = []
    fsm.filtersChanged.connect(lambda: received.append(1))
    fsm.clearCategoryFilters()
    assert len(received) == 0
