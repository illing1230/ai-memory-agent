"""Chat Room Pydantic 스키마"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class MemorySources(BaseModel):
    """메모리 소스 설정"""
    include_this_room: bool = True  # 이 대화방 메모리 (기본 true)
    other_chat_rooms: list[str] = []  # 다른 대화방 ID 목록
    include_personal: bool = False  # 내 개인 메모리 전체 (주의 필요)
    agent_instances: list[str] = []  # Agent Instance ID 목록
    include_agent: bool = False  # Agent 메모리 포함 (SDK용)
    include_document: bool = False  # 문서 메모리 포함 (SDK용)
    projects: list[str] = []  # 프로젝트 ID 목록
    departments: list[str] = []  # 부서 ID 목록


class ContextSources(BaseModel):
    """컨텍스트 소스 설정"""
    memory: MemorySources = MemorySources()
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


class ChatRoomUpdate(BaseModel):
    """대화방 수정 요청"""
    name: str | None = None
    context_sources: ContextSources | None = None


class ChatRoomResponse(ChatRoomBase):
    id: str
    owner_id: str
    project_id: str | None = None
    department_id: str | None = None
    context_sources: ContextSources | None = None
    member_role: str | None = None  # 내 역할 (owner/admin/member)
    share_role: str | None = None  # 공유 역할 (viewer/member/None=직접 멤버)
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
    """대화방 멤버 추가"""
    user_id: str
    role: Literal["admin", "member"] = "member"


class ChatRoomMemberResponse(BaseModel):
    """대화방 멤버 응답"""
    id: str
    chat_room_id: str
    user_id: str
    user_name: str | None = None
    user_email: str | None = None
    role: Literal["owner", "admin", "member"]
    joined_at: datetime

    class Config:
        from_attributes = True
