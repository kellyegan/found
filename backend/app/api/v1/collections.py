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

router = APIRouter()


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


@router.get("/collections")
def list_collections(repo: CollectionRepository = Depends(_get_repo)):
    return {
        "success": True,
        "data": [CollectionRead.model_validate(c) for c in repo.list()],
    }


@router.post("/collections", status_code=201)
def create_collection(
    data: CollectionCreate, repo: CollectionRepository = Depends(_get_repo)
):
    col = repo.create(Collection(name=data.name, description=data.description))
    return {"success": True, "data": CollectionRead.model_validate(col)}


@router.put("/collections/{collection_id}")
def update_collection(
    collection_id: UUID,
    data: CollectionUpdate,
    repo: CollectionRepository = Depends(_get_repo),
):
    col = _require_collection(collection_id, repo)
    col.name = data.name
    col.description = data.description
    return {"success": True, "data": CollectionRead.model_validate(repo.update(col))}


@router.delete("/collections/{collection_id}")
def delete_collection(
    collection_id: UUID, repo: CollectionRepository = Depends(_get_repo)
):
    _require_collection(collection_id, repo)
    repo.delete(repo.get_by_id(collection_id))
    return {"success": True, "data": None}


@router.get("/collections/{collection_id}/images")
def get_collection_images(
    collection_id: UUID, repo: CollectionRepository = Depends(_get_repo)
):
    _require_collection(collection_id, repo)
    images = repo.get_images(collection_id)
    return {"success": True, "data": [ImageRead.model_validate(i) for i in images]}


@router.post("/collections/{collection_id}/images")
def add_collection_images(
    collection_id: UUID,
    data: CollectionImagesRequest,
    repo: CollectionRepository = Depends(_get_repo),
):
    _require_collection(collection_id, repo)
    repo.add_images(collection_id, data.image_ids)
    return {"success": True, "data": None}


@router.delete("/collections/{collection_id}/images/{image_id}")
def remove_collection_image(
    collection_id: UUID,
    image_id: UUID,
    repo: CollectionRepository = Depends(_get_repo),
):
    _require_collection(collection_id, repo)
    repo.remove_image(collection_id, image_id)
    return {"success": True, "data": None}


@router.put("/collections/{collection_id}/order")
def reorder_collection(
    collection_id: UUID,
    data: CollectionReorderRequest,
    repo: CollectionRepository = Depends(_get_repo),
):
    _require_collection(collection_id, repo)
    repo.reorder(collection_id, data.image_ids)
    return {"success": True, "data": None}
