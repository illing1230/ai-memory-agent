"""MemoryRepository 테스트"""

import pytest
from src.memory.repository import MemoryRepository


class TestCreateMemory:
    async def test_create_basic(self, db, seed_users):
        repo = MemoryRepository(db)
        memory = await repo.create_memory(
            content="테스트 메모리",
            owner_id="user-1",
            scope="personal",
        )
        assert memory["content"] == "테스트 메모리"
        assert memory["owner_id"] == "user-1"
        assert memory["scope"] == "personal"
        assert memory["id"] is not None

    async def test_create_with_metadata(self, db, seed_users):
        repo = MemoryRepository(db)
        memory = await repo.create_memory(
            content="메타데이터 포함",
            owner_id="user-1",
            metadata={"source": "agent", "agent_instance_id": "ai-1"},
        )
        assert memory["metadata"]["source"] == "agent"
        assert memory["metadata"]["agent_instance_id"] == "ai-1"

    async def test_create_chatroom_scope(self, db, seed_chat_room):
        repo = MemoryRepository(db)
        memory = await repo.create_memory(
            content="대화방 메모리",
            owner_id="user-1",
            scope="chatroom",
            chat_room_id="room-1",
            category="decision",
            importance="high",
        )
        assert memory["scope"] == "chatroom"
        assert memory["chat_room_id"] == "room-1"
        assert memory["category"] == "decision"
        assert memory["importance"] == "high"

    async def test_create_with_topic_key(self, db, seed_users):
        repo = MemoryRepository(db)
        memory = await repo.create_memory(
            content="토픽 키 테스트",
            owner_id="user-1",
            topic_key="project-alpha",
        )
        assert memory["topic_key"] == "project-alpha"


class TestGetMemory:
    async def test_existing(self, db, seed_memories):
        repo = MemoryRepository(db)
        memory = await repo.get_memory("mem-1")
        assert memory is not None
        assert memory["content"] == "개인 메모리 내용"

    async def test_non_existing(self, db, seed_users):
        repo = MemoryRepository(db)
        assert await repo.get_memory("non-existent") is None

    async def test_metadata_parsed(self, db, seed_memories):
        repo = MemoryRepository(db)
        memory = await repo.get_memory("mem-3")
        assert isinstance(memory["metadata"], dict)
        assert memory["metadata"]["source"] == "agent"


class TestListMemories:
    async def test_by_owner(self, db, seed_memories):
        repo = MemoryRepository(db)
        memories = await repo.list_memories(owner_id="user-1")
        assert len(memories) == 3

    async def test_by_scope(self, db, seed_memories):
        repo = MemoryRepository(db)
        memories = await repo.list_memories(scope="personal")
        assert all(m["scope"] == "personal" for m in memories)

    async def test_by_chat_room(self, db, seed_memories):
        repo = MemoryRepository(db)
        memories = await repo.list_memories(chat_room_id="room-1")
        assert len(memories) == 1
        assert memories[0]["id"] == "mem-2"

    async def test_agent_instance_filter(self, db, seed_memories):
        repo = MemoryRepository(db)
        memories = await repo.list_memories(
            owner_id="user-1",
            agent_instance_id="agent-inst-1",
        )
        assert len(memories) == 1
        assert memories[0]["id"] == "mem-3"

    async def test_limit_offset(self, db, seed_memories):
        repo = MemoryRepository(db)
        memories = await repo.list_memories(owner_id="user-1", limit=1, offset=0)
        assert len(memories) == 1


class TestUpdateMemory:
    async def test_content_update(self, db, seed_memories):
        repo = MemoryRepository(db)
        updated = await repo.update_memory("mem-1", content="수정된 내용")
        assert updated["content"] == "수정된 내용"

    async def test_no_changes(self, db, seed_memories):
        repo = MemoryRepository(db)
        result = await repo.update_memory("mem-1")
        assert result["content"] == "개인 메모리 내용"


class TestDeleteMemory:
    async def test_existing(self, db, seed_memories):
        repo = MemoryRepository(db)
        assert await repo.delete_memory("mem-1") is True
        assert await repo.get_memory("mem-1") is None

    async def test_non_existing(self, db, seed_users):
        repo = MemoryRepository(db)
        assert await repo.delete_memory("non-existent") is False


class TestGetMemoriesByIds:
    async def test_batch_retrieval(self, db, seed_memories):
        repo = MemoryRepository(db)
        memories = await repo.get_memories_by_ids(["mem-1", "mem-2"])
        assert len(memories) == 2

    async def test_empty_list(self, db):
        repo = MemoryRepository(db)
        assert await repo.get_memories_by_ids([]) == []

    async def test_dedup(self, db, seed_memories):
        repo = MemoryRepository(db)
        memories = await repo.get_memories_by_ids(["mem-1", "mem-1"])
        assert len(memories) == 1


class TestSupersede:
    async def test_update_superseded(self, db, seed_memories):
        repo = MemoryRepository(db)
        # mem-1을 supersede로 표시하고 mem-2가 대체했다고 기록
        result = await repo.update_superseded("mem-1", superseded_by="mem-2")
        assert result["superseded"] == 1
        assert result["superseded_by"] == "mem-2"
        assert result["superseded_at"] is not None

    async def test_memory_history(self, db, seed_memories):
        repo = MemoryRepository(db)
        # mem-1 → mem-2 체인 생성
        await repo.update_superseded("mem-1", superseded_by="mem-2")
        history = await repo.get_memory_history("mem-1")
        assert len(history) >= 2
        # 시간순 정렬 확인
        for i in range(len(history) - 1):
            assert history[i]["created_at"] <= history[i + 1]["created_at"]


class TestGetMemoriesByTopicKey:
    async def test_by_topic(self, db, seed_users):
        repo = MemoryRepository(db)
        await repo.create_memory(content="토픽A-1", owner_id="user-1", topic_key="topicA")
        await repo.create_memory(content="토픽A-2", owner_id="user-1", topic_key="topicA")
        await repo.create_memory(content="토픽B", owner_id="user-1", topic_key="topicB")

        results = await repo.get_memories_by_topic_key("topicA")
        assert len(results) == 2
        assert all(r["topic_key"] == "topicA" for r in results)
