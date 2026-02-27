"""관리자 스키마"""

from pydantic import BaseModel
from typing import Optional


class DashboardStats(BaseModel):
    """대시보드 통계"""
    total_users: int
    total_chat_rooms: int
    total_memories: int
    total_messages: int
    total_departments: int
    total_projects: int


class AdminUser(BaseModel):
    """관리자용 사용자 정보"""
    id: str
    name: str
    email: str
    role: str
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[str] = None


class UpdateRoleRequest(BaseModel):
    """역할 변경 요청"""
    role: str  # 'user' | 'admin'


class UpdateDepartmentRequest(BaseModel):
    """부서 수정 요청"""
    name: str
    description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    """프로젝트 수정 요청"""
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None


class AdminChatRoom(BaseModel):
    """관리자용 대화방 정보"""
    id: str
    name: str
    room_type: str
    owner_id: str
    owner_name: Optional[str] = None
    member_count: int = 0
    message_count: int = 0
    created_at: Optional[str] = None


class AdminDepartment(BaseModel):
    """관리자용 부서 정보"""
    id: str
    name: str
    description: Optional[str] = None
    member_count: int = 0
    created_at: Optional[str] = None


class AdminProject(BaseModel):
    """관리자용 프로젝트 정보"""
    id: str
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    member_count: int = 0
    created_at: Optional[str] = None


class AdminMemory(BaseModel):
    """관리자용 메모리 정보"""
    id: str
    content: str
    scope: str
    owner_id: str
    owner_name: Optional[str] = None
    category: Optional[str] = None
    importance: Optional[str] = None
    created_at: Optional[str] = None


class PaginatedMemories(BaseModel):
    """페이지네이션된 메모리 목록"""
    items: list[AdminMemory]
    total: int
    limit: int
    offset: int


# === 지식 대시보드 스키마 ===

class MemoryStats(BaseModel):
    """메모리 통계"""
    total: int
    active: int
    superseded: int
    by_scope: dict[str, int]
    by_category: dict[str, int]
    by_importance: dict[str, int]
    recent_7d: int
    recent_30d: int


class HotTopic(BaseModel):
    """핫 토픽 (자주 언급되는 엔티티)"""
    entity_name: str
    entity_type: str
    mention_count: int


class StaleKnowledge(BaseModel):
    """오래된 지식 통계"""
    no_access_30d: int
    no_access_60d: int
    no_access_90d: int
    low_importance_stale: int


class UserContribution(BaseModel):
    """사용자 기여도"""
    user_id: str
    user_name: str
    memories_created: int
    memories_accessed: int


class DocumentStats(BaseModel):
    """문서 통계"""
    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    total_chunks: int


class KnowledgeDashboard(BaseModel):
    """팀 지식 대시보드"""
    memory_stats: MemoryStats
    hot_topics: list[HotTopic]
    stale_knowledge: StaleKnowledge
    contributions: list[UserContribution]
    document_stats: DocumentStats


# === Phase 3-3: Knowledge Quality Report ===

class TopEntity(BaseModel):
    name: str
    entity_type: str
    mention_count: int


class AgentContribution(BaseModel):
    agent_id: str
    agent_name: str
    memory_count: int = 0
    last_active: Optional[str] = None


class KnowledgeQualityReport(BaseModel):
    """전사 지식 품질 리포트"""
    total_memories: int = 0
    stale_memories_count: int = 0
    duplicate_candidates_count: int = 0
    superseded_chain_count: int = 0
    scope_distribution: dict[str, int] = {}
    category_distribution: dict[str, int] = {}
    top_entities: list[TopEntity] = []
    agent_contribution: list[AgentContribution] = []
