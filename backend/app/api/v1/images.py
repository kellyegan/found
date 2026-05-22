from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.repositories.image_repository import ImageRepository
from app.schemas.image import ImageCreate, ImageRead
from app.services.image_service import ImageService

router = APIRouter()


def _get_service(session: Session = Depends(get_session)) -> ImageService:
    return ImageService(ImageRepository(session))


@router.post("/images", status_code=201)
def create_image(data: ImageCreate, service: ImageService = Depends(_get_service)):
    image = service.create_image(data)
    return {"success": True, "data": ImageRead.model_validate(image)}


@router.get("/images")
def list_images(
    offset: int = 0,
    limit: int = 100,
    service: ImageService = Depends(_get_service),
):
    images = service.list_images(offset=offset, limit=limit)
    return {"success": True, "data": [ImageRead.model_validate(i) for i in images]}


@router.get("/images/{image_id}")
def get_image(image_id: UUID, service: ImageService = Depends(_get_service)):
    image = service.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": ImageRead.model_validate(image)}


@router.delete("/images/{image_id}")
def delete_image(image_id: UUID, service: ImageService = Depends(_get_service)):
    if not service.delete_image(image_id):
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": None}


@router.post("/images/{image_id}/verify")
def verify_image(image_id: UUID, service: ImageService = Depends(_get_service)):
    image = service.verify_file(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": ImageRead.model_validate(image)}
