"""Tests for cover_image_id on Collection."""


def _collection(client, name="Picks") -> dict:
    return client.post(
        "/api/v1/collections", json={"name": name, "description": ""}
    ).json()["data"]


def _add(client, col_id, *image_ids):
    client.post(f"/api/v1/collections/{col_id}/images", json={"image_ids": list(str(i) for i in image_ids)})


def _cover(client, col_id) -> str | None:
    return client.get(f"/api/v1/collections/{col_id}").json()["data"]["cover_image_id"]


# ── cover_image_id is present in the response ─────────────────────────────────

def test_cover_image_id_present_in_response(client):
    col = _collection(client)
    assert "cover_image_id" in col


def test_new_collection_has_null_cover(client):
    col = _collection(client)
    assert col["cover_image_id"] is None


# ── auto-selection ─────────────────────────────────────────────────────────────

def test_first_image_added_becomes_cover(client, make_image):
    col = _collection(client)
    img = make_image("/a.jpg")
    _add(client, col["id"], img.id)

    assert _cover(client, col["id"]) == str(img.id)


def test_second_image_added_does_not_change_cover(client, make_image):
    col = _collection(client)
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    _add(client, col["id"], img_a.id)
    _add(client, col["id"], img_b.id)

    assert _cover(client, col["id"]) == str(img_a.id)


def test_adding_to_non_empty_collection_does_not_reset_cover(client, make_image):
    col = _collection(client)
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    img_c = make_image("/c.jpg")
    _add(client, col["id"], img_a.id, img_b.id)
    _add(client, col["id"], img_c.id)

    assert _cover(client, col["id"]) == str(img_a.id)


# ── cover maintenance when images are removed ─────────────────────────────────

def test_removing_non_cover_image_leaves_cover_unchanged(client, make_image):
    col = _collection(client)
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    _add(client, col["id"], img_a.id, img_b.id)

    client.delete(f"/api/v1/collections/{col['id']}/images/{img_b.id}")

    assert _cover(client, col["id"]) == str(img_a.id)


def test_removing_cover_image_promotes_next_image(client, make_image):
    col = _collection(client)
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    _add(client, col["id"], img_a.id, img_b.id)

    client.delete(f"/api/v1/collections/{col['id']}/images/{img_a.id}")

    assert _cover(client, col["id"]) == str(img_b.id)


def test_removing_last_image_sets_cover_to_null(client, make_image):
    col = _collection(client)
    img = make_image("/a.jpg")
    _add(client, col["id"], img.id)

    client.delete(f"/api/v1/collections/{col['id']}/images/{img.id}")

    assert _cover(client, col["id"]) is None
