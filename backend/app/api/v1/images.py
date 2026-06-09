from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.core.database import get_session
from app.repositories.image_repository import ImageRepository
from app.repositories.job_repository import JobRepository
from app.schemas.image import (
    ImageGridRead, ImageIdsRequest, ImagePatch, ImageRead,
    RelocatePreviewRequest, RelocatePreviewResponse,
    RelocatePrefixRequest, RelocatePrefixResponse,
)
from app.schemas.job import ImportPreviewResponse, ImportRequest
from app.schemas.category import BulkCategoryRequest
from app.schemas.tag import BulkTagRequest
from app.repositories.category_repository import CategoryRepository
from app.repositories.tag_repository import TagRepository
from app.models.image import FileStatus
from app.services.image_service import ImageService, derive_relocation_prefixes
from app.services.import_service import ImportService

router = APIRouter(tags=["Images"])


def _get_service(session: Session = Depends(get_session)) -> ImageService:
    return ImageService(ImageRepository(session))


def _get_import_service(session: Session = Depends(get_session)) -> ImportService:
    return ImportService(session)


def _get_tag_repo(session: Session = Depends(get_session)) -> TagRepository:
    return TagRepository(session)


def _get_category_repo(session: Session = Depends(get_session)) -> CategoryRepository:
    return CategoryRepository(session)


@router.post("/images/import/preview", summary="Preview a bulk import")
def preview_import(
    request: ImportRequest,
    service: ImportService = Depends(_get_import_service),
):
    """Scan a list of paths and categorise them without writing to the database.
    Returns four buckets: new (ready to import), already_imported (exact path match),
    conflicts (same content, different path — resolve via PATCH before importing),
    and invalid (unreadable or unsupported files)."""
    result = service.preview_import(request.paths)
    return {"success": True, "data": ImportPreviewResponse(**result)}


@router.post("/images/import", summary="Bulk import images")
def import_images(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    service: ImportService = Depends(_get_import_service),
):
    """Queue a background job to index a list of file paths.
    Files are indexed in-place — never copied or moved.
    Returns a job ID that can be polled via `GET /jobs/{job_id}`."""
    job = service.create_job(len(request.paths))
    background_tasks.add_task(service.process_import, job.id, request.paths)
    return {"success": True, "data": {"job_id": str(job.id)}}


@router.post("/images/preview-relocation", summary="Preview a prefix relocation")
def preview_relocation(
    request: RelocatePreviewRequest,
    service: ImageService = Depends(_get_service),
):
    """Derive the path prefix mapping from a single relocated file and count affected images.
    Returns old_prefix, new_prefix, and the number of library images under old_prefix."""
    old_prefix, new_prefix = derive_relocation_prefixes(request.old_path, request.new_path)
    affected_count = sum(
        1 for img in service.repo.get_by_path_prefix(old_prefix)
        if img.file_status == FileStatus.missing
    )
    return {
        "success": True,
        "data": RelocatePreviewResponse(
            old_prefix=old_prefix,
            new_prefix=new_prefix,
            affected_count=affected_count,
        ),
    }


@router.post("/images/relocate-prefix", summary="Relocate images by path prefix")
def relocate_prefix(
    request: RelocatePrefixRequest,
    service: ImageService = Depends(_get_service),
):
    """Update paths for all images under old_prefix, substituting new_prefix.
    Only updates images whose new path exists on disk."""
    result = service.relocate_by_prefix(request.old_prefix, request.new_prefix)
    return {
        "success": True,
        "data": RelocatePrefixResponse(
            updated=len(result.updated),
            not_found=len(result.not_found),
            conflicts=len(result.conflicts),
            mismatched=len(result.mismatched),
        ),
    }


@router.post("/images/verify", summary="Batch verify images")
def batch_verify_images(
    request: ImageIdsRequest,
    service: ImageService = Depends(_get_service),
):
    """Verify file existence and refresh metadata for multiple images in one call.
    Sets file_status to missing when the file is gone, available when it is present."""
    service.batch_verify(request.image_ids)
    return {"success": True, "data": None}


@router.post("/images/bulk/delete", summary="Bulk delete images")
def bulk_delete_images(
    request: ImageIdsRequest,
    service: ImageService = Depends(_get_service),
):
    """Remove multiple image records from the library in a single atomic operation.
    Source files are never deleted. Non-existent IDs are silently ignored."""
    service.repo.bulk_delete(request.image_ids)
    return {"success": True, "data": None}


