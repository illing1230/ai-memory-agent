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
        scope: Literal["personal", "chatroom", "agent"] = "personal",
        vector_id: str | None = None,
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
               (id, content, vector_id, scope, owner_id,
                chat_room_id, source_message_id, category, importance, metadata, topic_key, superseded, superseded_by, superseded_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory_id,
                content,
                vector_id,
                scope,
                owner_id,
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
        chat_room_id: str | None = None,
        agent_instance_id: str | None = None,
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
        
        # agent_instance_id 필터링 (Python 레벨)
        if agent_instance_id:
            results = [
                r for r in results
                if r.get("metadata") and 
                   r["metadata"].get("source") == "agent" and
                   r["metadata"].get("agent_instance_id") == agent_instance_id
            ]
        
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
        # 엔티티 링크 정리 (CASCADE로도 처리되지만 명시적으로 삭제)
        await self.db.execute(
            "DELETE FROM memory_entities WHERE memory_id = ?", (memory_id,)
        )
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

    async def get_memories_by_ids(self, memory_ids: list[str]) -> list[dict[str, Any]]:
        """memory_id 목록으로 메모리 배치 조회 (N+1 방지)"""
        if not memory_ids:
            return []

        # 중복 제거
        unique_ids = list(set(memory_ids))
        placeholders = ",".join("?" * len(unique_ids))
        cursor = await self.db.execute(
            f"SELECT * FROM memories WHERE id IN ({placeholders})",
            unique_ids,
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            if data.get("metadata"):
                data["metadata"] = json.loads(data["metadata"])
            results.append(data)
        return results

    async def decay_unused_memories(self, days_threshold: int = 30) -> int:
        """오래 사용되지 않은 메모리의 importance를 하향 조정 (lazy decay)
        - high → medium (30일 미접근)
        - medium → low (60일 미접근)
        """
        now = datetime.utcnow().isoformat()
        # high → medium: last_accessed_at이 threshold일 이상 경과
        cursor = await self.db.execute(
            """UPDATE memories
               SET importance = 'medium', updated_at = ?
               WHERE importance = 'high'
                 AND superseded = 0
                 AND (
                     (last_accessed_at IS NOT NULL AND julianday(?) - julianday(last_accessed_at) > ?)
                     OR (last_accessed_at IS NULL AND julianday(?) - julianday(created_at) > ?)
                 )""",
            (now, now, days_threshold, now, days_threshold),
        )
        count_high = cursor.rowcount

        # medium → low: 2x threshold
        cursor = await self.db.execute(
            """UPDATE memories
               SET importance = 'low', updated_at = ?
               WHERE importance = 'medium'
                 AND superseded = 0
                 AND (
                     (last_accessed_at IS NOT NULL AND julianday(?) - julianday(last_accessed_at) > ?)
                     OR (last_accessed_at IS NULL AND julianday(?) - julianday(created_at) > ?)
                 )""",
            (now, now, days_threshold * 2, now, days_threshold * 2),
        )
        count_medium = cursor.rowcount

        if count_high + count_medium > 0:
            await self.db.commit()
            print(f"메모리 감쇠: high→medium {count_high}개, medium→low {count_medium}개")

        return count_high + count_medium

    async def update_access(self, memory_ids: list[str]) -> None:
        """메모리 접근 추적: last_accessed_at, access_count 업데이트"""
        if not memory_ids:
            return
        now = datetime.utcnow().isoformat()
        for mid in memory_ids:
            await self.db.execute(
                """UPDATE memories
                   SET last_accessed_at = ?, access_count = COALESCE(access_count, 0) + 1
                   WHERE id = ?""",
                (now, mid),
            )
        await self.db.commit()

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
        """메모리를 superseded 상태로 업데이트하고 Qdrant에서도 삭제"""
        # 먼저 메모리 정보 조회 (vector_id 필요)
        memory = await self.get_memory(memory_id)

        now = datetime.utcnow().isoformat()
        await self.db.execute(
            """UPDATE memories
               SET superseded = 1, superseded_by = ?, superseded_at = ?
               WHERE id = ?""",
            (superseded_by, now, memory_id),
        )
        await self.db.commit()

        # Qdrant에서도 삭제하여 검색에 노출되지 않도록 함
        if memory and memory.get("vector_id"):
            try:
                from src.shared.vector_store import delete_vector
                await delete_vector(memory["vector_id"])
                print(f"Superseded 메모리 Qdrant 삭제: {memory_id}")
            except Exception as e:
                print(f"Superseded 메모리 Qdrant 삭제 실패: {e}")

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
