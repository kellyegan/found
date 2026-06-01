"""Basic single-value filtering for GET /api/v1/images.

Covers filtering by tag, category, and collection.
Multi-value AND/exclude logic lives in test_multi_filter.py.
"""


def test_filter_by_tag(client, make_image):
    img_a = str(make_image("/filter/a.jpg").id)
    img_b = str(make_image("/filter/b.jpg").id)

    tag_id = client.post("/api/v1/tags", json={"name": "nature"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?tags=nature").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_tag_is_case_insensitive(client, make_image):
    img_a = str(make_image("/filter/c.jpg").id)
    tag_id = client.post("/api/v1/tags", json={"name": "urban"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?tags=URBAN").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_category(client, make_image):
    img_a = str(make_image("/filter/d.jpg").id)
    make_image("/filter/e.jpg")

    cat_id = client.post(
        "/api/v1/categories", json={"name": "Architecture", "description": ""}
    ).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/categories", json={"category_ids": [cat_id]})

    result = client.get(f"/api/v1/images?categories={cat_id}").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_collection(client, make_image):
    img_a = str(make_image("/filter/f.jpg").id)
    make_image("/filter/g.jpg")

    col_id = client.post(
        "/api/v1/collections", json={"name": "Picks", "description": ""}
    ).json()["data"]["id"]
    client.post(f"/api/v1/collections/{col_id}/images", json={"image_ids": [img_a]})

    result = client.get(f"/api/v1/images?collection={col_id}").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_no_filter_returns_all(client, make_image):
    for i in range(4):
        make_image(f"/filter/h{i}.jpg")

    result = client.get("/api/v1/images").json()["data"]
    assert len(result) == 4
