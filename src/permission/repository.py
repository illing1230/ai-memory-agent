"""Permission Repository"""

from typing import Any

import aiosqlite


class PermissionRepository:
    """권한 관련 데이터베이스 작업"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def check_memory_permission(
        self,
        memory_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """메모리 접근 권한 확인"""
        # 메모리 조회
        cursor = await self.db.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        )
        memory = await cursor.fetchone()
        if not memory:
            return {"allowed": False, "reason": "메모리를 찾을 수 없습니다"}

        memory = dict(memory)
        scope = memory["scope"]

        # 개인 메모리
        if scope == "personal":
            if memory["owner_id"] == user_id:
                return {"allowed": True, "reason": "소유자"}
            return {"allowed": False, "reason": "개인 메모리에 대한 접근 권한이 없습니다"}

        # 프로젝트 메모리
        if scope == "project":
            project_id = memory.get("project_id")
            if project_id:
                # 직접 멤버 확인
                cursor = await self.db.execute(
                    "SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ?",
                    (project_id, user_id),
                )
                if await cursor.fetchone():
                    return {"allowed": True, "reason": "프로젝트 멤버"}
                # 프로젝트 공유 확인
                if await self._check_share_access("project", project_id, user_id):
                    return {"allowed": True, "reason": "프로젝트 공유"}
            return {"allowed": False, "reason": "프로젝트 멤버가 아닙니다"}

        # 부서 메모리
        if scope == "department":
            department_id = memory.get("department_id")
            cursor = await self.db.execute(
                "SELECT department_id FROM users WHERE id = ?", (user_id,)
            )
            user = await cursor.fetchone()
            if user and user["department_id"] == department_id:
                return {"allowed": True, "reason": "같은 부서"}
            return {"allowed": False, "reason": "같은 부서가 아닙니다"}

        # 채팅방 메모리
        if scope == "chatroom":
            chat_room_id = memory.get("chat_room_id")
            if chat_room_id:
                # 직접 멤버 확인
                cursor = await self.db.execute(
                    "SELECT 1 FROM chat_room_members WHERE chat_room_id = ? AND user_id = ?",
                    (chat_room_id, user_id),
                )
                if await cursor.fetchone():
                    return {"allowed": True, "reason": "채팅방 멤버"}
                # 채팅방 공유 확인 (viewer/member 모두 메모리 접근 가능)
                if await self._check_share_access("chat_room", chat_room_id, user_id):
                    return {"allowed": True, "reason": "채팅방 공유"}
            return {"allowed": False, "reason": "채팅방 멤버가 아닙니다"}

        return {"allowed": False, "reason": "알 수 없는 권한 범위"}

    async def _check_share_access(
        self,
        resource_type: str,
        resource_id: str,
        user_id: str,
    ) -> bool:
        """shares 테이블에서 사용자의 리소스 접근 권한 확인 (user/project/department 레벨)"""
        # 1. 직접 사용자 공유
        cursor = await self.db.execute(
            """SELECT 1 FROM shares
               WHERE resource_type = ? AND resource_id = ?
               AND target_type = 'user' AND target_id = ?""",
            (resource_type, resource_id, user_id),
        )
        if await cursor.fetchone():
            return True

        # 2. 프로젝트 레벨 공유
        cursor = await self.db.execute(
            """SELECT 1 FROM shares s
               INNER JOIN project_members pm ON s.target_id = pm.project_id
               WHERE s.resource_type = ? AND s.resource_id = ?
               AND s.target_type = 'project' AND pm.user_id = ?""",
            (resource_type, resource_id, user_id),
        )
        if await cursor.fetchone():
            return True

        # 3. 부서 레벨 공유
        cursor = await self.db.execute(
            """SELECT 1 FROM shares s
               INNER JOIN users u ON s.target_id = u.department_id
               WHERE s.resource_type = ? AND s.resource_id = ?
               AND s.target_type = 'department' AND u.id = ?""",
            (resource_type, resource_id, user_id),
        )
        if await cursor.fetchone():
            return True

        return False

    async def check_project_permission(
        self,
        project_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """프로젝트 접근 권한 확인"""
        cursor = await self.db.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, user_id),
        )
        member = await cursor.fetchone()
        if member:
            return {"allowed": True, "reason": f"프로젝트 {member['role']}"}
        return {"allowed": False, "reason": "프로젝트 멤버가 아닙니다"}
