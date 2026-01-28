"""WebSocket 라우터"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import aiosqlite

from src.websocket.manager import manager
from src.shared.auth import verify_access_token
from src.shared.database import get_db_sync
from src.chat.service import ChatService
from src.chat.repository import ChatRepository
from src.user.repository import UserRepository

router = APIRouter()


@router.websocket("/chat/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None),
):
    """채팅방 WebSocket 엔드포인트"""
    
    # 인증 확인
    user_id = None
    if token:
        user_id = verify_access_token(token)
    
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # DB 연결
    db = get_db_sync()
    
    try:
        # 사용자 정보 조회
        user_repo = UserRepository(db)
        user = await user_repo.get_user(user_id)
        if not user:
            await websocket.close(code=4004, reason="User not found")
            return
        
        user_name = user.get("name", "Unknown")
        
        # 채팅방 멤버 확인
        chat_repo = ChatRepository(db)
        member = await chat_repo.get_member(room_id, user_id)
        if not member:
            await websocket.close(code=4003, reason="Not a member")
            return
        
        # 연결 등록
        await manager.connect(
            websocket=websocket,
            room_id=room_id,
            user_id=user_id,
            user_name=user_name,
        )
        
        # 현재 접속자 목록 전송
        await websocket.send_json({
            "type": "room:info",
            "data": {
                "room_id": room_id,
                "online_users": manager.get_room_users(room_id),
            },
        })
        
        # 메시지 처리 루프
        chat_service = ChatService(db)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                msg_data = message.get("data", {})
                
                if msg_type == "message:send":
                    # 메시지 전송
                    content = msg_data.get("content", "").strip()
                    if content:
                        result = await chat_service.send_message(
                            chat_room_id=room_id,
                            user_id=user_id,
                            content=content,
                        )
                        
                        # 사용자 메시지 브로드캐스트
                        await manager.broadcast_to_room(
                            room_id,
                            {
                                "type": "message:new",
                                "data": {
                                    **result["user_message"],
                                    "user_name": user_name,
                                },
                            },
                        )
                        
                        # AI 응답 브로드캐스트
                        if result.get("assistant_message"):
                            await manager.broadcast_to_room(
                                room_id,
                                {
                                    "type": "message:new",
                                    "data": {
                                        **result["assistant_message"],
                                        "user_name": "AI",
                                    },
                                },
                            )
                        
                        # 추출된 메모리 알림
                        if result.get("extracted_memories"):
                            await manager.send_to_user(
                                user_id,
                                {
                                    "type": "memory:extracted",
                                    "data": {
                                        "count": len(result["extracted_memories"]),
                                        "memories": [
                                            {"id": m["id"], "content": m["content"]}
                                            for m in result["extracted_memories"]
                                        ],
                                    },
                                },
                            )
                
                elif msg_type == "typing:start":
                    await manager.broadcast_to_room(
                        room_id,
                        {
                            "type": "typing:start",
                            "data": {"user_id": user_id, "user_name": user_name},
                        },
                        exclude_user=user_id,
                    )
                
                elif msg_type == "typing:stop":
                    await manager.broadcast_to_room(
                        room_id,
                        {
                            "type": "typing:stop",
                            "data": {"user_id": user_id},
                        },
                        exclude_user=user_id,
                    )
                
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(room_id, user_id)
