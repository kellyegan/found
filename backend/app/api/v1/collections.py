from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.models.collection import Collection
from app.repositories.collection_repository import CollectionRepository
from app.schemas.collection import (
    CollectionCreate,
    CollectionImagesRequest,
    CollectionRead,
    CollectionReorderRequest,
    CollectionUpdate,
)
from app.schemas.image import ImageRead

router = APIRouter(tags=["Collections"])


def _get_repo(session: Session = Depends(get_session)) -> CollectionRepository:
    return CollectionRepository(session)


def _require_collection(collection_id: UUID, repo: CollectionRepository) -> Collection:
    col = repo.get_by_id(collection_id)
    if not col:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Collection not found."},
        )
    return col


@router.get("/collections", summary="List collections")
def list_collections(repo: CollectionRepository = Depends(_get_repo)):
    """Return all collections."""
    return {
        "success": True,
        "data": [CollectionRead.model_validate(c) for c in repo.list()],
    }


@router.post("/collections", status_code=201, summary="Create collection")
def create_collection(
    data: CollectionCreate, repo: CollectionRepository = Depends(_get_repo)
):
    """Create a new collection."""
    col = repo.create(Collection(name=data.name, description=data.description))
    return {"success": True, "data": CollectionRead.model_validate(col)}


@router.get("/collections/{collection_id}", summary="Get collection")
def get_collection(
    collection_id: UUID, repo: CollectionRepository = Depends(_get_repo)
):
    """Retrieve a single collection by ID."""
    col = _require_collection(collection_id, repo)
    return {"success": True, "data": CollectionRead.model_validate(col)}


@router.put("/collections/{collection_id}", summary="Update collection")
def update_collection(
    collection_id: UUID,
    data: CollectionUpdate,
    repo: CollectionRepository = Depends(_get_repo),
):
    """Replace the name and description of an existing collection."""
    col = _require_collection(collection_id, repo)
    col.name = data.name
    col.description = data.description
    return {"success": True, "data": CollectionRead.model_validate(repo.update(col))}


@router.delete("/collections/{collection_id}", summary="Delete collection")
def delete_collection(
    collection_id: UUID, repo: CollectionRepository = Depends(_get_repo)
):
    """Delete a collection. Images in this collection are not deleted."""
    _require_collection(collection_id, repo)
    repo.delete(repo.get_by_id(collection_id))
    return {"success": True, "data": None}


@router.get("/images/{image_id}/collections", summary="Get collections for an image")
def get_image_collections(
    image_id: UUID, repo: CollectionRepository = Depends(_get_repo)
):
    """Return all collections that contain the given image."""
    collections = repo.get_image_collections(image_id)
    return {"success": True, "data": [CollectionRead.model_validate(c) for c in collections]}


@router.get("/collections/{collection_id}/images", summary="Get collection images")
def get_collection_images(
    collection_id: UUID, repo: CollectionRepository = Depends(_get_repo)
):
    """Return all images in a collection, in their current display order."""
    _require_collection(collection_id, repo)
    images = repo.get_images(collection_id)
    return {"success": True, "data": [ImageRead.model_validate(i) for i in images]}


@router.post("/collections/{collection_id}/images", summary="Add images to collection")
def add_collection_images(
    collection_id: UUID,
    data: CollectionImagesRequest,
    repo: CollectionRepository = Depends(_get_repo),
):
    """Add one or more images to a collection without affecting existing members."""
    _require_collection(collection_id, repo)
    repo.add_images(collection_id, data.image_ids)
    return {"success": True, "data": None}


@router.delete("/collections/{collection_id}/images/{image_id}", summary="Remove image from collection")
def remove_collection_image(
    collection_id: UUID,
    image_id: UUID,
    repo: CollectionRepository = Depends(_get_repo),
):
    """Remove a single image from a collection. The image record is not deleted."""
    _require_collection(collection_id, repo)
    repo.remove_image(collection_id, image_id)
    return {"success": True, "data": None}


@router.put("/collections/{collection_id}/order", summary="Reorder collection images")
def reorder_collection(
    collection_id: UUID,
    data: CollectionReorderRequest,
    repo: CollectionRepository = Depends(_get_repo),
):
    """Set the display order of images in a collection by providing a full ordered list of image IDs."""
    _require_collection(collection_id, repo)
    repo.reorder(collection_id, data.image_ids)
    return {"success": True, "data": None}
