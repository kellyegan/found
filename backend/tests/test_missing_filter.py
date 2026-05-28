from app.models.image import FileStatus


def test_missing_true_returns_only_missing_images(client, make_image):
    available = make_image("/a.jpg", file_status=FileStatus.available)
    missing   = make_image("/b.jpg", file_status=FileStatus.missing)

    result = client.get("/api/v1/images?missing=true").json()["data"]
    ids = {r["id"] for r in result}
    assert str(missing.id)   in ids
    assert str(available.id) not in ids


def test_missing_false_returns_only_non_missing_images(client, make_image):
    available    = make_image("/a.jpg", file_status=FileStatus.available)
    missing      = make_image("/b.jpg", file_status=FileStatus.missing)
    inaccessible = make_image("/c.jpg", file_status=FileStatus.inaccessible)

    result = client.get("/api/v1/images?missing=false").json()["data"]
    ids = {r["id"] for r in result}
    assert str(available.id)    in ids
    assert str(inaccessible.id) in ids
    assert str(missing.id)      not in ids


def test_missing_omitted_returns_all_images(client, make_image):
    available = make_image("/a.jpg", file_status=FileStatus.available)
    missing   = make_image("/b.jpg", file_status=FileStatus.missing)

    result = client.get("/api/v1/images").json()["data"]
    ids = {r["id"] for r in result}
    assert str(available.id) in ids
    assert str(missing.id)   in ids


def test_missing_true_combines_with_tag_filter(client, make_image):
    tagged_missing   = make_image("/a.jpg", file_status=FileStatus.missing)
    tagged_available = make_image("/b.jpg", file_status=FileStatus.available)
    untagged_missing = make_image("/c.jpg", file_status=FileStatus.missing)

    tag_id = client.post("/api/v1/tags", json={"name": "review"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{tagged_missing.id}/tags",   json={"tag_ids": [tag_id]})
    client.post(f"/api/v1/images/{tagged_available.id}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?tags=review&missing=true").json()["data"]
    ids = {r["id"] for r in result}
    assert str(tagged_missing.id)   in ids
    assert str(tagged_available.id) not in ids
    assert str(untagged_missing.id) not in ids
