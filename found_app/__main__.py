import sys
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from found_app.api.client import ApiClient
from found_app.app.controller import AppController
from found_app.core.connection_monitor import BackendConnectionManager
from found_app.core.process_manager import BackendProcessManager
from found_app.category_editor.category_editor_view_model import CategoryEditorViewModel
from found_app.collection_editor.collection_editor_view_model import CollectionEditorViewModel
from found_app.collections.collections_view_model import CollectionsViewModel
from found_app.filters.filter_state_manager import FilterStateManager
from found_app.import_workflow.import_view_model import ImportViewModel
from found_app.library.thumbnail_provider import ThumbnailProvider
from found_app.library.view_model import LibraryViewModel
from found_app.metadata.metadata_view_model import MetadataViewModel
from found_app.navigation.navigation_manager import NavigationManager
from found_app.tag_editor.tag_editor_view_model import TagEditorViewModel
from found_app.tag_search.tag_search_view_model import TagSearchViewModel
from found_app.selection.selection_manager import SelectionManager
from found_app.state.app_state import AppStateManager
from found_app.categories.categories_view_model import CategoriesViewModel
from found_app.theme.theme import ThemeManager
from found_app.version import get_app_metadata


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
    api_client = ApiClient(base_url=base_url)

    filter_state = FilterStateManager()
    library_state = LibraryViewModel(
        page_fetcher=api_client.fetch_images_page,
        filter_state=filter_state,
        image_verifier=api_client.verify_image,
    )
    categories_state = CategoriesViewModel(
        categories_fetcher=api_client.list_categories,
        category_creator=api_client.create_category,
        images_adder=api_client.add_images_to_category,
        filter_state=filter_state,
    )
    thumbnail_provider = ThumbnailProvider(base_url=base_url)
    selection_manager = SelectionManager()
    navigation_manager = NavigationManager()
    collections_state = CollectionsViewModel(
        collections_fetcher=api_client.list_collections,
        collection_creator=api_client.create_collection,
        images_adder=api_client.add_images_to_collection,
        collection_images_fetcher=api_client.fetch_collection_images,
    )
    import_state = ImportViewModel(
        scanner=api_client.scan_paths,
        importer=api_client.import_paths,
        job_fetcher=api_client.fetch_job,
        conflict_resolver=api_client.resolve_conflict,
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
        image_fetcher=api_client.fetch_image,
        selection_manager=selection_manager,
    )
    tag_search_state = TagSearchViewModel(
        tags_fetcher=api_client.search_tags,
        filter_state=filter_state,
    )
    tag_editor_search_state = TagSearchViewModel(
        tags_fetcher=api_client.search_tags,
    )
    tag_editor_state = TagEditorViewModel(
        image_tags_fetcher=api_client.fetch_image_tags,
        tag_modifier=api_client.bulk_modify_tags,
        tag_creator=api_client.create_tag,
        selection_manager=selection_manager,
    )
    category_editor_search_state = TagSearchViewModel(
        tags_fetcher=api_client.search_categories,
    )
    category_editor_state = CategoryEditorViewModel(
        image_categories_fetcher=api_client.fetch_image_categories,
        category_modifier=api_client.bulk_modify_categories,
        selection_manager=selection_manager,
    )
    collection_editor_state = CollectionEditorViewModel(
        image_collections_fetcher=api_client.fetch_image_collections,
        collection_adder=api_client.add_images_to_collection,
        collection_remover=api_client.remove_image_from_collection,
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
