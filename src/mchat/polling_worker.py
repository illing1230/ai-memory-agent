"""
Mchat Polling Worker - WebSocket 없이 REST API만 사용

WebSocket 대신 주기적으로 새 메시지를 폴링하는 방식

실행:
    python -m src.mchat.polling_worker
"""

import asyncio
import logging
import uuid
from datetime import datetime

import aiosqlite

from src.mchat.client import MchatClient
from src.chat.service import ChatService
from src.chat.repository import ChatRepository
from src.user.repository import UserRepository
from src.config import get_settings
from src.shared.database import init_database, get_db_sync

logger = logging.getLogger("mchat.polling")

# 설정
POLL_INTERVAL = 2  # 초 (폴링 주기)
CHANNELS_TO_WATCH: list[str] = []  # 빈 리스트면 전체 채널 모니터링

# 상태 저장
last_post_times: dict[str, int] = {}  # channel_id -> last_post_create_at


async def get_or_create_agent_user(db: aiosqlite.Connection, mchat_user_id: str, mchat_username: str) -> str:
    """Mchat 사용자 -> Agent 사용자 매핑"""
    cursor = await db.execute(
        "SELECT agent_user_id FROM mchat_user_mapping WHERE mchat_user_id = ?",
        (mchat_user_id,)
    )
    row = await cursor.fetchone()

    if row:
        return row[0]

    user_repo = UserRepository(db)
    email = f"{mchat_username}@mchat.local"
    user = await user_repo.get_user_by_email(email)

    if not user:
        user = await user_repo.create_user(name=mchat_username, email=email)

    await db.execute(
        """INSERT OR IGNORE INTO mchat_user_mapping (id, mchat_user_id, mchat_username, agent_user_id)
           VALUES (?, ?, ?, ?)""",
        (str(uuid.uuid4()), mchat_user_id, mchat_username, user["id"])
    )
    await db.commit()

    return user["id"]


async def get_or_create_agent_room(db: aiosqlite.Connection, mchat_channel_id: str, mchat_channel_name: str, agent_user_id: str) -> str:
    """Mchat 채널 -> Agent 대화방 매핑"""
    cursor = await db.execute(
        "SELECT agent_room_id FROM mchat_channel_mapping WHERE mchat_channel_id = ?",
        (mchat_channel_id,)
    )
    row = await cursor.fetchone()

    if row:
        return row[0]

    chat_repo = ChatRepository(db)
    room = await chat_repo.create_chat_room(
        name=f"Mchat: {mchat_channel_name or mchat_channel_id[:8]}",
        owner_id=agent_user_id,
        room_type="personal",
    )

    await chat_repo.add_member(room["id"], agent_user_id, "owner")

    await db.execute(
        """INSERT INTO mchat_channel_mapping (id, mchat_channel_id, mchat_channel_name, agent_room_id)
           VALUES (?, ?, ?, ?)""",
        (str(uuid.uuid4()), mchat_channel_id, mchat_channel_name, room["id"])
    )
    await db.commit()

    return room["id"]


async def process_message(
    db: aiosqlite.Connection,
    client: MchatClient,
    post: dict,
    channel_name: str,
    bot_user_id: str,
):
    """메시지 처리"""
    message = post.get("message", "")
    channel_id = post.get("channel_id", "")
    user_id = post.get("user_id", "")

    # 봇 자신의 메시지 무시 (무한루프 방지 - 최우선)
    if user_id == bot_user_id:
        return

    # 사용자 이름 조회
    try:
        user_info = await client.get_user(user_id)
        sender_name = user_info.get("username", "unknown")
    except Exception:
        sender_name = "unknown"

    logger.info(f"Message from @{sender_name}: {message[:50]}")

    try:
        # 매핑
        agent_user_id = await get_or_create_agent_user(db, user_id, sender_name)
        agent_room_id = await get_or_create_agent_room(db, channel_id, channel_name, agent_user_id)

        # ChatService로 처리
        chat_service = ChatService(db)
        result = await chat_service.send_message(
            chat_room_id=agent_room_id,
            user_id=agent_user_id,
            content=message,
        )

        logger.info(f"Message saved to room={agent_room_id[:8]}")

        # AI 응답 전송
        if result.get("assistant_message"):
            ai_response = result["assistant_message"]["content"]
            await client.create_post(channel_id=channel_id, message=ai_response)
            logger.info(f"AI response sent ({len(ai_response)} chars)")

        # 메모리 추출 로깅
        if result.get("extracted_memories"):
            count = len(result["extracted_memories"])
            logger.info(f"Extracted {count} memories")

    except Exception as e:
        logger.error(f"Message processing error: {e}", exc_info=True)


