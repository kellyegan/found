import pytest


@pytest.fixture
def image_id(make_image):
    return str(make_image("/photos/a.jpg").id)


@pytest.fixture
def tag_id(client):
    return client.post("/api/v1/tags", json={"name": "nature"}).json()["data"]["id"]


def test_create_tag(client):
    response = client.post("/api/v1/tags", json={"name": "nature"})
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "nature"
    assert data["data"]["id"] is not None


def test_tag_stored_lowercase(client):
    response = client.post("/api/v1/tags", json={"name": "NATURE"})
    assert response.json()["data"]["name"] == "nature"


def test_duplicate_tag_name_rejected(client):
    client.post("/api/v1/tags", json={"name": "nature"})
    response = client.post("/api/v1/tags", json={"name": "NATURE"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_tag"


def test_list_tags(client):
    client.post("/api/v1/tags", json={"name": "nature"})
    client.post("/api/v1/tags", json={"name": "urban"})
    response = client.get("/api/v1/tags")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_update_tag(client, tag_id):
    response = client.put(f"/api/v1/tags/{tag_id}", json={"name": "wildlife"})
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "wildlife"


def test_delete_tag(client, tag_id):
    response = client.delete(f"/api/v1/tags/{tag_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(client.get("/api/v1/tags").json()["data"]) == 0


def test_add_tags_to_image(client, image_id, tag_id):
    response = client.post(
        f"/api/v1/images/{image_id}/tags", json={"tag_ids": [tag_id]}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_replace_image_tags(client, image_id):
    tag_a = client.post("/api/v1/tags", json={"name": "a"}).json()["data"]["id"]
    tag_b = client.post("/api/v1/tags", json={"name": "b"}).json()["data"]["id"]
    tag_c = client.post("/api/v1/tags", json={"name": "c"}).json()["data"]["id"]

    client.post(f"/api/v1/images/{image_id}/tags", json={"tag_ids": [tag_a, tag_b]})
    client.put(f"/api/v1/images/{image_id}/tags", json={"tag_ids": [tag_c]})

    tags = client.get(f"/api/v1/images/{image_id}/tags").json()["data"]
    assert len(tags) == 1
    assert tags[0]["name"] == "c"


def test_remove_tag_from_image(client, image_id, tag_id):
    client.post(f"/api/v1/images/{image_id}/tags", json={"tag_ids": [tag_id]})
    response = client.delete(f"/api/v1/images/{image_id}/tags/{tag_id}")
    assert response.status_code == 200
    assert client.get(f"/api/v1/images/{image_id}/tags").json()["data"] == []
