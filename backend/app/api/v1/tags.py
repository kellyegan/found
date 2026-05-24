from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import ImageTagsRequest, TagCreate, TagRead, TagUpdate

router = APIRouter(tags=["Tags"])


def _get_repo(session: Session = Depends(get_session)) -> TagRepository:
    return TagRepository(session)


def _require_tag(tag_id: UUID, repo: TagRepository) -> Tag:
    tag = repo.get_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=404, detail={"code": "not_found", "message": "Tag not found."}
        )
    return tag


@router.get("/tags", summary="List tags")
def list_tags(repo: TagRepository = Depends(_get_repo)):
    """Return all tags."""
    return {"success": True, "data": [TagRead.model_validate(t) for t in repo.list()]}


@router.post("/tags", status_code=201, summary="Create tag")
def create_tag(data: TagCreate, repo: TagRepository = Depends(_get_repo)):
    """Create a new tag. Names are normalized to lowercase and must be unique."""
    name = data.name.lower()
    if repo.get_by_name(name):
        raise HTTPException(
            status_code=409,
            detail={"code": "duplicate_tag", "message": f"Tag '{name}' already exists."},
        )
    tag = repo.create(Tag(name=name))
    return {"success": True, "data": TagRead.model_validate(tag)}


@router.put("/tags/{tag_id}", summary="Update tag")
def update_tag(
    tag_id: UUID, data: TagUpdate, repo: TagRepository = Depends(_get_repo)
):
    """Rename a tag. The new name is normalized to lowercase."""
    tag = _require_tag(tag_id, repo)
    tag.name = data.name.lower()
    return {"success": True, "data": TagRead.model_validate(repo.update(tag))}


@router.delete("/tags/{tag_id}", summary="Delete tag")
def delete_tag(tag_id: UUID, repo: TagRepository = Depends(_get_repo)):
    """Delete a tag. Images assigned to this tag are not deleted."""
    _require_tag(tag_id, repo)
    repo.delete(repo.get_by_id(tag_id))
    return {"success": True, "data": None}


@router.get("/images/{image_id}/tags", summary="Get image tags")
def get_image_tags(image_id: UUID, repo: TagRepository = Depends(_get_repo)):
    """Return all tags assigned to an image."""
    tags = repo.get_image_tags(image_id)
    return {"success": True, "data": [TagRead.model_validate(t) for t in tags]}


@router.post("/images/{image_id}/tags", summary="Add tags to image")
def add_image_tags(
    image_id: UUID, data: ImageTagsRequest, repo: TagRepository = Depends(_get_repo)
):
    """Add one or more tags to an image without affecting existing assignments."""
    for tag_id in data.tag_ids:
        repo.add_image_tag(image_id, tag_id)
    return {"success": True, "data": None}


@router.put("/images/{image_id}/tags", summary="Replace image tags")
def replace_image_tags(
    image_id: UUID, data: ImageTagsRequest, repo: TagRepository = Depends(_get_repo)
):
    """Replace all tag assignments on an image with the provided list."""
    repo.clear_image_tags(image_id)
    for tag_id in data.tag_ids:
        repo.add_image_tag(image_id, tag_id)
    return {"success": True, "data": None}


@router.delete("/images/{image_id}/tags/{tag_id}", summary="Remove tag from image")
def remove_image_tag(
    image_id: UUID, tag_id: UUID, repo: TagRepository = Depends(_get_repo)
):
    """Remove a single tag assignment from an image."""
    repo.remove_image_tag(image_id, tag_id)
    return {"success": True, "data": None}
