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

    response = client.get("/api/v1/images?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 3


def test_list_images_pagination(client, make_image):
    from datetime import datetime, timezone, timedelta
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(5):
        make_image(f"/photos/page_{i}.jpg", imported_date=base + timedelta(seconds=i))

    page1 = client.get("/api/v1/images?limit=2").json()
    assert page1["success"] is True
    assert len(page1["data"]) == 2
    assert page1["has_more"] is True

    page2 = client.get(f"/api/v1/images?limit=2&cursor={page1['next_cursor']}").json()
    assert page2["success"] is True
    assert len(page2["data"]) == 2
    assert page2["has_more"] is True

    page3 = client.get(f"/api/v1/images?limit=2&cursor={page2['next_cursor']}").json()
    assert page3["success"] is True
    assert len(page3["data"]) == 1
    assert page3["has_more"] is False


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
