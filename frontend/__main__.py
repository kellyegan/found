import sys
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import httpx

from frontend.app.controller import AppController
from frontend.backend.connection_monitor import BackendConnectionManager
from frontend.backend.process_manager import BackendProcessManager
from frontend.collections.collections_view_model import CollectionsViewModel
from frontend.import_workflow.import_view_model import ImportViewModel
from frontend.library.thumbnail_provider import ThumbnailProvider
from frontend.library.view_model import LibraryViewModel
from frontend.navigation.navigation_manager import NavigationManager
from frontend.selection.selection_manager import SelectionManager
from frontend.state.app_state import AppStateManager
from frontend.theme.theme import ThemeManager


def _make_collections_fetcher(base_url: str):
    def fetch():
        try:
            response = httpx.get(f"{base_url}/api/v1/collections", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_collection_creator(base_url: str):
    def create(name: str):
        try:
            response = httpx.post(f"{base_url}/api/v1/collections", json={"name": name}, timeout=10.0)
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None
    return create


def _make_images_adder(base_url: str):
    def add(collection_id: str, image_ids: list):
        try:
            response = httpx.post(
                f"{base_url}/api/v1/collections/{collection_id}/images",
                json={"image_ids": image_ids},
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False
    return add


def _make_collection_images_fetcher(base_url: str):
    def fetch(collection_id: str):
        try:
            response = httpx.get(
                f"{base_url}/api/v1/collections/{collection_id}/images?view=grid",
                timeout=10.0,
            )
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_scanner(base_url: str):
    def scan(paths: list[str]):
        try:
            response = httpx.post(f"{base_url}/api/v1/images/import/preview", json={"paths": paths}, timeout=30.0)
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None
    return scan


def _make_importer(base_url: str):
    def do_import(paths: list[str]):
        try:
            response = httpx.post(f"{base_url}/api/v1/images/import", json={"paths": paths}, timeout=30.0)
            data = response.json()
            return data["data"]["job_id"] if data.get("success") else None
        except Exception:
            return None
    return do_import


def _make_job_fetcher(base_url: str):
    def fetch(job_id: str):
        try:
            response = httpx.get(f"{base_url}/api/v1/jobs/{job_id}", timeout=10.0)
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_conflict_resolver(base_url: str):
    def resolve(image_id: str, new_path: str) -> bool:
        try:
            response = httpx.patch(
                f"{base_url}/api/v1/images/{image_id}",
                json={"path": new_path},
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False
    return resolve


def _make_page_fetcher(base_url: str):
    def fetch(cursor=None, limit=100, import_job=None):
        try:
            url = f"{base_url}/api/v1/images?view=grid&limit={limit}"
            if cursor:
                url += f"&cursor={cursor}"
            if import_job:
                url += f"&import_job={import_job}"
            response = httpx.get(url, timeout=10.0)
            data = response.json()
            if data.get("success"):
                return {
                    "items": data.get("data", []),
                    "next_cursor": data.get("next_cursor"),
                    "has_more": data.get("has_more", False),
                }
            return None
        except Exception:
            return None
    return fetch


def main():
    app = QGuiApplication(sys.argv)

    theme = ThemeManager()
    app_state = AppStateManager()
    process_manager = BackendProcessManager()
    connection_monitor = BackendConnectionManager(
        health_checker=process_manager._health_checker,
        health_url=process_manager.health_url,
    )
    base_url = f"http://{process_manager._host}:{process_manager._port}"

    library_state = LibraryViewModel(page_fetcher=_make_page_fetcher(base_url))
    thumbnail_provider = ThumbnailProvider(base_url=base_url)
    selection_manager = SelectionManager()
    navigation_manager = NavigationManager()
    collections_state = CollectionsViewModel(
        collections_fetcher=_make_collections_fetcher(base_url),
        collection_creator=_make_collection_creator(base_url),
        images_adder=_make_images_adder(base_url),
        collection_images_fetcher=_make_collection_images_fetcher(base_url),
    )
    import_state = ImportViewModel(
        scanner=_make_scanner(base_url),
        importer=_make_importer(base_url),
        job_fetcher=_make_job_fetcher(base_url),
        conflict_resolver=_make_conflict_resolver(base_url),
    )

    controller = AppController(
        app_state,
        process_manager,
        connection_monitor=connection_monitor,
        library_view_model=library_state,
    )

    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbnails", thumbnail_provider)
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("AppState", app_state)
    engine.rootContext().setContextProperty("BackendConnection", connection_monitor)
    engine.rootContext().setContextProperty("LibraryState", library_state)
    engine.rootContext().setContextProperty("SelectionManager", selection_manager)
    engine.rootContext().setContextProperty("NavigationManager", navigation_manager)
    engine.rootContext().setContextProperty("CollectionsState", collections_state)
    engine.rootContext().setContextProperty("ImportState", import_state)
    engine.rootContext().setContextProperty("baseUrl", base_url)

    qml_path = Path(__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))

    if not engine.rootObjects():
        sys.exit(1)

    def _shutdown():
        controller.shutdown()
        library_state.shutdown()
        QThreadPool.globalInstance().waitForDone(2000)

    app.aboutToQuit.connect(_shutdown)

    controller.start()
    exit_code = app.exec()

    # Destroy the QML engine before Python GC runs so QML objects are torn
    # down while all Python-side owners are still alive.
    del engine

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
