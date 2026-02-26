"""MemoryService 테스트"""

import pytest
from unittest.mock import patch, AsyncMock

from src.memory.service import MemoryService
from src.shared.exceptions import NotFoundException, PermissionDeniedException


class TestCreateMemory:
    async def test_creates_with_embedding(self, db, seed_users, mock_embedding_provider, mock_vector_store):
        with patch("src.memory.service.get_embedding_provider", return_value=mock_embedding_provider):
            svc = MemoryService(db)
            memory = await svc.create_memory(
                content="테스트 메모리",
                owner_id="user-1",
                scope="personal",
            )
            assert memory["content"] == "테스트 메모리"
            assert memory["vector_id"] is not None
            mock_embedding_provider.embed.assert_awaited_once()
            mock_vector_store["upsert"].assert_awaited_once()


class TestGetMemory:
    async def test_owner_access(self, db, seed_memories):
        svc = MemoryService(db)
        memory = await svc.get_memory("mem-1", "user-1")
        assert memory["id"] == "mem-1"

    async def test_not_found(self, db, seed_users):
        svc = MemoryService(db)
        with pytest.raises(NotFoundException):
            await svc.get_memory("non-existent", "user-1")

    async def test_personal_scope_wrong_user(self, db, seed_memories):
        svc = MemoryService(db)
        with pytest.raises(PermissionDeniedException):
            await svc.get_memory("mem-1", "user-2")

    async def test_chatroom_member_access(self, db, seed_memories):
        """대화방 멤버는 chatroom 스코프 메모리에 접근 가능"""
        svc = MemoryService(db)
        memory = await svc.get_memory("mem-2", "user-2")
        assert memory["id"] == "mem-2"

    async def test_chatroom_non_member_denied(self, db, seed_memories):
        """대화방 비멤버는 chatroom 스코프 메모리 접근 불가"""
        svc = MemoryService(db)
        with pytest.raises(PermissionDeniedException):
            await svc.get_memory("mem-2", "user-3")


class TestListMemories:
    async def test_combined_scopes(self, db, seed_memories):
        svc = MemoryService(db)
        results = await svc.list_memories("user-1")
        # personal + chatroom(room-1 멤버) + agent
        assert len(results) >= 3

    async def test_user_not_found(self, db):
        svc = MemoryService(db)
        with pytest.raises(NotFoundException):
            await svc.list_memories("non-existent-user")

    async def test_scope_filter(self, db, seed_memories):
        svc = MemoryService(db)
        results = await svc.list_memories("user-1", scope="personal")
        assert all(r["memory"]["scope"] == "personal" for r in results)


class TestUpdateMemory:
    async def test_owner_can_update(self, db, seed_memories, mock_embedding_provider, mock_vector_store):
        with patch("src.memory.service.get_embedding_provider", return_value=mock_embedding_provider):
            svc = MemoryService(db)
            # mem-1에 vector_id 추가
            await db.execute("UPDATE memories SET vector_id = 'vec-1' WHERE id = 'mem-1'")
            await db.commit()

            updated = await svc.update_memory("mem-1", "user-1", content="수정됨")
            assert updated["content"] == "수정됨"

    async def test_non_owner_denied(self, db, seed_memories):
        svc = MemoryService(db)
        with pytest.raises(PermissionDeniedException):
            await svc.update_memory("mem-1", "user-2", content="해킹")


class TestDeleteMemory:
    async def test_owner_can_delete(self, db, seed_memories, mock_vector_store):
        svc = MemoryService(db)
        result = await svc.delete_memory("mem-1", "user-1")
        assert result is True

    async def test_non_owner_denied(self, db, seed_memories, mock_vector_store):
        svc = MemoryService(db)
        with pytest.raises(PermissionDeniedException):
            await svc.delete_memory("mem-1", "user-2")


class TestDeleteMemoriesByRoom:
    async def test_member_can_delete_own(self, db, seed_memories, mock_vector_store):
        svc = MemoryService(db)
        count = await svc.delete_memories_by_room("room-1", "user-1")
        assert count == 1  # mem-2만 삭제됨 (user-1 소유)

    async def test_non_member_denied(self, db, seed_memories, mock_vector_store):
        svc = MemoryService(db)
        with pytest.raises(PermissionDeniedException):
            await svc.delete_memories_by_room("room-1", "user-3")


class TestCheckDuplicate:
    async def test_duplicate_detected(self, db, seed_users, mock_embedding_provider, mock_vector_store):
        """유사도 threshold 이상이면 중복으로 판단"""
        mock_vector_store["search"].return_value = [
            {"id": "vec-1", "score": 0.97, "payload": {"memory_id": "mem-x"}}
        ]
        with patch("src.memory.service.get_embedding_provider", return_value=mock_embedding_provider):
            svc = MemoryService(db)
            is_dup = await svc._check_duplicate("중복 내용", "user-1")
            assert is_dup is True

    async def test_no_duplicate(self, db, seed_users, mock_embedding_provider, mock_vector_store):
        """유사도 threshold 미만이면 중복 아님"""
        mock_vector_store["search"].return_value = []
        with patch("src.memory.service.get_embedding_provider", return_value=mock_embedding_provider):
            svc = MemoryService(db)
            is_dup = await svc._check_duplicate("새로운 내용", "user-1")
            assert is_dup is False
