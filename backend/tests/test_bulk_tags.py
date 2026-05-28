"""Tests for POST /api/v1/images/bulk/tags."""


def _tag(client, name: str) -> str:
    return client.post("/api/v1/tags", json={"name": name}).json()["data"]["id"]


def _tags_on(client, image_id) -> set[str]:
    return {t["id"] for t in client.get(f"/api/v1/images/{image_id}/tags").json()["data"]}


# ── Add tags ──────────────────────────────────────────────────────────────────

def test_bulk_add_tags_to_multiple_images(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    tag_id = _tag(client, "nature")

    response = client.post(
        "/api/v1/images/bulk/tags",
        json={"image_ids": [str(img_a.id), str(img_b.id)], "add_tag_ids": [tag_id]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert tag_id in _tags_on(client, img_a.id)
    assert tag_id in _tags_on(client, img_b.id)


def test_bulk_add_multiple_tags_to_multiple_images(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    tag1_id = _tag(client, "nature")
    tag2_id = _tag(client, "landscape")

    client.post(
        "/api/v1/images/bulk/tags",
        json={"image_ids": [str(img_a.id), str(img_b.id)], "add_tag_ids": [tag1_id, tag2_id]},
    )
    assert _tags_on(client, img_a.id) == {tag1_id, tag2_id}
    assert _tags_on(client, img_b.id) == {tag1_id, tag2_id}


def test_bulk_add_ignores_duplicate_assignment(client, make_image):
    img = make_image("/a.jpg")
    tag_id = _tag(client, "nature")

    # Assign once via normal route
    client.post(f"/api/v1/images/{img.id}/tags", json={"tag_ids": [tag_id]})

    # Bulk add the same tag — should not error
    response = client.post(
        "/api/v1/images/bulk/tags",
        json={"image_ids": [str(img.id)], "add_tag_ids": [tag_id]},
    )
    assert response.status_code == 200
    assert _tags_on(client, img.id) == {tag_id}


# ── Remove tags ───────────────────────────────────────────────────────────────

def test_bulk_remove_tags_from_multiple_images(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    tag_id = _tag(client, "archive")

    client.post(f"/api/v1/images/{img_a.id}/tags", json={"tag_ids": [tag_id]})
    client.post(f"/api/v1/images/{img_b.id}/tags", json={"tag_ids": [tag_id]})

    response = client.post(
        "/api/v1/images/bulk/tags",
        json={"image_ids": [str(img_a.id), str(img_b.id)], "remove_tag_ids": [tag_id]},
    )
    assert response.status_code == 200
    assert tag_id not in _tags_on(client, img_a.id)
    assert tag_id not in _tags_on(client, img_b.id)


def test_bulk_remove_ignores_unassigned_tag(client, make_image):
    img = make_image("/a.jpg")
    tag_id = _tag(client, "archive")

    # Remove a tag that was never assigned — should not error
    response = client.post(
        "/api/v1/images/bulk/tags",
        json={"image_ids": [str(img.id)], "remove_tag_ids": [tag_id]},
    )
    assert response.status_code == 200


# ── Combined add + remove ─────────────────────────────────────────────────────

def test_bulk_add_and_remove_combined(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    keep_id   = _tag(client, "nature")
    remove_id = _tag(client, "archive")
    add_id    = _tag(client, "landscape")

    # Both images start with "nature" and "archive"
    for img in (img_a, img_b):
        client.post(f"/api/v1/images/{img.id}/tags", json={"tag_ids": [keep_id, remove_id]})

    client.post(
        "/api/v1/images/bulk/tags",
        json={
            "image_ids": [str(img_a.id), str(img_b.id)],
            "add_tag_ids": [add_id],
            "remove_tag_ids": [remove_id],
        },
    )

    for img in (img_a, img_b):
        tags = _tags_on(client, img.id)
        assert keep_id   in tags
        assert add_id    in tags
        assert remove_id not in tags


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_bulk_empty_image_ids_is_no_op(client):
    response = client.post(
        "/api/v1/images/bulk/tags",
        json={"image_ids": [], "add_tag_ids": []},
    )
    assert response.status_code == 200


def test_bulk_does_not_affect_unincluded_images(client, make_image):
    img_target  = make_image("/a.jpg")
    img_bystander = make_image("/b.jpg")
    tag_id = _tag(client, "nature")

    client.post(f"/api/v1/images/{img_bystander.id}/tags", json={"tag_ids": [tag_id]})

    client.post(
        "/api/v1/images/bulk/tags",
        json={"image_ids": [str(img_target.id)], "remove_tag_ids": [tag_id]},
    )
    # Bystander should still have the tag
    assert tag_id in _tags_on(client, img_bystander.id)
