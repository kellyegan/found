import pytest

_COLLECTION = {"name": "Favourites", "description": "My best picks"}


@pytest.fixture
def image_ids(make_image):
    return [str(make_image(f"/photos/img{i}.jpg").id) for i in range(3)]


@pytest.fixture
def collection_id(client):
    return client.post("/api/v1/collections", json=_COLLECTION).json()["data"]["id"]


def test_create_collection(client):
    response = client.post("/api/v1/collections", json=_COLLECTION)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Favourites"
    assert data["data"]["id"] is not None


def test_list_collections(client):
    client.post("/api/v1/collections", json=_COLLECTION)
    client.post("/api/v1/collections", json={"name": "Moodboard", "description": ""})
    response = client.get("/api/v1/collections")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_update_collection(client, collection_id):
    response = client.put(
        f"/api/v1/collections/{collection_id}",
        json={"name": "Best Of", "description": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Best Of"


def test_delete_collection(client, collection_id):
    response = client.delete(f"/api/v1/collections/{collection_id}")
    assert response.status_code == 200
    assert len(client.get("/api/v1/collections").json()["data"]) == 0


def test_add_images_to_collection(client, collection_id, image_ids):
    response = client.post(
        f"/api/v1/collections/{collection_id}/images",
        json={"image_ids": image_ids},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_collection_images_ordered(client, collection_id, image_ids):
    client.post(
        f"/api/v1/collections/{collection_id}/images",
        json={"image_ids": image_ids},
    )
    response = client.get(f"/api/v1/collections/{collection_id}/images")
    assert response.status_code == 200
    returned_ids = [img["id"] for img in response.json()["data"]]
    assert returned_ids == image_ids


def test_remove_image_from_collection(client, collection_id, image_ids):
    client.post(
        f"/api/v1/collections/{collection_id}/images",
        json={"image_ids": image_ids},
    )
    client.delete(f"/api/v1/collections/{collection_id}/images/{image_ids[0]}")
    remaining = client.get(f"/api/v1/collections/{collection_id}/images").json()["data"]
    assert len(remaining) == 2
    assert all(img["id"] != image_ids[0] for img in remaining)


def test_reorder_collection_images(client, collection_id, image_ids):
    client.post(
        f"/api/v1/collections/{collection_id}/images",
        json={"image_ids": image_ids},
    )
    reversed_ids = list(reversed(image_ids))
    client.put(
        f"/api/v1/collections/{collection_id}/order",
        json={"image_ids": reversed_ids},
    )
    returned_ids = [
        img["id"]
        for img in client.get(f"/api/v1/collections/{collection_id}/images").json()["data"]
    ]
    assert returned_ids == reversed_ids


def test_get_image_collections(client, collection_id, image_ids):
    client.post(
        f"/api/v1/collections/{collection_id}/images",
        json={"image_ids": [image_ids[0]]},
    )
    response = client.get(f"/api/v1/images/{image_ids[0]}/collections")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == collection_id


def test_get_image_collections_empty(client, image_ids):
    response = client.get(f"/api/v1/images/{image_ids[0]}/collections")
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_get_image_collections_multiple(client, image_ids):
    col_b = client.post(
        "/api/v1/collections", json={"name": "Moodboard", "description": ""}
    ).json()["data"]["id"]
    col_c = client.post(
        "/api/v1/collections", json={"name": "References", "description": ""}
    ).json()["data"]["id"]
    client.post(f"/api/v1/collections/{col_b}/images", json={"image_ids": [image_ids[0]]})
    client.post(f"/api/v1/collections/{col_c}/images", json={"image_ids": [image_ids[0]]})
    data = client.get(f"/api/v1/images/{image_ids[0]}/collections").json()["data"]
    assert len(data) == 2
    returned_ids = {c["id"] for c in data}
    assert returned_ids == {col_b, col_c}
