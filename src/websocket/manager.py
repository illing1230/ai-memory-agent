"""WebSocket 연결 관리자"""

import asyncio
from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import WebSocket


@dataclass
class Connection:
    """WebSocket 연결 정보"""
    websocket: WebSocket
    user_id: str
    user_name: str
    connected_at: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # room_id -> set of connections
        self.room_connections: Dict[str, Set[Connection]] = {}
        # user_id -> connection (1:1)
        self.user_connections: Dict[str, Connection] = {}
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        room_id: str,
        user_id: str,
        user_name: str,
    ) -> Connection:
        """연결 수락 및 등록"""
        await websocket.accept()
        
        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            user_name=user_name,
        )
        
        async with self._lock:
            if room_id not in self.room_connections:
                self.room_connections[room_id] = set()
            self.room_connections[room_id].add(connection)
            self.user_connections[user_id] = connection
        
        # 입장 알림
        await self.broadcast_to_room(
            room_id,
            {
                "type": "member:join",
                "data": {
                    "user_id": user_id,
                    "user_name": user_name,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
            exclude_user=user_id,
        )
        
        return connection
    
    async def disconnect(self, room_id: str, user_id: str):
        """연결 해제"""
        connection = None
        async with self._lock:
            connection = self.user_connections.pop(user_id, None)
            
            if room_id in self.room_connections and connection:
                self.room_connections[room_id].discard(connection)
                
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
        
        # 퇴장 알림
        if connection:
            await self.broadcast_to_room(
                room_id,
                {
                    "type": "member:leave",
                    "data": {
                        "user_id": user_id,
                        "user_name": connection.user_name,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                },
                exclude_user=user_id,
            )
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_user: Optional[str] = None,
    ):
        """채팅방 전체에 메시지 브로드캐스트"""
        connections = self.room_connections.get(room_id, set()).copy()
        
        disconnected = []
        for conn in connections:
            if exclude_user and conn.user_id == exclude_user:
                continue
            
            try:
                await conn.websocket.send_json(message)
            except Exception:
                disconnected.append(conn)
        
        # 끊어진 연결 정리
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if room_id in self.room_connections:
                        self.room_connections[room_id].discard(conn)
                    self.user_connections.pop(conn.user_id, None)
    
    async def send_to_user(self, user_id: str, message: dict):
        """특정 사용자에게 메시지 전송"""
        connection = self.user_connections.get(user_id)
        if connection:
            try:
                await connection.websocket.send_json(message)
            except Exception:
                pass
    
    def get_room_users(self, room_id: str) -> list[dict]:
        """채팅방 접속 사용자 목록"""
        connections = self.room_connections.get(room_id, set())
        return [
            {
                "user_id": conn.user_id,
                "user_name": conn.user_name,
                "connected_at": conn.connected_at.isoformat(),
            }
            for conn in connections
        ]
    
    def get_room_user_count(self, room_id: str) -> int:
        """채팅방 접속 인원 수"""
        return len(self.room_connections.get(room_id, set()))


# 전역 연결 관리자
manager = ConnectionManager()
