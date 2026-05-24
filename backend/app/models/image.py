from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class FileStatus(str, Enum):
    available = "available"
    missing = "missing"
    inaccessible = "inaccessible"


class Image(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    filename: str
    path: str = Field(unique=True)
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    imported_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    sha256_hash: Optional[str] = Field(default=None, index=True)
    thumbnail_path: Optional[str] = None
    file_status: FileStatus = FileStatus.available
    import_job_id: Optional[UUID] = Field(default=None, foreign_key="importjob.id", index=True)
