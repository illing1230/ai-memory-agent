"""Share Service"""
import aiosqlite
from typing import Any

from src.share.repository import ShareRepository
from src.user.repository import UserRepository
from src.shared.exceptions import ForbiddenException, NotFoundException


class ShareService:
    """공유 설정 관련 비즈니스 로직"""
    
    def __init__(self, db: aiosqlite.Connection):
        self.repo = ShareRepository(db)
        self.user_repo = UserRepository(db)
    
    async def create_share(
        self,
        resource_type: str,
        resource_id: str,
        target_type: str,
        target_id: str,
        role: str,
        created_by: str,
    ) -> dict[str, Any]:
        """공유 설정 생성"""
        # 이미 존재하는지 확인
        exists = await self.repo.check_share_exists(
            resource_type, resource_id, target_type, target_id
        )
        if exists:
            raise ForbiddenException("이미 공유된 대상입니다")
        
        # 공유 설정 생성
        share = await self.repo.create_share(
            resource_type=resource_type,
            resource_id=resource_id,
            target_type=target_type,
            target_id=target_id,
            role=role,
            created_by=created_by,
        )
        
        return share
    
    async def get_share(self, share_id: str) -> dict[str, Any]:
        """공유 설정 조회"""
        share = await self.repo.get_share(share_id)
        if not share:
            raise NotFoundException("공유 설정", share_id)
        return share
    
    async def get_resource_shares(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[dict[str, Any]]:
        """리소스의 모든 공유 설정 조회 (상세 정보 포함)"""
        shares = await self.repo.get_resource_shares(resource_type, resource_id)
        
        # 상세 정보 추가
        for share in shares:
            if share["target_type"] == "user":
                user = await self.user_repo.get_user(share["target_id"])
                if user:
                    share["target_name"] = user["name"]
                    share["target_email"] = user["email"]
            
            creator = await self.user_repo.get_user(share["created_by"])
            if creator:
                share["creator_name"] = creator["name"]
        
        return shares
    
    async def get_user_shares(self, user_id: str) -> list[dict[str, Any]]:
        """사용자와 공유된 모든 리소스 조회"""
        return await self.repo.get_user_shares(user_id)
    
    async def update_share_role(
        self,
        share_id: str,
        role: str,
        user_id: str,
    ) -> dict[str, Any]:
        """공유 설정 역할 수정"""
        share = await self.repo.get_share(share_id)
        if not share:
            raise NotFoundException("공유 설정", share_id)
        
        # 생성자만 수정 가능
        if share["created_by"] != user_id:
            raise ForbiddenException("공유 설정을 수정할 권한이 없습니다")
        
        updated_share = await self.repo.update_share_role(share_id, role)
        return updated_share
    
    async def delete_share(
        self,
        share_id: str,
        user_id: str,
    ) -> bool:
        """공유 설정 삭제"""
        share = await self.repo.get_share(share_id)
        if not share:
            raise NotFoundException("공유 설정", share_id)
        
        # 생성자만 삭제 가능
        if share["created_by"] != user_id:
            raise ForbiddenException("공유 설정을 삭제할 권한이 없습니다")
        
        return await self.repo.delete_share(share_id)
    
    async def delete_resource_shares(
        self,
        resource_type: str,
        resource_id: str,
    ) -> int:
        """리소스의 모든 공유 설정 삭제"""
        return await self.repo.delete_resource_shares(resource_type, resource_id)
