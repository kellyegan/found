from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.core.database import get_session
from app.repositories.image_repository import ImageRepository
from app.repositories.job_repository import JobRepository
from app.schemas.image import ImageCreate, ImageRead
from app.schemas.job import ImportRequest
from app.services.image_service import ImageService
from app.services.import_service import ImportService

router = APIRouter()


def _get_service(session: Session = Depends(get_session)) -> ImageService:
    return ImageService(ImageRepository(session))


def _get_import_service(session: Session = Depends(get_session)) -> ImportService:
    return ImportService(session)


@router.post("/images/import")
def import_images(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    service: ImportService = Depends(_get_import_service),
):
    job = service.create_job(len(request.paths))
    background_tasks.add_task(service.process_import, job.id, request.paths)
    return {"success": True, "data": {"job_id": str(job.id)}}


@router.post("/images", status_code=201)
def create_image(data: ImageCreate, service: ImageService = Depends(_get_service)):
    image = service.create_image(data)
    return {"success": True, "data": ImageRead.model_validate(image)}


@router.get("/images")
def list_images(
    offset: int = 0,
    limit: int = 100,
    tag: Optional[str] = None,
    category: Optional[str] = None,
    collection: Optional[UUID] = None,
    service: ImageService = Depends(_get_service),
):
    images = service.list_images(
        offset=offset, limit=limit,
        tag=tag, category=category, collection_id=collection,
    )
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


@router.get("/images/{image_id}/thumbnail")
def get_thumbnail(image_id: UUID, service: ImageService = Depends(_get_service)):
    image = service.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    if not image.sha256_hash:
        raise HTTPException(
            status_code=404,
            detail={"code": "no_hash", "message": "Image has no hash; cannot generate thumbnail."},
        )
    thumb_path = service.get_or_create_thumbnail(image)
    return FileResponse(thumb_path, media_type="image/jpeg")


@router.post("/images/{image_id}/verify")
def verify_image(image_id: UUID, service: ImageService = Depends(_get_service)):
    image = service.verify_file(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": ImageRead.model_validate(image)}
