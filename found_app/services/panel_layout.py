from PySide6.QtCore import QObject, Property, Signal, Slot

from found_app.core.app_settings import AppSettings

_PANEL_IDS = ["collections", "metadata"]
_DEFAULT_EDGES = {"collections": "left", "metadata": "right"}
_DEFAULT_ORDER = ["collections", "metadata"]


class PanelLayoutManager(QObject):
    layoutChanged = Signal()
    openStateChanged = Signal()

    def __init__(self, parent=None, settings: AppSettings | None = None):
        super().__init__(parent)
        self._settings = settings

        order_default = ",".join(_DEFAULT_ORDER)
        order_str = (
            self._settings.get("panels/order", order_default)
            if self._settings else order_default
        )
        self._order: list[str] = [p for p in order_str.split(",") if p]

        self._edges: dict[str, str] = {}
        for panel_id in _PANEL_IDS:
            default_edge = _DEFAULT_EDGES[panel_id]
            self._edges[panel_id] = (
                self._settings.get(f"panels/{panel_id}/edge", default_edge)
                if self._settings else default_edge
            )

        self._open: dict[str, str] = {"left": "", "right": ""}
        self._saved_view_states: dict[str, dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Reactive properties (QML binds to these directly)
    # ------------------------------------------------------------------

    @Property("QVariant", notify=layoutChanged)
    def edges(self) -> dict:
        return dict(self._edges)

    @Property("QVariant", notify=layoutChanged)
    def order(self) -> list:
        return list(self._order)

    @Property("QVariant", notify=openStateChanged)
    def openPanels(self) -> dict:
        return dict(self._open)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    @Slot(str, str, int)
    def setLayout(self, panelId: str, edge: str, sideIndex: int) -> None:
        old_edge = self._edges[panelId]
        was_open = self._open.get(old_edge) == panelId
        open_state_changed = False

        if old_edge != edge and was_open:
            self._open[old_edge] = ""
            self._open[edge] = panelId
            open_state_changed = True

        self._edges[panelId] = edge

        order = [p for p in self._order if p != panelId]
        peers = [p for p in order if self._edges[p] == edge]

        if sideIndex >= len(peers):
            ref = peers[-1] if peers else None
            insert_at = order.index(ref) + 1 if ref else len(order)
        else:
            insert_at = order.index(peers[sideIndex])

        order.insert(insert_at, panelId)
        self._order = order

        if self._settings:
            self._settings.set(f"panels/{panelId}/edge", edge)
            self._settings.set("panels/order", ",".join(self._order))

        self.layoutChanged.emit()
        if open_state_changed:
            self.openStateChanged.emit()

    @Slot(str, str)
    def setPanelEdge(self, panelId: str, edge: str) -> None:
        """Move panel to edge, appending to end of that side's stack."""
        self.setLayout(panelId, edge, len(self._order))

    @Slot(str)
    def togglePanel(self, panelId: str) -> None:
        edge = self._edges[panelId]
        self._open[edge] = "" if self._open.get(edge) == panelId else panelId
        self.openStateChanged.emit()

    @Slot(str)
    def saveViewState(self, view: str) -> None:
        self._saved_view_states[view] = dict(self._open)

    @Slot(str, "QVariantList")
    def restoreViewState(self, view: str, availablePanels: list) -> None:
        saved = self._saved_view_states.get(view, {})
        self._open = {"left": "", "right": ""}
        for side, panel_id in saved.items():
            if panel_id and panel_id in availablePanels:
                self._open[side] = panel_id
        self.openStateChanged.emit()
