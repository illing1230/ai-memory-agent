"""Chat Room Pydantic 스키마"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class ContextSources(BaseModel):
    """컨텍스트 소스 설정"""
    memory: dict = {
        "personal": True,
        "projects": [],
        "departments": []
    }
    rag: dict = {
        "collections": [],
        "filters": {}
    }


class ChatRoomBase(BaseModel):
    name: str
    room_type: Literal["personal", "project", "department"] = "personal"


class ChatRoomCreate(ChatRoomBase):
    project_id: str | None = None
    department_id: str | None = None
    context_sources: ContextSources | None = None


class ChatRoomResponse(ChatRoomBase):
    id: str
    owner_id: str
    project_id: str | None = None
    department_id: str | None = None
    context_sources: ContextSources | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str
    mentions: list[str] | None = None


class MessageResponse(BaseModel):
    id: str
    chat_room_id: str
    user_id: str
    user_name: str | None = None
    role: Literal["user", "assistant"]
    content: str
    mentions: list[str] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """채팅 요청 (AI 호출용)"""
    message: str
    

class ChatResponse(BaseModel):
    """채팅 응답"""
    user_message: MessageResponse
    assistant_message: MessageResponse | None = None
    extracted_memories: list[dict] = []


class ChatRoomMemberCreate(BaseModel):
    """채팅방 멤버 추가"""
    user_id: str
    role: Literal["admin", "member"] = "member"


class ChatRoomMemberResponse(BaseModel):
    """채팅방 멤버 응답"""
    id: str
    chat_room_id: str
    user_id: str
    user_name: str | None = None
    user_email: str | None = None
    role: Literal["owner", "admin", "member"]
    joined_at: datetime

    class Config:
        from_attributes = True
