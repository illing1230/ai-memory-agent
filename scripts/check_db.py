"""DB 상태 확인 스크립트"""

import asyncio
import aiosqlite
from src.config import get_settings


async def check_db():
    settings = get_settings()
    db = await aiosqlite.connect(settings.sqlite_db_path)
    db.row_factory = aiosqlite.Row
    
    print("=" * 50)
    print("DB 상태 확인")
    print("=" * 50)
    
    # 1. 사용자 목록
    print("\n[사용자 목록]")
    cursor = await db.execute("SELECT id, name, email FROM users")
    rows = await cursor.fetchall()
    for row in rows:
        print(f"  - {row['name']} ({row['email']}) | id: {row['id'][:8]}...")
    
    # 2. 채팅방 목록
    print("\n[채팅방 목록]")
    cursor = await db.execute("SELECT id, name, room_type, owner_id FROM chat_rooms")
    rows = await cursor.fetchall()
    for row in rows:
        print(f"  - {row['name']} ({row['room_type']}) | id: {row['id'][:8]}...")
    
    # 3. 채팅방 멤버
    print("\n[채팅방 멤버]")
    cursor = await db.execute("""
        SELECT crm.chat_room_id, crm.user_id, crm.role, u.name as user_name, cr.name as room_name
        FROM chat_room_members crm
        JOIN users u ON crm.user_id = u.id
        JOIN chat_rooms cr ON crm.chat_room_id = cr.id
    """)
    rows = await cursor.fetchall()
    for row in rows:
        print(f"  - {row['room_name']} | {row['user_name']} ({row['role']})")
    
    # 4. Mchat 매핑
    print("\n[Mchat 사용자 매핑]")
    try:
        cursor = await db.execute("SELECT mchat_user_id, mchat_username, agent_user_id FROM mchat_user_mapping")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"  - {row['mchat_username']} | mchat: {row['mchat_user_id'][:8]}... → agent: {row['agent_user_id'][:8]}...")
    except:
        print("  (테이블 없음)")
    
    print("\n[Mchat 채널 매핑]")
    try:
        cursor = await db.execute("SELECT mchat_channel_id, mchat_channel_name, agent_room_id FROM mchat_channel_mapping")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"  - {row['mchat_channel_name']} | mchat: {row['mchat_channel_id'][:8]}... → agent: {row['agent_room_id'][:8]}...")
    except:
        print("  (테이블 없음)")
    
    # 5. 메시지 수
    print("\n[메시지 통계]")
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM chat_messages")
    row = await cursor.fetchone()
    print(f"  총 메시지: {row['cnt']}개")
    
    # 6. 메모리 수
    print("\n[메모리 통계]")
    cursor = await db.execute("SELECT scope, COUNT(*) as cnt FROM memories GROUP BY scope")
    rows = await cursor.fetchall()
    for row in rows:
        print(f"  - {row['scope']}: {row['cnt']}개")
    
    await db.close()


if __name__ == "__main__":
    asyncio.run(check_db())
