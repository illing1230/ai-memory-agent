"""
Mchat Worker - 실제 AI Memory Agent 연동

실행:
    python -m src.mchat.worker
"""

import asyncio
import aiosqlite

from src.mchat.client import MchatClient
from src.chat.service import ChatService
from src.chat.repository import ChatRepository
from src.memory.repository import MemoryRepository
from src.user.repository import UserRepository
from src.config import get_settings
from src.shared.database import init_db


# Mchat 채널 → Agent 채팅방 매핑 (임시 - 추후 DB로 관리)
CHANNEL_MAPPING = {}


async def get_or_create_agent_room(
    db: aiosqlite.Connection,
    mchat_channel_id: str,
    mchat_channel_name: str,
    mchat_user_id: str,
) -> str:
    """Mchat 채널에 매핑된 Agent 채팅방 ID 반환 (없으면 생성)"""
    
    # 캐시 확인
    if mchat_channel_id in CHANNEL_MAPPING:
        return CHANNEL_MAPPING[mchat_channel_id]
    
    # DB에서 매핑 조회
    cursor = await db.execute(
        "SELECT agent_room_id FROM mchat_channel_mapping WHERE mchat_channel_id = ?",
        (mchat_channel_id,)
    )
    row = await cursor.fetchone()
    
    if row:
        CHANNEL_MAPPING[mchat_channel_id] = row[0]
        return row[0]
    
    # 없으면 새 채팅방 생성
    chat_repo = ChatRepository(db)
    room = await chat_repo.create_chat_room(
        name=f"Mchat: {mchat_channel_name or mchat_channel_id[:8]}",
        owner_id=mchat_user_id,
        room_type="personal",
    )
    
    # 매핑 저장
    await db.execute(
        """INSERT INTO mchat_channel_mapping (id, mchat_channel_id, mchat_channel_name, agent_room_id)
           VALUES (?, ?, ?, ?)""",
        (f"map_{mchat_channel_id[:8]}", mchat_channel_id, mchat_channel_name, room["id"])
    )
    await db.commit()
    
    CHANNEL_MAPPING[mchat_channel_id] = room["id"]
    return room["id"]


async def get_or_create_agent_user(
    db: aiosqlite.Connection,
    mchat_user_id: str,
    mchat_username: str,
) -> str:
    """Mchat 사용자에 매핑된 Agent 사용자 ID 반환 (없으면 생성)"""
    
    # DB에서 매핑 조회
    cursor = await db.execute(
        "SELECT agent_user_id FROM mchat_user_mapping WHERE mchat_user_id = ?",
        (mchat_user_id,)
    )
    row = await cursor.fetchone()
    
    if row:
        return row[0]
    
    # Agent 사용자 존재 확인
    user_repo = UserRepository(db)
    user = await user_repo.get_user(mchat_user_id)
    
    if not user:
        # 새 사용자 생성
        user = await user_repo.create_user(
            user_id=mchat_user_id,
            email=f"{mchat_username}@mchat.local",
            name=mchat_username,
        )
    
    # 매핑 저장
    await db.execute(
        """INSERT OR IGNORE INTO mchat_user_mapping (id, mchat_user_id, mchat_username, agent_user_id)
           VALUES (?, ?, ?, ?)""",
        (f"umap_{mchat_user_id[:8]}", mchat_user_id, mchat_username, user["id"])
    )
    await db.commit()
    
    return user["id"]


async def ensure_mapping_tables(db: aiosqlite.Connection):
    """매핑 테이블 생성"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mchat_channel_mapping (
            id TEXT PRIMARY KEY,
            mchat_channel_id TEXT UNIQUE NOT NULL,
            mchat_channel_name TEXT,
            mchat_team_id TEXT,
            agent_room_id TEXT,
            sync_enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mchat_user_mapping (
            id TEXT PRIMARY KEY,
            mchat_user_id TEXT UNIQUE NOT NULL,
            mchat_username TEXT,
            agent_user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await db.commit()


async def main():
    settings = get_settings()
    
    print("=" * 50)
    print("Mchat Worker - AI Memory Agent 연동")
    print("=" * 50)
    print(f"MCHAT_URL: {settings.mchat_url}")
    print(f"MCHAT_ENABLED: {settings.mchat_enabled}")
    
    if not settings.mchat_enabled:
        print("Mchat is disabled. Set MCHAT_ENABLED=true in .env")
        return
    
    if not settings.mchat_token:
        print("MCHAT_TOKEN is not set in .env")
        return
    
    # DB 초기화
    await init_db()
    db = await aiosqlite.connect(settings.sqlite_db_path)
    db.row_factory = aiosqlite.Row
    
    # 매핑 테이블 생성
    await ensure_mapping_tables(db)
    
    # Mchat 클라이언트 생성
    client = MchatClient()
    
    # Bot 정보 조회
    print("\n[Bot 정보 조회]")
    me = await client.get_me()
    print(f"Bot ID: {me['id']}")
    print(f"Username: {me['username']}")
    
    bot_user_id = me["id"]
    
    # 이벤트 핸들러 등록
    @client.on("posted")
    async def handle_message(event):
        """새 메시지 수신 시 처리"""
        data = event.get("data", {})
        post = data.get("post", {})
        
        message = post.get("message", "")
        channel_id = post.get("channel_id", "")
        user_id = post.get("user_id", "")
        channel_name = data.get("channel_display_name", "")
        sender_name = data.get("sender_name", "unknown")
        
        # AI 응답 메시지는 무시 (무한루프 방지)
        if message.startswith("🤖") or message.startswith("✅") or message.startswith("🔍"):
            return
        
        print(f"\n[새 메시지] @{sender_name}: {message[:50]}...")
        
        try:
            # Agent 사용자/채팅방 매핑
            agent_user_id = await get_or_create_agent_user(db, user_id, sender_name)
            agent_room_id = await get_or_create_agent_room(db, channel_id, channel_name, agent_user_id)
            
            # ChatService로 메시지 처리
            chat_service = ChatService(db)
            
            # 1. 메시지 저장 + AI 응답 생성
            result = await chat_service.send_message(
                chat_room_id=agent_room_id,
                user_id=agent_user_id,
                content=message,
            )
            
            print(f"  [저장완료] room={agent_room_id}")
            
            # 2. AI 응답이 있으면 Mchat에 전송
            if result.get("assistant_message"):
                ai_response = result["assistant_message"]["content"]
                
                await client.create_post(
                    channel_id=channel_id,
                    message=ai_response,
                )
                print(f"  [AI 응답] {ai_response[:50]}...")
            
            # 3. 추출된 메모리 알림
            if result.get("extracted_memories"):
                count = len(result["extracted_memories"])
                print(f"  [메모리 추출] {count}개")
                
        except Exception as e:
            print(f"  [오류] {e}")
            import traceback
            traceback.print_exc()
    
    # WebSocket 연결 시작
    print("\n[WebSocket 연결 시작]")
    print("메시지를 기다리는 중... (Ctrl+C로 종료)")
    
    try:
        await client.connect_websocket()
    except KeyboardInterrupt:
        print("\n종료 중...")
        await client.stop()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
