from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True)


class ImageTag(SQLModel, table=True):
    image_id: UUID = Field(foreign_key="image.id", primary_key=True)
    tag_id: UUID = Field(foreign_key="tag.id", primary_key=True)
