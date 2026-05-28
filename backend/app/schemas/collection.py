from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionUpdate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_date: datetime
    cover_image_id: Optional[UUID]

    model_config = {"from_attributes": True}


class CollectionImagesRequest(BaseModel):
    image_ids: list[UUID]


class CollectionReorderRequest(BaseModel):
    image_ids: list[UUID]
