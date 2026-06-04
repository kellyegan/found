from PySide6.QtCore import QThreadPool

from found_app.core.api_client import ApiClient
from found_app.core.app_controller import AppController
from found_app.core.app_state import AppStateManager
from found_app.core.connection_monitor import BackendConnectionManager
from found_app.core.process_manager import BackendProcessManager
from found_app.categories.categories_view_model import CategoriesViewModel
from found_app.category_editor.category_editor_view_model import CategoryEditorViewModel
from found_app.collection_editor.collection_editor_view_model import CollectionEditorViewModel
from found_app.collections.collections_view_model import CollectionsViewModel
from found_app.import_workflow.import_view_model import ImportViewModel
from found_app.providers.thumbnail_provider import ThumbnailProvider
from found_app.viewmodels.library_view_model import LibraryViewModel
from found_app.metadata.metadata_view_model import MetadataViewModel
from found_app.services.filter_state import FilterStateManager
from found_app.services.navigation import NavigationManager
from found_app.services.selection import SelectionManager
from found_app.tag_editor.tag_editor_view_model import TagEditorViewModel
from found_app.tag_search.tag_search_view_model import TagSearchViewModel
from found_app.theme.theme import ThemeManager
from found_app.version import get_app_metadata


class AppContainer:
    """Owns all ViewModel instantiation, signal wiring, and lifecycle."""

    def __init__(self):
        self._theme = ThemeManager()
        self._app_state = AppStateManager()
        self._process_manager = BackendProcessManager()
        self._connection_monitor = BackendConnectionManager(
            health_checker=self._process_manager._health_checker,
            health_url=self._process_manager.health_url,
        )
        base_url = f"http://{self._process_manager._host}:{self._process_manager._port}"
        self._base_url = base_url
        self._api_client = ApiClient(base_url=base_url)

        self._filter_state = FilterStateManager()
        self._library_state = LibraryViewModel(
            page_fetcher=self._api_client.fetch_images_page,
            filter_state=self._filter_state,
            image_verifier=self._api_client.verify_image,
        )
        self._categories_state = CategoriesViewModel(
            categories_fetcher=self._api_client.list_categories,
            category_creator=self._api_client.create_category,
            images_adder=self._api_client.add_images_to_category,
            filter_state=self._filter_state,
        )
        self.thumbnail_provider = ThumbnailProvider(base_url=base_url)
        self._selection_manager = SelectionManager()
        self._navigation_manager = NavigationManager()
        self._collections_state = CollectionsViewModel(
            collections_fetcher=self._api_client.list_collections,
            collection_creator=self._api_client.create_collection,
            images_adder=self._api_client.add_images_to_collection,
            collection_images_fetcher=self._api_client.fetch_collection_images,
        )
        self._import_state = ImportViewModel(
            scanner=self._api_client.scan_paths,
            importer=self._api_client.import_paths,
            job_fetcher=self._api_client.fetch_job,
            conflict_resolver=self._api_client.resolve_conflict,
        )
        self._metadata_state = MetadataViewModel(
            image_fetcher=self._api_client.fetch_image,
            selection_manager=self._selection_manager,
        )
        self._tag_search_state = TagSearchViewModel(
            tags_fetcher=self._api_client.search_tags,
            filter_state=self._filter_state,
        )
        self._tag_editor_search_state = TagSearchViewModel(
            tags_fetcher=self._api_client.search_tags,
        )
        self._tag_editor_state = TagEditorViewModel(
            image_tags_fetcher=self._api_client.fetch_image_tags,
            tag_modifier=self._api_client.bulk_modify_tags,
            tag_creator=self._api_client.create_tag,
            selection_manager=self._selection_manager,
        )
        self._category_editor_search_state = TagSearchViewModel(
            tags_fetcher=self._api_client.search_categories,
        )
        self._category_editor_state = CategoryEditorViewModel(
            image_categories_fetcher=self._api_client.fetch_image_categories,
            category_modifier=self._api_client.bulk_modify_categories,
            selection_manager=self._selection_manager,
        )
        self._collection_editor_state = CollectionEditorViewModel(
            image_collections_fetcher=self._api_client.fetch_image_collections,
            collection_adder=self._api_client.add_images_to_collection,
            collection_remover=self._api_client.remove_image_from_collection,
            selection_manager=self._selection_manager,
        )

        self._controller = AppController(
            self._app_state,
            self._process_manager,
            connection_monitor=self._connection_monitor,
            library_view_model=self._library_state,
        )

        self._wire_signals()

    def _wire_signals(self):
        def _on_import_loading_state_changed(state: str) -> None:
            if state == "Scanning":
                self._filter_state.setImportJobFilter("")

        self._import_state.loadingStateChanged.connect(_on_import_loading_state_changed)
        self._import_state.importJobDone.connect(self._filter_state.setImportJobFilter)

        def _on_tag_modified() -> None:
            if self._filter_state.tagFilters:
                self._library_state.reload()

        def _on_category_modified() -> None:
            if self._filter_state.categoryFilters:
                self._library_state.reload()

        self._tag_editor_state.modified.connect(_on_tag_modified)
        self._category_editor_state.modified.connect(_on_category_modified)
        self._collection_editor_state.modified.connect(
            self._collections_state.reloadCollectionImages
        )

    def wire_engine(self, engine) -> None:
        app_metadata = get_app_metadata()
        ctx = engine.rootContext()
        engine.addImageProvider("thumbnails", self.thumbnail_provider)
        ctx.setContextProperty("Theme", self._theme)
        ctx.setContextProperty("foundVersion", app_metadata["version"])
        ctx.setContextProperty("foundLicense", app_metadata["license"])
        ctx.setContextProperty("AppState", self._app_state)
        ctx.setContextProperty("BackendConnection", self._connection_monitor)
        ctx.setContextProperty("LibraryState", self._library_state)
        ctx.setContextProperty("SelectionManager", self._selection_manager)
        ctx.setContextProperty("NavigationManager", self._navigation_manager)
        ctx.setContextProperty("CategoriesState", self._categories_state)
        ctx.setContextProperty("CollectionsState", self._collections_state)
        ctx.setContextProperty("ImportState", self._import_state)
        ctx.setContextProperty("FilterState", self._filter_state)
        ctx.setContextProperty("MetadataState", self._metadata_state)
        ctx.setContextProperty("TagSearchState", self._tag_search_state)
        ctx.setContextProperty("TagEditorSearchState", self._tag_editor_search_state)
        ctx.setContextProperty("TagEditorState", self._tag_editor_state)
        ctx.setContextProperty("CategoryEditorSearchState", self._category_editor_search_state)
        ctx.setContextProperty("CategoryEditorState", self._category_editor_state)
        ctx.setContextProperty("CollectionEditorState", self._collection_editor_state)
        ctx.setContextProperty("baseUrl", self._base_url)

    def start(self) -> None:
        self._controller.start()

    def shutdown(self) -> None:
        self._controller.shutdown()
        self._library_state.shutdown()
        QThreadPool.globalInstance().waitForDone(2000)
