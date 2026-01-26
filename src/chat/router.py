"""Chat Room API Router"""

from fastapi import APIRouter, Depends, HTTPException, Header
import aiosqlite

from src.shared.database import get_db
from src.shared.exceptions import NotFoundException
from src.chat.service import ChatService
from src.chat.schemas import (
    ChatRoomCreate,
    ChatRoomResponse,
    ContextSources,
    MessageCreate,
    MessageResponse,
    ChatResponse,
)

router = APIRouter()


def get_chat_service(db: aiosqlite.Connection = Depends(get_db)) -> ChatService:
    return ChatService(db)


def get_current_user_id(x_user_id: str = Header(..., description="현재 사용자 ID")) -> str:
    return x_user_id


# ==================== Chat Room ====================

@router.post("", response_model=ChatRoomResponse)
async def create_chat_room(
    data: ChatRoomCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 생성"""
    context_sources = data.context_sources.model_dump() if data.context_sources else None
    return await service.create_chat_room(
        name=data.name,
        owner_id=user_id,
        room_type=data.room_type,
        project_id=data.project_id,
        department_id=data.department_id,
        context_sources=context_sources,
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


@router.put("/{room_id}", response_model=ChatRoomResponse)
async def update_chat_room(
    room_id: str,
    name: str | None = None,
    context_sources: ContextSources | None = None,
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 수정"""
    try:
        cs = context_sources.model_dump() if context_sources else None
        return await service.update_chat_room(room_id, name, cs)
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


# ==================== Messages ====================

@router.get("/{room_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    room_id: str,
    limit: int = 50,
    offset: int = 0,
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 메시지 목록"""
    try:
        return await service.get_messages(room_id, limit, offset)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/{room_id}/messages", response_model=ChatResponse)
async def send_message(
    room_id: str,
    data: MessageCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """메시지 전송 (@ai 멘션 시 AI 응답 포함)"""
    try:
        result = await service.send_message(
            chat_room_id=room_id,
            user_id=user_id,
            content=data.content,
        )
        return result
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
