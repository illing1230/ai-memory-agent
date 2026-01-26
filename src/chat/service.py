"""Chat Room Service"""

import re
from typing import Any, Literal

import aiosqlite

from src.chat.repository import ChatRepository
from src.memory.repository import MemoryRepository
from src.user.repository import UserRepository
from src.shared.exceptions import NotFoundException
from src.shared.vector_store import search_vectors
from src.shared.providers import get_embedding_provider, get_llm_provider
from src.config import get_settings


# AI 시스템 사용자 ID (고정)
AI_USER_ID = "ai-assistant"
AI_USER_NAME = "AI Assistant"


class ChatService:
    """채팅방 관련 비즈니스 로직"""

    def __init__(self, db: aiosqlite.Connection):
        self.repo = ChatRepository(db)
        self.memory_repo = MemoryRepository(db)
        self.user_repo = UserRepository(db)
        self.settings = get_settings()

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
        # 기본 context_sources 설정
        if context_sources is None:
            context_sources = {
                "memory": {
                    "personal": True,
                    "projects": [],
                    "departments": []
                },
                "rag": {
                    "collections": [],
                    "filters": {}
                }
            }
        
        return await self.repo.create_chat_room(
            name=name,
            owner_id=owner_id,
            room_type=room_type,
            project_id=project_id,
            department_id=department_id,
            context_sources=context_sources,
        )

    async def get_chat_room(self, room_id: str) -> dict[str, Any]:
        """채팅방 조회"""
        room = await self.repo.get_chat_room(room_id)
        if not room:
            raise NotFoundException("채팅방", room_id)
        return room

    async def list_chat_rooms(
        self,
        owner_id: str | None = None,
        room_type: str | None = None,
        project_id: str | None = None,
        department_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """채팅방 목록"""
        return await self.repo.list_chat_rooms(
            owner_id=owner_id,
            room_type=room_type,
            project_id=project_id,
            department_id=department_id,
        )

    async def update_chat_room(
        self,
        room_id: str,
        name: str | None = None,
        context_sources: dict | None = None,
    ) -> dict[str, Any]:
        """채팅방 수정"""
        await self.get_chat_room(room_id)
        return await self.repo.update_chat_room(room_id, name, context_sources)

    async def delete_chat_room(self, room_id: str) -> bool:
        """채팅방 삭제"""
        await self.get_chat_room(room_id)
        return await self.repo.delete_chat_room(room_id)

    # ==================== Chat Messages ====================

    async def send_message(
        self,
        chat_room_id: str,
        user_id: str,
        content: str,
    ) -> dict[str, Any]:
        """메시지 전송 (AI 멘션 감지 포함)"""
        # 채팅방 확인
        room = await self.get_chat_room(chat_room_id)
        
        # 멘션 파싱
        mentions = self._parse_mentions(content)
        
        # 사용자 메시지 저장
        user_message = await self.repo.create_message(
            chat_room_id=chat_room_id,
            user_id=user_id,
            content=content,
            role="user",
            mentions=mentions,
        )
        
        result = {
            "user_message": user_message,
            "assistant_message": None,
            "extracted_memories": [],
        }
        
        # @ai 멘션이 있으면 AI 응답 생성
        if "ai" in mentions:
            ai_response = await self._generate_ai_response(
                room=room,
                user_id=user_id,
                user_message=content,
            )
            
            # AI 메시지 저장
            assistant_message = await self.repo.create_message(
                chat_room_id=chat_room_id,
                user_id=AI_USER_ID,
                content=ai_response["response"],
                role="assistant",
            )
            result["assistant_message"] = assistant_message
            
            # 메모리 추출
            if ai_response.get("extracted_memories"):
                result["extracted_memories"] = ai_response["extracted_memories"]
        
        return result

    async def get_messages(
        self,
        chat_room_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """채팅방 메시지 목록"""
        await self.get_chat_room(chat_room_id)
        return await self.repo.list_messages(chat_room_id, limit, offset)

    # ==================== AI Response ====================

    async def _generate_ai_response(
        self,
        room: dict[str, Any],
        user_id: str,
        user_message: str,
    ) -> dict[str, Any]:
        """AI 응답 생성"""
        # 1. 최근 대화 컨텍스트 가져오기
        recent_messages = await self.repo.get_recent_messages(room["id"], limit=10)
        
        # 2. 관련 메모리 검색
        relevant_memories = await self._search_relevant_memories(
            query=user_message,
            user_id=user_id,
            context_sources=room.get("context_sources", {}),
        )
        
        # 3. 프롬프트 구성
        system_prompt = self._build_system_prompt(relevant_memories)
        conversation = self._build_conversation(recent_messages)
        
        # 4. LLM 호출
        llm_provider = get_llm_provider()
        response = await llm_provider.generate(
            prompt=user_message,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1000,
        )
        
        # 5. 메모리 추출 (대화에서)
        extracted_memories = await self._extract_and_save_memories(
            conversation=recent_messages + [{"role": "user", "content": user_message}],
            room=room,
            user_id=user_id,
        )
        
        return {
            "response": response,
            "extracted_memories": extracted_memories,
        }

    async def _search_relevant_memories(
        self,
        query: str,
        user_id: str,
        context_sources: dict,
    ) -> list[dict[str, Any]]:
        """컨텍스트 소스 기반 메모리 검색"""
        memory_config = context_sources.get("memory", {})
        
        # 임베딩 생성
        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed(query)
        
        all_memories = []
        
        # 개인 메모리
        if memory_config.get("personal", False):
            results = await search_vectors(
                query_vector=query_vector,
                limit=5,
                filter_conditions={"owner_id": user_id, "scope": "personal"},
            )
            for r in results:
                memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                if memory:
                    all_memories.append({"memory": memory, "score": r["score"]})
        
        # 프로젝트 메모리
        for project_id in memory_config.get("projects", []):
            results = await search_vectors(
                query_vector=query_vector,
                limit=3,
                filter_conditions={"project_id": project_id, "scope": "project"},
            )
            for r in results:
                memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                if memory:
                    all_memories.append({"memory": memory, "score": r["score"]})
        
        # 부서 메모리
        for dept_id in memory_config.get("departments", []):
            results = await search_vectors(
                query_vector=query_vector,
                limit=3,
                filter_conditions={"department_id": dept_id, "scope": "department"},
            )
            for r in results:
                memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                if memory:
                    all_memories.append({"memory": memory, "score": r["score"]})
        
        # 점수순 정렬 및 중복 제거
        seen = set()
        unique_memories = []
        for m in sorted(all_memories, key=lambda x: x["score"], reverse=True):
            if m["memory"]["id"] not in seen:
                seen.add(m["memory"]["id"])
                unique_memories.append(m)
        
        return unique_memories[:10]

    def _build_system_prompt(self, memories: list[dict[str, Any]]) -> str:
        """시스템 프롬프트 구성"""
        base_prompt = """당신은 팀의 AI 어시스턴트입니다. 
사용자들의 질문에 친절하고 정확하게 답변하세요.
아래는 관련된 메모리(기억)입니다. 답변 시 참고하세요."""
        
        if memories:
            memory_text = "\n\n[관련 메모리]\n"
            for i, m in enumerate(memories, 1):
                mem = m["memory"]
                memory_text += f"{i}. {mem['content']} (유사도: {m['score']:.2f})\n"
            base_prompt += memory_text
        
        return base_prompt

    def _build_conversation(self, messages: list[dict[str, Any]]) -> str:
        """대화 컨텍스트 구성"""
        conv_text = ""
        for msg in messages:
            role = msg.get("role", "user")
            name = msg.get("user_name", "Unknown")
            content = msg.get("content", "")
            
            if role == "assistant":
                conv_text += f"Assistant: {content}\n"
            else:
                conv_text += f"{name}: {content}\n"
        
        return conv_text

    async def _extract_and_save_memories(
        self,
        conversation: list[dict[str, Any]],
        room: dict[str, Any],
        user_id: str,
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출 및 저장"""
        llm_provider = get_llm_provider()
        
        # 대화 형식 맞추기
        conv_for_extraction = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in conversation
        ]
        
        # 메모리 추출
        extracted = await llm_provider.extract_memories(conv_for_extraction)
        
        saved_memories = []
        for item in extracted:
            content = item.get("content", "")
            if not content or len(content) < self.settings.min_message_length_for_extraction:
                continue
            
            # 메모리 저장 (room의 context_sources 기반으로 scope 결정)
            # 기본은 personal
            scope = "personal"
            project_id = None
            department_id = None
            
            # 채팅방 타입에 따라 scope 결정
            if room.get("room_type") == "project" and room.get("project_id"):
                scope = "project"
                project_id = room["project_id"]
            elif room.get("room_type") == "department" and room.get("department_id"):
                scope = "department"
                department_id = room["department_id"]
            
            # 중복 체크는 일단 스킵 (간소화)
            import uuid
            from src.shared.vector_store import upsert_vector
            
            embedding_provider = get_embedding_provider()
            vector = await embedding_provider.embed(content)
            vector_id = str(uuid.uuid4())
            
            memory = await self.memory_repo.create_memory(
                content=content,
                owner_id=user_id,
                scope=scope,
                vector_id=vector_id,
                project_id=project_id,
                department_id=department_id,
                chat_room_id=room["id"],
                category=item.get("category"),
                importance=item.get("importance", "medium"),
            )
            
            # 벡터 저장
            payload = {
                "memory_id": memory["id"],
                "scope": scope,
                "owner_id": user_id,
                "project_id": project_id,
                "department_id": department_id,
            }
            await upsert_vector(vector_id, vector, payload)
            
            saved_memories.append(memory)
        
        return saved_memories

    def _parse_mentions(self, content: str) -> list[str]:
        """멘션 파싱 (@ai, @user 등)"""
        pattern = r"@(\w+)"
        matches = re.findall(pattern, content.lower())
        return list(set(matches))
