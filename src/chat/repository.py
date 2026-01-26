"""Chat Room Repository"""

import json
import uuid
from typing import Any, Literal

import aiosqlite


class ChatRepository:
    """채팅방 관련 데이터베이스 작업"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    # ==================== Chat Room ====================

    async def create_chat_room(
        self,
        name: str,
        owner_id: str,
        room_type: Literal["personal", "project", "department"] = "personal",
        project_id: str | None = None,
        department_id: str | None = None,
        context_sources: dict | None = None,
    ) -> dict[str, Any]:
        """채팅방 생성"""
        room_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO chat_rooms (id, name, room_type, owner_id, project_id, department_id, context_sources)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (room_id, name, room_type, owner_id, project_id, department_id, 
             json.dumps(context_sources) if context_sources else None),
        )
        await self.db.commit()
        return await self.get_chat_room(room_id)

    async def get_chat_room(self, room_id: str) -> dict[str, Any] | None:
        """채팅방 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM chat_rooms WHERE id = ?", (room_id,)
        )
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            if data.get("context_sources"):
                data["context_sources"] = json.loads(data["context_sources"])
            return data
        return None

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
        results = []
        for row in rows:
            data = dict(row)
            if data.get("context_sources"):
                data["context_sources"] = json.loads(data["context_sources"])
            results.append(data)
        return results

    async def update_chat_room(
        self,
        room_id: str,
        name: str | None = None,
        context_sources: dict | None = None,
    ) -> dict[str, Any] | None:
        """채팅방 수정"""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if context_sources is not None:
            updates.append("context_sources = ?")
            params.append(json.dumps(context_sources))

        if not updates:
            return await self.get_chat_room(room_id)

        params.append(room_id)
        await self.db.execute(
            f"UPDATE chat_rooms SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await self.db.commit()
        return await self.get_chat_room(room_id)

    async def delete_chat_room(self, room_id: str) -> bool:
        """채팅방 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM chat_rooms WHERE id = ?", (room_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ==================== Chat Messages ====================

    async def create_message(
        self,
        chat_room_id: str,
        user_id: str,
        content: str,
        role: Literal["user", "assistant"] = "user",
        mentions: list[str] | None = None,
    ) -> dict[str, Any]:
        """메시지 생성"""
        message_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO chat_messages (id, chat_room_id, user_id, role, content, mentions)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_id, chat_room_id, user_id, role, content,
             json.dumps(mentions) if mentions else None),
        )
        await self.db.commit()
        return await self.get_message(message_id)

    async def get_message(self, message_id: str) -> dict[str, Any] | None:
        """메시지 조회"""
        cursor = await self.db.execute(
            """SELECT m.*, u.name as user_name 
               FROM chat_messages m
               LEFT JOIN users u ON m.user_id = u.id
               WHERE m.id = ?""",
            (message_id,)
        )
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            if data.get("mentions"):
                data["mentions"] = json.loads(data["mentions"])
            return data
        return None

    async def list_messages(
        self,
        chat_room_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """채팅방 메시지 목록 조회"""
        cursor = await self.db.execute(
            """SELECT m.*, u.name as user_name 
               FROM chat_messages m
               LEFT JOIN users u ON m.user_id = u.id
               WHERE m.chat_room_id = ?
               ORDER BY m.created_at ASC
               LIMIT ? OFFSET ?""",
            (chat_room_id, limit, offset),
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            if data.get("mentions"):
                data["mentions"] = json.loads(data["mentions"])
            results.append(data)
        return results

    async def get_recent_messages(
        self,
        chat_room_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """최근 메시지 조회 (컨텍스트용)"""
        cursor = await self.db.execute(
            """SELECT m.*, u.name as user_name 
               FROM chat_messages m
               LEFT JOIN users u ON m.user_id = u.id
               WHERE m.chat_room_id = ?
               ORDER BY m.created_at DESC
               LIMIT ?""",
            (chat_room_id, limit),
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            if data.get("mentions"):
                data["mentions"] = json.loads(data["mentions"])
            results.append(data)
        # 시간순 정렬 (오래된 것부터)
        return list(reversed(results))
