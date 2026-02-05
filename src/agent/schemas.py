"""Agent Pydantic 스키마"""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


# Agent Type 스키마
class AgentTypeBase(BaseModel):
    name: str
    description: str | None = None
    version: str = "1.0.0"
    config_schema: dict | None = None
    capabilities: list[str] = []
    public_scope: Literal["private", "project", "department", "public"] = "private"
    project_id: str | None = None


class AgentTypeCreate(AgentTypeBase):
    pass


class AgentTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    config_schema: dict | None = None
    capabilities: list[str] | None = None
    public_scope: Literal["private", "project", "department", "public"] | None = None
    project_id: str | None = None
    status: Literal["active", "deprecated"] | None = None


class AgentTypeResponse(AgentTypeBase):
    id: str
    developer_id: str
    status: Literal["active", "deprecated"]
    created_at: datetime
    updated_at: datetime
    capabilities: list[str] | None = None
    project_id: str | None = None

    class Config:
        from_attributes = True


# Agent Instance 스키마
class AgentInstanceBase(BaseModel):
    name: str
    config: dict | None = None
    webhook_url: str | None = None


class AgentInstanceCreate(AgentInstanceBase):
    agent_type_id: str


class AgentInstanceUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    webhook_url: str | None = None
    status: Literal["active", "inactive"] | None = None


class AgentInstanceResponse(AgentInstanceBase):
    id: str
    agent_type_id: str
    owner_id: str
    api_key: str
    status: Literal["active", "inactive"]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Agent 데이터 스키마
class AgentDataBase(BaseModel):
    data_type: Literal["memory", "message", "log"]
    content: str
    external_user_id: str | None = None
    metadata: dict | None = None


class AgentDataCreate(AgentDataBase):
    pass


class AgentDataResponse(AgentDataBase):
    id: str
    agent_instance_id: str
    internal_user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# 사용자 매핑 스키마
class ExternalUserMappingCreate(BaseModel):
    external_user_id: str
    internal_user_id: str
    external_system_name: str | None = None


class ExternalUserMappingResponse(BaseModel):
    id: str
    agent_instance_id: str
    external_user_id: str
    internal_user_id: str
    external_system_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# Agent 메모리 소스 스키마
class ChatRoomSource(BaseModel):
    id: str
    name: str
    room_type: str | None = None


class MemorySourcesResponse(BaseModel):
    chat_rooms: list[ChatRoomSource]
    agent: dict[str, Any] | None = None
    document: dict[str, Any] | None = None


# Agent 메모리 검색 스키마
class AgentMemoryContextSources(BaseModel):
    include_personal: bool = False
    include_agent: bool = False
    include_document: bool = False
    chat_rooms: list[str] = []


class AgentMemorySearchRequest(BaseModel):
    query: str
    context_sources: AgentMemoryContextSources | None = None
    limit: int = Field(default=10, ge=1, le=50)
    external_user_id: str | None = None


class AgentMemorySearchResult(BaseModel):
    memory_id: str
    content: str
    scope: str
    category: str | None = None
    importance: str = "medium"
    score: float
    created_at: datetime
    metadata: dict | None = None


class AgentMemorySearchResponse(BaseModel):
    results: list[AgentMemorySearchResult]
    total: int
    query: str


# Agent 데이터 목록 스키마
class AgentDataListResponse(BaseModel):
    data: list[AgentDataResponse]
    total: int


# Agent Instance 공유 스키마
class AgentInstanceShareCreate(BaseModel):
    shared_with_user_id: str | None = None
    shared_with_project_id: str | None = None
    shared_with_department_id: str | None = None
    role: Literal["viewer", "member"] = "viewer"


class AgentInstanceShareResponse(BaseModel):
    id: str
    agent_instance_id: str
    shared_with_user_id: str | None = None
    shared_with_project_id: str | None = None
    shared_with_department_id: str | None = None
    role: Literal["viewer", "member"]
    created_at: datetime

    class Config:
        from_attributes = True
