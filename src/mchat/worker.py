"""
Mchat Worker - AI Memory Agent 연동

FastAPI lifespan에서 자동 시작되거나, 단독 실행 가능:
    python -m src.mchat.worker
"""

import asyncio
import logging
import re
import uuid

import aiosqlite

from src.mchat.client import MchatClient
from src.mchat.summary import (
    start_summary_scheduler,
    stop_summary_scheduler,
    trigger_summary_now,
)
from src.chat.service import ChatService
from src.chat.repository import ChatRepository
from src.user.repository import UserRepository
from src.config import get_settings
from src.shared.database import init_database, get_db_sync

logger = logging.getLogger("mchat.worker")

# 런타임 캐시
_channel_cache: dict[str, str] = {}  # mchat_channel_id -> agent_room_id

# 글로벌 상태 (router에서 참조)
_mchat_client: MchatClient | None = None
_mchat_bot_user_id: str | None = None
_health_check_task: asyncio.Task | None = None
_summary_scheduler_task: asyncio.Task | None = None
_worker_db: aiosqlite.Connection | None = None

# 메시지 통계
_stats = {
    "messages_received": 0,
    "messages_responded": 0,
    "memories_extracted": 0,
    "errors": 0,
}


def get_mchat_client() -> MchatClient | None:
    return _mchat_client


def get_mchat_bot_user_id() -> str | None:
    return _mchat_bot_user_id


def get_mchat_stats() -> dict:
    return dict(_stats)


async def get_or_create_agent_room(
    db: aiosqlite.Connection,
    mchat_channel_id: str,
    mchat_channel_name: str,
    agent_user_id: str,
) -> str:
    """Mchat 채널에 매핑된 Agent 대화방 ID 반환 (없으면 생성)"""

    # 캐시 확인
    if mchat_channel_id in _channel_cache:
        return _channel_cache[mchat_channel_id]

    # DB에서 매핑 조회
    cursor = await db.execute(
        "SELECT agent_room_id FROM mchat_channel_mapping WHERE mchat_channel_id = ?",
        (mchat_channel_id,)
    )
    row = await cursor.fetchone()

    if row:
        _channel_cache[mchat_channel_id] = row[0]
        return row[0]

    # 없으면 새 대화방 생성
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

    _channel_cache[mchat_channel_id] = room["id"]
    logger.info(f"New channel mapping: {mchat_channel_name} -> {room['id']}")
    return room["id"]


async def get_or_create_agent_user(
    db: aiosqlite.Connection,
    mchat_client: MchatClient,
    mchat_user_id: str,
    mchat_username: str,
) -> str:
    """Mchat 사용자에 매핑된 Agent 사용자 ID 반환 (없으면 이메일 기반 매칭 또는 생성)"""

    # DB에서 매핑 조회
    cursor = await db.execute(
        "SELECT agent_user_id FROM mchat_user_mapping WHERE mchat_user_id = ?",
        (mchat_user_id,)
    )
    row = await cursor.fetchone()

    if row:
        return row[0]

    user_repo = UserRepository(db)

    # Mattermost에서 사용자 이메일 조회 → 기존 Agent 계정 매칭
    mchat_email = None
    try:
        mchat_user_info = await mchat_client.get_user(mchat_user_id)
        mchat_email = mchat_user_info.get("email", "")
    except Exception as e:
        logger.warning(f"Failed to get Mattermost user info: {e}")

    user = None

    # 1) Mattermost 이메일로 기존 Agent 사용자 매칭
    if mchat_email:
        user = await user_repo.get_user_by_email(mchat_email)
        if user:
            logger.info(f"Email match: {mchat_email} -> existing agent user {user['id']}")

    # 2) 매칭 실패 시 새 사용자 생성
    if not user:
        fallback_email = f"{mchat_username.lstrip('@')}@mchat.local"
        user = await user_repo.get_user_by_email(fallback_email)
        if not user:
            display_name = mchat_username.lstrip("@")
            user = await user_repo.create_user(
                name=display_name,
                email=mchat_email or fallback_email,
            )
            logger.info(f"New agent user created: {display_name} ({mchat_email or fallback_email})")

    # 매핑 저장
    await db.execute(
        """INSERT OR IGNORE INTO mchat_user_mapping (id, mchat_user_id, mchat_username, agent_user_id)
           VALUES (?, ?, ?, ?)""",
        (str(uuid.uuid4()), mchat_user_id, mchat_username, user["id"])
    )
    await db.commit()

    logger.info(f"User mapping: {mchat_username} -> {user['id']}")
    return user["id"]


