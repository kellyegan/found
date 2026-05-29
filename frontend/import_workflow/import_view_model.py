from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot
from PySide6.QtQml import QJSValue

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".tiff", ".tif", ".bmp", ".heic", ".heif",
}


def _expand_paths(paths: list[str]) -> list[str]:
    """Expand directories to individual supported-extension files; pass files through."""
    result = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS:
                    result.append(str(child))
        else:
            result.append(p)
    return result


class ImportViewModel(QObject):
    loadingStateChanged = Signal(str)
    pendingFilesChanged = Signal()
    importCompleted = Signal()
    progressChanged = Signal(float)
    conflictChoicesChanged = Signal()

    def __init__(
        self,
        scanner: Callable,
        importer: Callable,
        job_fetcher: Callable,
        conflict_resolver: Callable | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._scanner = scanner
        self._importer = importer
        self._job_fetcher = job_fetcher
        self._conflict_resolver = conflict_resolver

        self._loading_state = "Idle"
        self._pending_files: list = []
        self._duplicate_files: list = []
        self._conflict_files: list = []
        self._invalid_files: list = []
        self._imported_count = 0
        self._skipped_count = 0
        self._error_count = 0
        self._job_id = ""
        self._progress: float = 0.0
        self._conflict_choices: dict[str, str] = {}
        self._scan_thread: Optional[_ScanThread] = None
        self._import_thread: Optional[_ImportThread] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state

    @Property(list, notify=pendingFilesChanged)
    def pendingFiles(self) -> list:
        return self._pending_files

    @Property(list, notify=pendingFilesChanged)
    def duplicateFiles(self) -> list:
        return self._duplicate_files

    @Property(list, notify=pendingFilesChanged)
    def conflictFiles(self) -> list:
        return self._conflict_files

    @Property(list, notify=pendingFilesChanged)
    def invalidFiles(self) -> list:
        return self._invalid_files

    @Property(int, notify=importCompleted)
    def importedCount(self) -> int:
        return self._imported_count

    @Property(int, notify=importCompleted)
    def skippedCount(self) -> int:
        return self._skipped_count

    @Property(int, notify=importCompleted)
    def errorCount(self) -> int:
        return self._error_count

    @Property(str, notify=importCompleted)
    def jobId(self) -> str:
        return self._job_id

    @Property(float, notify=progressChanged)
    def progress(self) -> float:
        return self._progress

    @Property(object, notify=conflictChoicesChanged)
    def conflictChoices(self) -> dict:
        return self._conflict_choices

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot("QVariant")
    def scanPaths(self, paths) -> None:
        if isinstance(paths, QJSValue):
            paths = paths.toVariant() or []
        self._set_state("Scanning")
        thread = _ScanThread(self._scanner, list(paths))
        thread.result.connect(self._on_scan_result)
        self._scan_thread = thread
        thread.start()

    @Slot(str, str)
    def setConflictChoice(self, path: str, choice: str) -> None:
        self._conflict_choices[path] = choice
        self.conflictChoicesChanged.emit()

    @Slot()
    def executeImport(self) -> None:
        self._set_state("Importing")
        thread = _ImportThread(
            self._importer,
            self._job_fetcher,
            list(self._pending_files),
            self._conflict_files,
            dict(self._conflict_choices),
            self._conflict_resolver,
        )
        thread.result.connect(self._on_import_result)
        self._import_thread = thread
        thread.start()

    @Slot()
    def cancel(self) -> None:
        self._pending_files = []
        self._duplicate_files = []
        self._conflict_files = []
        self._invalid_files = []
        self._imported_count = 0
        self._skipped_count = 0
        self._error_count = 0
        self._job_id = ""
        self._progress = 0.0
        self._conflict_choices = {}
        self.pendingFilesChanged.emit()
        self.progressChanged.emit(0.0)
        self.conflictChoicesChanged.emit()
        self._set_state("Idle")

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _on_scan_result(self, data: dict | None) -> None:
        if data is None:
            self._set_state("Error")
            return
        self._pending_files = data.get("new", [])
        self._duplicate_files = data.get("already_imported", [])
        self._conflict_files = data.get("conflicts", [])
        self._invalid_files = data.get("invalid", [])
        self.pendingFilesChanged.emit()
        self._set_state("Previewing")

    def _on_import_result(self, data: dict | None) -> None:
        if data is None:
            self._set_state("Error")
            return
        self._job_id = data.get("job_id", "")
        self._imported_count = data.get("successful_imports", 0)
        self._skipped_count = data.get("duplicate_paths", 0) + data.get("duplicate_hashes", 0)
        self._error_count = data.get("failed_imports", 0)
        total = data.get("total_files", 0)
        processed = data.get("processed_files", 0)
        self._progress = processed / total if total > 0 else 1.0
        self.progressChanged.emit(self._progress)
        self.importCompleted.emit()
        self._set_state("Complete")

    def _set_state(self, state: str) -> None:
        self._loading_state = state
        self.loadingStateChanged.emit(state)


class _ScanThread(QThread):
    result = Signal(object)

    def __init__(self, scanner: Callable, paths: list[str], parent=None):
        super().__init__(parent)
        self._scanner = scanner
        self._paths = paths

    def run(self) -> None:
        try:
            expanded = _expand_paths(self._paths)
            data = self._scanner(expanded)
            self.result.emit(data)
        except Exception:
            self.result.emit(None)


class _ImportThread(QThread):
    result = Signal(object)

    def __init__(
        self,
        importer: Callable,
        job_fetcher: Callable,
        paths: list[str],
        conflicts: list,
        choices: dict[str, str],
        resolver: Callable | None,
        parent=None,
    ):
        super().__init__(parent)
        self._importer = importer
        self._job_fetcher = job_fetcher
        self._paths = paths
        self._conflicts = conflicts
        self._choices = choices
        self._resolver = resolver

    def run(self) -> None:
        try:
            self._resolve_conflicts()
            job_id = self._importer(self._paths)
            if job_id is None:
                self.result.emit(None)
                return
            job = self._poll_until_complete(job_id)
            if job is None:
                self.result.emit(None)
                return
            self.result.emit({**job, "job_id": job_id})
        except Exception:
            self.result.emit(None)

    def _resolve_conflicts(self) -> None:
        if self._resolver is None:
            return
        for conflict in self._conflicts:
            path = conflict.get("path", "")
            choice = self._choices.get(path, "keep")
            if choice == "update":
                self._resolver(conflict["existing_image_id"], path)

    def _poll_until_complete(self, job_id: str) -> dict | None:
        import time
        while True:
            try:
                job = self._job_fetcher(job_id)
                if job is None:
                    return None
                if job.get("status") == "completed":
                    return job
                time.sleep(0.5)
            except Exception:
                return None
