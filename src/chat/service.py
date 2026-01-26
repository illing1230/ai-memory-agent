"""Chat Room Service"""

from typing import Any, Literal

import aiosqlite

from src.chat.repository import ChatRepository
from src.shared.exceptions import NotFoundException


class ChatService:
    """채팅방 관련 비즈니스 로직"""

    def __init__(self, db: aiosqlite.Connection):
        self.repo = ChatRepository(db)

    async def create_chat_room(
        self,
        name: str,
        owner_id: str,
        room_type: Literal["personal", "project", "department"] = "personal",
        project_id: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """채팅방 생성"""
        return await self.repo.create_chat_room(
            name=name,
            owner_id=owner_id,
            room_type=room_type,
            project_id=project_id,
            department_id=department_id,
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

    async def delete_chat_room(self, room_id: str) -> bool:
        """채팅방 삭제"""
        await self.get_chat_room(room_id)
        return await self.repo.delete_chat_room(room_id)