async def _is_channel_sync_enabled(db: aiosqlite.Connection, mchat_channel_id: str) -> bool:
    """채널 동기화가 활성화되어 있는지 확인"""
    cursor = await db.execute(
        "SELECT sync_enabled FROM mchat_channel_mapping WHERE mchat_channel_id = ?",
        (mchat_channel_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        # 매핑이 없으면 새 채널 → 기본적으로 활성화
        return True
    return bool(row["sync_enabled"])


async def _should_respond(
    db: aiosqlite.Connection,
    message: str,
    user_id: str,
    bot_user_id: str,
    channel_id: str,
    channel_type: str,
) -> bool:
    """메시지에 응답할지 판단"""
    settings = get_settings()

    # 봇 자신의 메시지는 무시 (무한루프 방지 - 최우선)
    if user_id == bot_user_id:
        return False

    # 채널 동기화가 꺼져 있으면 무시
    if not await _is_channel_sync_enabled(db, channel_id):
        return False

    # DM 채널에서는 항상 응답 (설정에 따라)
    if channel_type == "D" and settings.mchat_respond_to_all_dm:
        return True

    # @ai 멘션이 포함된 경우 응답
    if "@ai" in message.lower():
        return True

    # 봇 이름으로 멘션된 경우 응답
    bot_name = settings.mchat_bot_name
    if f"@{bot_name}" in message.lower():
        return True

    return False


async def _health_check_loop(client: MchatClient):
    """주기적 헬스 체크 (30초 간격)"""
    while True:
        try:
            await asyncio.sleep(30)
            ok = await client.ping()
            if ok:
                logger.debug("Health check: OK")
            else:
                logger.warning("Health check: Mattermost server unreachable")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Health check error: {e}")


async def _handle_summary_command(
    client: MchatClient,
    db: aiosqlite.Connection,
    message: str,
    channel_id: str,
    channel_name: str,
    post_id: str | None,
    bot_user_id: str | None,
) -> bool:
    """@ai 요약 봇 커맨드 처리. 처리했으면 True, 아니면 False 반환."""
    # "@ai 요약" 또는 "@ai 요약 48시간" 패턴 매칭
    match = re.search(r"@ai\s+요약(?:\s+(\d+)\s*시간)?", message, re.IGNORECASE)
    if not match:
        return False

    hours = int(match.group(1)) if match.group(1) else 24

    # 진행 중 리액션
    if post_id:
        try:
            await client.add_reaction(post_id, "hourglass_flowing_sand")
        except Exception:
            pass

    try:
        result = await trigger_summary_now(
            client=client,
            db=db,
            mchat_channel_id=channel_id,
            hours=hours,
            bot_user_id=bot_user_id,
        )

        if result:
            # 완료 리액션
            if post_id:
                try:
                    await client.add_reaction(post_id, "white_check_mark")
                except Exception:
                    pass
            logger.info(f"Manual summary completed for {channel_name} ({hours}h)")
        else:
            await client.create_post(
                channel_id=channel_id,
                message=f"최근 {hours}시간 동안 요약할 메시지가 없습니다.",
            )
    except Exception as e:
        logger.error(f"Manual summary failed: {e}", exc_info=True)
        await client.create_post(
            channel_id=channel_id,
            message=f"요약 생성 중 오류가 발생했습니다: {str(e)[:100]}",
        )

    return True


async def start_mchat_worker():
    """Mchat worker 시작 (lifespan에서 호출)"""
    global _mchat_client, _mchat_bot_user_id, _health_check_task, _worker_db

    settings = get_settings()

    logger.info("=" * 50)
    logger.info("Mchat Worker starting")
    logger.info(f"MCHAT_URL: {settings.mchat_url}")
    logger.info(f"MCHAT_SSL_VERIFY: {settings.mchat_ssl_verify}")
    logger.info(f"MCHAT_RESPOND_TO_ALL_DM: {settings.mchat_respond_to_all_dm}")

    # DB 연결
    db = await get_db_sync()

    # Mchat 클라이언트 생성
    client = MchatClient()
    _mchat_client = client

    # Bot 정보 조회
    try:
        me = await client.get_me()
        bot_user_id = me["id"]
        _mchat_bot_user_id = bot_user_id
        logger.info(f"Bot ID: {bot_user_id}, Username: {me['username']}")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        _mchat_client = None
        await db.close()
        return

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
        channel_type = data.get("channel_type", "")

        # 응답 여부 판단
        if not await _should_respond(db, message, user_id, bot_user_id, channel_id, channel_type):
            return

        _stats["messages_received"] += 1
        logger.info(f"Message from @{sender_name}: {message[:80]}")

        try:
            # "@ai 요약" 봇 커맨드 체크
            summary_handled = await _handle_summary_command(
                client, db, message, channel_id, channel_name,
                post.get("id"), bot_user_id,
            )
            if summary_handled:
                _stats["messages_responded"] += 1
                return

            # Agent 사용자/대화방 매핑
            agent_user_id = await get_or_create_agent_user(db, client, user_id, sender_name)
            agent_room_id = await get_or_create_agent_room(db, channel_id, channel_name, agent_user_id)

            # ChatService로 메시지 처리
            # _should_respond를 통과한 메시지는 항상 AI 응답 필요
            # ChatService는 @ai 멘션이 있어야 AI 응답을 생성하므로, 없으면 추가
            chat_message = message if "@ai" in message.lower() else f"@ai {message}"

            chat_service = ChatService(db)

            result = await chat_service.send_message(
                chat_room_id=agent_room_id,
                user_id=agent_user_id,
                content=chat_message,
            )

            logger.info(f"Message saved to room={agent_room_id[:8]}")

            # AI 응답 전송
            if result.get("assistant_message"):
                ai_response = result["assistant_message"]["content"]
                await client.create_post(
                    channel_id=channel_id,
                    message=ai_response,
                )
                _stats["messages_responded"] += 1
                logger.info(f"AI response sent ({len(ai_response)} chars)")

            # 추출된 메모리 로깅
            if result.get("extracted_memories"):
                count = len(result["extracted_memories"])
                _stats["memories_extracted"] += count
                logger.info(f"Extracted {count} memories")

        except Exception as e:
            _stats["errors"] += 1
            logger.error(f"Message handling error: {e}", exc_info=True)

    # Health check 백그라운드 태스크 시작
    _health_check_task = asyncio.create_task(_health_check_loop(client))
    _worker_db = db

    # 요약 스케줄러 시작
    if settings.mchat_summary_enabled:
        _summary_scheduler_task = start_summary_scheduler(client, db, bot_user_id)
        logger.info("Summary scheduler started")
    else:
        logger.info("Summary scheduler disabled (MCHAT_SUMMARY_ENABLED=false)")

    # WebSocket 연결 시작
    logger.info("Starting WebSocket connection...")
    try:
        await client.connect_websocket()
    except asyncio.CancelledError:
        logger.info("Worker cancelled, shutting down...")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        if _summary_scheduler_task:
            await stop_summary_scheduler()
        if _health_check_task:
            _health_check_task.cancel()
            try:
                await _health_check_task
            except asyncio.CancelledError:
                pass
        await client.stop()
        await db.close()
        logger.info("Worker shutdown complete")


async def stop_mchat_worker():
    """Mchat worker 정지"""
    global _mchat_client, _health_check_task, _summary_scheduler_task, _worker_db

    # 요약 스케줄러 종료
    if _summary_scheduler_task:
        await stop_summary_scheduler()
        _summary_scheduler_task = None

    if _health_check_task:
        _health_check_task.cancel()
        try:
            await _health_check_task
        except asyncio.CancelledError:
            pass
        _health_check_task = None

    if _mchat_client:
        logger.info("Stopping Mchat worker...")
        await _mchat_client.stop()
        _mchat_client = None

    if _worker_db:
        await _worker_db.close()
        _worker_db = None


# 단독 실행용
async def main():
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if not settings.mchat_enabled:
        logger.error("Mchat is disabled. Set MCHAT_ENABLED=true in .env")
        return

    if not settings.mchat_token:
        logger.error("MCHAT_TOKEN is not set in .env")
        return

    await init_database()
    await start_mchat_worker()


if __name__ == "__main__":
    asyncio.run(main())
