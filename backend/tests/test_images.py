def test_get_image(client, make_image):
    image = make_image("/photos/photo.jpg")
    response = client.get(f"/api/v1/images/{image.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == str(image.id)
    assert data["data"]["filename"] == "photo.jpg"


def test_get_image_not_found(client):
    response = client.get("/api/v1/images/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "not_found"


def test_list_images(client, make_image):
    for i in range(3):
        make_image(f"/photos/photo_{i}.jpg")

    response = client.get("/api/v1/images?offset=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 3


def test_list_images_pagination(client, make_image):
    for i in range(5):
        make_image(f"/photos/page_{i}.jpg")

    page = client.get("/api/v1/images?offset=2&limit=2").json()
    assert page["success"] is True
    assert len(page["data"]) == 2


def test_delete_image(client, make_image):
    image = make_image("/photos/photo.jpg")
    response = client.delete(f"/api/v1/images/{image.id}")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert client.get(f"/api/v1/images/{image.id}").status_code == 404


def test_delete_image_not_found(client):
    response = client.delete("/api/v1/images/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["success"] is False
