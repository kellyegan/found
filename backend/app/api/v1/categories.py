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

router = APIRouter()


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


@router.get("/categories")
def list_categories(repo: CategoryRepository = Depends(_get_repo)):
    return {
        "success": True,
        "data": [CategoryRead.model_validate(c) for c in repo.list()],
    }


@router.post("/categories", status_code=201)
def create_category(data: CategoryCreate, repo: CategoryRepository = Depends(_get_repo)):
    category = repo.create(Category(name=data.name, description=data.description))
    return {"success": True, "data": CategoryRead.model_validate(category)}


@router.put("/categories/{category_id}")
def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    repo: CategoryRepository = Depends(_get_repo),
):
    cat = _require_category(category_id, repo)
    cat.name = data.name
    cat.description = data.description
    return {"success": True, "data": CategoryRead.model_validate(repo.update(cat))}


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: UUID, repo: CategoryRepository = Depends(_get_repo)
):
    _require_category(category_id, repo)
    repo.delete(repo.get_by_id(category_id))
    return {"success": True, "data": None}


@router.get("/images/{image_id}/categories")
def get_image_categories(
    image_id: UUID, repo: CategoryRepository = Depends(_get_repo)
):
    cats = repo.get_image_categories(image_id)
    return {"success": True, "data": [CategoryRead.model_validate(c) for c in cats]}


@router.post("/images/{image_id}/categories")
def add_image_categories(
    image_id: UUID,
    data: ImageCategoriesRequest,
    repo: CategoryRepository = Depends(_get_repo),
):
    for category_id in data.category_ids:
        repo.add_image_category(image_id, category_id)
    return {"success": True, "data": None}


@router.put("/images/{image_id}/categories")
def replace_image_categories(
    image_id: UUID,
    data: ImageCategoriesRequest,
    repo: CategoryRepository = Depends(_get_repo),
):
    repo.clear_image_categories(image_id)
    for category_id in data.category_ids:
        repo.add_image_category(image_id, category_id)
    return {"success": True, "data": None}


@router.delete("/images/{image_id}/categories/{category_id}")
def remove_image_category(
    image_id: UUID,
    category_id: UUID,
    repo: CategoryRepository = Depends(_get_repo),
):
    repo.remove_image_category(image_id, category_id)
    return {"success": True, "data": None}
