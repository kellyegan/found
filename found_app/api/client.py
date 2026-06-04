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
    ):
        self._base_url = base_url
        self._client = client or httpx.AsyncClient(base_url=base_url)

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

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "ApiClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
