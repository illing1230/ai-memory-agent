"""Share Repository"""
import aiosqlite
import uuid
from typing import Any


class ShareRepository:
    """공유 설정 관련 데이터베이스 작업"""
    
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
    
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
        share_id = str(uuid.uuid4())
        
        await self.db.execute(
            """
            INSERT INTO shares (id, resource_type, resource_id, target_type, target_id, role, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (share_id, resource_type, resource_id, target_type, target_id, role, created_by),
        )
        await self.db.commit()
        
        return await self.get_share(share_id)
    
    async def get_share(self, share_id: str) -> dict[str, Any] | None:
        """공유 설정 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM shares WHERE id = ?",
            (share_id,),
        )
        row = await cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    async def get_resource_shares(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[dict[str, Any]]:
        """리소스의 모든 공유 설정 조회"""
        cursor = await self.db.execute(
            """
            SELECT * FROM shares
            WHERE resource_type = ? AND resource_id = ?
            ORDER BY created_at DESC
            """,
            (resource_type, resource_id),
        )
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def get_user_shares(self, user_id: str) -> list[dict[str, Any]]:
        """사용자와 공유된 모든 리소스 조회"""
        cursor = await self.db.execute(
            """
            SELECT * FROM shares
            WHERE target_type = 'user' AND target_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def get_project_shares(self, project_id: str) -> list[dict[str, Any]]:
        """프로젝트와 공유된 모든 리소스 조회"""
        cursor = await self.db.execute(
            """
            SELECT * FROM shares
            WHERE target_type = 'project' AND target_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        )
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def get_department_shares(self, department_id: str) -> list[dict[str, Any]]:
        """부서와 공유된 모든 리소스 조회"""
        cursor = await self.db.execute(
            """
            SELECT * FROM shares
            WHERE target_type = 'department' AND target_id = ?
            ORDER BY created_at DESC
            """,
            (department_id,),
        )
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def update_share_role(self, share_id: str, role: str) -> dict[str, Any] | None:
        """공유 설정 역할 수정"""
        await self.db.execute(
            "UPDATE shares SET role = ? WHERE id = ?",
            (role, share_id),
        )
        await self.db.commit()
        
        return await self.get_share(share_id)
    
    async def delete_share(self, share_id: str) -> bool:
        """공유 설정 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM shares WHERE id = ?",
            (share_id,),
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    async def delete_resource_shares(
        self,
        resource_type: str,
        resource_id: str,
    ) -> int:
        """리소스의 모든 공유 설정 삭제"""
        cursor = await self.db.execute(
            """
            DELETE FROM shares
            WHERE resource_type = ? AND resource_id = ?
            """,
            (resource_type, resource_id),
        )
        await self.db.commit()
        
        return cursor.rowcount
    
    async def check_share_exists(
        self,
        resource_type: str,
        resource_id: str,
        target_type: str,
        target_id: str,
    ) -> bool:
        """공유 설정 존재 여부 확인"""
        cursor = await self.db.execute(
            """
            SELECT id FROM shares
            WHERE resource_type = ? AND resource_id = ?
              AND target_type = ? AND target_id = ?
            """,
            (resource_type, resource_id, target_type, target_id),
        )
        row = await cursor.fetchone()
        
        return row is not None
