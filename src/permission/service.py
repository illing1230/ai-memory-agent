"""Permission Service"""

from typing import Any, Literal

import aiosqlite

from src.permission.repository import PermissionRepository


class PermissionService:
    """권한 관련 비즈니스 로직"""

    def __init__(self, db: aiosqlite.Connection):
        self.repo = PermissionRepository(db)

    async def check_permission(
        self,
        user_id: str,
        resource_type: Literal["memory", "chat_room", "project"],
        resource_id: str,
        action: str = "read",
    ) -> dict[str, Any]:
        """권한 확인"""
        if resource_type == "memory":
            result = await self.repo.check_memory_permission(resource_id, user_id)
        elif resource_type == "project":
            result = await self.repo.check_project_permission(resource_id, user_id)
        else:
            result = {"allowed": False, "reason": "지원하지 않는 리소스 타입"}

        return {
            "allowed": result["allowed"],
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "reason": result.get("reason"),
        }
