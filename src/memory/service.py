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
        scope: Literal["personal", "project", "department", "chatroom"] = "personal",
        project_id: str | None = None,
        department_id: str | None = None,
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
            "project_id": project_id,
            "department_id": department_id,
        }

        # SQLite에 메모리 저장
        memory = await self.repo.create_memory(
            content=content,
            owner_id=owner_id,
            scope=scope,
            vector_id=vector_id,
            project_id=project_id,
            department_id=department_id,
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
        project_id: str | None = None,
        department_id: str | None = None,
        chat_room_id: str | None = None,
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
                limit=limit,
            )
            all_memories.extend(personal)

        # 2. 대화방 메모리 (scope=chatroom 또는 chat_room_id가 있는 것 중 owner가 나인 것)
        if scope is None or scope == "chatroom":
            chatroom_memories = await self.repo.list_memories(
                owner_id=user_id,
                scope="chatroom",
                limit=limit,
            )
            all_memories.extend(chatroom_memories)

        # 3. 프로젝트 메모리 (멤버인 프로젝트)
        if scope is None or scope == "project":
            user_projects = await self.user_repo.get_user_projects(user_id)
            for project in user_projects:
                if project_id and project["id"] != project_id:
                    continue
                project_memories = await self.repo.list_memories(
                    scope="project",
                    project_id=project["id"],
                    limit=limit,
                )
                all_memories.extend(project_memories)

        # 4. 부서 메모리
        if scope is None or scope == "department":
            user_dept_id = user.get("department_id")
            if user_dept_id:
                if department_id is None or department_id == user_dept_id:
                    dept_memories = await self.repo.list_memories(
                        scope="department",
                        department_id=user_dept_id,
                        limit=limit,
                    )
                    all_memories.extend(dept_memories)

        # 중복 제거 및 정렬
        seen = set()
        unique_memories = []
        for m in all_memories:
            if m["id"] not in seen:
                seen.add(m["id"])
                unique_memories.append(m)

        # 최신순 정렬
        unique_memories.sort(key=lambda x: x["created_at"], reverse=True)

        return unique_memories[:limit]

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        score_threshold: float | None = None,
        scope: str | None = None,
        project_id: str | None = None,
        department_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """메모리 시맨틱 검색"""
        # 쿼리 임베딩
        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed(query)

        # 필터 조건 구성
        filter_conditions = await self._build_search_filter(
            user_id, scope, project_id, department_id
        )

        # 벡터 검색
        results = await search_vectors(
            query_vector=query_vector,
            limit=limit * 2,  # 필터링 후 결과 부족 대비
            score_threshold=score_threshold,
            filter_conditions=filter_conditions,
        )

        # 메모리 정보 조회
        search_results = []
        for result in results:
            memory_id = result["payload"].get("memory_id")
            if memory_id:
                memory = await self.repo.get_memory(memory_id)
                if memory:
                    # 출처 정보 조회
                    source_info = {}
                    if memory["scope"] == "chatroom" and memory.get("chat_room_id"):
                        from src.chat.repository import ChatRepository
                        chat_repo = ChatRepository(self.repo.db)
                        room = await chat_repo.get_chat_room(memory["chat_room_id"])
                        if room:
                            source_info["chat_room_name"] = room["name"]
                    elif memory["scope"] == "project" and memory.get("project_id"):
                        from src.user.repository import UserRepository
                        user_repo = UserRepository(self.repo.db)
                        project = await user_repo.get_project(memory["project_id"])
                        if project:
                            source_info["project_name"] = project["name"]
                    
                    search_results.append({
                        "memory": memory,
                        "score": result["score"],
                        "source_info": source_info,
                    })

        return search_results[:limit]

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
                "project_id": memory.get("project_id"),
                "department_id": memory.get("department_id"),
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
        scope: Literal["personal", "project", "department"] = "personal",
        project_id: str | None = None,
        department_id: str | None = None,
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
                project_id=project_id,
                department_id=department_id,
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

        # 대화방 메모리: 소유자만
        if scope == "chatroom":
            if memory["owner_id"] != user_id:
                raise PermissionDeniedException()
            return True

        # 프로젝트 메모리: 프로젝트 멤버만
        if scope == "project":
            project_id = memory.get("project_id")
            if project_id:
                is_member = await self.user_repo.is_project_member(project_id, user_id)
                if not is_member:
                    raise PermissionDeniedException()
            return True

        # 부서 메모리: 같은 부서원만
        if scope == "department":
            user = await self.user_repo.get_user(user_id)
            if not user:
                raise PermissionDeniedException()
            if user.get("department_id") != memory.get("department_id"):
                raise PermissionDeniedException()
            return True

        return True

    async def _build_search_filter(
        self,
        user_id: str,
        scope: str | None = None,
        project_id: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """검색 필터 조건 구성"""
        user = await self.user_repo.get_user(user_id)

        # 접근 가능한 scope 목록 구성
        allowed_conditions = []

        # 개인 메모리
        if scope is None or scope in ("personal", "all"):
            allowed_conditions.append(("owner_id", user_id))

        # 프로젝트 메모리
        if scope is None or scope in ("project", "all"):
            user_projects = await self.user_repo.get_user_projects(user_id)
            project_ids = [p["id"] for p in user_projects]
            if project_id and project_id in project_ids:
                project_ids = [project_id]
            if project_ids:
                allowed_conditions.append(("project_id", project_ids))

        # 부서 메모리
        if scope is None or scope in ("department", "all"):
            user_dept_id = user.get("department_id") if user else None
            if user_dept_id:
                if department_id is None or department_id == user_dept_id:
                    allowed_conditions.append(("department_id", user_dept_id))

        # 필터 반환 (간소화된 버전)
        filter_dict = {}
        if scope and scope != "all":
            filter_dict["scope"] = scope

        return filter_dict

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
