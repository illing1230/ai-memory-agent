"""Memory Repository - 데이터 접근 계층"""

import json
import uuid
from datetime import datetime
from typing import Any, Literal

import aiosqlite


class MemoryRepository:
    """메모리 관련 데이터베이스 작업"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create_memory(
        self,
        content: str,
        owner_id: str,
        scope: Literal["personal", "project", "department", "chatroom"] = "personal",
        vector_id: str | None = None,
        project_id: str | None = None,
        department_id: str | None = None,
        chat_room_id: str | None = None,
        source_message_id: str | None = None,
        category: str | None = None,
        importance: str = "medium",
        metadata: dict | None = None,
        topic_key: str | None = None,
        superseded: bool = False,
        superseded_by: str | None = None,
        superseded_at: str | None = None,
    ) -> dict[str, Any]:
        """메모리 생성"""
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await self.db.execute(
            """INSERT INTO memories 
               (id, content, vector_id, scope, owner_id, project_id, department_id,
                chat_room_id, source_message_id, category, importance, metadata, topic_key, superseded, superseded_by, superseded_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory_id,
                content,
                vector_id,
                scope,
                owner_id,
                project_id,
                department_id,
                chat_room_id,
                source_message_id,
                category,
                importance,
                json.dumps(metadata) if metadata else None,
                topic_key,
                1 if superseded else 0,
                superseded_by,
                superseded_at,
                now,
                now,
            ),
        )
        await self.db.commit()
        return await self.get_memory(memory_id)

    async def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        """메모리 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        )
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            if data.get("metadata"):
                data["metadata"] = json.loads(data["metadata"])
            return data
        return None

    async def list_memories(
        self,
        owner_id: str | None = None,
        scope: str | None = None,
        project_id: str | None = None,
        department_id: str | None = None,
        chat_room_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """메모리 목록 조회"""
        conditions = []
        params = []

        if owner_id:
            conditions.append("owner_id = ?")
            params.append(owner_id)
        if scope:
            conditions.append("scope = ?")
            params.append(scope)
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if department_id:
            conditions.append("department_id = ?")
            params.append(department_id)
        if chat_room_id:
            conditions.append("chat_room_id = ?")
            params.append(chat_room_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.extend([limit, offset])

        cursor = await self.db.execute(
            f"""SELECT * FROM memories 
                WHERE {where_clause} 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?""",
            params,
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            if data.get("metadata"):
                data["metadata"] = json.loads(data["metadata"])
            results.append(data)
        return results

    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        vector_id: str | None = None,
        category: str | None = None,
        importance: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any] | None:
        """메모리 수정"""
        updates = []
        params = []

        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if vector_id is not None:
            updates.append("vector_id = ?")
            params.append(vector_id)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if importance is not None:
            updates.append("importance = ?")
            params.append(importance)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))

        if not updates:
            return await self.get_memory(memory_id)

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(memory_id)

        await self.db.execute(
            f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await self.db.commit()
        return await self.get_memory(memory_id)

    async def delete_memory(self, memory_id: str) -> bool:
        """메모리 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM memories WHERE id = ?", (memory_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def get_memories_by_vector_ids(
        self, vector_ids: list[str]
    ) -> list[dict[str, Any]]:
        """벡터 ID로 메모리 조회"""
        if not vector_ids:
            return []

        placeholders = ",".join("?" * len(vector_ids))
        cursor = await self.db.execute(
            f"SELECT * FROM memories WHERE vector_id IN ({placeholders})",
            vector_ids,
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            if data.get("metadata"):
                data["metadata"] = json.loads(data["metadata"])
            results.append(data)
        return results

    async def log_memory_access(
        self,
        memory_id: str,
        user_id: str,
        action: Literal["read", "update", "delete"],
    ) -> None:
        """메모리 접근 로그 기록"""
        log_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO memory_access_log (id, memory_id, user_id, action)
               VALUES (?, ?, ?, ?)""",
            (log_id, memory_id, user_id, action),
        )
        await self.db.commit()

    async def update_superseded(
        self,
        memory_id: str,
        superseded_by: str,
    ) -> dict[str, Any] | None:
        """메모리를 superseded 상태로 업데이트"""
        now = datetime.utcnow().isoformat()
        await self.db.execute(
            """UPDATE memories 
               SET superseded = 1, superseded_by = ?, superseded_at = ?
               WHERE id = ?""",
            (superseded_by, now, memory_id),
        )
        await self.db.commit()
        return await self.get_memory(memory_id)

    async def get_memories_by_topic_key(
        self,
        topic_key: str,
        owner_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """topic_key로 메모리 검색"""
        conditions = ["topic_key = ?"]
        params = [topic_key]
        
        if owner_id:
            conditions.append("owner_id = ?")
            params.append(owner_id)
        
        params.append(limit)
        
        where_clause = " AND ".join(conditions)
        cursor = await self.db.execute(
            f"""SELECT * FROM memories 
                WHERE {where_clause} 
                ORDER BY created_at DESC 
                LIMIT ?""",
            params,
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            if data.get("metadata"):
                data["metadata"] = json.loads(data["metadata"])
            results.append(data)
        return results
