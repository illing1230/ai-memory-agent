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


class AdminChatRoom(BaseModel):
    """관리자용 채팅방 정보"""
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
