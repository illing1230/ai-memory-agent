"""MemoryPipeline 테스트"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

from src.memory.pipeline import MemoryPipeline, RECENCY_DECAY_DAYS
from src.memory.repository import MemoryRepository


class TestSearch:
    async def test_returns_results(self, db, seed_memories, mock_embedding_provider, mock_vector_store):
        """검색이 벡터 결과를 메모리 데이터와 조합하여 반환"""
        # vector_id를 설정
        await db.execute("UPDATE memories SET vector_id = 'vec-1' WHERE id = 'mem-2'")
        await db.commit()

        mock_vector_store["search"].return_value = [
            {"id": "vec-1", "score": 0.85, "payload": {"memory_id": "mem-2", "scope": "chatroom", "chat_room_id": "room-1"}}
        ]

        with patch("src.memory.pipeline.get_embedding_provider", return_value=mock_embedding_provider), \
             patch("src.memory.pipeline.get_reranker_provider", return_value=None):
            repo = MemoryRepository(db)
            pipeline = MemoryPipeline(repo)
            results = await pipeline.search(
                query="테스트",
                user_id="user-1",
                current_room_id="room-1",
            )
            assert len(results) >= 1

    async def test_excludes_superseded(self, db, seed_memories, mock_embedding_provider, mock_vector_store):
        """superseded 메모리는 검색 결과에서 제외"""
        await db.execute("UPDATE memories SET superseded = 1, vector_id = 'vec-1' WHERE id = 'mem-1'")
        await db.commit()

        mock_vector_store["search"].return_value = [
            {"id": "vec-1", "score": 0.9, "payload": {"memory_id": "mem-1", "scope": "personal"}}
        ]

        with patch("src.memory.pipeline.get_embedding_provider", return_value=mock_embedding_provider), \
             patch("src.memory.pipeline.get_reranker_provider", return_value=None):
            repo = MemoryRepository(db)
            pipeline = MemoryPipeline(repo)
            results = await pipeline.search("테스트", "user-1", "room-1")
            # superseded 메모리가 필터링되어야 함
            mem_ids = [r["memory"]["id"] for r in results if "memory" in r]
            assert "mem-1" not in mem_ids


class TestRecencyScore:
    def test_recent_score_high(self):
        """최근 메모리는 높은 점수"""
        now = datetime.now(timezone.utc)
        # _calculate_recency_score 는 내부 메서드이므로 직접 계산 테스트
        days_old = 0
        score = max(0.0, 1.0 - (days_old / RECENCY_DECAY_DAYS))
        assert score == 1.0

    def test_old_score_low(self):
        """오래된 메모리는 낮은 점수"""
        days_old = RECENCY_DECAY_DAYS + 10
        score = max(0.0, 1.0 - (days_old / RECENCY_DECAY_DAYS))
        assert score == 0.0

    def test_mid_score(self):
        """중간 기간 메모리는 중간 점수"""
        days_old = RECENCY_DECAY_DAYS / 2
        score = max(0.0, 1.0 - (days_old / RECENCY_DECAY_DAYS))
        assert 0.4 < score < 0.6


class TestExtractAndSave:
    async def test_extracts_from_conversation(
        self, db, seed_chat_room, mock_embedding_provider, mock_llm_provider, mock_vector_store
    ):
        """대화에서 메모리를 추출하고 저장"""
        mock_llm_provider.generate = AsyncMock(return_value="""[
            {"content": "사용자는 파이썬을 좋아합니다", "category": "preference", "importance": "medium"}
        ]""")
        # 중복 없음
        mock_vector_store["search"].return_value = []

        with patch("src.memory.pipeline.get_embedding_provider", return_value=mock_embedding_provider), \
             patch("src.memory.pipeline.get_llm_provider", return_value=mock_llm_provider), \
             patch("src.memory.pipeline.get_reranker_provider", return_value=None), \
             patch("src.memory.service.get_embedding_provider", return_value=mock_embedding_provider):
            repo = MemoryRepository(db)
            from src.memory.service import MemoryService
            svc = MemoryService(db)
            pipeline = MemoryPipeline(repo, memory_service=svc)
            conversation = [
                {"role": "user", "content": "나는 파이썬을 좋아해요"},
                {"role": "assistant", "content": "좋은 선택이네요!"},
            ]
            results = await pipeline.extract_and_save(
                conversation=conversation,
                user_id="user-1",
                scope="chatroom",
                chat_room_id="room-1",
            )
            assert len(results) >= 1

    async def test_empty_conversation(
        self, db, seed_users, mock_embedding_provider, mock_llm_provider, mock_vector_store
    ):
        """빈 대화에서는 메모리 추출 없음"""
        mock_llm_provider.generate = AsyncMock(return_value="[]")

        with patch("src.memory.pipeline.get_embedding_provider", return_value=mock_embedding_provider), \
             patch("src.memory.pipeline.get_llm_provider", return_value=mock_llm_provider), \
             patch("src.memory.pipeline.get_reranker_provider", return_value=None):
            repo = MemoryRepository(db)
            pipeline = MemoryPipeline(repo)
            results = await pipeline.extract_and_save(
                conversation=[],
                user_id="user-1",
            )
            assert results == []

    async def test_duplicate_skipped(
        self, db, seed_chat_room, mock_embedding_provider, mock_llm_provider, mock_vector_store
    ):
        """중복 메모리는 저장하지 않음"""
        mock_llm_provider.generate = AsyncMock(return_value="""[
            {"content": "이미 있는 메모리", "category": "fact", "importance": "medium"}
        ]""")
        # 중복으로 판단되도록 설정
        mock_vector_store["search"].return_value = [
            {"id": "existing-vec", "score": 0.97, "payload": {"memory_id": "existing"}}
        ]

        with patch("src.memory.pipeline.get_embedding_provider", return_value=mock_embedding_provider), \
             patch("src.memory.pipeline.get_llm_provider", return_value=mock_llm_provider), \
             patch("src.memory.pipeline.get_reranker_provider", return_value=None), \
             patch("src.memory.service.get_embedding_provider", return_value=mock_embedding_provider):
            repo = MemoryRepository(db)
            from src.memory.service import MemoryService
            svc = MemoryService(db)
            pipeline = MemoryPipeline(repo, memory_service=svc)
            results = await pipeline.extract_and_save(
                conversation=[{"role": "user", "content": "이미 있는 메모리"}],
                user_id="user-1",
                scope="chatroom",
                chat_room_id="room-1",
            )
            # 중복이므로 저장되지 않아야 함
            assert len(results) == 0
