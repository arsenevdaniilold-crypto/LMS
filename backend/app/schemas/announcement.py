import uuid
from datetime import datetime

from pydantic import BaseModel


class AnnouncementAuthorResponse(BaseModel):
    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}


class AnnouncementFileResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    file_size: int
    download_url: str


class AnnouncementResponse(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    title: str
    text: str
    author: AnnouncementAuthorResponse
    created_at: datetime
    files: list[AnnouncementFileResponse]
