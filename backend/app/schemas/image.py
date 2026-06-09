from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.image import FileStatus


class ImageRead(BaseModel):
    id: UUID
    filename: str
    path: str
    width: Optional[int]
    height: Optional[int]
    file_size: Optional[int]
    mime_type: Optional[str]
    created_date: Optional[datetime]
    modified_date: Optional[datetime]
    imported_date: datetime
    sha256_hash: Optional[str]
    thumbnail_path: Optional[str]
    file_status: FileStatus
    import_job_id: Optional[UUID]

    model_config = {"from_attributes": True}


class ImageGridRead(BaseModel):
    id: UUID
    filename: str
    width: Optional[int]
    height: Optional[int]
    thumbnail_path: Optional[str]
    file_status: FileStatus

    model_config = {"from_attributes": True}


class ImagePatch(BaseModel):
    path: str


class ImageIdsRequest(BaseModel):
    image_ids: list[UUID]


class RelocatePreviewRequest(BaseModel):
    old_path: str
    new_path: str


class RelocatePreviewResponse(BaseModel):
    old_prefix: str
    new_prefix: str
    affected_count: int


class RelocatePrefixRequest(BaseModel):
    old_prefix: str
    new_prefix: str


class RelocatePrefixResponse(BaseModel):
    updated: int
    not_found: int
    conflicts: int
