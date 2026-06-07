import httpx


class ApiError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class NetworkError(Exception):
    pass


class NotFoundError(ApiError):
    def __init__(self, message: str = "Not found"):
        super().__init__("not_found", message)


class ApiClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        client: httpx.AsyncClient | None = None,
        sync_client: httpx.Client | None = None,
    ):
        self._base_url = base_url
        self._client = client or httpx.AsyncClient(base_url=base_url)
        self._sync_client = sync_client or httpx.Client(base_url=base_url)

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def request(self, method: str, path: str, **kwargs):
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.NetworkError as exc:
            raise NetworkError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            raise NetworkError(f"Request timed out: {exc}") from exc

        return self._parse_response(response)

    def _parse_response(self, response: httpx.Response):
        if response.status_code == 404:
            try:
                error = response.json().get("error", {})
                message = error.get("message", "Not found")
            except Exception:
                message = "Not found"
            raise NotFoundError(message)

        try:
            body = response.json()
        except Exception as exc:
            raise ApiError("parse_error", f"Invalid response body: {exc}") from exc

        if not body.get("success"):
            error = body.get("error", {})
            raise ApiError(
                error.get("code", "unknown"),
                error.get("message", "Unknown error"),
            )

        return body.get("data")

    async def list_images(
        self,
        cursor: str | None = None,
        limit: int = 100,
        view: str = "grid",
    ) -> tuple[list[dict], str | None, bool]:
        params: dict = {"limit": limit, "view": view}
        if cursor is not None:
            params["cursor"] = cursor
        try:
            response = await self._client.get("/api/v1/images", params=params)
        except httpx.NetworkError as exc:
            raise NetworkError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            raise NetworkError(f"Request timed out: {exc}") from exc
        try:
            body = response.json()
        except Exception as exc:
            raise ApiError("parse_error", f"Invalid response body: {exc}") from exc
        if not body.get("success"):
            error = body.get("error", {})
            raise ApiError(
                error.get("code", "unknown"),
                error.get("message", "Unknown error"),
            )
        return body.get("data", []), body.get("next_cursor"), body.get("has_more", False)

    def fetch_images_page(
        self,
        cursor=None,
        limit=100,
        import_job=None,
        category=None,
        tag=None,
        file_status=None,
        exclude_category=None,
        exclude_tag=None,
    ) -> dict | None:
        try:
            params: dict = {"view": "grid", "limit": limit}
            if cursor:
                params["cursor"] = cursor
            if import_job:
                params["import_job"] = import_job
            if category:
                params["categories"] = category
            if exclude_category:
                params["exclude_categories"] = exclude_category
            if tag:
                params["tags"] = tag
            if exclude_tag:
                params["exclude_tags"] = exclude_tag
            if file_status == "missing":
                params["missing"] = True
            response = self._sync_client.get("/api/v1/images", params=params, timeout=10.0)
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

    def fetch_image(self, image_id: str) -> dict | None:
        try:
            response = self._sync_client.get(f"/api/v1/images/{image_id}", timeout=10.0)
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None

    def verify_image(self, image_id: str) -> str | None:
        try:
            response = self._sync_client.post(f"/api/v1/images/{image_id}/verify", timeout=10.0)
            data = response.json()
            if data.get("success"):
                return data.get("data", {}).get("file_status")
            return None
        except Exception:
            return None

    def scan_paths(self, paths: list[str]) -> dict | None:
        try:
            response = self._sync_client.post(
                "/api/v1/images/import/preview", json={"paths": paths}, timeout=30.0
            )
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None

    def import_paths(self, paths: list[str]) -> str | None:
        try:
            response = self._sync_client.post(
                "/api/v1/images/import", json={"paths": paths}, timeout=30.0
            )
            data = response.json()
            return data["data"]["job_id"] if data.get("success") else None
        except Exception:
            return None

    def fetch_job(self, job_id: str) -> dict | None:
        try:
            response = self._sync_client.get(f"/api/v1/jobs/{job_id}", timeout=10.0)
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None

    def resolve_conflict(self, image_id: str, new_path: str) -> bool:
        try:
            response = self._sync_client.patch(
                f"/api/v1/images/{image_id}", json={"path": new_path}, timeout=10.0
            )
            return response.json().get("success", False)
        except Exception:
            return False

    def create_tag(self, name: str) -> dict | None:
        try:
            response = self._sync_client.post("/api/v1/tags", json={"name": name}, timeout=10.0)
            data = response.json()
            if data.get("success"):
                return data.get("data")
            if response.status_code == 409:
                search = self._sync_client.get(
                    "/api/v1/tags/search", params={"q": name}, timeout=10.0
                )
                search_data = search.json()
                tags = search_data.get("data", []) if search_data.get("success") else []
                for tag in tags:
                    if tag.get("name", "").lower() == name.lower():
                        return tag
            return None
        except Exception:
            return None

    def search_tags(self, term: str) -> list | None:
        try:
            response = self._sync_client.get(
                "/api/v1/tags/search", params={"q": term}, timeout=10.0
            )
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def fetch_image_tags(self, image_id: str) -> list | None:
        try:
            response = self._sync_client.get(f"/api/v1/images/{image_id}/tags", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def bulk_modify_tags(
        self, image_ids: list, add_tag_ids: list, remove_tag_ids: list
    ) -> bool:
        try:
            response = self._sync_client.post(
                "/api/v1/images/bulk/tags",
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

    def list_categories(self) -> list | None:
        try:
            response = self._sync_client.get("/api/v1/categories", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def create_category(self, name: str) -> dict | None:
        try:
            response = self._sync_client.post(
                "/api/v1/categories",
                json={"name": name, "description": ""},
                timeout=10.0,
            )
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None

    def search_categories(self, term: str) -> list | None:
        try:
            response = self._sync_client.get(
                "/api/v1/categories/search", params={"q": term}, timeout=10.0
            )
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def add_images_to_category(self, category_id: str, image_ids: list) -> bool:
        try:
            response = self._sync_client.post(
                "/api/v1/images/bulk/categories",
                json={"image_ids": image_ids, "add_category_ids": [category_id]},
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False

    def fetch_image_categories(self, image_id: str) -> list | None:
        try:
            response = self._sync_client.get(
                f"/api/v1/images/{image_id}/categories", timeout=10.0
            )
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def bulk_modify_categories(
        self, image_ids: list, add_category_ids: list, remove_category_ids: list
    ) -> bool:
        try:
            response = self._sync_client.post(
                "/api/v1/images/bulk/categories",
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

    def list_collections(self) -> list | None:
        try:
            response = self._sync_client.get("/api/v1/collections", timeout=10.0)
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def create_collection(self, name: str) -> dict | None:
        try:
            response = self._sync_client.post(
                "/api/v1/collections", json={"name": name}, timeout=10.0
            )
            data = response.json()
            return data.get("data") if data.get("success") else None
        except Exception:
            return None

    def add_images_to_collection(self, collection_id: str, image_ids: list) -> bool:
        try:
            response = self._sync_client.post(
                f"/api/v1/collections/{collection_id}/images",
                json={"image_ids": image_ids},
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False

    def fetch_collection_images(self, collection_id: str) -> list | None:
        try:
            response = self._sync_client.get(
                f"/api/v1/collections/{collection_id}/images",
                params={"view": "grid"},
                timeout=10.0,
            )
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def fetch_image_collections(self, image_id: str) -> list | None:
        try:
            response = self._sync_client.get(
                f"/api/v1/images/{image_id}/collections", timeout=10.0
            )
            data = response.json()
            return data.get("data", []) if data.get("success") else None
        except Exception:
            return None

    def remove_image_from_collection(self, collection_id: str, image_id: str) -> bool:
        try:
            response = self._sync_client.delete(
                f"/api/v1/collections/{collection_id}/images/{image_id}",
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False

    def delete_image(self, image_id: str) -> bool:
        try:
            response = self._sync_client.delete(
                f"/api/v1/images/{image_id}", timeout=10.0
            )
            return response.json().get("success", False)
        except Exception:
            return False

    def bulk_delete_images(self, image_ids: list) -> bool:
        try:
            response = self._sync_client.post(
                "/api/v1/images/bulk/delete",
                json={"image_ids": image_ids},
                timeout=10.0,
            )
            return response.json().get("success", False)
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "ApiClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
