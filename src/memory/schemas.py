"""Memory Pydantic 스키마"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class MemoryBase(BaseModel):
    content: str
    scope: Literal["personal", "project", "department", "chatroom"] = "personal"
    category: str | None = None
    importance: Literal["high", "medium", "low"] = "medium"
    metadata: dict | None = None


class MemoryCreate(MemoryBase):
    project_id: str | None = None
    department_id: str | None = None
    chat_room_id: str | None = None
    source_message_id: str | None = None


class MemoryUpdate(BaseModel):
    content: str | None = None
    category: str | None = None
    importance: Literal["high", "medium", "low"] | None = None
    metadata: dict | None = None


class MemoryResponse(MemoryBase):
    id: str
    vector_id: str | None = None
    owner_id: str
    project_id: str | None = None
    department_id: str | None = None
    chat_room_id: str | None = None
    source_message_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    scope: Literal["personal", "project", "department", "chatroom", "all"] | None = None
    project_id: str | None = None
    department_id: str | None = None
    chat_room_id: str | None = None


class MemorySearchResult(BaseModel):
    memory: MemoryResponse
    score: float


class MemorySearchResponse(BaseModel):
    results: list[MemorySearchResult]
    total: int
    query: str


class MemoryExtractRequest(BaseModel):
    """메모리 자동 추출 요청"""
    conversation: list[dict[str, str]]
    scope: Literal["personal", "project", "department", "chatroom"] = "personal"
    project_id: str | None = None
    department_id: str | None = None
    chat_room_id: str | None = None
