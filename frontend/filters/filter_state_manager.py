from PySide6.QtCore import QObject, Property, Signal, Slot

_CYCLE = {"off": "include", "include": "exclude", "exclude": "off"}


class FilterStateManager(QObject):
    filtersChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._category_filters: dict[str, str] = {}  # id -> "include" | "exclude"
        self._tag_filters: dict[str, str] = {}        # id -> "include" | "exclude"
        self._show_missing_only: bool = False
        self._import_job: str | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=filtersChanged)
    def hasActiveFilters(self) -> bool:
        return bool(
            self._category_filters or self._tag_filters
            or self._show_missing_only or self._import_job
        )

    @Property("QVariant", notify=filtersChanged)
    def categoryFilters(self) -> dict:
        return dict(self._category_filters)

    @Property("QVariant", notify=filtersChanged)
    def tagFilters(self) -> dict:
        return dict(self._tag_filters)

    @Property(bool, notify=filtersChanged)
    def showMissingOnly(self) -> bool:
        return self._show_missing_only

    @Property(str, notify=filtersChanged)
    def importJobId(self) -> str:
        return self._import_job or ""

    @Property("QVariant", notify=filtersChanged)
    def queryParams(self) -> dict:
        params: dict = {}
        for cat_id, mode in self._category_filters.items():
            if mode == "include":
                params["category"] = cat_id
                break
        for tag_id, mode in self._tag_filters.items():
            if mode == "include":
                params["tag"] = tag_id
                break
        if self._show_missing_only:
            params["file_status"] = "missing"
        if self._import_job:
            params["import_job"] = self._import_job
        return params

    # ------------------------------------------------------------------
    # Category filter slots
    # ------------------------------------------------------------------

    @Slot(str, str)
    def setCategoryFilter(self, category_id: str, mode: str) -> None:
        if mode == "off":
            self._category_filters.pop(category_id, None)
        else:
            self._category_filters[category_id] = mode
        self.filtersChanged.emit()

    @Slot(str)
    def cycleCategoryFilter(self, category_id: str) -> None:
        current = self._category_filters.get(category_id, "off")
        nxt = _CYCLE[current]
        if nxt == "off":
            self._category_filters.pop(category_id, None)
        else:
            self._category_filters[category_id] = nxt
        self.filtersChanged.emit()

    @Slot()
    def clearCategoryFilters(self) -> None:
        if self._category_filters:
            self._category_filters.clear()
            self.filtersChanged.emit()

    # ------------------------------------------------------------------
    # Tag filter slots
    # ------------------------------------------------------------------

    @Slot(str, str)
    def setTagFilter(self, tag_id: str, mode: str) -> None:
        if mode == "off":
            self._tag_filters.pop(tag_id, None)
        else:
            self._tag_filters[tag_id] = mode
        self.filtersChanged.emit()

    @Slot(str)
    def cycleTagFilter(self, tag_id: str) -> None:
        current = self._tag_filters.get(tag_id, "off")
        nxt = _CYCLE[current]
        if nxt == "off":
            self._tag_filters.pop(tag_id, None)
        else:
            self._tag_filters[tag_id] = nxt
        self.filtersChanged.emit()

    # ------------------------------------------------------------------
    # Missing image toggle
    # ------------------------------------------------------------------

    @Slot(bool)
    def setShowMissingOnly(self, value: bool) -> None:
        if self._show_missing_only != value:
            self._show_missing_only = value
            self.filtersChanged.emit()

    # ------------------------------------------------------------------
    # Import job filter
    # ------------------------------------------------------------------

    @Slot(str)
    def setImportJobFilter(self, job_id: str) -> None:
        new_val = job_id.strip() or None
        if self._import_job != new_val:
            self._import_job = new_val
            self.filtersChanged.emit()

    # ------------------------------------------------------------------
    # Clear all
    # ------------------------------------------------------------------

    @Slot()
    def clearAllFilters(self) -> None:
        if not self.hasActiveFilters:
            return
        self._category_filters.clear()
        self._tag_filters.clear()
        self._show_missing_only = False
        self._import_job = None
        self.filtersChanged.emit()
