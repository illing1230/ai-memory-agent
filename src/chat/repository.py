"""Chat Room Repository"""

import uuid
from typing import Any, Literal

import aiosqlite


class ChatRepository:
    """채팅방 관련 데이터베이스 작업"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create_chat_room(
        self,
        name: str,
        owner_id: str,
        room_type: Literal["personal", "project", "department"] = "personal",
        project_id: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """채팅방 생성"""
        room_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO chat_rooms (id, name, room_type, owner_id, project_id, department_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (room_id, name, room_type, owner_id, project_id, department_id),
        )
        await self.db.commit()
        return await self.get_chat_room(room_id)

    async def get_chat_room(self, room_id: str) -> dict[str, Any] | None:
        """채팅방 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM chat_rooms WHERE id = ?", (room_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_chat_rooms(
        self,
        owner_id: str | None = None,
        room_type: str | None = None,
        project_id: str | None = None,
        department_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """채팅방 목록 조회"""
        conditions = []
        params = []

        if owner_id:
            conditions.append("owner_id = ?")
            params.append(owner_id)
        if room_type:
            conditions.append("room_type = ?")
            params.append(room_type)
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if department_id:
            conditions.append("department_id = ?")
            params.append(department_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor = await self.db.execute(
            f"SELECT * FROM chat_rooms WHERE {where_clause} ORDER BY created_at DESC",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def delete_chat_room(self, room_id: str) -> bool:
        """채팅방 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM chat_rooms WHERE id = ?", (room_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0
