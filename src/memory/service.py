"""Memory Service - 비즈니스 로직"""

import uuid
from typing import Any, Literal

import aiosqlite

from src.config import get_settings
from src.memory.repository import MemoryRepository
from src.user.repository import UserRepository
from src.shared.exceptions import NotFoundException, PermissionDeniedException
from src.shared.vector_store import upsert_vector, search_vectors, delete_vector
from src.shared.providers import get_embedding_provider, get_llm_provider


class MemoryService:
    """메모리 관련 비즈니스 로직"""

    def __init__(self, db: aiosqlite.Connection):
        self.repo = MemoryRepository(db)
        self.user_repo = UserRepository(db)
        self.settings = get_settings()

    async def create_memory(
        self,
        content: str,
        owner_id: str,
        scope: Literal["personal", "chatroom", "agent"] = "personal",
        chat_room_id: str | None = None,
        source_message_id: str | None = None,
        category: str | None = None,
        importance: str = "medium",
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """메모리 생성 (벡터 임베딩 포함)"""
        # 벡터 생성
        embedding_provider = get_embedding_provider()
        vector = await embedding_provider.embed(content)
        vector_id = str(uuid.uuid4())

        # Qdrant에 벡터 저장
        payload = {
            "memory_id": None,  # 아래에서 업데이트
            "scope": scope,
            "owner_id": owner_id,
            "chat_room_id": chat_room_id,
        }

        # SQLite에 메모리 저장
        memory = await self.repo.create_memory(
            content=content,
            owner_id=owner_id,
            scope=scope,
            vector_id=vector_id,
            chat_room_id=chat_room_id,
            source_message_id=source_message_id,
            category=category,
            importance=importance,
            metadata=metadata,
        )

        # Qdrant payload에 memory_id 추가
        payload["memory_id"] = memory["id"]
        await upsert_vector(vector_id, vector, payload)

        return memory

    async def get_memory(
        self,
        memory_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """메모리 조회 (권한 체크 포함)"""
        memory = await self.repo.get_memory(memory_id)
        if not memory:
            raise NotFoundException("메모리", memory_id)

        # 권한 체크
        await self._check_permission(memory, user_id)

        # 접근 로그 기록
        await self.repo.log_memory_access(memory_id, user_id, "read")

        return memory

    async def list_memories(
        self,
        user_id: str,
        scope: str | None = None,
        agent_instance_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """사용자가 접근 가능한 메모리 목록"""
        # 사용자 정보 조회
        user = await self.user_repo.get_user(user_id)
        if not user:
            raise NotFoundException("사용자", user_id)

        all_memories = []

        # 1. 개인 메모리 (scope=personal이고 owner가 나인 것)
        if scope is None or scope == "personal":
            personal = await self.repo.list_memories(
                owner_id=user_id,
                scope="personal",
                agent_instance_id=agent_instance_id,
                limit=limit,
            )
            all_memories.extend(personal)

        # 2. 대화방 메모리 (사용자가 참여한 모든 대화방의 메모리)
        if scope is None or scope == "chatroom":
            # 사용자가 참여한 대화방 ID 목록 조회
            cursor = await self.repo.db.execute(
                "SELECT chat_room_id FROM chat_room_members WHERE user_id = ?",
                (user_id,),
            )
            rows = await cursor.fetchall()
            my_room_ids = [row[0] for row in rows]

            for room_id in my_room_ids:
                room_memories = await self.repo.list_memories(
                    scope="chatroom",
                    chat_room_id=room_id,
                    agent_instance_id=agent_instance_id,
                    limit=limit,
                )
                all_memories.extend(room_memories)

        # 3. 에이전트 메모리 (scope=agent이고 owner가 나인 것)
        if scope is None or scope == "agent":
            agent_memories = await self.repo.list_memories(
                owner_id=user_id,
                scope="agent",
                agent_instance_id=agent_instance_id,
                limit=limit,
            )
            all_memories.extend(agent_memories)

        # 중복 제거 및 정렬
        seen = set()
        unique_memories = []
        for m in all_memories:
            if m["id"] not in seen:
                seen.add(m["id"])
                unique_memories.append(m)

        # 최신순 정렬
        unique_memories.sort(key=lambda x: x["created_at"], reverse=True)

        # owner_id → 이름 캐시 (N+1 방지)
        owner_name_cache: dict[str, str] = {}

        # 출처 정보 추가
        memories_with_source = []
        for memory in unique_memories[:limit]:
            source_info = {}

            # 소유자 이름
            owner_id = memory.get("owner_id")
            if owner_id:
                if owner_id not in owner_name_cache:
                    owner = await self.user_repo.get_user(owner_id)
                    owner_name_cache[owner_id] = owner["name"] if owner else "알 수 없음"
                source_info["owner_name"] = owner_name_cache[owner_id]

            if memory["scope"] == "chatroom" and memory.get("chat_room_id"):
                from src.chat.repository import ChatRepository
                chat_repo = ChatRepository(self.repo.db)
                room = await chat_repo.get_chat_room(memory["chat_room_id"])
                if room:
                    source_info["chat_room_name"] = room["name"]

            # Agent Instance 정보 추가
            if memory.get("metadata") and memory["metadata"].get("source") == "agent":
                agent_instance_id = memory["metadata"].get("agent_instance_id")
                if agent_instance_id:
                    from src.agent.repository import AgentRepository
                    agent_repo = AgentRepository(self.repo.db)
                    instance = await agent_repo.get_agent_instance(agent_instance_id)
                    if instance:
                        source_info["agent_instance_name"] = instance["name"]

            memories_with_source.append({
                "memory": memory,
                "source_info": source_info,
            })

        return memories_with_source

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        score_threshold: float | None = None,
        scope: str | None = None,
        agent_instance_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """메모리 시맨틱 검색 (Reranker 적용)"""
        from src.shared.providers import get_reranker_provider

        # 쿼리 임베딩
        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed(query)

        # 필터 조건 구성
        filter_conditions = await self._build_search_filter(user_id, scope)

        # 벡터 검색
        results = await search_vectors(
            query_vector=query_vector,
            limit=limit * 2,  # 필터링 후 결과 부족 대비
            score_threshold=score_threshold,
            filter_conditions=filter_conditions,
        )

        # 배치 메모리 조회 (N+1 해소)
        memory_ids = [r["payload"].get("memory_id") for r in results if r["payload"].get("memory_id")]
        memories_list = await self.repo.get_memories_by_ids(memory_ids) if memory_ids else []
        memories_by_id = {m["id"]: m for m in memories_list}

        # 메모리 정보 조합 + superseded 필터링
        candidates = []
        for result in results:
            memory_id = result["payload"].get("memory_id")
            if not memory_id:
                continue
            memory = memories_by_id.get(memory_id)
            if not memory or memory.get("superseded", False):
                continue

            # agent_instance_id 필터링
            if agent_instance_id:
                if not (memory.get("metadata") and
                        memory["metadata"].get("source") == "agent" and
                        memory["metadata"].get("agent_instance_id") == agent_instance_id):
                    continue

            candidates.append({
                "memory": memory,
                "score": result["score"],
            })

        # Reranker 적용
        reranker = get_reranker_provider()
        if reranker and len(candidates) > 1:
            try:
                documents = [c["memory"]["content"] for c in candidates]
                reranked = await reranker.rerank(
                    query=query,
                    documents=documents,
                    top_n=limit,
                )
                reranked_candidates = []
                for item in reranked:
                    idx = item["index"]
                    if idx < len(candidates):
                        candidate = candidates[idx].copy()
                        candidate["score"] = item["relevance_score"]
                        reranked_candidates.append(candidate)
                candidates = reranked_candidates
            except Exception as e:
                print(f"Reranker 실패, 벡터 점수 사용: {e}")

        # 접근 추적
        accessed_ids = [c["memory"]["id"] for c in candidates[:limit]]
        if accessed_ids:
            try:
                await self.repo.update_access(accessed_ids)
            except Exception:
                pass

        # 출처 정보 추가
        search_results = []
        for c in candidates[:limit]:
            memory = c["memory"]
            source_info = {}
            if memory["scope"] == "chatroom" and memory.get("chat_room_id"):
                from src.chat.repository import ChatRepository
                chat_repo = ChatRepository(self.repo.db)
                room = await chat_repo.get_chat_room(memory["chat_room_id"])
                if room:
                    source_info["chat_room_name"] = room["name"]

            # Agent Instance 정보 추가
            if memory.get("metadata") and memory["metadata"].get("source") == "agent":
                mem_agent_instance_id = memory["metadata"].get("agent_instance_id")
                if mem_agent_instance_id:
                    from src.agent.repository import AgentRepository
                    agent_repo = AgentRepository(self.repo.db)
                    instance = await agent_repo.get_agent_instance(mem_agent_instance_id)
                    if instance:
                        source_info["agent_instance_name"] = instance["name"]

            search_results.append({
                "memory": memory,
                "score": c["score"],
                "source_info": source_info,
            })

        return search_results

    async def update_memory(
        self,
        memory_id: str,
        user_id: str,
        content: str | None = None,
        category: str | None = None,
        importance: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """메모리 수정"""
        memory = await self.repo.get_memory(memory_id)
        if not memory:
            raise NotFoundException("메모리", memory_id)

        # 소유자만 수정 가능
        if memory["owner_id"] != user_id:
            raise PermissionDeniedException("메모리를 수정할 권한이 없습니다")

        # 내용 변경 시 벡터 업데이트
        vector_id = memory.get("vector_id")
        if content and vector_id:
            embedding_provider = get_embedding_provider()
            vector = await embedding_provider.embed(content)
            payload = {
                "memory_id": memory_id,
                "scope": memory["scope"],
                "owner_id": memory["owner_id"],
                "chat_room_id": memory.get("chat_room_id"),
            }
            await upsert_vector(vector_id, vector, payload)

        # DB 업데이트
        updated = await self.repo.update_memory(
            memory_id,
            content=content,
            category=category,
            importance=importance,
            metadata=metadata,
        )

        # 접근 로그
        await self.repo.log_memory_access(memory_id, user_id, "update")

        return updated

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str,
    ) -> bool:
        """메모리 삭제"""
        memory = await self.repo.get_memory(memory_id)
        if not memory:
            raise NotFoundException("메모리", memory_id)

        # 소유자만 삭제 가능
        if memory["owner_id"] != user_id:
            raise PermissionDeniedException("메모리를 삭제할 권한이 없습니다")

        # 벡터 삭제
        vector_id = memory.get("vector_id")
        if vector_id:
            await delete_vector(vector_id)

        # DB 삭제
        await self.repo.log_memory_access(memory_id, user_id, "delete")
        return await self.repo.delete_memory(memory_id)

    async def extract_memories(
        self,
        conversation: list[dict[str, str]],
        owner_id: str,
        scope: Literal["personal", "chatroom"] = "personal",
        chat_room_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 자동 추출"""
        llm_provider = get_llm_provider()

        # LLM으로 메모리 추출
        extracted = await llm_provider.extract_memories(conversation)

        created_memories = []
        for item in extracted:
            content = item.get("content", "")
            if not content or len(content) < self.settings.min_message_length_for_extraction:
                continue

            # 중복 체크
            is_duplicate = await self._check_duplicate(content, owner_id)
            if is_duplicate:
                continue

            # 메모리 생성
            memory = await self.create_memory(
                content=content,
                owner_id=owner_id,
                scope=scope,
                chat_room_id=chat_room_id,
                category=item.get("category"),
                importance=item.get("importance", "medium"),
            )
            created_memories.append(memory)

        return created_memories

    async def _check_permission(
        self,
        memory: dict[str, Any],
        user_id: str,
    ) -> bool:
        """메모리 접근 권한 체크"""
        scope = memory["scope"]

        # 개인 메모리: 소유자만
        if scope == "personal":
            if memory["owner_id"] != user_id:
                raise PermissionDeniedException()
            return True

        # 대화방 메모리: 소유자 또는 대화방 멤버
        if scope == "chatroom":
            if memory["owner_id"] == user_id:
                return True
            # 대화방 멤버인지 확인
            chat_room_id = memory.get("chat_room_id")
            if chat_room_id:
                cursor = await self.repo.db.execute(
                    "SELECT 1 FROM chat_room_members WHERE chat_room_id = ? AND user_id = ?",
                    (chat_room_id, user_id),
                )
                if await cursor.fetchone():
                    return True
            raise PermissionDeniedException()

        # 에이전트 메모리: 소유자만
        if scope == "agent":
            if memory["owner_id"] != user_id:
                raise PermissionDeniedException()
            return True

        return True

    async def _build_search_filter(
        self,
        user_id: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """검색 필터 조건 구성

        scope가 지정된 경우:
          - personal/agent: owner_id로 필터
          - chatroom: 사용자가 멤버인 대화방의 chat_room_id로 필터
        scope가 None (전체 검색):
          - personal/agent memories owned by user OR chatroom memories from joined rooms
          - Qdrant "should" (OR) 조건 사용
        """
        if scope and scope != "all":
            if scope == "chatroom":
                # 사용자가 참여한 대화방 ID 목록
                cursor = await self.repo.db.execute(
                    "SELECT chat_room_id FROM chat_room_members WHERE user_id = ?",
                    (user_id,),
                )
                rows = await cursor.fetchall()
                room_ids = [row[0] for row in rows]
                if room_ids:
                    return {
                        "should": [
                            {"key": "chat_room_id", "match": {"any": room_ids}},
                        ],
                        "must": [
                            {"key": "scope", "match": {"value": "chatroom"}},
                        ],
                    }
                else:
                    # 참여 대화방 없음 — 매칭 불가 조건
                    return {"scope": "chatroom", "owner_id": user_id}
            else:
                return {"owner_id": user_id, "scope": scope}

        # scope가 None: 전체 검색 (personal + chatroom + agent)
        # 사용자가 참여한 대화방 ID 목록
        cursor = await self.repo.db.execute(
            "SELECT chat_room_id FROM chat_room_members WHERE user_id = ?",
            (user_id,),
        )
        rows = await cursor.fetchall()
        room_ids = [row[0] for row in rows]

        # OR 조건: 내 메모리 OR 내가 속한 대화방 메모리
        should_conditions = [
            {"key": "owner_id", "match": {"value": user_id}},
        ]
        if room_ids:
            should_conditions.append(
                {"key": "chat_room_id", "match": {"any": room_ids}},
            )

        return {"should": should_conditions}

    async def _check_duplicate(
        self,
        content: str,
        owner_id: str,
    ) -> bool:
        """중복 메모리 체크"""
        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed(content)

        results = await search_vectors(
            query_vector=query_vector,
            limit=5,
            score_threshold=self.settings.duplicate_threshold,
            filter_conditions={"owner_id": owner_id},
        )

        return len(results) > 0
