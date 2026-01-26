"""Chat Room Service"""

import re
from typing import Any, Literal

import aiosqlite

from src.chat.repository import ChatRepository
from src.memory.repository import MemoryRepository
from src.user.repository import UserRepository
from src.shared.exceptions import NotFoundException, ForbiddenException
from src.shared.vector_store import search_vectors, upsert_vector
from src.shared.providers import get_embedding_provider, get_llm_provider
from src.config import get_settings
import uuid


# AI 시스템 사용자 ID (고정)
AI_USER_ID = "ai-assistant"
AI_USER_NAME = "AI Assistant"

# 슬래시 커맨드 패턴
COMMAND_PATTERN = r"^/(\w+)\s*(.*)"


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
        """채팅방 생성 + 생성자를 owner로 추가"""
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
        
        # 채팅방 생성
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
        
        return room

    async def get_chat_room(self, room_id: str) -> dict[str, Any]:
        """채팅방 조회"""
        room = await self.repo.get_chat_room(room_id)
        if not room:
            raise NotFoundException("채팅방", room_id)
        return room

    async def list_chat_rooms(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """사용자가 속한 채팅방 목록"""
        return await self.repo.get_user_rooms(user_id)

    async def update_chat_room(
        self,
        room_id: str,
        user_id: str,
        name: str | None = None,
        context_sources: dict | None = None,
    ) -> dict[str, Any]:
        """채팅방 수정 (owner/admin만 가능)"""
        await self._check_admin_permission(room_id, user_id)
        return await self.repo.update_chat_room(room_id, name, context_sources)

    async def delete_chat_room(self, room_id: str, user_id: str) -> bool:
        """채팅방 삭제 (owner만 가능)"""
        await self._check_owner_permission(room_id, user_id)
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
        
        # 이미 멤버인지 확인
        if await self.repo.is_member(room_id, target_user_id):
            raise ForbiddenException("이미 채팅방 멤버입니다")
        
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
        
        # owner 역할은 변경 불가
        if role == "owner":
            raise ForbiddenException("owner 역할은 부여할 수 없습니다")
        
        member = await self.repo.get_member(room_id, target_user_id)
        if not member:
            raise NotFoundException("채팅방 멤버", target_user_id)
        
        # owner의 역할은 변경 불가
        if member["role"] == "owner":
            raise ForbiddenException("owner의 역할은 변경할 수 없습니다")
        
        return await self.repo.update_member_role(room_id, target_user_id, role)

    async def remove_member(
        self,
        room_id: str,
        user_id: str,
        target_user_id: str,
    ) -> bool:
        """멤버 제거 (owner/admin 또는 본인만 가능)"""
        member = await self.repo.get_member(room_id, user_id)
        if not member:
            raise ForbiddenException("채팅방 멤버가 아닙니다")
        
        # 본인 탈퇴
        if user_id == target_user_id:
            if member["role"] == "owner":
                raise ForbiddenException("owner는 채팅방을 나갈 수 없습니다. 채팅방을 삭제하세요.")
            return await self.repo.remove_member(room_id, target_user_id)
        
        # 다른 사람 강퇴 (owner/admin만)
        if member["role"] not in ["owner", "admin"]:
            raise ForbiddenException("멤버를 제거할 권한이 없습니다")
        
        target_member = await self.repo.get_member(room_id, target_user_id)
        if not target_member:
            raise NotFoundException("채팅방 멤버", target_user_id)
        
        # owner는 강퇴 불가
        if target_member["role"] == "owner":
            raise ForbiddenException("owner는 강퇴할 수 없습니다")
        
        # admin은 admin 강퇴 불가
        if member["role"] == "admin" and target_member["role"] == "admin":
            raise ForbiddenException("admin은 다른 admin을 강퇴할 수 없습니다")
        
        return await self.repo.remove_member(room_id, target_user_id)

    # ==================== Permission Check ====================

    async def _check_member_permission(self, room_id: str, user_id: str) -> dict[str, Any]:
        """멤버 권한 체크"""
        member = await self.repo.get_member(room_id, user_id)
        if not member:
            raise ForbiddenException("채팅방 멤버가 아닙니다")
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
        
        # 멤버 권한 체크
        await self._check_member_permission(chat_room_id, user_id)
        
        # 슬래시 커맨드 체크
        command_match = re.match(COMMAND_PATTERN, content.strip())
        if command_match:
            command = command_match.group(1).lower()
            args = command_match.group(2).strip()
            return await self._handle_command(room, user_id, command, args, content)
        
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
            
            assistant_message = await self.repo.create_message(
                chat_room_id=chat_room_id,
                user_id=AI_USER_ID,
                content=ai_response["response"],
                role="assistant",
            )
            result["assistant_message"] = assistant_message
            
            if ai_response.get("extracted_memories"):
                result["extracted_memories"] = ai_response["extracted_memories"]
        
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
        
        # 사용자 메시지 저장
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
            
        else:
            response = f"❌ 알 수 없는 커맨드: /{command}\n\n/help 로 사용 가능한 커맨드를 확인하세요."
        
        # AI 응답 메시지 저장
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
        """/remember 커맨드: 메모리 저장"""
        if not content:
            return "❌ 저장할 내용을 입력하세요.\n\n예: `/remember 김과장은 오전 회의를 선호한다`", []
        
        try:
            scope = "personal"
            project_id = None
            department_id = None
            
            if room.get("room_type") == "project" and room.get("project_id"):
                scope = "project"
                project_id = room["project_id"]
            elif room.get("room_type") == "department" and room.get("department_id"):
                scope = "department"
                department_id = room["department_id"]
            
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
                category="fact",
                importance="medium",
            )
            
            payload = {
                "memory_id": memory["id"],
                "scope": scope,
                "owner_id": user_id,
                "project_id": project_id,
                "department_id": department_id,
            }
            await upsert_vector(vector_id, vector, payload)
            
            return f"✅ 메모리가 저장되었습니다!\n\n📝 **{content}**\n\n범위: {scope}", [memory]
            
        except Exception as e:
            print(f"메모리 저장 실패: {e}")
            return f"❌ 메모리 저장 실패: {str(e)}", []

    async def _cmd_forget(
        self,
        room: dict[str, Any],
        user_id: str,
        query: str,
    ) -> str:
        """/forget 커맨드: 메모리 삭제"""
        if not query:
            return "❌ 삭제할 메모리 검색어를 입력하세요.\n\n예: `/forget 김과장 회의`"
        
        try:
            embedding_provider = get_embedding_provider()
            query_vector = await embedding_provider.embed(query)
            
            results = await search_vectors(
                query_vector=query_vector,
                limit=5,
                filter_conditions={"owner_id": user_id},
            )
            
            if not results:
                return f"🔍 '{query}'와 관련된 메모리를 찾을 수 없습니다."
            
            top_result = results[0]
            memory_id = top_result["payload"].get("memory_id")
            
            if memory_id:
                memory = await self.memory_repo.get_memory(memory_id)
                if memory:
                    await self.memory_repo.delete_memory(memory_id)
                    return f"🗑️ 메모리가 삭제되었습니다.\n\n삭제됨: **{memory['content']}**"
            
            return "❌ 메모리 삭제에 실패했습니다."
            
        except Exception as e:
            print(f"메모리 삭제 실패: {e}")
            return f"❌ 메모리 삭제 실패: {str(e)}"

    async def _cmd_search(
        self,
        room: dict[str, Any],
        user_id: str,
        query: str,
    ) -> str:
        """/search 커맨드: 메모리 검색"""
        if not query:
            return "❌ 검색어를 입력하세요.\n\n예: `/search 회의 선호`"
        
        try:
            context_sources = room.get("context_sources", {})
            memories = await self._search_relevant_memories(query, user_id, context_sources)
            
            if not memories:
                return f"🔍 '{query}'와 관련된 메모리를 찾을 수 없습니다."
            
            response = f"🔍 **'{query}' 검색 결과** ({len(memories)}개)\n\n"
            for i, m in enumerate(memories, 1):
                mem = m["memory"]
                score = m["score"]
                response += f"{i}. {mem['content']}\n   _(유사도: {score:.0%}, 범위: {mem['scope']})_\n\n"
            
            return response
            
        except Exception as e:
            print(f"메모리 검색 실패: {e}")
            return f"❌ 메모리 검색 실패: {str(e)}"

    async def _cmd_members(
        self,
        room: dict[str, Any],
        user_id: str,
    ) -> str:
        """/members 커맨드: 멤버 목록"""
        try:
            members = await self.repo.list_members(room["id"])
            
            if not members:
                return "👥 채팅방 멤버가 없습니다."
            
            response = f"👥 **채팅방 멤버** ({len(members)}명)\n\n"
            role_emoji = {"owner": "👑", "admin": "⭐", "member": "👤"}
            
            for m in members:
                emoji = role_emoji.get(m["role"], "👤")
                name = m.get("user_name", "Unknown")
                response += f"{emoji} **{name}** ({m['role']})\n"
            
            return response
            
        except Exception as e:
            return f"❌ 멤버 목록 조회 실패: {str(e)}"

    async def _cmd_invite(
        self,
        room: dict[str, Any],
        user_id: str,
        args: str,
    ) -> str:
        """/invite 커맨드: 멤버 초대"""
        if not args:
            return "❌ 초대할 사용자 이메일을 입력하세요.\n\n예: `/invite kim@samsung.com`"
        
        try:
            # admin 권한 체크
            member = await self.repo.get_member(room["id"], user_id)
            if not member or member["role"] not in ["owner", "admin"]:
                return "❌ 멤버를 초대할 권한이 없습니다. (owner/admin만 가능)"
            
            # 이메일로 사용자 찾기
            email = args.strip()
            target_user = await self.user_repo.get_user_by_email(email)
            
            if not target_user:
                return f"❌ '{email}' 사용자를 찾을 수 없습니다."
            
            # 이미 멤버인지 확인
            if await self.repo.is_member(room["id"], target_user["id"]):
                return f"ℹ️ {target_user['name']}님은 이미 채팅방 멤버입니다."
            
            # 멤버 추가
            await self.repo.add_member(room["id"], target_user["id"], "member")
            
            return f"✅ **{target_user['name']}**님을 채팅방에 초대했습니다!"
            
        except Exception as e:
            return f"❌ 멤버 초대 실패: {str(e)}"

    def _cmd_help(self) -> str:
        """/help 커맨드: 도움말"""
        return """📖 **사용 가능한 커맨드**

**메모리 관리**
• `/remember <내용>` - 메모리로 저장
• `/forget <검색어>` - 메모리 삭제
• `/search <검색어>` - 메모리 검색

**채팅방 관리**
• `/members` - 멤버 목록 보기
• `/invite <이메일>` - 멤버 초대 (관리자만)

**AI 호출**
• `@ai <질문>` - AI에게 질문

**기타**
• `/help` - 이 도움말 표시"""

    async def get_messages(
        self,
        chat_room_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """채팅방 메시지 목록 (멤버만 조회 가능)"""
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
        """AI 응답 생성"""
        recent_messages = await self.repo.get_recent_messages(room["id"], limit=20)
        
        relevant_memories = await self._search_relevant_memories(
            query=user_message,
            user_id=user_id,
            context_sources=room.get("context_sources", {}),
        )
        
        system_prompt = self._build_system_prompt(relevant_memories)
        conversation_context = self._build_conversation(recent_messages)
        
        full_prompt = f"""[최근 대화 내용]
{conversation_context}

[현재 질문]
{user_message}

위 대화 내용을 참고하여 현재 질문에 답변해주세요."""
        
        llm_provider = get_llm_provider()
        response = await llm_provider.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1000,
        )
        
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
        
        if not memory_config.get("personal") and not memory_config.get("projects") and not memory_config.get("departments"):
            return []
        
        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed(query)
        
        all_memories = []
        
        if memory_config.get("personal", False):
            try:
                results = await search_vectors(
                    query_vector=query_vector,
                    limit=5,
                    filter_conditions={"owner_id": user_id, "scope": "personal"},
                )
                for r in results:
                    memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                    if memory:
                        all_memories.append({"memory": memory, "score": r["score"]})
            except Exception as e:
                print(f"개인 메모리 검색 실패: {e}")
        
        for project_id in memory_config.get("projects", []):
            try:
                results = await search_vectors(
                    query_vector=query_vector,
                    limit=3,
                    filter_conditions={"project_id": project_id, "scope": "project"},
                )
                for r in results:
                    memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                    if memory:
                        all_memories.append({"memory": memory, "score": r["score"]})
            except Exception as e:
                print(f"프로젝트 메모리 검색 실패: {e}")
        
        for dept_id in memory_config.get("departments", []):
            try:
                results = await search_vectors(
                    query_vector=query_vector,
                    limit=3,
                    filter_conditions={"department_id": dept_id, "scope": "department"},
                )
                for r in results:
                    memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                    if memory:
                        all_memories.append({"memory": memory, "score": r["score"]})
            except Exception as e:
                print(f"부서 메모리 검색 실패: {e}")
        
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
대화 내용을 잘 참고하여 맥락에 맞는 답변을 해주세요."""
        
        if memories:
            memory_text = "\n\n[저장된 메모리 - 참고용]\n"
            for i, m in enumerate(memories, 1):
                mem = m["memory"]
                memory_text += f"{i}. {mem['content']} (유사도: {m['score']:.2f})\n"
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

    async def _extract_and_save_memories(
        self,
        conversation: list[dict[str, Any]],
        room: dict[str, Any],
        user_id: str,
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출 및 저장"""
        try:
            llm_provider = get_llm_provider()
            
            conv_for_extraction = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in conversation
            ]
            
            extracted = await llm_provider.extract_memories(conv_for_extraction)
        except Exception as e:
            print(f"메모리 추출 실패: {e}")
            return []
        
        saved_memories = []
        for item in extracted:
            content = item.get("content", "")
            if not content or len(content) < self.settings.min_message_length_for_extraction:
                continue
            
            scope = "personal"
            project_id = None
            department_id = None
            
            if room.get("room_type") == "project" and room.get("project_id"):
                scope = "project"
                project_id = room["project_id"]
            elif room.get("room_type") == "department" and room.get("department_id"):
                scope = "department"
                department_id = room["department_id"]
            
            try:
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
                
                payload = {
                    "memory_id": memory["id"],
                    "scope": scope,
                    "owner_id": user_id,
                    "project_id": project_id,
                    "department_id": department_id,
                }
                await upsert_vector(vector_id, vector, payload)
                
                saved_memories.append(memory)
            except Exception as e:
                print(f"메모리 저장 실패: {e}")
                continue
        
        return saved_memories

    def _parse_mentions(self, content: str) -> list[str]:
        """멘션 파싱 (@ai, @user 등)"""
        pattern = r"@(\w+)"
        matches = re.findall(pattern, content.lower())
        return list(set(matches))
