import sys
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import httpx

from frontend.app.controller import AppController
from frontend.backend.connection_monitor import BackendConnectionManager
from frontend.backend.process_manager import BackendProcessManager
from frontend.category_editor.category_editor_view_model import CategoryEditorViewModel
from frontend.collection_editor.collection_editor_view_model import CollectionEditorViewModel
from frontend.collections.collections_view_model import CollectionsViewModel
from frontend.filters.filter_state_manager import FilterStateManager
from frontend.import_workflow.import_view_model import ImportViewModel
from frontend.library.thumbnail_provider import ThumbnailProvider
from frontend.library.view_model import LibraryViewModel
from frontend.metadata.metadata_view_model import MetadataViewModel
from frontend.navigation.navigation_manager import NavigationManager
from frontend.tag_editor.tag_editor_view_model import TagEditorViewModel
from frontend.tag_search.tag_search_view_model import TagSearchViewModel
from frontend.selection.selection_manager import SelectionManager
from frontend.state.app_state import AppStateManager
from frontend.categories.categories_view_model import CategoriesViewModel
from frontend.theme.theme import ThemeManager
from frontend.version import get_app_metadata


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


def _make_categories_fetcher(base_url: str):
    def fetch():
        try:
            response = httpx.get(f"{base_url}/api/v1/categories", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_category_creator(base_url: str):
    def create(name: str):
        try:
            response = httpx.post(
                f"{base_url}/api/v1/categories",
                json={"name": name, "description": ""},
                timeout=10.0,
            )
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None
    return create


def _make_image_fetcher(base_url: str):
    def fetch(image_id: str):
        try:
            response = httpx.get(f"{base_url}/api/v1/images/{image_id}", timeout=10.0)
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_category_images_adder(base_url: str):
    def add(category_id: str, image_ids: list):
        try:
            response = httpx.post(
                f"{base_url}/api/v1/images/bulk/categories",
                json={"image_ids": image_ids, "add_category_ids": [category_id]},
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False
    return add


def _make_tag_creator(base_url: str):
    def create(name: str):
        try:
            response = httpx.post(
                f"{base_url}/api/v1/tags",
                json={"name": name},
                timeout=10.0,
            )
            data = response.json()
            if data.get("success"):
                return data.get("data")
            # Tag already exists (409) — find it by exact name
            if response.status_code == 409:
                search = httpx.get(
                    f"{base_url}/api/v1/tags/search",
                    params={"q": name},
                    timeout=10.0,
                )
                search_data = search.json()
                tags = search_data.get("data", []) if search_data.get("success") else []
                for tag in tags:
                    if tag.get("name", "").lower() == name.lower():
                        return tag
            return None
        except Exception:
            return None
    return create


def _make_tags_fetcher(base_url: str):
    def fetch(term: str):
        try:
            response = httpx.get(f"{base_url}/api/v1/tags/search", params={"q": term}, timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_image_tags_fetcher(base_url: str):
    def fetch(image_id: str):
        try:
            response = httpx.get(f"{base_url}/api/v1/images/{image_id}/tags", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_bulk_tag_modifier(base_url: str):
    def modify(image_ids: list, add_tag_ids: list, remove_tag_ids: list) -> bool:
        try:
            response = httpx.post(
                f"{base_url}/api/v1/images/bulk/tags",
                json={
                    "image_ids": image_ids,
                    "add_tag_ids": add_tag_ids,
                    "remove_tag_ids": remove_tag_ids,
                },
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False
    return modify


def _make_image_categories_fetcher(base_url: str):
    def fetch(image_id: str):
        try:
            response = httpx.get(f"{base_url}/api/v1/images/{image_id}/categories", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_bulk_category_modifier(base_url: str):
    def modify(image_ids: list, add_category_ids: list, remove_category_ids: list) -> bool:
        try:
            response = httpx.post(
                f"{base_url}/api/v1/images/bulk/categories",
                json={
                    "image_ids": image_ids,
                    "add_category_ids": add_category_ids,
                    "remove_category_ids": remove_category_ids,
                },
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False
    return modify


def _make_category_searcher(base_url: str):
    def search(term: str):
        try:
            response = httpx.get(f"{base_url}/api/v1/categories/search", params={"q": term}, timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return search


def _make_image_collections_fetcher(base_url: str):
    def fetch(image_id: str):
        try:
            response = httpx.get(f"{base_url}/api/v1/images/{image_id}/collections", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None
    return fetch


def _make_collection_adder(base_url: str):
    def add(collection_id: str, image_ids: list) -> bool:
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


def _make_collection_remover(base_url: str):
    def remove(collection_id: str, image_id: str) -> bool:
        try:
            response = httpx.delete(
                f"{base_url}/api/v1/collections/{collection_id}/images/{image_id}",
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False
    return remove


def _make_image_verifier(base_url: str):
    def verify(image_id: str) -> str | None:
        try:
            response = httpx.post(f"{base_url}/api/v1/images/{image_id}/verify", timeout=10.0)
            data = response.json()
            if data.get("success"):
                return data.get("data", {}).get("file_status")
            return None
        except Exception:
            return None
    return verify


def _make_page_fetcher(base_url: str):
    def fetch(cursor=None, limit=100, import_job=None, category=None, tag=None,
              file_status=None, exclude_category=None, exclude_tag=None):
        try:
            params: dict = {"view": "grid", "limit": limit}
            if cursor:
                params["cursor"] = cursor
            if import_job:
                params["import_job"] = import_job
            if category:
                params["categories"] = category        # API uses plural
            if exclude_category:
                params["exclude_categories"] = exclude_category
            if tag:
                params["tags"] = tag                   # API uses plural
            if exclude_tag:
                params["exclude_tags"] = exclude_tag
            if file_status == "missing":
                params["missing"] = True               # API uses boolean flag
            response = httpx.get(f"{base_url}/api/v1/images", params=params, timeout=10.0)
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

    filter_state = FilterStateManager()
    library_state = LibraryViewModel(
        page_fetcher=_make_page_fetcher(base_url),
        filter_state=filter_state,
        image_verifier=_make_image_verifier(base_url),
    )
    categories_state = CategoriesViewModel(
        categories_fetcher=_make_categories_fetcher(base_url),
        category_creator=_make_category_creator(base_url),
        images_adder=_make_category_images_adder(base_url),
        filter_state=filter_state,
    )
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

    def _on_import_loading_state_changed(state: str) -> None:
        if state == "Scanning":
            filter_state.setImportJobFilter("")

    import_state.loadingStateChanged.connect(_on_import_loading_state_changed)
    import_state.importJobDone.connect(filter_state.setImportJobFilter)

    def _on_tag_modified() -> None:
        if filter_state.tagFilters:
            library_state.reload()

    def _on_category_modified() -> None:
        if filter_state.categoryFilters:
            library_state.reload()

    metadata_state = MetadataViewModel(
        image_fetcher=_make_image_fetcher(base_url),
        selection_manager=selection_manager,
    )
    tag_search_state = TagSearchViewModel(
        tags_fetcher=_make_tags_fetcher(base_url),
        filter_state=filter_state,
    )
    tag_editor_search_state = TagSearchViewModel(
        tags_fetcher=_make_tags_fetcher(base_url),
    )
    tag_editor_state = TagEditorViewModel(
        image_tags_fetcher=_make_image_tags_fetcher(base_url),
        tag_modifier=_make_bulk_tag_modifier(base_url),
        tag_creator=_make_tag_creator(base_url),
        selection_manager=selection_manager,
    )
    category_editor_search_state = TagSearchViewModel(
        tags_fetcher=_make_category_searcher(base_url),
    )
    category_editor_state = CategoryEditorViewModel(
        image_categories_fetcher=_make_image_categories_fetcher(base_url),
        category_modifier=_make_bulk_category_modifier(base_url),
        selection_manager=selection_manager,
    )
    collection_editor_state = CollectionEditorViewModel(
        image_collections_fetcher=_make_image_collections_fetcher(base_url),
        collection_adder=_make_collection_adder(base_url),
        collection_remover=_make_collection_remover(base_url),
        selection_manager=selection_manager,
    )

    tag_editor_state.modified.connect(_on_tag_modified)
    category_editor_state.modified.connect(_on_category_modified)
    collection_editor_state.modified.connect(collections_state.reloadCollectionImages)

    controller = AppController(
        app_state,
        process_manager,
        connection_monitor=connection_monitor,
        library_view_model=library_state,
    )

    app_metadata = get_app_metadata()

    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbnails", thumbnail_provider)
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("foundVersion", app_metadata["version"])
    engine.rootContext().setContextProperty("foundLicense", app_metadata["license"])
    engine.rootContext().setContextProperty("AppState", app_state)
    engine.rootContext().setContextProperty("BackendConnection", connection_monitor)
    engine.rootContext().setContextProperty("LibraryState", library_state)
    engine.rootContext().setContextProperty("SelectionManager", selection_manager)
    engine.rootContext().setContextProperty("NavigationManager", navigation_manager)
    engine.rootContext().setContextProperty("CategoriesState", categories_state)
    engine.rootContext().setContextProperty("CollectionsState", collections_state)
    engine.rootContext().setContextProperty("ImportState", import_state)
    engine.rootContext().setContextProperty("FilterState", filter_state)
    engine.rootContext().setContextProperty("MetadataState", metadata_state)
    engine.rootContext().setContextProperty("TagSearchState", tag_search_state)
    engine.rootContext().setContextProperty("TagEditorSearchState", tag_editor_search_state)
    engine.rootContext().setContextProperty("TagEditorState", tag_editor_state)
    engine.rootContext().setContextProperty("CategoryEditorSearchState", category_editor_search_state)
    engine.rootContext().setContextProperty("CategoryEditorState", category_editor_state)
    engine.rootContext().setContextProperty("CollectionEditorState", collection_editor_state)
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
