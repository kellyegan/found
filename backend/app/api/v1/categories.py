from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ImageCategoriesRequest,
)

router = APIRouter(tags=["Categories"])


def _get_repo(session: Session = Depends(get_session)) -> CategoryRepository:
    return CategoryRepository(session)


def _require_category(category_id: UUID, repo: CategoryRepository) -> Category:
    cat = repo.get_by_id(category_id)
    if not cat:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Category not found."},
        )
    return cat


@router.get("/categories", summary="List categories")
def list_categories(repo: CategoryRepository = Depends(_get_repo)):
    """Return all categories."""
    return {
        "success": True,
        "data": [CategoryRead.model_validate(c) for c in repo.list()],
    }


@router.post("/categories", status_code=201, summary="Create category")
def create_category(data: CategoryCreate, repo: CategoryRepository = Depends(_get_repo)):
    """Create a new category."""
    category = repo.create(Category(name=data.name, description=data.description))
    return {"success": True, "data": CategoryRead.model_validate(category)}


@router.get("/categories/search", summary="Search categories")
def search_categories(q: str = "", repo: CategoryRepository = Depends(_get_repo)):
    """Return categories whose names contain q (case-insensitive).
    Prefix matches are returned before mid-word matches; alphabetical within each group.
    An empty q returns all categories. Designed for autocomplete use."""
    return {"success": True, "data": [CategoryRead.model_validate(c) for c in repo.search(q)]}


@router.put("/categories/{category_id}", summary="Update category")
def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    repo: CategoryRepository = Depends(_get_repo),
):
    """Replace the name and description of an existing category."""
    cat = _require_category(category_id, repo)
    cat.name = data.name
    cat.description = data.description
    return {"success": True, "data": CategoryRead.model_validate(repo.update(cat))}


@router.delete("/categories/{category_id}", summary="Delete category")
def delete_category(
    category_id: UUID, repo: CategoryRepository = Depends(_get_repo)
):
    """Delete a category. Images assigned to this category are not deleted."""
    _require_category(category_id, repo)
    repo.delete(repo.get_by_id(category_id))
    return {"success": True, "data": None}


@router.get("/images/{image_id}/categories", summary="Get image categories")
def get_image_categories(
    image_id: UUID, repo: CategoryRepository = Depends(_get_repo)
):
    """Return all categories assigned to an image."""
    cats = repo.get_image_categories(image_id)
    return {"success": True, "data": [CategoryRead.model_validate(c) for c in cats]}


@router.post("/images/{image_id}/categories", summary="Add categories to image")
def add_image_categories(
    image_id: UUID,
    data: ImageCategoriesRequest,
    repo: CategoryRepository = Depends(_get_repo),
):
    """Add one or more categories to an image without affecting existing assignments."""
    for category_id in data.category_ids:
        repo.add_image_category(image_id, category_id)
    return {"success": True, "data": None}


@router.put("/images/{image_id}/categories", summary="Replace image categories")
def replace_image_categories(
    image_id: UUID,
    data: ImageCategoriesRequest,
    repo: CategoryRepository = Depends(_get_repo),
):
    """Replace all category assignments on an image with the provided list."""
    repo.clear_image_categories(image_id)
    for category_id in data.category_ids:
        repo.add_image_category(image_id, category_id)
    return {"success": True, "data": None}


@router.delete("/images/{image_id}/categories/{category_id}", summary="Remove category from image")
def remove_image_category(
    image_id: UUID,
    category_id: UUID,
    repo: CategoryRepository = Depends(_get_repo),
):
    """Remove a single category assignment from an image."""
    repo.remove_image_category(image_id, category_id)
    return {"success": True, "data": None}
