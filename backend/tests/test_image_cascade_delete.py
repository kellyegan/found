"""Tests verifying that deleting an image cleans up every table that references it.

SQLite has no FK cascade configured for these association tables, so the
repository must clean them up explicitly.
"""
import pytest
from sqlmodel import select

from app.models.category import Category, ImageCategory
from app.models.collection import Collection, CollectionImage
from app.models.import_result import ImportResult, ImportResultOutcome
from app.models.job import ImportJob
from app.models.tag import ImageTag, Tag


# ── fixtures / helpers ──────────────────────────────────────────────────────

@pytest.fixture
def make_tag(session):
    def _factory(name: str) -> Tag:
        tag = Tag(name=name)
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return tag
    return _factory


@pytest.fixture
def make_category(session):
    def _factory(name: str) -> Category:
        category = Category(name=name)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    return _factory


@pytest.fixture
def make_collection(session):
    def _factory(name: str) -> Collection:
        collection = Collection(name=name)
        session.add(collection)
        session.commit()
        session.refresh(collection)
        return collection
    return _factory


@pytest.fixture
def make_import_job(session):
    def _factory() -> ImportJob:
        job = ImportJob(total_files=1)
        session.add(job)
        session.commit()
        session.refresh(job)
        return job
    return _factory


def _link_tag(session, image, tag):
    session.add(ImageTag(image_id=image.id, tag_id=tag.id))
    session.commit()


def _link_category(session, image, category):
    session.add(ImageCategory(image_id=image.id, category_id=category.id))
    session.commit()


def _link_collection(session, collection, image, sort_order=0):
    session.add(CollectionImage(collection_id=collection.id, image_id=image.id, sort_order=sort_order))
    session.commit()


# ── single delete cascades ──────────────────────────────────────────────────

def test_delete_image_removes_tag_links(client, session, make_image, make_tag):
    img = make_image("/a.jpg")
    tag = make_tag("landscape")
    _link_tag(session, img, tag)

    response = client.delete(f"/api/v1/images/{img.id}")
    assert response.status_code == 200

    assert session.exec(select(ImageTag).where(ImageTag.image_id == img.id)).all() == []


def test_delete_image_removes_category_links(client, session, make_image, make_category):
    img = make_image("/a.jpg")
    category = make_category("Inspiration")
    _link_category(session, img, category)

    response = client.delete(f"/api/v1/images/{img.id}")
    assert response.status_code == 200

    assert session.exec(select(ImageCategory).where(ImageCategory.image_id == img.id)).all() == []


def test_delete_image_removes_collection_links(client, session, make_image, make_collection):
    img = make_image("/a.jpg")
    collection = make_collection("Picks")
    _link_collection(session, collection, img)

    response = client.delete(f"/api/v1/images/{img.id}")
    assert response.status_code == 200

    assert session.exec(select(CollectionImage).where(CollectionImage.image_id == img.id)).all() == []


def test_delete_image_clears_collection_cover_when_last_image(client, session, make_image, make_collection):
    img = make_image("/a.jpg")
    collection = make_collection("Picks")
    _link_collection(session, collection, img)
    collection.cover_image_id = img.id
    session.add(collection)
    session.commit()

    response = client.delete(f"/api/v1/images/{img.id}")
    assert response.status_code == 200

    session.refresh(collection)
    assert collection.cover_image_id is None


def test_delete_image_promotes_next_cover(client, session, make_image, make_collection):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    collection = make_collection("Picks")
    _link_collection(session, collection, img_a, sort_order=0)
    _link_collection(session, collection, img_b, sort_order=1)
    collection.cover_image_id = img_a.id
    session.add(collection)
    session.commit()

    response = client.delete(f"/api/v1/images/{img_a.id}")
    assert response.status_code == 200

    session.refresh(collection)
    assert collection.cover_image_id == img_b.id


def test_delete_image_nulls_import_result_reference(client, session, make_image, make_import_job):
    img = make_image("/a.jpg")
    job = make_import_job()
    result = ImportResult(
        job_id=job.id,
        path="/dup.jpg",
        outcome=ImportResultOutcome.duplicate_hash,
        existing_image_id=img.id,
    )
    session.add(result)
    session.commit()

    response = client.delete(f"/api/v1/images/{img.id}")
    assert response.status_code == 200

    session.refresh(result)
    assert result.existing_image_id is None


# ── bulk delete cascades ────────────────────────────────────────────────────

def test_bulk_delete_removes_tag_and_category_links(client, session, make_image, make_tag, make_category):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    tag = make_tag("landscape")
    category = make_category("Inspiration")
    _link_tag(session, img_a, tag)
    _link_category(session, img_b, category)

    response = client.post(
        "/api/v1/images/bulk/delete",
        json={"image_ids": [str(img_a.id), str(img_b.id)]},
    )
    assert response.status_code == 200

    assert session.exec(select(ImageTag).where(ImageTag.image_id == img_a.id)).all() == []
    assert session.exec(select(ImageCategory).where(ImageCategory.image_id == img_b.id)).all() == []


def test_bulk_delete_removes_collection_links_and_promotes_cover(client, session, make_image, make_collection):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    img_c = make_image("/c.jpg")
    collection = make_collection("Picks")
    _link_collection(session, collection, img_a, sort_order=0)
    _link_collection(session, collection, img_b, sort_order=1)
    _link_collection(session, collection, img_c, sort_order=2)
    collection.cover_image_id = img_a.id
    session.add(collection)
    session.commit()

    response = client.post(
        "/api/v1/images/bulk/delete",
        json={"image_ids": [str(img_a.id), str(img_b.id)]},
    )
    assert response.status_code == 200

    remaining = session.exec(
        select(CollectionImage).where(CollectionImage.collection_id == collection.id)
    ).all()
    assert {row.image_id for row in remaining} == {img_c.id}

    session.refresh(collection)
    assert collection.cover_image_id == img_c.id


def test_bulk_delete_nulls_import_result_references(client, session, make_image, make_import_job):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    job = make_import_job()
    result_a = ImportResult(job_id=job.id, path="/dup_a.jpg", outcome=ImportResultOutcome.duplicate_hash, existing_image_id=img_a.id)
    result_b = ImportResult(job_id=job.id, path="/dup_b.jpg", outcome=ImportResultOutcome.duplicate_hash, existing_image_id=img_b.id)
    session.add(result_a)
    session.add(result_b)
    session.commit()

    response = client.post(
        "/api/v1/images/bulk/delete",
        json={"image_ids": [str(img_a.id), str(img_b.id)]},
    )
    assert response.status_code == 200

    session.refresh(result_a)
    session.refresh(result_b)
    assert result_a.existing_image_id is None
    assert result_b.existing_image_id is None
