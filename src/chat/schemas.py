"""Chat Room Pydantic 스키마"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class ChatRoomBase(BaseModel):
    name: str
    room_type: Literal["personal", "project", "department"] = "personal"


class ChatRoomCreate(ChatRoomBase):
    project_id: str | None = None
    department_id: str | None = None


class ChatRoomResponse(ChatRoomBase):
    id: str
    owner_id: str
    project_id: str | None = None
    department_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str
    role: Literal["user", "assistant"] = "user"


class MessageResponse(BaseModel):
    id: str
    chat_room_id: str
    content: str
    role: str
    created_at: datetime
