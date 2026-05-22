from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ImportJobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ImportJob(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: ImportJobStatus = ImportJobStatus.queued
    total_files: int = 0
    processed_files: int = 0
    successful_imports: int = 0
    duplicate_paths: int = 0
    duplicate_hashes: int = 0
    failed_imports: int = 0
    created_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_date: Optional[datetime] = None
