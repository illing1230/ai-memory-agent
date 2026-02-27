"""관리자 API 라우터"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from src.shared.database import get_db
from src.shared.auth import get_current_admin_user
from src.admin.service import AdminService
from src.admin.schemas import (
    DashboardStats,
    AdminUser,
    UpdateRoleRequest,
    AdminChatRoom,
    AdminDepartment,
    AdminProject,
    PaginatedMemories,
    KnowledgeDashboard,
    KnowledgeQualityReport,
    UpdateDepartmentRequest,
    UpdateProjectRequest,
)
from src.agent.schemas import AgentDashboard, AgentApiLogList

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """대시보드 통계"""
    service = AdminService(db)
    return await service.get_dashboard_stats()


@router.get("/users", response_model=list[AdminUser])
async def get_users(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """전체 사용자 목록"""
    service = AdminService(db)
    return await service.get_users()


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """사용자 역할 변경"""
    if request.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="역할은 'user' 또는 'admin'만 가능합니다")
    service = AdminService(db)
    await service.update_user_role(user_id, request.role)
    return {"message": "역할이 변경되었습니다"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """사용자 삭제"""
    if user_id == admin_id:
        raise HTTPException(status_code=400, detail="자기 자신은 삭제할 수 없습니다")
    service = AdminService(db)
    await service.delete_user(user_id)
    return {"message": "사용자가 삭제되었습니다"}


@router.get("/departments", response_model=list[AdminDepartment])
async def get_departments(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """부서 목록"""
    service = AdminService(db)
    return await service.get_departments()


@router.get("/projects", response_model=list[AdminProject])
async def get_projects(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """프로젝트 목록"""
    service = AdminService(db)
    return await service.get_projects()


@router.put("/departments/{department_id}")
async def update_department(
    department_id: str,
    request: UpdateDepartmentRequest,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """부서 수정"""
    service = AdminService(db)
    await service.update_department(department_id, request.name, request.description)
    return {"message": "부서가 수정되었습니다"}


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: str,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """부서 삭제"""
    service = AdminService(db)
    await service.delete_department(department_id)
    return {"message": "부서가 삭제되었습니다"}


@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """프로젝트 수정"""
    service = AdminService(db)
    await service.update_project(project_id, request.name, request.description, request.department_id)
    return {"message": "프로젝트가 수정되었습니다"}


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """프로젝트 삭제"""
    service = AdminService(db)
    await service.delete_project(project_id)
    return {"message": "프로젝트가 삭제되었습니다"}


@router.get("/chat-rooms", response_model=list[AdminChatRoom])
async def get_chat_rooms(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """대화방 목록"""
    service = AdminService(db)
    return await service.get_chat_rooms()


@router.delete("/chat-rooms/{room_id}")
async def delete_chat_room(
    room_id: str,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """대화방 삭제"""
    service = AdminService(db)
    await service.delete_chat_room(room_id)
    return {"message": "대화방이 삭제되었습니다"}


@router.get("/memories", response_model=PaginatedMemories)
async def get_memories(
    limit: int = 20,
    offset: int = 0,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """전체 메모리 목록"""
    service = AdminService(db)
    return await service.get_memories(limit=limit, offset=offset)


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """메모리 삭제"""
    service = AdminService(db)
    await service.delete_memory(memory_id)
    return {"message": "메모리가 삭제되었습니다"}


@router.get("/knowledge-dashboard", response_model=KnowledgeDashboard)
async def get_knowledge_dashboard(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """팀 지식 대시보드"""
    service = AdminService(db)
    return await service.get_knowledge_dashboard()


# ==================== Phase 2-1: Agent Dashboard ====================

@router.get("/agent-dashboard", response_model=AgentDashboard)
async def get_agent_dashboard(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """에이전트 대시보드"""
    service = AdminService(db)
    return await service.get_agent_dashboard()


# ==================== Phase 2-2: Admin API Logs ====================

@router.get("/agent-api-logs", response_model=AgentApiLogList)
async def get_admin_agent_api_logs(
    instance_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """관리자용 전체 API 로그 조회"""
    service = AdminService(db)
    logs, total = await service.get_admin_api_logs(
        instance_id=instance_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return {"logs": logs, "total": total}


# ==================== Phase 3-3: Knowledge Quality Report ====================

@router.get("/knowledge-quality-report", response_model=KnowledgeQualityReport)
async def get_knowledge_quality_report(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """전사 지식 품질 리포트"""
    service = AdminService(db)
    return await service.get_knowledge_quality_report()
