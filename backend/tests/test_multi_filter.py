"""
Tests for multi-value include/exclude filtering on GET /api/v1/images.

Include logic: image must have ALL specified tags/categories (AND).
Exclude logic: image must have NONE of the specified tags/categories.
"""


def _tag(client, name: str) -> str:
    return client.post("/api/v1/tags", json={"name": name}).json()["data"]["id"]


def _category(client, name: str) -> str:
    return client.post("/api/v1/categories", json={"name": name, "description": ""}).json()["data"]["id"]


def _tag_image(client, image_id, *tag_ids):
    client.post(f"/api/v1/images/{image_id}/tags", json={"tag_ids": list(tag_ids)})


def _categorise_image(client, image_id, *cat_ids):
    client.post(f"/api/v1/images/{image_id}/categories", json={"category_ids": list(cat_ids)})


def _ids(response_data):
    return {r["id"] for r in response_data}


# ── Multiple include tags (AND) ───────────────────────────────────────────────

def test_multiple_tags_returns_only_images_with_all_tags(client, make_image):
    img_both = make_image("/a.jpg")
    img_one  = make_image("/b.jpg")
    img_none = make_image("/c.jpg")

    nature_id    = _tag(client, "nature")
    landscape_id = _tag(client, "landscape")
    _tag_image(client, img_both.id, nature_id, landscape_id)
    _tag_image(client, img_one.id, nature_id)

    result = _ids(client.get("/api/v1/images?tags=nature,landscape").json()["data"])
    assert str(img_both.id) in result
    assert str(img_one.id)  not in result
    assert str(img_none.id) not in result


def test_single_tag_param_works(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    tag_id = _tag(client, "urban")
    _tag_image(client, img_a.id, tag_id)

    result = _ids(client.get("/api/v1/images?tags=urban").json()["data"])
    assert str(img_a.id) in result
    assert str(img_b.id) not in result


def test_tags_filter_is_case_insensitive(client, make_image):
    img = make_image("/a.jpg")
    tag_id = _tag(client, "brutalism")
    _tag_image(client, img.id, tag_id)

    result = _ids(client.get("/api/v1/images?tags=BRUTALISM").json()["data"])
    assert str(img.id) in result


# ── Multiple include categories (AND) ────────────────────────────────────────

def test_multiple_categories_returns_only_images_with_all_categories(client, make_image):
    img_both = make_image("/a.jpg")
    img_one  = make_image("/b.jpg")

    arch_id   = _category(client, "Architecture")
    design_id = _category(client, "Design")
    _categorise_image(client, img_both.id, arch_id, design_id)
    _categorise_image(client, img_one.id, arch_id)

    result = _ids(client.get(f"/api/v1/images?categories={arch_id},{design_id}").json()["data"])
    assert str(img_both.id) in result
    assert str(img_one.id)  not in result


def test_single_category_param_works(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    cat_id = _category(client, "Reference")
    _categorise_image(client, img_a.id, cat_id)

    result = _ids(client.get(f"/api/v1/images?categories={cat_id}").json()["data"])
    assert str(img_a.id) in result
    assert str(img_b.id) not in result


# ── Exclude tags ──────────────────────────────────────────────────────────────

def test_exclude_single_tag_removes_matching_images(client, make_image):
    img_tagged   = make_image("/a.jpg")
    img_untagged = make_image("/b.jpg")
    tag_id = _tag(client, "archive")
    _tag_image(client, img_tagged.id, tag_id)

    result = _ids(client.get("/api/v1/images?exclude_tags=archive").json()["data"])
    assert str(img_tagged.id)   not in result
    assert str(img_untagged.id) in result


def test_exclude_multiple_tags_removes_images_with_any_excluded_tag(client, make_image):
    img_a = make_image("/a.jpg")  # has "archive"
    img_b = make_image("/b.jpg")  # has "draft"
    img_c = make_image("/c.jpg")  # clean

    archive_id = _tag(client, "archive")
    draft_id   = _tag(client, "draft")
    _tag_image(client, img_a.id, archive_id)
    _tag_image(client, img_b.id, draft_id)

    result = _ids(client.get("/api/v1/images?exclude_tags=archive,draft").json()["data"])
    assert str(img_a.id) not in result
    assert str(img_b.id) not in result
    assert str(img_c.id) in result


# ── Exclude categories ────────────────────────────────────────────────────────

def test_exclude_single_category_removes_matching_images(client, make_image):
    img_cat = make_image("/a.jpg")
    img_clean = make_image("/b.jpg")
    cat_id = _category(client, "Temporary")
    _categorise_image(client, img_cat.id, cat_id)

    result = _ids(client.get(f"/api/v1/images?exclude_categories={cat_id}").json()["data"])
    assert str(img_cat.id)   not in result
    assert str(img_clean.id) in result


# ── Combined include + exclude ────────────────────────────────────────────────

def test_include_and_exclude_tags_combined(client, make_image):
    img_keep    = make_image("/a.jpg")  # nature only
    img_exclude = make_image("/b.jpg")  # nature + archive
    img_skip    = make_image("/c.jpg")  # no tags

    nature_id  = _tag(client, "nature")
    archive_id = _tag(client, "archive")
    _tag_image(client, img_keep.id, nature_id)
    _tag_image(client, img_exclude.id, nature_id, archive_id)

    result = _ids(client.get("/api/v1/images?tags=nature&exclude_tags=archive").json()["data"])
    assert str(img_keep.id)    in result
    assert str(img_exclude.id) not in result
    assert str(img_skip.id)    not in result


def test_include_tags_and_exclude_categories_combined(client, make_image):
    img_keep    = make_image("/a.jpg")  # has tag "nature", no excluded category
    img_exclude = make_image("/b.jpg")  # has tag "nature", has category "Temporary"

    nature_id = _tag(client, "nature")
    temp_id   = _category(client, "Temporary")
    _tag_image(client, img_keep.id, nature_id)
    _tag_image(client, img_exclude.id, nature_id)
    _categorise_image(client, img_exclude.id, temp_id)

    result = _ids(client.get(f"/api/v1/images?tags=nature&exclude_categories={temp_id}").json()["data"])
    assert str(img_keep.id)    in result
    assert str(img_exclude.id) not in result
