"""Share Router"""
from fastapi import APIRouter, Depends, HTTPException
from aiosqlite import Connection

from src.share.schemas import ShareCreate, ShareUpdate, ShareResponse, ShareWithDetails
from src.share.service import ShareService
from src.shared.database import get_db
from src.shared.auth import get_current_user_id

router = APIRouter(prefix="/shares", tags=["shares"])


@router.post("", response_model=ShareResponse)
async def create_share(
    share_data: ShareCreate,
    db: Connection = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """공유 설정 생성"""
    service = ShareService(db)
    share = await service.create_share(
        resource_type=share_data.resource_type,
        resource_id=share_data.resource_id,
        target_type=share_data.target_type,
        target_id=share_data.target_id,
        role=share_data.role,
        created_by=user_id,
    )
    return share


@router.get("/{share_id}", response_model=ShareResponse)
async def get_share(
    share_id: str,
    db: Connection = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """공유 설정 조회"""
    service = ShareService(db)
    share = await service.get_share(share_id)
    return share


@router.get("/resource/{resource_type}/{resource_id}", response_model=list[ShareWithDetails])
async def get_resource_shares(
    resource_type: str,
    resource_id: str,
    db: Connection = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """리소스의 모든 공유 설정 조회"""
    service = ShareService(db)
    shares = await service.get_resource_shares(resource_type, resource_id)
    return shares


@router.get("/shared-with-me", response_model=list[ShareResponse])
async def get_shared_with_me(
    db: Connection = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """나와 공유된 모든 리소스 조회"""
    service = ShareService(db)
    shares = await service.get_user_shares(user_id)
    return shares


@router.put("/{share_id}", response_model=ShareResponse)
async def update_share_role(
    share_id: str,
    role_data: ShareUpdate,
    db: Connection = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """공유 설정 역할 수정"""
    service = ShareService(db)
    share = await service.update_share_role(share_id, role_data.role, user_id)
    return share


@router.delete("/{share_id}")
async def delete_share(
    share_id: str,
    db: Connection = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """공유 설정 삭제"""
    service = ShareService(db)
    await service.delete_share(share_id, user_id)
    return {"message": "공유 설정이 삭제되었습니다"}
