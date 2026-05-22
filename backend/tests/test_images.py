import pytest


_IMAGE_PAYLOAD = {
    "filename": "photo.jpg",
    "path": "/photos/photo.jpg",
    "width": 1920,
    "height": 1080,
    "file_size": 204800,
    "mime_type": "image/jpeg",
}


def test_create_image(client):
    response = client.post("/api/v1/images", json=_IMAGE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] is not None
    assert data["data"]["filename"] == "photo.jpg"
    assert data["data"]["path"] == "/photos/photo.jpg"
    assert data["data"]["file_status"] == "available"
    assert data["data"]["imported_date"] is not None


def test_get_image(client):
    image_id = client.post("/api/v1/images", json=_IMAGE_PAYLOAD).json()["data"]["id"]

    response = client.get(f"/api/v1/images/{image_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == image_id
    assert data["data"]["filename"] == "photo.jpg"


def test_get_image_not_found(client):
    response = client.get("/api/v1/images/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "not_found"


def test_list_images(client):
    for i in range(3):
        payload = {**_IMAGE_PAYLOAD, "path": f"/photos/photo_{i}.jpg"}
        client.post("/api/v1/images", json=payload)

    response = client.get("/api/v1/images?offset=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 3


def test_list_images_pagination(client):
    for i in range(5):
        payload = {**_IMAGE_PAYLOAD, "path": f"/photos/page_{i}.jpg"}
        client.post("/api/v1/images", json=payload)

    page = client.get("/api/v1/images?offset=2&limit=2").json()
    assert page["success"] is True
    assert len(page["data"]) == 2


def test_delete_image(client):
    image_id = client.post("/api/v1/images", json=_IMAGE_PAYLOAD).json()["data"]["id"]

    response = client.delete(f"/api/v1/images/{image_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    assert client.get(f"/api/v1/images/{image_id}").status_code == 404


def test_delete_image_not_found(client):
    response = client.delete("/api/v1/images/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["success"] is False
