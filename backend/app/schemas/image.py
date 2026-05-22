from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.image import FileStatus


class ImageCreate(BaseModel):
    filename: str
    path: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    sha256_hash: Optional[str] = None


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

    model_config = {"from_attributes": True}
