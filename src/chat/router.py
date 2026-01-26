"""Chat Room API Router"""

from fastapi import APIRouter, Depends, HTTPException, Header
import aiosqlite

from src.shared.database import get_db
from src.shared.exceptions import NotFoundException
from src.chat.service import ChatService
from src.chat.schemas import (
    ChatRoomCreate,
    ChatRoomResponse,
)

router = APIRouter()


def get_chat_service(db: aiosqlite.Connection = Depends(get_db)) -> ChatService:
    return ChatService(db)


def get_current_user_id(x_user_id: str = Header(..., description="현재 사용자 ID")) -> str:
    return x_user_id


@router.post("", response_model=ChatRoomResponse)
async def create_chat_room(
    data: ChatRoomCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 생성"""
    return await service.create_chat_room(
        name=data.name,
        owner_id=user_id,
        room_type=data.room_type,
        project_id=data.project_id,
        department_id=data.department_id,
    )


@router.get("", response_model=list[ChatRoomResponse])
async def list_chat_rooms(
    room_type: str | None = None,
    project_id: str | None = None,
    department_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 목록"""
    return await service.list_chat_rooms(
        owner_id=user_id,
        room_type=room_type,
        project_id=project_id,
        department_id=department_id,
    )


@router.get("/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: str,
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 조회"""
    try:
        return await service.get_chat_room(room_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/{room_id}")
async def delete_chat_room(
    room_id: str,
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 삭제"""
    try:
        await service.delete_chat_room(room_id)
        return {"message": "채팅방이 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