async def poll_channel(
    client: MchatClient,
    db: aiosqlite.Connection,
    channel_id: str,
    channel_name: str,
    bot_user_id: str,
):
    """채널의 새 메시지 폴링"""
    global last_post_times

    try:
        posts_data = await client.get_posts_for_channel(channel_id, page=0, per_page=10)

        if not posts_data or "posts" not in posts_data:
            return

        posts = posts_data.get("posts", {})
        order = posts_data.get("order", [])

        if not order:
            return

        last_time = last_post_times.get(channel_id, 0)

        new_posts = []
        for post_id in order:
            post = posts.get(post_id, {})
            create_at = post.get("create_at", 0)

            if create_at > last_time:
                new_posts.append(post)

        # 오래된 것부터 처리
        new_posts.sort(key=lambda x: x.get("create_at", 0))

        for post in new_posts:
            await process_message(db, client, post, channel_name, bot_user_id)
            last_post_times[channel_id] = post.get("create_at", 0)

    except Exception as e:
        logger.error(f"Polling error for {channel_id[:8]}: {e}")


async def main():
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    logger.info("=" * 50)
    logger.info("Mchat Polling Worker (REST API only)")
    logger.info(f"MCHAT_URL: {settings.mchat_url}")
    logger.info(f"POLL_INTERVAL: {POLL_INTERVAL}s")

    if not settings.mchat_enabled:
        logger.error("Mchat is disabled. Set MCHAT_ENABLED=true in .env")
        return

    if not settings.mchat_token:
        logger.error("MCHAT_TOKEN is not set in .env")
        return

    # DB 초기화
    await init_database()
    db = await get_db_sync()

    # Mchat 클라이언트
    client = MchatClient()

    # Bot 정보
    me = await client.get_me()
    bot_user_id = me["id"]
    logger.info(f"Bot ID: {bot_user_id}, Username: {me['username']}")

    # 모니터링할 채널 목록
    channels_to_poll = []

    if CHANNELS_TO_WATCH:
        for ch_id in CHANNELS_TO_WATCH:
            try:
                ch = await client.get_channel(ch_id)
                channels_to_poll.append({"id": ch_id, "name": ch.get("display_name", ch_id)})
            except Exception:
                logger.warning(f"Cannot access channel: {ch_id}")
    else:
        logger.info("Discovering channels...")
        teams = await client.get_teams()
        for team in teams:
            channels = await client.get_channels_for_team(team["id"])
            for ch in channels:
                channels_to_poll.append({
                    "id": ch["id"],
                    "name": ch.get("display_name") or ch.get("name", ch["id"][:8]),
                })
        logger.info(f"Monitoring {len(channels_to_poll)} channels")

    # 초기 last_post_times 설정 (현재 시간으로)
    current_time = int(datetime.now().timestamp() * 1000)
    for ch in channels_to_poll:
        last_post_times[ch["id"]] = current_time

    logger.info(f"Polling started ({POLL_INTERVAL}s interval)")

    try:
        while True:
            for ch in channels_to_poll:
                await poll_channel(client, db, ch["id"], ch["name"], bot_user_id)

            await asyncio.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
