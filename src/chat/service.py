"""Chat Room Service"""

import re
from typing import Any, Literal
from datetime import datetime, timedelta, timezone

import aiosqlite

from src.chat.repository import ChatRepository
from src.memory.repository import MemoryRepository
from src.memory.pipeline import MemoryPipeline
from src.memory.entity_repository import EntityRepository
from src.user.repository import UserRepository
from src.document.repository import DocumentRepository
from src.shared.exceptions import NotFoundException, ForbiddenException
from src.shared.vector_store import search_vectors, upsert_vector
from src.shared.providers import get_embedding_provider, get_llm_provider, get_reranker_provider
from src.config import get_settings
import uuid


# AI 시스템 사용자 ID (고정)
AI_USER_ID = "ai-assistant"
AI_USER_NAME = "AI Assistant"

# 슬래시 커맨드 패턴
COMMAND_PATTERN = r"^/(\w+)\s*(.*)"


class ChatService:
    """대화방 관련 비즈니스 로직"""

    # room_id → pending asyncio.Task (debounce 타이머)
    _extraction_timers: dict[str, "asyncio.Task"] = {}
    EXTRACTION_DEBOUNCE_SEC: float = 5.0

    def __init__(self, db: aiosqlite.Connection):
        self.repo = ChatRepository(db)
        self.memory_repo = MemoryRepository(db)
        self.user_repo = UserRepository(db)
        self.document_repo = DocumentRepository(db)
        self.entity_repo = EntityRepository(db)
        self.settings = get_settings()
        self.memory_pipeline = MemoryPipeline(memory_repo=self.memory_repo)

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
        """대화방 생성 + 생성자를 owner로 추가 + 프로젝트/부서 멤버 자동 초대"""
        # 기본 context_sources 설정 (새 구조)
        if context_sources is None:
            context_sources = {
                "memory": {
                    "include_this_room": True,
                    "other_chat_rooms": [],
                },
                "rag": {
                    "collections": [],
                    "filters": {}
                }
            }
        
        # 대화방 생성
        room = await self.repo.create_chat_room(
            name=name,
            owner_id=owner_id,
            room_type=room_type,
            project_id=project_id,
            department_id=department_id,
            context_sources=context_sources,
        )
        
        # 생성자를 owner로 추가
        await self.repo.add_member(room["id"], owner_id, "owner")
        
        # 프로젝트 타입: 프로젝트 멤버 자동 초대
        if room_type == "project" and project_id:
            project_members = await self.repo.get_project_members(project_id)
            for member in project_members:
                user_id = member.get("user_id")
                # owner는 이미 추가되었으므로 제외
                if user_id and user_id != owner_id:
                    try:
                        await self.repo.add_member(room["id"], user_id, "member")
                        print(f"프로젝트 멤버 자동 초대: {user_id}")
                    except Exception as e:
                        print(f"프로젝트 멤버 초대 실패 ({user_id}): {e}")
        
        # 부서 타입: 부서 멤버 자동 초대
        if room_type == "department" and department_id:
            department_members = await self.repo.get_department_members(department_id)
            for member in department_members:
                user_id = member.get("user_id")
                # owner는 이미 추가되었으므로 제외
                if user_id and user_id != owner_id:
                    try:
                        await self.repo.add_member(room["id"], user_id, "member")
                        print(f"부서 멤버 자동 초대: {user_id}")
                    except Exception as e:
                        print(f"부서 멤버 초대 실패 ({user_id}): {e}")
        
        return room

    async def get_chat_room(self, room_id: str) -> dict[str, Any]:
        """대화방 조회"""
        room = await self.repo.get_chat_room(room_id)
        if not room:
            raise NotFoundException("대화방", room_id)
        return room

    async def list_chat_rooms(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """사용자가 속한 대화방 목록"""
        return await self.repo.get_user_rooms(user_id)

    async def update_chat_room(
        self,
        room_id: str,
        user_id: str,
        name: str | None = None,
        context_sources: dict | None = None,
    ) -> dict[str, Any]:
        """대화방 수정 (owner/admin만 가능)"""
        await self._check_admin_permission(room_id, user_id)
        
        # 변경 전 상태 확인
        old_room = await self.repo.get_chat_room(room_id)
        old_context_sources = old_room.get("context_sources", {})
        
        # 대화방 업데이트
        updated_room = await self.repo.update_chat_room(room_id, name, context_sources)
        
        # 컨텍스트 소스가 변경된 경우 시스템 메시지 전송
        if context_sources and context_sources != old_context_sources:
            await self._send_context_sources_update_message(
                room_id=room_id,
                old_context_sources=old_context_sources,
                new_context_sources=context_sources,
                user_id=user_id,
            )
        
        return updated_room

    async def _send_context_sources_update_message(
        self,
        room_id: str,
        old_context_sources: dict,
        new_context_sources: dict,
        user_id: str,
    ) -> None:
        """컨텍스트 소스 변경 알림 메시지 전송"""
        try:
            old_memory = old_context_sources.get("memory", {})
            new_memory = new_context_sources.get("memory", {})
            
            changes = []
            
            # include_this_room 변경 확인
            if old_memory.get("include_this_room") != new_memory.get("include_this_room"):
                old_val = "사용" if old_memory.get("include_this_room") else "사용 안 함"
                new_val = "사용" if new_memory.get("include_this_room") else "사용 안 함"
                changes.append(f"• 이 대화방 메모리: {old_val} → {new_val}")
            
            # other_chat_rooms 변경 확인
            old_rooms = set(old_memory.get("other_chat_rooms", []))
            new_rooms = set(new_memory.get("other_chat_rooms", []))
            if old_rooms != new_rooms:
                added = new_rooms - old_rooms
                removed = old_rooms - new_rooms
                if added:
                    changes.append(f"• 추가된 대화방: {len(added)}개")
                if removed:
                    changes.append(f"• 제거된 대화방: {len(removed)}개")
            
            if changes:
                message = f"🔧 **컨텍스트 소스 설정이 변경되었습니다**\n\n"
                message += "\n".join(changes)
                message += "\n\n이제 AI가 새로운 설정에 따라 메모리를 검색합니다."
                
                # 시스템 메시지로 전송
                await self.repo.create_message(
                    chat_room_id=room_id,
                    user_id=AI_USER_ID,
                    content=message,
                    role="assistant",
                )
                
                print(f"컨텍스트 소스 변경 알림 전송: {room_id}")
        except Exception as e:
            print(f"컨텍스트 소스 변경 알림 전송 실패: {e}")

    async def delete_chat_room(self, room_id: str, user_id: str) -> bool:
        """대화방 삭제 (owner만 가능)"""
        await self._check_owner_permission(room_id, user_id)
        
        # Vector DB에서 대화방 메모리 삭제
        try:
            from src.shared.vector_store import delete_vectors_by_filter
            await delete_vectors_by_filter({"chat_room_id": room_id})
            print(f"대화방 {room_id}의 Vector DB 데이터 삭제 완료")
        except Exception as e:
            print(f"Vector DB 삭제 실패: {e}")
        
        return await self.repo.delete_chat_room(room_id)

    # ==================== Chat Room Members ====================

    async def add_member(
        self,
        room_id: str,
        user_id: str,
        target_user_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        """멤버 추가 (owner/admin만 가능)"""
        await self._check_admin_permission(room_id, user_id)
        
        if await self.repo.is_member(room_id, target_user_id):
            raise ForbiddenException("이미 대화방 멤버입니다")
        
        return await self.repo.add_member(room_id, target_user_id, role)

    async def list_members(self, room_id: str, user_id: str) -> list[dict[str, Any]]:
        """멤버 목록 (멤버만 조회 가능)"""
        await self._check_member_permission(room_id, user_id)
        return await self.repo.list_members(room_id)

    async def update_member_role(
        self,
        room_id: str,
        user_id: str,
        target_user_id: str,
        role: str,
    ) -> dict[str, Any]:
        """멤버 역할 변경 (owner만 가능)"""
        await self._check_owner_permission(room_id, user_id)
        
        if role == "owner":
            raise ForbiddenException("owner 역할은 부여할 수 없습니다")
        
        member = await self.repo.get_member(room_id, target_user_id)
        if not member:
            raise NotFoundException("대화방 멤버", target_user_id)
        
        if member["role"] == "owner":
            raise ForbiddenException("owner의 역할은 변경할 수 없습니다")
        
        return await self.repo.update_member_role(room_id, target_user_id, role)

    async def remove_member(
        self,
        room_id: str,
        user_id: str,
        target_user_id: str,
    ) -> bool:
        """멤버 제거"""
        member = await self.repo.get_member(room_id, user_id)
        if not member:
            raise ForbiddenException("대화방 멤버가 아닙니다")
        
        if user_id == target_user_id:
            if member["role"] == "owner":
                raise ForbiddenException("owner는 대화방을 나갈 수 없습니다")
            return await self.repo.remove_member(room_id, target_user_id)
        
        if member["role"] not in ["owner", "admin"]:
            raise ForbiddenException("멤버를 제거할 권한이 없습니다")
        
        target_member = await self.repo.get_member(room_id, target_user_id)
        if not target_member:
            raise NotFoundException("대화방 멤버", target_user_id)
        
        if target_member["role"] == "owner":
            raise ForbiddenException("owner는 강퇴할 수 없습니다")
        
        if member["role"] == "admin" and target_member["role"] == "admin":
            raise ForbiddenException("admin은 다른 admin을 강퇴할 수 없습니다")
        
        return await self.repo.remove_member(room_id, target_user_id)

    # ==================== Permission Check ====================

    async def _check_member_permission(self, room_id: str, user_id: str) -> dict[str, Any]:
        """멤버 권한 체크"""
        member = await self.repo.get_member(room_id, user_id)
        if not member:
            raise ForbiddenException("대화방 멤버가 아닙니다")
        return member

    async def _check_admin_permission(self, room_id: str, user_id: str) -> dict[str, Any]:
        """admin 이상 권한 체크"""
        member = await self._check_member_permission(room_id, user_id)
        if member["role"] not in ["owner", "admin"]:
            raise ForbiddenException("관리자 권한이 필요합니다")
        return member

    async def _check_owner_permission(self, room_id: str, user_id: str) -> dict[str, Any]:
        """owner 권한 체크"""
        member = await self._check_member_permission(room_id, user_id)
        if member["role"] != "owner":
            raise ForbiddenException("소유자 권한이 필요합니다")
        return member

    # ==================== Chat Messages ====================

    async def send_message(
        self,
        chat_room_id: str,
        user_id: str,
        content: str,
    ) -> dict[str, Any]:
        """메시지 전송 (멤버만 가능)"""
        room = await self.get_chat_room(chat_room_id)
        await self._check_member_permission(chat_room_id, user_id)
        
        command_match = re.match(COMMAND_PATTERN, content.strip())
        if command_match:
            command = command_match.group(1).lower()
            args = command_match.group(2).strip()
            return await self._handle_command(room, user_id, command, args, content)
        
        mentions = self._parse_mentions(content)
        
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
        
        if "ai" in mentions:
            # AI 응답 생성 (비동기) — 내부에서 백그라운드 메모리 추출도 수행
            ai_response = await self._generate_ai_response(
                room=room,
                user_id=user_id,
                user_message=content,
            )

            # AI 응답 저장
            assistant_message = await self.repo.create_message(
                chat_room_id=chat_room_id,
                user_id=AI_USER_ID,
                content=ai_response["response"],
                role="assistant",
                sources=ai_response.get("sources"),
            )
            result["assistant_message"] = assistant_message
        else:
            # @ai 멘션 없는 일반 메시지 → debounce 후 메모리 추출
            if self.settings.auto_extract_memory and len(content) >= self.settings.min_message_length_for_extraction:
                self._schedule_extraction(room=room, user_id=user_id)

        return result

    async def _handle_command(
        self,
        room: dict[str, Any],
        user_id: str,
        command: str,
        args: str,
        original_content: str,
    ) -> dict[str, Any]:
        """슬래시 커맨드 처리"""
        user_message = await self.repo.create_message(
            chat_room_id=room["id"],
            user_id=user_id,
            content=original_content,
            role="user",
        )
        
        result = {
            "user_message": user_message,
            "assistant_message": None,
            "extracted_memories": [],
        }
        
        if command == "remember":
            response, memories = await self._cmd_remember(room, user_id, args)
            result["extracted_memories"] = memories
        elif command == "forget":
            response = await self._cmd_forget(room, user_id, args)
        elif command == "search":
            response = await self._cmd_search(room, user_id, args)
        elif command == "help":
            response = self._cmd_help()
        elif command == "members":
            response = await self._cmd_members(room, user_id)
        elif command == "invite":
            response = await self._cmd_invite(room, user_id, args)
        elif command == "memory":
            response, memories = await self._cmd_memory(room, user_id)
            result["extracted_memories"] = memories
        else:
            response = f"❌ 알 수 없는 커맨드: /{command}\n\n/help 로 확인하세요."
        
        assistant_message = await self.repo.create_message(
            chat_room_id=room["id"],
            user_id=AI_USER_ID,
            content=response,
            role="assistant",
        )
        result["assistant_message"] = assistant_message
        
        return result

    async def _cmd_remember(
        self,
        room: dict[str, Any],
        user_id: str,
        content: str,
    ) -> tuple[str, list[dict]]:
        """/remember - 메모리 저장 (개인 + 대화방) - MemoryPipeline 위임"""
        if not content:
            return "❌ 저장할 내용을 입력하세요.\n\n예: `/remember 김과장은 오전 회의를 선호한다`", []

        try:
            saved_memories, relationship = await self.memory_pipeline.save_manual(
                content=content,
                user_id=user_id,
                room=room,
            )

            response = f"✅ 메모리가 저장되었습니다!\n\n📝 {content}\n\n범위: 개인 + 대화방"

            if relationship == "UPDATE":
                response += f"\n\nℹ️ 기존 메모리가 최신 정보로 업데이트되었습니다."

            return response, saved_memories

        except Exception as e:
            print(f"메모리 저장 실패: {e}")
            return f"❌ 메모리 저장 실패: {str(e)}", []

    async def _cmd_forget(
        self,
        room: dict[str, Any],
        user_id: str,
        query: str,
    ) -> str:
        """/forget - 메모리 삭제"""
        if not query:
            return "❌ 삭제할 메모리 검색어를 입력하세요.\n\n예: `/forget 김과장 회의`"
        
        try:
            embedding_provider = get_embedding_provider()
            query_vector = await embedding_provider.embed(query)
            
            # 이 대화방 메모리에서만 검색
            results = await search_vectors(
                query_vector=query_vector,
                limit=5,
                filter_conditions={"chat_room_id": room["id"]},
            )
            
            if not results:
                return f"🔍 '{query}'와 관련된 메모리를 찾을 수 없습니다."
            
            top_result = results[0]
            memory_id = top_result["payload"].get("memory_id")
            
            if memory_id:
                memory = await self.memory_repo.get_memory(memory_id)
                if memory:
                    await self.memory_repo.delete_memory(memory_id)
                    return f"🗑️ 메모리가 삭제되었습니다.\n\n삭제됨: {memory['content']}"
            
            return "❌ 메모리 삭제에 실패했습니다."
            
        except Exception as e:
            return f"❌ 메모리 삭제 실패: {str(e)}"

    async def _cmd_search(
        self,
        room: dict[str, Any],
        user_id: str,
        query: str,
    ) -> str:
        """/search - 메모리 검색"""
        if not query:
            return "❌ 검색어를 입력하세요.\n\n예: `/search 회의 선호`"

        try:
            context_sources = room.get("context_sources", {})
            memories = await self.memory_pipeline.search(query, user_id, room["id"], context_sources)
            
            if not memories:
                return f"🔍 '{query}'와 관련된 메모리를 찾을 수 없습니다."
            
            response = f"🔍 '{query}' 검색 결과 ({len(memories)}개)\n\n"
            for i, m in enumerate(memories, 1):
                mem = m["memory"]
                score = m["score"]
                scope_label = "이 대화방" if mem["scope"] == "chatroom" else mem["scope"]
                response += f"{i}. {mem['content']}\n   _(유사도: {score:.0%}, 범위: {scope_label})_\n\n"
            
            return response
            
        except Exception as e:
            return f"❌ 메모리 검색 실패: {str(e)}"

    async def _cmd_members(
        self,
        room: dict[str, Any],
        user_id: str,
    ) -> str:
        """/members - 멤버 목록"""
        try:
            members = await self.repo.list_members(room["id"])
            
            if not members:
                return "👥 대화방 멤버가 없습니다."
            
            response = f"👥 대화방 멤버 ({len(members)}명)\n\n"
            role_emoji = {"owner": "👑", "admin": "⭐", "member": "👤"}
            
            for m in members:
                emoji = role_emoji.get(m["role"], "👤")
                name = m.get("user_name", "Unknown")
                response += f"{emoji} {name} ({m['role']})\n"
            
            return response
            
        except Exception as e:
            return f"❌ 멤버 목록 조회 실패: {str(e)}"

    async def _cmd_invite(
        self,
        room: dict[str, Any],
        user_id: str,
        args: str,
    ) -> str:
        """/invite - 멤버 초대"""
        if not args:
            return "❌ 초대할 사용자 이메일을 입력하세요.\n\n예: `/invite kim@samsung.com`"
        
        try:
            member = await self.repo.get_member(room["id"], user_id)
            if not member or member["role"] not in ["owner", "admin"]:
                return "❌ 멤버를 초대할 권한이 없습니다. (owner/admin만 가능)"
            
            email = args.strip()
            target_user = await self.user_repo.get_user_by_email(email)
            
            if not target_user:
                return f"❌ '{email}' 사용자를 찾을 수 없습니다."
            
            if await self.repo.is_member(room["id"], target_user["id"]):
                return f"ℹ️ {target_user['name']}님은 이미 대화방 멤버입니다."
            
            await self.repo.add_member(room["id"], target_user["id"], "member")
            
            return f"✅ {target_user['name']}님을 대화방에 초대했습니다!"
            
        except Exception as e:
            return f"❌ 멤버 초대 실패: {str(e)}"

    def _cmd_help(self) -> str:
        """/help - 도움말"""
        return """📖 **사용 가능한 커맨드**

**메모리 관리**
• `/remember <내용>` - 개인 + 대화방 메모리 저장
• `/memory` - 최근 대화에서 메모리 자동 추출
• `/forget <검색어>` - 메모리 삭제
• `/search <검색어>` - 메모리 검색

**대화방 관리**
• `/members` - 멤버 목록 보기
• `/invite <이메일>` - 멤버 초대 (관리자만)

**AI 호출**
• `@ai <질문>` - AI에게 질문

**기타**
• `/help` - 이 도움말 표시

**맞춤 설정**
메모리 소스 설정에서 개인 메모리, 다른 대화방 메모리를 활성화하면
AI가 해당 메모리들도 참조합니다."""

    async def get_messages(
        self,
        chat_room_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """대화방 메시지 목록 (멤버만)"""
        await self.get_chat_room(chat_room_id)
        await self._check_member_permission(chat_room_id, user_id)
        return await self.repo.list_messages(chat_room_id, limit, offset)

    # ==================== AI Response ====================

    async def _generate_ai_response(
        self,
        room: dict[str, Any],
        user_id: str,
        user_message: str,
    ) -> dict[str, Any]:
        """AI 응답 생성 (우선순위: 대화 > RAG 문서 > 메모리) - 스트리밍 지원"""
        # @ai 멘션 제거 (LLM에 전달할 때 불필요)
        clean_message = re.sub(r"@ai\s*", "", user_message, flags=re.IGNORECASE).strip()

        # Step 1: 최근 대화 (최우선)
        recent_messages = await self.repo.get_recent_messages(room["id"], limit=20)

        # Step 2: RAG 문서 검색 (높은 우선순위)
        document_chunks = await self._search_relevant_documents(
            query=clean_message,
            chat_room_id=room["id"],
            user_id=user_id,
        )

        # Step 3: 메모리 검색 (보조) - MemoryPipeline 위임
        relevant_memories = await self.memory_pipeline.search(
            query=clean_message,
            user_id=user_id,
            current_room_id=room["id"],
            context_sources=room.get("context_sources", {}),
        )
        
        # 사용자 이름 조회
        user_info = await self.user_repo.get_user(user_id)
        user_name = user_info["name"] if user_info else None

        system_prompt = self._build_system_prompt(relevant_memories, document_chunks, user_name=user_name)
        conversation_context = self._build_conversation(recent_messages)
        
        full_prompt = f"""[최근 대화 내용]
{conversation_context}

[현재 질문]
{clean_message}

위 대화 내용을 참고하여 현재 질문에 답변해주세요."""
        
        llm_provider = get_llm_provider()
        
        # 스트리밍 응답 수집
        full_response = ""
        try:
            async for chunk in llm_provider.generate_stream(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000,
            ):
                full_response += chunk
                # WebSocket으로 실시간 전송
                from src.websocket.manager import manager
                await manager.broadcast_to_room(
                    room["id"],
                    {
                        "type": "message:stream",
                        "data": {
                            "chunk": chunk,
                            "user_id": AI_USER_ID,
                            "room_id": room["id"],
                        },
                    },
                )
        except Exception as e:
            import traceback
            print(f"스트리밍 응답 실패: {e}")
            print(f"스트리밍 traceback: {traceback.format_exc()}")
            # 스트리밍 실패 시 일반 generate로 폴백
            full_response = await llm_provider.generate(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000,
            )
        
        # 소스 정보 수집 — 실제 참조된 것만 필터링
        MIN_SCORE = 0.1          # 절대 최소 점수
        RELATIVE_RATIO = 0.4     # 최고 점수 대비 비율

        filtered_memories = []
        if relevant_memories:
            top_score = max(m["score"] for m in relevant_memories)
            threshold = max(MIN_SCORE, top_score * RELATIVE_RATIO)
            filtered_memories = [m for m in relevant_memories if m["score"] >= threshold]

        filtered_documents = []
        if document_chunks:
            top_doc_score = max(d["score"] for d in document_chunks)
            doc_threshold = max(MIN_SCORE, top_doc_score * RELATIVE_RATIO)
            filtered_documents = [d for d in document_chunks if d["score"] >= doc_threshold]

        sources_data = {
            "documents": [
                {
                    "document_id": d["document_id"],
                    "document_name": d["document_name"],
                    "content": d["content"][:200],
                    "score": d["score"],
                    **({"slide_number": d["slide_number"]} if d.get("slide_number") else {}),
                    **({"slide_image_url": d["slide_image_url"]} if d.get("slide_image_url") else {}),
                }
                for d in filtered_documents
            ],
            "memories": [
                {
                    "memory_id": m["memory"]["id"],
                    "content": m["memory"]["content"][:200],
                    "scope": m["memory"]["scope"],
                    "score": m["score"],
                    "source_name": (
                        m.get("source_info", {}).get("chat_room_name")
                        or m.get("source_info", {}).get("agent_instance_name")
                        or "개인"
                    ),
                }
                for m in filtered_memories
            ],
        }

        # 스트리밍 완료 후 sources 전송
        from src.websocket.manager import manager
        await manager.broadcast_to_room(
            room["id"],
            {
                "type": "message:stream_end",
                "data": {
                    "room_id": room["id"],
                    "sources": sources_data,
                },
            },
        )

        # 백그라운드에서 Vector DB 저장과 메모리 추출 처리
        import asyncio
        asyncio.create_task(self._save_ai_response_and_extract_memories(
            full_response=full_response,
            recent_messages=recent_messages,
            user_message=user_message,
            room=room,
            user_id=user_id,
        ))

        return {
            "response": full_response,
            "extracted_memories": [],  # 백그라운드에서 처리되므로 빈 리스트 반환
            "sources": sources_data,
        }

    async def _search_relevant_documents(
        self,
        query: str,
        chat_room_id: str,
        user_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """대화방에 연결된 문서에서 관련 청크 검색 (하이브리드: 벡터 + 키워드 + Reranker)"""
        doc_ids = await self.document_repo.get_linked_document_ids(chat_room_id)
        if not doc_ids:
            return []

        # --- 벡터 검색 ---
        vector_results = []
        try:
            embedding_provider = get_embedding_provider()
            query_vector = await embedding_provider.embed(query)
            vector_results = await search_vectors(
                query_vector=query_vector,
                limit=limit * 3,  # 하이브리드 합산을 위해 더 많이 가져옴
                filter_conditions={
                    "scope": "document",
                    "document_id": doc_ids,
                },
            )
        except Exception as e:
            print(f"문서 벡터 검색 실패: {e}")

        # --- 엔티티 그래프 기반 쿼리 확장 + 키워드 검색 ---
        keyword_results = []
        expanded_query = query
        if user_id:
            try:
                matched = await self.entity_repo.find_entities_by_query(query, user_id)
                entity_ids = [e["id"] for e in matched]
                related_ids = await self.entity_repo.get_related_entity_ids(entity_ids, user_id) if entity_ids else []

                all_entity_ids = list(set(entity_ids + related_ids))
                if all_entity_ids:
                    all_entities = await self.entity_repo.get_entities_by_ids(all_entity_ids)
                    entity_names = [e["name"] for e in all_entities]
                    expanded_query = f"{query} {' '.join(entity_names)}"
                    print(f"문서 검색 쿼리 확장: {query} → {expanded_query}")
            except Exception as e:
                print(f"엔티티 쿼리 확장 실패: {e}")

        try:
            keyword_results = await self.document_repo.search_chunks_by_keyword(
                query=expanded_query, document_ids=doc_ids, limit=limit * 3,
            )
        except Exception as e:
            print(f"문서 키워드 검색 실패: {e}")

        # --- RRF (Reciprocal Rank Fusion) 합산 ---
        def rrf_score(rank: int, k: int = 60) -> float:
            return 1.0 / (k + rank)

        scores: dict[tuple, float] = {}  # (doc_id, chunk_index) → total_score
        chunk_data: dict[tuple, dict] = {}  # (doc_id, chunk_index) → payload/content

        for rank, r in enumerate(vector_results):
            doc_id = r["payload"].get("document_id")
            chunk_idx = r["payload"].get("chunk_index")
            key = (doc_id, chunk_idx)
            scores[key] = scores.get(key, 0) + rrf_score(rank)
            if key not in chunk_data:
                chunk_data[key] = {"source": "vector", "payload": r["payload"], "vector_score": r["score"]}

        for rank, r in enumerate(keyword_results):
            doc_id = r["document_id"]
            # 키워드 결과에서 chunk_index 조회 (FTS에는 chunk_id만 있으므로 DB 조회 필요)
            chunk_idx = r.get("chunk_index")
            key = (doc_id, chunk_idx)
            scores[key] = scores.get(key, 0) + rrf_score(rank)
            if key not in chunk_data:
                chunk_data[key] = {"source": "keyword", "content": r.get("content", ""), "keyword_score": r.get("score", 0)}

        if not scores:
            return []

        # 상위 N개 선택
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:limit * 2]

        # --- Enrichment ---
        enriched = []
        for key in sorted_keys:
            doc_id, chunk_idx = key
            data = chunk_data.get(key, {})

            # 청크 내용 조회
            content = data.get("content", "")
            slide_number = None
            slide_image_url = None
            if not content:
                chunks = await self.document_repo.get_chunks(doc_id)
                for c in chunks:
                    if c["chunk_index"] == chunk_idx:
                        content = c["content"]
                        slide_number = c.get("slide_number")
                        if slide_number:
                            slide_image_url = f"/api/v1/documents/{doc_id}/slides/{slide_number}"
                        break
            else:
                # 키워드 결과에서도 슬라이드 정보 조회
                chunks = await self.document_repo.get_chunks(doc_id)
                for c in chunks:
                    if c["chunk_index"] == chunk_idx:
                        slide_number = c.get("slide_number")
                        if slide_number:
                            slide_image_url = f"/api/v1/documents/{doc_id}/slides/{slide_number}"
                        break

            doc = await self.document_repo.get_document(doc_id)

            enriched.append({
                "content": content,
                "score": scores[key],
                "document_name": doc["name"] if doc else "Unknown",
                "chunk_index": chunk_idx,
                "document_id": doc_id,
                "slide_number": slide_number,
                "slide_image_url": slide_image_url,
            })

        # --- Reranker 적용 ---
        reranker = get_reranker_provider()
        if reranker and len(enriched) > 1:
            try:
                documents = [e["content"] for e in enriched]
                reranked = await reranker.rerank(query=query, documents=documents, top_n=limit)
                reranked_enriched = []
                for item in reranked:
                    idx = item["index"]
                    if idx < len(enriched):
                        entry = enriched[idx].copy()
                        entry["vector_score"] = entry["score"]
                        entry["score"] = item["relevance_score"]
                        reranked_enriched.append(entry)
                enriched = reranked_enriched
                print(f"문서 Reranker 적용: {len(enriched)}개 리랭킹 완료")
            except Exception as e:
                print(f"문서 Reranker 실패, RRF 점수 사용: {e}")
                enriched = enriched[:limit]
        else:
            enriched = enriched[:limit]

        return enriched

    def _build_system_prompt(
        self,
        memories: list[dict[str, Any]],
        document_chunks: list[dict[str, Any]] | None = None,
        user_name: str | None = None,
    ) -> str:
        """시스템 프롬프트 구성 (우선순위: RAG 문서 > 메모리)"""
        # 현재 날짜 (UTC+9)
        current_date = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y년 %m월 %d일")

        base_prompt = f"""당신의 이름은 {AI_USER_NAME}입니다.
당신은 팀의 AI 어시스턴트로서, 사용자들의 질문에 친절하고 정확하게 답변합니다.
반드시 한국어로 답변하세요. 절대로 중국어, 영어 등 다른 언어로 답변하지 마세요.
절대로 자신을 Qwen, LLaMA, GPT 등 다른 AI 모델로 소개하지 마세요.
"너 이름이 뭐야?" 또는 "누구야?"와 같이 당신의 정체를 묻는 질문에는 "{AI_USER_NAME}"라고 답변하세요.

{f'시스템 기본 사용자명: {user_name}' if user_name else ''}
현재 날짜: {current_date}

[핵심 규칙 - 반드시 따르세요]
1. 아래 [저장된 메모리] 섹션의 내용을 최우선으로 사용하세요.
2. "내 이름이 뭐야?" → 메모리에 이름이 있으면 반드시 그 이름을 답하세요. 메모리에 없을 때만 시스템 기본 사용자명을 사용하세요.
3. 사용자의 선호도, 관심사, 개인 정보에 대한 질문 → 메모리 내용 기반으로 답하세요.
4. 여러 메모리에 상반된 정보가 있으면 최신 메모리를 우선 적용하세요.
5. 날짜 관련 질문에는 현재 날짜를 기준으로 답변해주세요."""

        # RAG 문서 (높은 우선순위 - 먼저 배치)
        if document_chunks:
            doc_text = "\n\n[참고 문서 - 업로드된 문서에서 검색된 내용]\n"
            for i, chunk in enumerate(document_chunks, 1):
                doc_name = chunk.get("document_name", "Unknown")
                content = chunk.get("content", "")
                score = chunk.get("score", 0)
                doc_text += f"{i}. [{doc_name}] {content} (유사도: {score:.2f})\n"
            doc_text += "\n위 문서 내용을 우선적으로 참고하여 답변해주세요."
            base_prompt += doc_text

        # 메모리 (보조 - 뒤에 배치)
        if memories:
            memory_text = "\n\n[저장된 메모리 - 참고용]\n"
            for i, m in enumerate(memories, 1):
                mem = m["memory"]
                created_at = mem.get("created_at", "")
                memory_text += f"{i}. {mem['content']} (유사도: {m['score']:.2f}, 생성일: {created_at[:10]})\n"
            base_prompt += memory_text

        return base_prompt

    def _build_conversation(self, messages: list[dict[str, Any]]) -> str:
        """대화 컨텍스트 구성"""
        if not messages:
            return "(이전 대화 없음)"
        
        conv_text = ""
        for msg in messages:
            role = msg.get("role", "user")
            name = msg.get("user_name", "Unknown")
            content = msg.get("content", "")
            
            if role == "assistant":
                conv_text += f"AI: {content}\n"
            else:
                conv_text += f"{name}: {content}\n"
        
        return conv_text.strip()

    async def _cmd_memory(
        self,
        room: dict[str, Any],
        user_id: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """/memory - 최근 대화에서 메모리 추출 - MemoryPipeline 위임"""
        messages = await self.repo.get_recent_messages(room["id"], limit=20)
        if len(messages) < 2:
            return "💬 대화가 부족합니다. 메모리를 추출하려면 최소 2개 이상의 메시지가 필요합니다.", []

        try:
            recent = messages[-10:]
            saved_memories = await self.memory_pipeline.extract_and_save(
                conversation=recent,
                room=room,
                user_id=user_id,
            )

            if not saved_memories:
                return "ℹ️ 추출할 메모리가 없습니다.", []

            lines = [f"🧠 {len(saved_memories)}개의 메모리가 추출되었습니다!\n"]
            for m in saved_memories:
                lines.append(f"• {m['content']}")

            return "\n".join(lines), saved_memories

        except Exception as e:
            print(f"메모리 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ 메모리 추출 실패: {e}", []

    async def _extract_and_save_memories(
        self,
        conversation: list[dict[str, Any]],
        room: dict[str, Any],
        user_id: str,
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출 및 저장 - MemoryPipeline 위임"""
        return await self.memory_pipeline.extract_and_save(
            conversation=conversation,
            room=room,
            user_id=user_id,
        )

    def _parse_mentions(self, content: str) -> list[str]:
        """멘션 파싱"""
        pattern = r"@(\w+)"
        matches = re.findall(pattern, content.lower())
        return list(set(matches))

    async def _save_ai_response_and_extract_memories(
        self,
        full_response: str,
        recent_messages: list[dict[str, Any]],
        user_message: str,
        room: dict[str, Any],
        user_id: str,
    ) -> None:
        """백그라운드에서 사용자 발화 기반 메모리 추출 처리 — 자체 DB 커넥션 사용"""
        from src.shared.database import get_db_sync

        db = None
        try:
            db = await get_db_sync()
            bg_memory_repo = MemoryRepository(db)
            bg_pipeline = MemoryPipeline(memory_repo=bg_memory_repo)

            # 사용자 메시지만 포함하여 메모리 추출
            user_messages_only = [
                msg for msg in recent_messages if msg.get("role") == "user"
            ] + [{"role": "user", "content": user_message}]

            extracted_memories = await bg_pipeline.extract_and_save(
                conversation=user_messages_only,
                room=room,
                user_id=user_id,
            )

            if extracted_memories:
                from src.websocket.manager import manager
                notification = {
                    "type": "memory:extracted",
                    "data": {
                        "count": len(extracted_memories),
                        "memories": extracted_memories,
                        "room_id": room["id"],
                    },
                }
                await manager.broadcast_to_room(room["id"], notification)
                print(f"메모리 추출 알림 전송: {len(extracted_memories)}개")
        except Exception as e:
            print(f"메모리 추출 실패: {e}")
        finally:
            if db:
                await db.close()

    def _schedule_extraction(self, room: dict[str, Any], user_id: str) -> None:
        """debounce 방식으로 메모리 추출 예약 — 연속 메시지는 마지막 메시지 후 N초 뒤 1회만 실행"""
        import asyncio

        room_id = room["id"]

        # 기존 타이머 취소
        existing = ChatService._extraction_timers.get(room_id)
        if existing and not existing.done():
            existing.cancel()
            print(f"[debounce] 기존 타이머 취소: {room_id[:8]}...")

        # 새 타이머 등록
        ChatService._extraction_timers[room_id] = asyncio.create_task(
            self._debounced_extract(room=room, user_id=user_id)
        )

    async def _debounced_extract(self, room: dict[str, Any], user_id: str) -> None:
        """debounce 대기 후 메모리 추출 실행"""
        import asyncio

        room_id = room["id"]
        try:
            await asyncio.sleep(self.EXTRACTION_DEBOUNCE_SEC)
        except asyncio.CancelledError:
            return
        finally:
            ChatService._extraction_timers.pop(room_id, None)

        print(f"[debounce] {self.EXTRACTION_DEBOUNCE_SEC}초 경과 → 메모리 추출 시작: {room_id[:8]}...")
        await self._extract_memory_from_message(room=room, user_id=user_id)

    async def _extract_memory_from_message(
        self,
        room: dict[str, Any],
        user_id: str,
    ) -> None:
        """일반 메시지(비@ai)에서 백그라운드 메모리 추출 — 자체 DB 커넥션 사용"""
        from src.shared.database import get_db_sync

        db = None
        try:
            db = await get_db_sync()
            bg_repo = ChatRepository(db)
            bg_memory_repo = MemoryRepository(db)
            bg_pipeline = MemoryPipeline(memory_repo=bg_memory_repo)

            recent_messages = await bg_repo.get_recent_messages(room["id"], limit=10)
            user_messages = [msg for msg in recent_messages if msg.get("role") == "user"]

            if not user_messages:
                return

            extracted_memories = await bg_pipeline.extract_and_save(
                conversation=user_messages,
                room=room,
                user_id=user_id,
            )

            if extracted_memories:
                from src.websocket.manager import manager
                await manager.broadcast_to_room(room["id"], {
                    "type": "memory:extracted",
                    "data": {
                        "count": len(extracted_memories),
                        "memories": extracted_memories,
                        "room_id": room["id"],
                    },
                })
                print(f"[일반 메시지] 메모리 추출 알림: {len(extracted_memories)}개")
        except Exception as e:
            print(f"[일반 메시지] 메모리 추출 실패: {e}")
        finally:
            if db:
                await db.close()