@router.post("/images/bulk/categories", summary="Bulk category operations")
def bulk_categorise_images(
    request: BulkCategoryRequest,
    repo: CategoryRepository = Depends(_get_category_repo),
):
    """Add and/or remove categories on multiple images in a single atomic operation.
    Duplicate assignments and missing assignments are silently ignored."""
    repo.bulk_categorise_images(request.image_ids, request.add_category_ids, request.remove_category_ids)
    return {"success": True, "data": None}


@router.post("/images/bulk/tags", summary="Bulk tag operations")
def bulk_tag_images(
    request: BulkTagRequest,
    repo: TagRepository = Depends(_get_tag_repo),
):
    """Add and/or remove tags on multiple images in a single atomic operation.
    Duplicate assignments and missing assignments are silently ignored."""
    repo.bulk_tag_images(request.image_ids, request.add_tag_ids, request.remove_tag_ids)
    return {"success": True, "data": None}


@router.get("/images", summary="List images")
def list_images(
    cursor: Optional[str] = None,
    limit: int = 100,
    view: Optional[str] = None,
    tags: Optional[str] = None,
    categories: Optional[str] = None,
    exclude_tags: Optional[str] = None,
    exclude_categories: Optional[str] = None,
    collection: Optional[UUID] = None,
    import_job: Optional[UUID] = None,
    missing: Optional[bool] = None,
    service: ImageService = Depends(_get_service),
):
    """Return a cursor-paginated list of images with optional filtering.

    Pass `cursor` from a previous response's `next_cursor` to fetch the next page.
    `tags` and `categories` accept comma-separated values; images must match ALL (AND logic).
    `exclude_tags` and `exclude_categories` remove images matching ANY of the values.
    Tags are matched case-insensitively; categories are case-sensitive.
    `missing=true` returns only images whose file is no longer found on disk;
    `missing=false` returns only images whose file is present.
    """
    def _split(value: Optional[str]) -> Optional[list[str]]:
        return [v.strip() for v in value.split(",")] if value else None

    images, next_cursor, has_more = service.list_images(
        cursor=cursor, limit=limit,
        tags=_split(tags), categories=_split(categories),
        exclude_tags=_split(exclude_tags), exclude_categories=_split(exclude_categories),
        collection_id=collection, import_job_id=import_job,
        missing=missing,
    )
    schema = ImageGridRead if view == "grid" else ImageRead
    return {
        "success": True,
        "data": [schema.model_validate(i) for i in images],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/images/{image_id}", summary="Get image")
def get_image(image_id: UUID, service: ImageService = Depends(_get_service)):
    """Retrieve a single image record by ID."""
    image = service.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": ImageRead.model_validate(image)}


@router.patch("/images/{image_id}", summary="Update image path")
def patch_image(
    image_id: UUID,
    data: ImagePatch,
    service: ImageService = Depends(_get_service),
):
    """Update the file path of an existing image record. Derives filename from the new path.
    Use this to point a duplicate-hash record at its new location on disk."""
    image = service.patch_path(image_id, data.path)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": ImageRead.model_validate(image)}


@router.delete("/images/{image_id}", summary="Delete image")
def delete_image(image_id: UUID, service: ImageService = Depends(_get_service)):
    """Remove an image record from the library. The source file is never deleted from disk."""
    if not service.delete_image(image_id):
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": None}


@router.get("/images/{image_id}/file", summary="Get full image file")
def get_image_file(image_id: UUID, service: ImageService = Depends(_get_service)):
    """Stream the original image file from disk at its recorded path.
    The file is never copied or moved."""
    image = service.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    if not image.mime_type or not image.mime_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail={"code": "unsupported_format", "message": "Image format is not supported."},
        )
    path = Path(image.path)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "file_not_found", "message": "Image file not found on disk."},
        )
    try:
        path.open("rb").close()
    except OSError:
        raise HTTPException(
            status_code=500,
            detail={"code": "read_failure", "message": "Failed to read image file."},
        )
    return FileResponse(str(path), media_type=image.mime_type)


@router.get("/images/{image_id}/thumbnail", summary="Get thumbnail")
def get_thumbnail(image_id: UUID, service: ImageService = Depends(_get_service)):
    """Return a JPEG thumbnail for the image, generating and caching it on first request.
    Requires the image to have been hashed (i.e. fully indexed)."""
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


@router.post("/images/{image_id}/verify", summary="Verify image file")
def verify_image(image_id: UUID, service: ImageService = Depends(_get_service)):
    """Check that the source file still exists at its recorded path and refresh its metadata."""
    image = service.verify_file(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Image not found."},
        )
    return {"success": True, "data": ImageRead.model_validate(image)}
