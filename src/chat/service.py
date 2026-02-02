"""Chat Room Service"""

import re
from typing import Any, Literal

import aiosqlite

from src.chat.repository import ChatRepository
from src.memory.repository import MemoryRepository
from src.user.repository import UserRepository
from src.document.repository import DocumentRepository
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
        self.document_repo = DocumentRepository(db)
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
        # 기본 context_sources 설정 (새 구조)
        if context_sources is None:
            context_sources = {
                "memory": {
                    "include_this_room": True,
                    "other_chat_rooms": [],
                    "include_personal": False,
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
        
        # Vector DB에서 채팅방 메모리 삭제
        try:
            from src.shared.vector_store import delete_vectors_by_filter
            await delete_vectors_by_filter({"chat_room_id": room_id})
            print(f"채팅방 {room_id}의 Vector DB 데이터 삭제 완료")
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
        
        if role == "owner":
            raise ForbiddenException("owner 역할은 부여할 수 없습니다")
        
        member = await self.repo.get_member(room_id, target_user_id)
        if not member:
            raise NotFoundException("채팅방 멤버", target_user_id)
        
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
            raise ForbiddenException("채팅방 멤버가 아닙니다")
        
        if user_id == target_user_id:
            if member["role"] == "owner":
                raise ForbiddenException("owner는 채팅방을 나갈 수 없습니다")
            return await self.repo.remove_member(room_id, target_user_id)
        
        if member["role"] not in ["owner", "admin"]:
            raise ForbiddenException("멤버를 제거할 권한이 없습니다")
        
        target_member = await self.repo.get_member(room_id, target_user_id)
        if not target_member:
            raise NotFoundException("채팅방 멤버", target_user_id)
        
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
        """/remember - 메모리 저장
        
        기본: 개인 메모리 + 채팅방 메모리 둘 다 저장
        옵션:
        - /remember <내용> : 개인 + 채팅방 메모리 저장 (기본)
        - /remember -d <내용> : 개인 + 채팅방 + 부서 메모리 저장
        - /remember --dept <내용> : 개인 + 채팅방 + 부서 메모리 저장
        - /remember -p <프로젝트명> <내용> : 개인 + 채팅방 + 지정 프로젝트 메모리 저장
        - /remember --proj <프로젝트명> <내용> : 개인 + 채팅방 + 지정 프로젝트 메모리 저장
        """
        if not content:
            return "❌ 저장할 내용을 입력하세요.\n\n예: `/remember 김과장은 오전 회의를 선호한다`\n예: `/remember -d 팀 회의는 매주 월요일 10시`\n예: `/remember -p AI프로젝트 마감일은 매월 말일`", []
        
        # 옵션 파싱
        include_dept = False
        include_proj = False
        project_name = None
        
        if content.startswith('--dept '):
            include_dept = True
            content = content[len('--dept '):].strip()
        elif content.startswith('-d '):
            include_dept = True
            content = content[len('-d '):].strip()
        elif content.startswith('--proj '):
            include_proj = True
            content = content[len('--proj '):].strip()
        elif content.startswith('-p '):
            include_proj = True
            content = content[len('-p '):].strip()
        
        if not content:
            return "❌ 저장할 내용을 입력하세요.", []
        
        # 사용자 부서 정보 조회 (부서 메모리 저장 시 필요)
        user_dept_id = None
        if include_dept:
            user = await self.user_repo.get_user(user_id)
            if user:
                user_dept_id = user.get("department_id")
            if not user_dept_id:
                return "❌ 부서 정보가 없어 부서 메모리를 저장할 수 없습니다.", []
        
        # 사용자 프로젝트 정보 조회 (프로젝트 메모리 저장 시 필요)
        user_proj_id = None
        if include_proj:
            # 프로젝트 이름 추출 (첫 단어)
            parts = content.split(maxsplit=1)
            if len(parts) >= 2:
                project_name = parts[0]
                content = parts[1]
            else:
                return "❌ 프로젝트명과 내용을 입력하세요.\n\n예: `/remember -p AI프로젝트 마감일은 매월 말일`", []
            
            # 프로젝트 이름으로 검색
            user_projects = await self.user_repo.get_user_projects(user_id)
            found_project = None
            for proj in user_projects:
                if proj["name"] == project_name:
                    found_project = proj
                    break
            
            if not found_project:
                return f"❌ '{project_name}' 프로젝트를 찾을 수 없습니다.\n\n내 프로젝트 목록: {', '.join([p['name'] for p in user_projects])}", []
            
            user_proj_id = found_project["id"]
        
        try:
            embedding_provider = get_embedding_provider()
            vector = await embedding_provider.embed(content)
            
            saved_memories = []
            saved_scopes = []
            
            # 1. 개인 메모리 저장
            vector_id_personal = str(uuid.uuid4())
            memory_personal = await self.memory_repo.create_memory(
                content=content,
                owner_id=user_id,
                scope="personal",
                vector_id=vector_id_personal,
                chat_room_id=None,
                category="fact",
                importance="medium",
            )
            await upsert_vector(vector_id_personal, vector, {
                "memory_id": memory_personal["id"],
                "scope": "personal",
                "owner_id": user_id,
            })
            saved_memories.append(memory_personal)
            saved_scopes.append("개인")
            
            # 2. 채팅방 메모리 저장
            vector_id_chatroom = str(uuid.uuid4())
            memory_chatroom = await self.memory_repo.create_memory(
                content=content,
                owner_id=user_id,
                scope="chatroom",
                vector_id=vector_id_chatroom,
                chat_room_id=room["id"],
                category="fact",
                importance="medium",
            )
            await upsert_vector(vector_id_chatroom, vector, {
                "memory_id": memory_chatroom["id"],
                "scope": "chatroom",
                "owner_id": user_id,
                "chat_room_id": room["id"],
            })
            saved_memories.append(memory_chatroom)
            saved_scopes.append("채팅방")
            
            # 3. 부서 메모리 저장 (옵션)
            if include_dept and user_dept_id:
                vector_id_dept = str(uuid.uuid4())
                memory_dept = await self.memory_repo.create_memory(
                    content=content,
                    owner_id=user_id,
                    scope="department",
                    vector_id=vector_id_dept,
                    department_id=user_dept_id,
                    category="fact",
                    importance="medium",
                )
                await upsert_vector(vector_id_dept, vector, {
                    "memory_id": memory_dept["id"],
                    "scope": "department",
                    "owner_id": user_id,
                    "department_id": user_dept_id,
                })
                saved_memories.append(memory_dept)
                saved_scopes.append("부서")
            
            # 4. 프로젝트 메모리 저장 (옵션)
            if include_proj and user_proj_id:
                vector_id_proj = str(uuid.uuid4())
                memory_proj = await self.memory_repo.create_memory(
                    content=content,
                    owner_id=user_id,
                    scope="project",
                    vector_id=vector_id_proj,
                    project_id=user_proj_id,
                    category="fact",
                    importance="medium",
                )
                await upsert_vector(vector_id_proj, vector, {
                    "memory_id": memory_proj["id"],
                    "scope": "project",
                    "owner_id": user_id,
                    "project_id": user_proj_id,
                })
                saved_memories.append(memory_proj)
                saved_scopes.append("프로젝트")
            
            scope_label = " + ".join(saved_scopes)
            return f"✅ 메모리가 저장되었습니다!\n\n📝 {content}\n\n범위: {scope_label}", saved_memories
            
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
            
            # 이 채팅방 메모리에서만 검색
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
            memories = await self._search_relevant_memories(query, user_id, room["id"], context_sources)
            
            if not memories:
                return f"🔍 '{query}'와 관련된 메모리를 찾을 수 없습니다."
            
            response = f"🔍 '{query}' 검색 결과 ({len(memories)}개)\n\n"
            for i, m in enumerate(memories, 1):
                mem = m["memory"]
                score = m["score"]
                scope_label = "이 채팅방" if mem["scope"] == "chatroom" else mem["scope"]
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
                return "👥 채팅방 멤버가 없습니다."
            
            response = f"👥 채팅방 멤버 ({len(members)}명)\n\n"
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
                return f"ℹ️ {target_user['name']}님은 이미 채팅방 멤버입니다."
            
            await self.repo.add_member(room["id"], target_user["id"], "member")
            
            return f"✅ {target_user['name']}님을 채팅방에 초대했습니다!"
            
        except Exception as e:
            return f"❌ 멤버 초대 실패: {str(e)}"

    def _cmd_help(self) -> str:
        """/help - 도움말"""
        return """📖 **사용 가능한 커맨드**

**메모리 관리**
• `/remember <내용>` - 개인 + 채팅방 메모리 저장
• `/remember -d <내용>` - 개인 + 채팅방 + 부서 메모리 저장
• `/remember -p <프로젝트명> <내용>` - 개인 + 채팅방 + 지정 프로젝트 메모리 저장
• `/forget <검색어>` - 메모리 삭제
• `/search <검색어>` - 메모리 검색

**채팅방 관리**
• `/members` - 멤버 목록 보기
• `/invite <이메일>` - 멤버 초대 (관리자만)

**AI 호출**
• `@ai <질문>` - AI에게 질문

**기타**
• `/help` - 이 도움말 표시

**맞춤 설정**
메모리 소스 설정에서 개인 메모리, 다른 채팅방, 부서 메모리, 프로젝트 메모리를 활성화하면
AI가 해당 메모리들도 참조합니다."""

    async def get_messages(
        self,
        chat_room_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """채팅방 메시지 목록 (멤버만)"""
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
        """AI 응답 생성 (우선순위: 대화 > RAG 문서 > 메모리)"""
        # Step 1: 최근 대화 (최우선)
        recent_messages = await self.repo.get_recent_messages(room["id"], limit=20)
        
        # Step 2: RAG 문서 검색 (높은 우선순위)
        document_chunks = await self._search_relevant_documents(
            query=user_message,
            chat_room_id=room["id"],
        )
        
        # Step 3: 메모리 검색 (보조)
        relevant_memories = await self._search_relevant_memories(
            query=user_message,
            user_id=user_id,
            current_room_id=room["id"],
            context_sources=room.get("context_sources", {}),
        )
        
        system_prompt = self._build_system_prompt(relevant_memories, document_chunks)
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
        
        # AI 응답을 Vector DB에 저장 (채팅방 메모리)
        try:
            embedding_provider = get_embedding_provider()
            vector = await embedding_provider.embed(response)
            vector_id = str(uuid.uuid4())
            
            # AI 응답을 채팅방 메모리로 저장
            memory = await self.memory_repo.create_memory(
                content=response,
                owner_id=user_id,
                scope="chatroom",
                vector_id=vector_id,
                chat_room_id=room["id"],
                category="ai_response",
                importance="medium",
            )
            
            # Vector DB에 저장
            await upsert_vector(vector_id, vector, {
                "memory_id": memory["id"],
                "scope": "chatroom",
                "owner_id": user_id,
                "chat_room_id": room["id"],
            })
            
            print(f"AI 응답을 Vector DB에 저장했습니다: {memory['id']}")
        except Exception as e:
            print(f"AI 응답 Vector DB 저장 실패: {e}")
        
        extracted_memories = await self._extract_and_save_memories(
            conversation=recent_messages + [{"role": "user", "content": user_message}],
            room=room,
            user_id=user_id,
        )
        
        return {
            "response": response,
            "extracted_memories": extracted_memories,
        }

    async def _search_relevant_documents(
        self,
        query: str,
        chat_room_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """채팅방에 연결된 문서에서 관련 청크 검색 (RAG)"""
        doc_ids = await self.document_repo.get_linked_document_ids(chat_room_id)
        if not doc_ids:
            return []

        try:
            embedding_provider = get_embedding_provider()
            query_vector = await embedding_provider.embed(query)
        except Exception as e:
            print(f"문서 검색용 임베딩 실패: {e}")
            return []

        try:
            results = await search_vectors(
                query_vector=query_vector,
                limit=limit,
                filter_conditions={
                    "scope": "document",
                    "document_id": doc_ids,
                },
            )
        except Exception as e:
            print(f"문서 벡터 검색 실패: {e}")
            return []

        enriched = []
        for r in results:
            doc_id = r["payload"].get("document_id")
            chunk_idx = r["payload"].get("chunk_index")
            doc = await self.document_repo.get_document(doc_id)

            chunks = await self.document_repo.get_chunks(doc_id)
            chunk_content = ""
            for c in chunks:
                if c["chunk_index"] == chunk_idx:
                    chunk_content = c["content"]
                    break

            enriched.append({
                "content": chunk_content,
                "score": r["score"],
                "document_name": doc["name"] if doc else "Unknown",
                "chunk_index": chunk_idx,
                "document_id": doc_id,
            })

        return enriched

    async def _search_relevant_memories(
        self,
        query: str,
        user_id: str,
        current_room_id: str,
        context_sources: dict | None,
    ) -> list[dict[str, Any]]:
        """컨텍스트 소스 기반 메모리 검색 (새 구조)"""
        # context_sources가 None이면 기본값 사용
        if context_sources is None:
            context_sources = {}
        
        memory_config = context_sources.get("memory", {})
        
        # 디버깅: context_sources 확인
        print(f"\n========== 메모리 검색 시작 ==========")
        print(f"현재 채팅방 ID: {current_room_id}")
        print(f"context_sources: {context_sources}")
        print(f"memory_config: {memory_config}")
        print(f"other_chat_rooms: {memory_config.get('other_chat_rooms', [])}")
        
        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed(query)
        
        all_memories = []
        
        # 1. 이 채팅방 메모리 (기본)
        if memory_config.get("include_this_room", True):
            try:
                print(f"\n[1] 이 채팅방({current_room_id}) 메모리 검색 중...")
                results = await search_vectors(
                    query_vector=query_vector,
                    limit=5,
                    filter_conditions={"chat_room_id": current_room_id},
                )
                print(f"    검색 결과: {len(results)}개")
                for r in results:
                    print(f"    - score: {r['score']:.3f}, payload: {r['payload']}")
                    memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                    if memory:
                        all_memories.append({"memory": memory, "score": r["score"]})
            except Exception as e:
                print(f"    실패: {e}")
        
        # 2. 다른 채팅방 메모리
        other_rooms = memory_config.get("other_chat_rooms", [])
        print(f"\n[2] 다른 채팅방 검색 대상: {other_rooms}")
        for room_id in other_rooms:
            try:
                print(f"    채팅방({room_id}) 검색 중...")
                results = await search_vectors(
                    query_vector=query_vector,
                    limit=3,
                    filter_conditions={"chat_room_id": room_id},
                )
                print(f"    검색 결과: {len(results)}개")
                for r in results:
                    print(f"    - score: {r['score']:.3f}, payload: {r['payload']}")
                    memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                    if memory:
                        all_memories.append({"memory": memory, "score": r["score"]})
            except Exception as e:
                print(f"    실패: {e}")
        
        # 3. 내 개인 메모리 전체
        if memory_config.get("include_personal", False):
            try:
                print(f"\n[3] 개인 메모리 검색 중...")
                results = await search_vectors(
                    query_vector=query_vector,
                    limit=5,
                    filter_conditions={"owner_id": user_id, "scope": "personal"},
                )
                print(f"    검색 결과: {len(results)}개")
                for r in results:
                    memory = await self.memory_repo.get_memory(r["payload"].get("memory_id"))
                    if memory:
                        all_memories.append({"memory": memory, "score": r["score"]})
            except Exception as e:
                print(f"    실패: {e}")
        
        # 4. 프로젝트 메모리
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
        
        # 5. 부서 메모리
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
        
        # 중복 제거 및 정렬
        seen = set()
        unique_memories = []
        for m in sorted(all_memories, key=lambda x: x["score"], reverse=True):
            if m["memory"]["id"] not in seen:
                seen.add(m["memory"]["id"])
                unique_memories.append(m)
        
        print(f"\n========== 총 메모리 검색 결과: {len(unique_memories)}개 ==========")
        for m in unique_memories:
            print(f"  - {m['memory']['content'][:50]}... (score: {m['score']:.3f})")
        print("")
        
        return unique_memories[:10]

    def _build_system_prompt(
        self,
        memories: list[dict[str, Any]],
        document_chunks: list[dict[str, Any]] | None = None,
    ) -> str:
        """시스템 프롬프트 구성 (우선순위: RAG 문서 > 메모리)"""
        base_prompt = """당신은 팀의 AI 어시스턴트입니다.
사용자들의 질문에 친절하고 정확하게 답변하세요.
대화 내용을 잘 참고하여 맥락에 맞는 답변을 해주세요."""

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
        """대화에서 메모리 추출 및 저장 (chatroom scope)"""
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
            
            # 채팅방 메모리로 저장
            scope = "chatroom"
            
            try:
                embedding_provider = get_embedding_provider()
                vector = await embedding_provider.embed(content)
                vector_id = str(uuid.uuid4())
                
                memory = await self.memory_repo.create_memory(
                    content=content,
                    owner_id=user_id,
                    scope=scope,
                    vector_id=vector_id,
                    chat_room_id=room["id"],
                    category=item.get("category"),
                    importance=item.get("importance", "medium"),
                )
                
                payload = {
                    "memory_id": memory["id"],
                    "scope": scope,
                    "owner_id": user_id,
                    "chat_room_id": room["id"],
                }
                await upsert_vector(vector_id, vector, payload)
                
                saved_memories.append(memory)
            except Exception as e:
                print(f"메모리 저장 실패: {e}")
                continue
        
        return saved_memories

    def _parse_mentions(self, content: str) -> list[str]:
        """멘션 파싱"""
        pattern = r"@(\w+)"
        matches = re.findall(pattern, content.lower())
        return list(set(matches))
