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
)

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
