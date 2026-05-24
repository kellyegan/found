from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ImportResultOutcome(str, Enum):
    duplicate_hash = "duplicate_hash"
    failed = "failed"


class ImportResult(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    job_id: UUID = Field(foreign_key="importjob.id", index=True)
    path: str
    outcome: ImportResultOutcome
    existing_image_id: Optional[UUID] = Field(default=None, foreign_key="image.id")
