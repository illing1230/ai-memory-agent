"""Permission API Router"""

from fastapi import APIRouter, Depends, Header
import aiosqlite

from src.shared.database import get_db
from src.permission.service import PermissionService
from src.permission.schemas import (
    PermissionCheckRequest,
    PermissionCheckResponse,
)

router = APIRouter()


def get_permission_service(db: aiosqlite.Connection = Depends(get_db)) -> PermissionService:
    return PermissionService(db)


def get_current_user_id(x_user_id: str = Header(..., description="현재 사용자 ID")) -> str:
    return x_user_id


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permission(
    data: PermissionCheckRequest,
    user_id: str = Depends(get_current_user_id),
    service: PermissionService = Depends(get_permission_service),
):
    """권한 확인"""
    return await service.check_permission(
        user_id=user_id,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        action=data.action,
    )
