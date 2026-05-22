import pytest

_IMAGE = {"filename": "b.jpg", "path": "/photos/b.jpg"}
_CATEGORY = {"name": "Architecture", "description": "Buildings and structures"}


@pytest.fixture
def image_id(client):
    return client.post("/api/v1/images", json=_IMAGE).json()["data"]["id"]


@pytest.fixture
def category_id(client):
    return client.post("/api/v1/categories", json=_CATEGORY).json()["data"]["id"]


def test_create_category(client):
    response = client.post("/api/v1/categories", json=_CATEGORY)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Architecture"
    assert data["data"]["description"] == "Buildings and structures"


def test_list_categories(client):
    client.post("/api/v1/categories", json=_CATEGORY)
    client.post("/api/v1/categories", json={"name": "Nature", "description": ""})
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_update_category(client, category_id):
    response = client.put(
        f"/api/v1/categories/{category_id}",
        json={"name": "Urban", "description": "City scenes"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Urban"
    assert data["description"] == "City scenes"


def test_delete_category(client, category_id):
    response = client.delete(f"/api/v1/categories/{category_id}")
    assert response.status_code == 200
    assert len(client.get("/api/v1/categories").json()["data"]) == 0


def test_assign_category_to_image(client, image_id, category_id):
    response = client.post(
        f"/api/v1/images/{image_id}/categories",
        json={"category_ids": [category_id]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_prevent_duplicate_category_assignment(client, image_id, category_id):
    client.post(
        f"/api/v1/images/{image_id}/categories",
        json={"category_ids": [category_id]},
    )
    client.post(
        f"/api/v1/images/{image_id}/categories",
        json={"category_ids": [category_id]},
    )
    categories = client.get(f"/api/v1/images/{image_id}/categories").json()["data"]
    assert len(categories) == 1


def test_replace_image_categories(client, image_id):
    cat_a = client.post(
        "/api/v1/categories", json={"name": "A", "description": ""}
    ).json()["data"]["id"]
    cat_b = client.post(
        "/api/v1/categories", json={"name": "B", "description": ""}
    ).json()["data"]["id"]

    client.post(
        f"/api/v1/images/{image_id}/categories", json={"category_ids": [cat_a]}
    )
    client.put(
        f"/api/v1/images/{image_id}/categories", json={"category_ids": [cat_b]}
    )

    categories = client.get(f"/api/v1/images/{image_id}/categories").json()["data"]
    assert len(categories) == 1
    assert categories[0]["name"] == "B"


def test_remove_category_from_image(client, image_id, category_id):
    client.post(
        f"/api/v1/images/{image_id}/categories",
        json={"category_ids": [category_id]},
    )
    response = client.delete(
        f"/api/v1/images/{image_id}/categories/{category_id}"
    )
    assert response.status_code == 200
    assert client.get(f"/api/v1/images/{image_id}/categories").json()["data"] == []
