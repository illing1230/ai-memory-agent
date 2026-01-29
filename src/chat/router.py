"""Chat Room API Router"""

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from src.shared.database import get_db
from src.shared.exceptions import NotFoundException, ForbiddenException
from src.shared.auth import get_current_user_id
from src.chat.service import ChatService
from src.chat.schemas import (
    ChatRoomCreate,
    ChatRoomResponse,
    ContextSources,
    MessageCreate,
    MessageResponse,
    ChatResponse,
    ChatRoomMemberCreate,
    ChatRoomMemberResponse,
)

router = APIRouter()


def get_chat_service(db: aiosqlite.Connection = Depends(get_db)) -> ChatService:
    return ChatService(db)


# ==================== Chat Room ====================

@router.post("", response_model=ChatRoomResponse)
async def create_chat_room(
    data: ChatRoomCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 생성 (생성자가 자동으로 owner가 됨)"""
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
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """내가 속한 채팅방 목록"""
    return await service.list_chat_rooms(user_id=user_id)


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
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 수정 (owner/admin만)"""
    try:
        cs = context_sources.model_dump() if context_sources else None
        return await service.update_chat_room(room_id, user_id, name, cs)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/{room_id}")
async def delete_chat_room(
    room_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 삭제 (owner만)"""
    try:
        await service.delete_chat_room(room_id, user_id)
        return {"message": "채팅방이 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Members ====================

@router.post("/{room_id}/members", response_model=ChatRoomMemberResponse)
async def add_member(
    room_id: str,
    data: ChatRoomMemberCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """멤버 추가 (owner/admin만)"""
    try:
        return await service.add_member(room_id, user_id, data.user_id, data.role)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/{room_id}/members", response_model=list[ChatRoomMemberResponse])
async def list_members(
    room_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """멤버 목록 (멤버만 조회 가능)"""
    try:
        return await service.list_members(room_id, user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.put("/{room_id}/members/{target_user_id}")
async def update_member_role(
    room_id: str,
    target_user_id: str,
    role: str,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """멤버 역할 변경 (owner만)"""
    try:
        return await service.update_member_role(room_id, user_id, target_user_id, role)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/{room_id}/members/{target_user_id}")
async def remove_member(
    room_id: str,
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """멤버 제거 (owner/admin 또는 본인)"""
    try:
        await service.remove_member(room_id, user_id, target_user_id)
        return {"message": "멤버가 제거되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Messages ====================

@router.get("/{room_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    room_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채팅방 메시지 목록 (멤버만)"""
    try:
        return await service.get_messages(room_id, user_id, limit, offset)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.post("/{room_id}/messages", response_model=ChatResponse)
async def send_message(
    room_id: str,
    data: MessageCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """메시지 전송 (멤버만, @ai 멘션 시 AI 응답)"""
    try:
        result = await service.send_message(
            chat_room_id=room_id,
            user_id=user_id,
            content=data.content,
        )
        return result
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenException as e:
        raise HTTPException(status_code=403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
