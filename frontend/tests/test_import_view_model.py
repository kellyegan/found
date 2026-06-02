"""
Tests for ImportViewModel — Slice 9 Commit 1.

Covers:
- Initial state: loadingState "Idle", all buckets empty, counts zero
- scanPaths(): Idle → Scanning → Previewing, populates new/duplicate/conflict/invalid buckets
- scanPaths(): expands a directory to its supported-extension files
- scanPaths(): transitions to Error when scanner raises or returns None
- executeImport(): Previewing → Importing → Complete, populates counts and jobId
- executeImport(): transitions to Error when importer returns None or raises
- cancel(): resets to Idle and clears all state
- signals: loadingStateChanged fired on every transition
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QEventLoop, QTimer

from frontend.import_workflow.import_view_model import ImportViewModel


SAMPLE_SCAN_RESULT = {
    "new": ["/path/a.jpg", "/path/b.png"],
    "already_imported": [
        {"image_id": "uuid-2", "path": "/path/c.jpg", "filename": "c.jpg"}
    ],
    "conflicts": [
        {
            "path": "/path/d.jpg",
            "existing_image_id": "uuid-1",
            "existing_path": "/old/d.jpg",
            "existing_filename": "d.jpg",
        }
    ],
    "invalid": ["/path/bad.txt"],
}

SAMPLE_JOB_COMPLETE = {
    "status": "completed",
    "total_files": 2,
    "processed_files": 2,
    "successful_imports": 2,
    "duplicate_paths": 0,
    "duplicate_hashes": 0,
    "failed_imports": 0,
}


SAMPLE_SCAN_WITH_CONFLICT = {
    "new": ["/path/a.jpg"],
    "already_imported": [],
    "conflicts": [
        {
            "path": "/path/d.jpg",
            "existing_image_id": "uuid-1",
            "existing_path": "/old/d.jpg",
            "existing_filename": "d.jpg",
        }
    ],
    "invalid": [],
}


def _vm(
    scanner=None,
    importer=None,
    job_fetcher=None,
    conflict_resolver=None,
):
    return ImportViewModel(
        scanner=scanner or (lambda paths: {"new": [], "already_imported": [], "conflicts": [], "invalid": []}),
        importer=importer or (lambda paths: "job-id-123"),
        job_fetcher=job_fetcher or (lambda job_id: SAMPLE_JOB_COMPLETE),
        conflict_resolver=conflict_resolver or (lambda image_id, new_path: True),
    )


def wait_for_state(vm, target: str, timeout_ms: int = 2000) -> None:
    if vm.loadingState == target:
        return
    loop = QEventLoop()

    def check(name: str):
        if name == target:
            loop.quit()

    vm.loadingStateChanged.connect(check)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_pending_files_defaults_to_empty(qapp):
    assert _vm().pendingFiles == []


def test_duplicate_files_defaults_to_empty(qapp):
    assert _vm().duplicateFiles == []


def test_conflict_files_defaults_to_empty(qapp):
    assert _vm().conflictFiles == []


def test_invalid_files_defaults_to_empty(qapp):
    assert _vm().invalidFiles == []


def test_imported_count_defaults_to_zero(qapp):
    assert _vm().importedCount == 0


def test_skipped_count_defaults_to_zero(qapp):
    assert _vm().skippedCount == 0


def test_error_count_defaults_to_zero(qapp):
    assert _vm().errorCount == 0


def test_job_id_defaults_to_empty(qapp):
    assert _vm().jobId == ""


# ---------------------------------------------------------------------------
# scanPaths() — state transitions
# ---------------------------------------------------------------------------


def test_scan_transitions_to_previewing(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    assert vm.loadingState == "Previewing"


def test_scan_transitions_to_error_when_scanner_returns_none(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: None)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


def test_scan_transitions_to_error_when_scanner_raises(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    def bad_scanner(paths):
        raise RuntimeError("network error")
    vm = _vm(scanner=bad_scanner)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


# ---------------------------------------------------------------------------
# scanPaths() — data
# ---------------------------------------------------------------------------


def test_scan_populates_pending_files(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    assert vm.pendingFiles == ["/path/a.jpg", "/path/b.png"]


def test_scan_populates_duplicate_files(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    assert len(vm.duplicateFiles) == 1
    assert vm.duplicateFiles[0]["path"] == "/path/c.jpg"
    assert vm.duplicateFiles[0]["image_id"] == "uuid-2"
    assert vm.duplicateFiles[0]["filename"] == "c.jpg"


def test_scan_populates_conflict_files(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    assert len(vm.conflictFiles) == 1
    assert vm.conflictFiles[0]["path"] == "/path/d.jpg"


def test_scan_populates_invalid_files(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    assert vm.invalidFiles == ["/path/bad.txt"]


# ---------------------------------------------------------------------------
# scanPaths() — directory expansion
# ---------------------------------------------------------------------------


def test_scan_expands_directory_to_supported_files(qapp, tmp_path):
    received = []
    subdir = tmp_path / "photos"
    subdir.mkdir()
    (subdir / "a.jpg").touch()
    (subdir / "b.png").touch()
    (subdir / "c.txt").touch()  # unsupported — should be excluded from scan call

    def capturing_scanner(paths):
        received.extend(paths)
        return {"new": paths, "already_imported": [], "conflicts": [], "invalid": []}

    vm = _vm(scanner=capturing_scanner)
    vm.scanPaths([str(tmp_path)])
    wait_for_state(vm, "Previewing")

    assert any("a.jpg" in p for p in received)
    assert any("b.png" in p for p in received)
    assert not any("c.txt" in p for p in received)


def test_scan_expands_nested_directories(qapp, tmp_path):
    received = []
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "deep.jpg").touch()

    def capturing_scanner(paths):
        received.extend(paths)
        return {"new": paths, "already_imported": [], "conflicts": [], "invalid": []}

    vm = _vm(scanner=capturing_scanner)
    vm.scanPaths([str(tmp_path)])
    wait_for_state(vm, "Previewing")
    assert any("deep.jpg" in p for p in received)


def test_scan_passes_file_paths_directly(qapp, tmp_path):
    received = []
    img = tmp_path / "photo.jpg"
    img.touch()

    def capturing_scanner(paths):
        received.extend(paths)
        return {"new": paths, "already_imported": [], "conflicts": [], "invalid": []}

    vm = _vm(scanner=capturing_scanner)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    assert str(img) in received


# ---------------------------------------------------------------------------
# scanPaths() — signals
# ---------------------------------------------------------------------------


def test_scan_emits_loading_state_changed(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    received = []
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.loadingStateChanged.connect(received.append)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    assert "Previewing" in received


# ---------------------------------------------------------------------------
# executeImport() — state transitions
# ---------------------------------------------------------------------------


def test_execute_import_transitions_to_complete(qapp):
    vm = _vm()
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.loadingState == "Complete"


def test_execute_import_transitions_to_error_when_importer_returns_none(qapp):
    vm = _vm(importer=lambda paths: None)
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


def test_execute_import_transitions_to_error_when_importer_raises(qapp):
    def bad(paths):
        raise RuntimeError("API error")
    vm = _vm(importer=bad)
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


# ---------------------------------------------------------------------------
# executeImport() — data
# ---------------------------------------------------------------------------


def test_execute_import_sets_imported_count(qapp):
    vm = _vm(job_fetcher=lambda jid: {**SAMPLE_JOB_COMPLETE, "successful_imports": 3})
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.importedCount == 3


def test_execute_import_sets_skipped_count(qapp):
    vm = _vm(job_fetcher=lambda jid: {**SAMPLE_JOB_COMPLETE, "duplicate_paths": 1, "duplicate_hashes": 2})
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.skippedCount == 3


def test_execute_import_sets_error_count(qapp):
    vm = _vm(job_fetcher=lambda jid: {**SAMPLE_JOB_COMPLETE, "failed_imports": 2})
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.errorCount == 2


def test_execute_import_sets_job_id(qapp):
    vm = _vm(importer=lambda paths: "my-job-id")
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.jobId == "my-job-id"


# ---------------------------------------------------------------------------
# cancel()
# ---------------------------------------------------------------------------


def test_cancel_from_previewing_resets_to_idle(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    vm.cancel()
    assert vm.loadingState == "Idle"


def test_cancel_clears_pending_files(qapp, tmp_path):
    img = tmp_path / "a.jpg"
    img.touch()
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_RESULT)
    vm.scanPaths([str(img)])
    wait_for_state(vm, "Previewing")
    vm.cancel()
    assert vm.pendingFiles == []


def test_cancel_from_complete_resets_to_idle(qapp):
    vm = _vm()
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    vm.cancel()
    assert vm.loadingState == "Idle"


# ---------------------------------------------------------------------------
# progress — Slice 9 Commit 3
# ---------------------------------------------------------------------------


def test_progress_defaults_to_zero(qapp):
    assert _vm().progress == 0.0


def test_progress_is_one_after_complete(qapp):
    vm = _vm(job_fetcher=lambda jid: {**SAMPLE_JOB_COMPLETE, "total_files": 2, "processed_files": 2})
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.progress == 1.0


def test_progress_resets_on_cancel(qapp):
    vm = _vm()
    vm.scanPaths([])
    wait_for_state(vm, "Previewing")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    vm.cancel()
    assert vm.progress == 0.0


# ---------------------------------------------------------------------------
# conflict choices — Slice 9 Commit 4B
# ---------------------------------------------------------------------------


def test_conflict_choices_defaults_to_empty(qapp):
    assert _vm().conflictChoices == {}


def test_set_conflict_choice_stores_update(qapp):
    vm = _vm()
    vm.setConflictChoice("/path/d.jpg", "update")
    assert vm.conflictChoices.get("/path/d.jpg") == "update"


def test_set_conflict_choice_stores_keep(qapp):
    vm = _vm()
    vm.setConflictChoice("/path/d.jpg", "keep")
    assert vm.conflictChoices.get("/path/d.jpg") == "keep"


def test_cancel_clears_conflict_choices(qapp):
    vm = _vm()
    vm.setConflictChoice("/path/d.jpg", "update")
    vm.cancel()
    assert vm.conflictChoices == {}


def test_execute_import_calls_resolver_for_update_choice(qapp):
    calls = []

    def resolver(image_id, new_path):
        calls.append((image_id, new_path))
        return True

    vm = _vm(
        scanner=lambda paths: SAMPLE_SCAN_WITH_CONFLICT,
        conflict_resolver=resolver,
    )
    vm.scanPaths(["/path/d.jpg"])
    wait_for_state(vm, "Previewing")
    vm.setConflictChoice("/path/d.jpg", "update")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert ("uuid-1", "/path/d.jpg") in calls


def test_execute_import_skips_resolver_for_keep_choice(qapp):
    calls = []

    def resolver(image_id, new_path):
        calls.append((image_id, new_path))
        return True

    vm = _vm(
        scanner=lambda paths: SAMPLE_SCAN_WITH_CONFLICT,
        conflict_resolver=resolver,
    )
    vm.scanPaths(["/path/d.jpg"])
    wait_for_state(vm, "Previewing")
    vm.setConflictChoice("/path/d.jpg", "keep")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert calls == []


def test_execute_import_defaults_to_keep_when_no_choice(qapp):
    calls = []

    def resolver(image_id, new_path):
        calls.append((image_id, new_path))
        return True

    vm = _vm(
        scanner=lambda paths: SAMPLE_SCAN_WITH_CONFLICT,
        conflict_resolver=resolver,
    )
    vm.scanPaths(["/path/d.jpg"])
    wait_for_state(vm, "Previewing")
    # no setConflictChoice call — should default to "keep"
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert calls == []


# ---------------------------------------------------------------------------
# updatedCount — conflicts resolved as "update path"
# ---------------------------------------------------------------------------


def test_updated_count_defaults_to_zero(qapp):
    assert _vm().updatedCount == 0


def test_updated_count_reflects_update_choices(qapp):
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_WITH_CONFLICT)
    vm.scanPaths(["/path/d.jpg"])
    wait_for_state(vm, "Previewing")
    vm.setConflictChoice("/path/d.jpg", "update")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.updatedCount == 1


def test_updated_count_is_zero_for_keep_choices(qapp):
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_WITH_CONFLICT)
    vm.scanPaths(["/path/d.jpg"])
    wait_for_state(vm, "Previewing")
    vm.setConflictChoice("/path/d.jpg", "keep")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    assert vm.updatedCount == 0


def test_updated_count_resets_on_cancel(qapp):
    vm = _vm(scanner=lambda paths: SAMPLE_SCAN_WITH_CONFLICT)
    vm.scanPaths(["/path/d.jpg"])
    wait_for_state(vm, "Previewing")
    vm.setConflictChoice("/path/d.jpg", "update")
    vm.executeImport()
    wait_for_state(vm, "Complete")
    vm.cancel()
    assert vm.updatedCount == 0
