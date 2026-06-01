import uuid
from datetime import datetime

from pydantic import BaseModel


class MaterialAuthorResponse(BaseModel):
    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}


class MaterialItemResponse(BaseModel):
    id: uuid.UUID
    item_type: str
    url: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    download_url: str | None = None


class MaterialResponse(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    title: str
    description: str | None
    author: MaterialAuthorResponse
    created_at: datetime
    items: list[MaterialItemResponse]


class MaterialUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
