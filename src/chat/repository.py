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
        """채팅방 삭제 (관련 메시지, 멤버, 메모리도 함께 삭제)"""
        # 1. 채팅방 메시지 삭제
        await self.db.execute(
            "DELETE FROM chat_messages WHERE chat_room_id = ?", (room_id,)
        )
        
        # 2. 채팅방 멤버 삭제
        await self.db.execute(
            "DELETE FROM chat_room_members WHERE chat_room_id = ?", (room_id,)
        )
        
        # 3. 채팅방 메모리 삭제 (scope="chatroom"인 메모리만)
        await self.db.execute(
            "DELETE FROM memories WHERE chat_room_id = ? AND scope = 'chatroom'", (room_id,)
        )
        
        # 4. 채팅방 삭제
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

    # ==================== Chat Room Members ====================

    async def add_member(
        self,
        chat_room_id: str,
        user_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        """채팅방 멤버 추가"""
        member_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO chat_room_members (id, chat_room_id, user_id, role)
               VALUES (?, ?, ?, ?)""",
            (member_id, chat_room_id, user_id, role),
        )
        await self.db.commit()
        return await self.get_member(chat_room_id, user_id)

    async def get_member(
        self,
        chat_room_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        """채팅방 멤버 조회"""
        cursor = await self.db.execute(
            """SELECT m.*, u.name as user_name, u.email as user_email
               FROM chat_room_members m
               LEFT JOIN users u ON m.user_id = u.id
               WHERE m.chat_room_id = ? AND m.user_id = ?""",
            (chat_room_id, user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_members(
        self,
        chat_room_id: str,
    ) -> list[dict[str, Any]]:
        """채팅방 멤버 목록"""
        cursor = await self.db.execute(
            """SELECT m.*, u.name as user_name, u.email as user_email
               FROM chat_room_members m
               LEFT JOIN users u ON m.user_id = u.id
               WHERE m.chat_room_id = ?
               ORDER BY m.role, m.joined_at""",
            (chat_room_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_member_role(
        self,
        chat_room_id: str,
        user_id: str,
        role: str,
    ) -> dict[str, Any] | None:
        """채팅방 멤버 역할 변경"""
        await self.db.execute(
            """UPDATE chat_room_members SET role = ?
               WHERE chat_room_id = ? AND user_id = ?""",
            (role, chat_room_id, user_id),
        )
        await self.db.commit()
        return await self.get_member(chat_room_id, user_id)

    async def remove_member(
        self,
        chat_room_id: str,
        user_id: str,
    ) -> bool:
        """채팅방 멤버 제거"""
        cursor = await self.db.execute(
            """DELETE FROM chat_room_members
               WHERE chat_room_id = ? AND user_id = ?""",
            (chat_room_id, user_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def is_member(
        self,
        chat_room_id: str,
        user_id: str,
    ) -> bool:
        """멤버 여부 확인"""
        member = await self.get_member(chat_room_id, user_id)
        return member is not None

    async def get_user_rooms(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """사용자가 속한 채팅방 목록 (멤버 + 공유받은 채팅방)"""
        # 1. 멤버로 속한 채팅방
        cursor = await self.db.execute(
            """SELECT r.*, m.role as member_role
               FROM chat_rooms r
               INNER JOIN chat_room_members m ON r.id = m.chat_room_id
               WHERE m.user_id = ?""",
            (user_id,),
        )
        member_rows = await cursor.fetchall()
        
        # 2. 공유받은 채팅방
        cursor = await self.db.execute(
            """SELECT r.*, s.role as member_role
               FROM chat_rooms r
               INNER JOIN shares s ON r.id = s.resource_id
               WHERE s.resource_type = 'chat_room'
               AND s.target_type = 'user'
               AND s.target_id = ?""",
            (user_id,),
        )
        shared_rows = await cursor.fetchall()
        
        # 중복 제거 (멤버로 속한 채팅방이 우선)
        seen_ids = set()
        results = []
        
        # 멤버 채팅방 먼저 추가
        for row in member_rows:
            data = dict(row)
            if data.get("context_sources"):
                data["context_sources"] = json.loads(data["context_sources"])
            results.append(data)
            seen_ids.add(data["id"])
        
        # 공유받은 채팅방 추가 (중복 제외)
        for row in shared_rows:
            data = dict(row)
            if data["id"] not in seen_ids:
                if data.get("context_sources"):
                    data["context_sources"] = json.loads(data["context_sources"])
                results.append(data)
                seen_ids.add(data["id"])
        
        # created_at 기준 정렬
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return results
