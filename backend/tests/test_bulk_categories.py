"""Tests for POST /api/v1/images/bulk/categories."""


def _category(client, name: str) -> str:
    return client.post(
        "/api/v1/categories", json={"name": name, "description": ""}
    ).json()["data"]["id"]


def _cats_on(client, image_id) -> set[str]:
    return {c["id"] for c in client.get(f"/api/v1/images/{image_id}/categories").json()["data"]}


# ── Add categories ────────────────────────────────────────────────────────────

def test_bulk_add_categories_to_multiple_images(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    cat_id = _category(client, "Architecture")

    response = client.post(
        "/api/v1/images/bulk/categories",
        json={"image_ids": [str(img_a.id), str(img_b.id)], "add_category_ids": [cat_id]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert cat_id in _cats_on(client, img_a.id)
    assert cat_id in _cats_on(client, img_b.id)


def test_bulk_add_multiple_categories_to_multiple_images(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    cat1_id = _category(client, "Architecture")
    cat2_id = _category(client, "Design")

    client.post(
        "/api/v1/images/bulk/categories",
        json={"image_ids": [str(img_a.id), str(img_b.id)], "add_category_ids": [cat1_id, cat2_id]},
    )
    assert _cats_on(client, img_a.id) == {cat1_id, cat2_id}
    assert _cats_on(client, img_b.id) == {cat1_id, cat2_id}


def test_bulk_add_ignores_duplicate_assignment(client, make_image):
    img = make_image("/a.jpg")
    cat_id = _category(client, "Architecture")

    client.post(f"/api/v1/images/{img.id}/categories", json={"category_ids": [cat_id]})

    response = client.post(
        "/api/v1/images/bulk/categories",
        json={"image_ids": [str(img.id)], "add_category_ids": [cat_id]},
    )
    assert response.status_code == 200
    assert _cats_on(client, img.id) == {cat_id}


# ── Remove categories ─────────────────────────────────────────────────────────

def test_bulk_remove_categories_from_multiple_images(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    cat_id = _category(client, "Temporary")

    for img in (img_a, img_b):
        client.post(f"/api/v1/images/{img.id}/categories", json={"category_ids": [cat_id]})

    response = client.post(
        "/api/v1/images/bulk/categories",
        json={"image_ids": [str(img_a.id), str(img_b.id)], "remove_category_ids": [cat_id]},
    )
    assert response.status_code == 200
    assert cat_id not in _cats_on(client, img_a.id)
    assert cat_id not in _cats_on(client, img_b.id)


def test_bulk_remove_ignores_unassigned_category(client, make_image):
    img = make_image("/a.jpg")
    cat_id = _category(client, "Temporary")

    response = client.post(
        "/api/v1/images/bulk/categories",
        json={"image_ids": [str(img.id)], "remove_category_ids": [cat_id]},
    )
    assert response.status_code == 200


# ── Combined add + remove ─────────────────────────────────────────────────────

def test_bulk_add_and_remove_combined(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    keep_id   = _category(client, "Architecture")
    remove_id = _category(client, "Temporary")
    add_id    = _category(client, "Design")

    for img in (img_a, img_b):
        client.post(
            f"/api/v1/images/{img.id}/categories",
            json={"category_ids": [keep_id, remove_id]},
        )

    client.post(
        "/api/v1/images/bulk/categories",
        json={
            "image_ids": [str(img_a.id), str(img_b.id)],
            "add_category_ids": [add_id],
            "remove_category_ids": [remove_id],
        },
    )

    for img in (img_a, img_b):
        cats = _cats_on(client, img.id)
        assert keep_id   in cats
        assert add_id    in cats
        assert remove_id not in cats


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_bulk_empty_image_ids_is_no_op(client):
    response = client.post(
        "/api/v1/images/bulk/categories",
        json={"image_ids": [], "add_category_ids": []},
    )
    assert response.status_code == 200


def test_bulk_does_not_affect_unincluded_images(client, make_image):
    img_target    = make_image("/a.jpg")
    img_bystander = make_image("/b.jpg")
    cat_id = _category(client, "Architecture")

    client.post(f"/api/v1/images/{img_bystander.id}/categories", json={"category_ids": [cat_id]})

    client.post(
        "/api/v1/images/bulk/categories",
        json={"image_ids": [str(img_target.id)], "remove_category_ids": [cat_id]},
    )
    assert cat_id in _cats_on(client, img_bystander.id)
