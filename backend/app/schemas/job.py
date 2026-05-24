from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.job import ImportJobStatus


class ImportRequest(BaseModel):
    paths: List[str]


class ImportResultRead(BaseModel):
    path: str
    outcome: str
    existing_image_id: Optional[UUID]

    model_config = {"from_attributes": True}


class ImportJobRead(BaseModel):
    id: UUID
    status: ImportJobStatus
    total_files: int
    processed_files: int
    successful_imports: int
    duplicate_paths: int
    duplicate_hashes: int
    failed_imports: int
    created_date: datetime
    completed_date: Optional[datetime]
    results: List[ImportResultRead] = []

    model_config = {"from_attributes": True}
