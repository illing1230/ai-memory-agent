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
    """Mchat 채널에 매핑된 Agent 대화방 ID 반환 (없으면 생성)
    
    채널별로 공유 대화방을 생성하고, 채널의 모든 멤버를 추가합니다.
    """

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
        # 사용자가 대화방 멤버인지 확인
        cursor = await db.execute(
            "SELECT 1 FROM chat_room_members WHERE chat_room_id = ? AND user_id = ?",
            (row[0], agent_user_id)
        )
        if not await cursor.fetchone():
            # 멤버가 아니면 추가
            await db.execute(
                "INSERT INTO chat_room_members (id, chat_room_id, user_id, role) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), row[0], agent_user_id, "member")
            )
            await db.commit()
        return row[0]

    # 없으면 새 대화방 생성 (채널 공유 대화방)
    chat_repo = ChatRepository(db)
    room = await chat_repo.create_chat_room(
        name=f"Mchat: {mchat_channel_name or mchat_channel_id[:8]}",
        owner_id=agent_user_id,
        room_type="project",  # 채널 공유 대화방
        context_sources={
            "memory": {
                "include_this_room": True,
                "other_chat_rooms": [],
                "agent_instances": [],
            },
            "rag": {"collections": [], "filters": {}},
        },
    )

    await chat_repo.add_member(room["id"], agent_user_id, "owner")

    await db.execute(
        """INSERT INTO mchat_channel_mapping (id, mchat_channel_id, mchat_channel_name, agent_room_id)
           VALUES (?, ?, ?, ?)""",
        (str(uuid.uuid4()), mchat_channel_id, mchat_channel_name, room["id"])
    )
    await db.commit()

    _channel_cache[mchat_channel_id] = room["id"]
    logger.info(f"New channel mapping: {mchat_channel_name} -> {room['id']} (shared room)")
    return room["id"]


async def sync_channel_members_to_room(
    db: aiosqlite.Connection,
    mchat_client: MchatClient,
    mchat_channel_id: str,
    agent_room_id: str,
    bot_user_id: str | None,
):
    """Mchat 채널 멤버와 Agent 대화방 멤버를 동기화 (추가/제거)"""
    
    try:
        # 채널 멤버 목록 조회
        channel_members = await mchat_client.get_channel_members(mchat_channel_id)
        
        # 채널 멤버의 Agent 사용자 ID 집합
        channel_agent_user_ids = set()
        for member in channel_members:
            mchat_user_id = member["user_id"]
            mchat_username = member.get("username", f"user_{mchat_user_id[:8]}")
            
            # 봇 사용자 제외
            if bot_user_id and mchat_user_id == bot_user_id:
                continue
            
            # Agent 사용자 매핑 (없으면 생성)
            try:
                agent_user_id = await get_or_create_agent_user(db, mchat_client, mchat_user_id, mchat_username)
                channel_agent_user_ids.add(agent_user_id)
            except Exception as e:
                logger.warning(f"Failed to map user {mchat_username}: {e}")
        
        # 대화방 멤버 목록 조회
        cursor = await db.execute(
            "SELECT user_id FROM chat_room_members WHERE chat_room_id = ? AND role != 'owner'",
            (agent_room_id,)
        )
        room_member_rows = await cursor.fetchall()
        room_member_user_ids = {row["user_id"] for row in room_member_rows}
        
        # 1) 채널에 있지만 대화방에 없는 멤버 추가
        to_add = channel_agent_user_ids - room_member_user_ids
        for user_id in to_add:
            # 중복 체크 (현재 메시지 발신자가 이미 위에서 추가되었을 수 있음)
            cursor = await db.execute(
                "SELECT 1 FROM chat_room_members WHERE chat_room_id = ? AND user_id = ?",
                (agent_room_id, user_id)
            )
            if not await cursor.fetchone():
                await db.execute(
                    "INSERT INTO chat_room_members (id, chat_room_id, user_id, role) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), agent_room_id, user_id, "member")
                )
                logger.info(f"Added user={user_id[:8]} to room={agent_room_id[:8]}")
        
        # 2) 대화방에 있지만 채널에 없는 멤버 제거
        to_remove = room_member_user_ids - channel_agent_user_ids
        for user_id in to_remove:
            await db.execute(
                "DELETE FROM chat_room_members WHERE chat_room_id = ? AND user_id = ? AND role != 'owner'",
                (agent_room_id, user_id)
            )
            logger.info(f"Removed user={user_id[:8]} from room={agent_room_id[:8]}")
        
        if to_add or to_remove:
            await db.commit()
            logger.info(f"Synced channel members: +{len(to_add)} -{len(to_remove)}")
        
    except Exception as e:
        logger.error(f"Failed to sync channel members to room: {e}")


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


async def _should_sync(
    db: aiosqlite.Connection,
    user_id: str,
    bot_user_id: str,
    channel_id: str,
    message: str,
) -> bool:
    """메시지를 AI Memory Agent 대화방에 동기화할지 판단"""
    
    # 봇 자신의 메시지는 무시 (무한루프 방지 - 최우선)
    if user_id == bot_user_id:
        return False

    # 채널 동기화가 꺼져 있으면 무시
    if not await _is_channel_sync_enabled(db, channel_id):
        return False

    # 시스템 메시지 필터링 (사용자 추가/삭제 알림 등)
    system_patterns = [
        r"가 .+ (채널에|팀에) 추가함",
        r"가 .+에서 (나갔음|퇴장했음)",
        r"added to the (channel|team) by",
        r"removed from the (channel|team) by",
        r"has (added|removed) .+ to (the channel|the team)",
    ]
    for pattern in system_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            logger.info(f"Skipping system message: {message[:50]}")
            return False

    # 위 조건을 통과하면 항상 동기화
    return True


async def _should_respond_ai(
    message: str,
    channel_type: str,
) -> bool:
    """AI 응답을 생성할지 판단"""
    settings = get_settings()

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

        # 메시지 동기화 여부 판단 (봇 메시지 제외, 채널 동기화 활성화 확인, 시스템 메시지 필터링)
        if not await _should_sync(db, user_id, bot_user_id, channel_id, message):
            return

        _stats["messages_received"] += 1
        logger.info(f"Message from @{sender_name}: {message[:80]}")

        try:
            # "@ai 요약" 봇 커맨드 체크 (이건 항상 응답)
            summary_handled = await _handle_summary_command(
                client, db, message, channel_id, channel_name,
                post.get("id"), bot_user_id,
            )
            if summary_handled:
                _stats["messages_responded"] += 1
                return

            # AI 응답 여부 판단 (@ai 멘션, 봇 이름 멘션, DM)
            should_respond = await _should_respond_ai(message, channel_type)

            # Agent 사용자/대화방 매핑
            agent_user_id = await get_or_create_agent_user(db, client, user_id, sender_name)
            agent_room_id = await get_or_create_agent_room(db, channel_id, channel_name, agent_user_id)

            # 현재 사용자가 대화방 멤버인지 확인 후 추가
            cursor = await db.execute(
                "SELECT 1 FROM chat_room_members WHERE chat_room_id = ? AND user_id = ?",
                (agent_room_id, agent_user_id)
            )
            if not await cursor.fetchone():
                # 멤버가 아니면 추가
                await db.execute(
                    "INSERT INTO chat_room_members (id, chat_room_id, user_id, role) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), agent_room_id, agent_user_id, "member")
                )
                logger.info(f"Added {sender_name} to room={agent_room_id[:8]}")
                await db.commit()

            # 채널 멤버 동기화: 매 메시지마다 채널 멤버와 대화방 멤버를 완전히 동기화 (추가/제거)
            await sync_channel_members_to_room(db, client, channel_id, agent_room_id, bot_user_id)

            # ChatService로 메시지 처리
            chat_service = ChatService(db)

            if should_respond:
                # AI 응답 필요: @ai 멘션 추가
                chat_message = message if "@ai" in message.lower() else f"@ai {message}"

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
            else:
                # AI 응답 없음: 메시지만 저장 (사용자 메시지만 저장됨)
                result = await chat_service.send_message(
                    chat_room_id=agent_room_id,
                    user_id=agent_user_id,
                    content=message,
                )
                logger.info(f"Message saved to room={agent_room_id[:8]} (no AI response)")

        except Exception as e:
            _stats["errors"] += 1
            logger.error(f"Message handling error: {e}", exc_info=True)

    @client.on("channel_deleted")
    async def handle_channel_deleted(event):
        """채널 삭제 시 관련 대화방과 메모리 삭제"""
        data = event.get("data", {})
        channel_id = data.get("channel_id", "")
        channel_name = data.get("channel_name", "")

        logger.info(f"Channel deleted: {channel_name} ({channel_id})")

        try:
            # 매핑 정보 조회
            cursor = await db.execute(
                "SELECT agent_room_id FROM mchat_channel_mapping WHERE mchat_channel_id = ?",
                (channel_id,)
            )
            row = await cursor.fetchone()

            if not row:
                logger.info(f"No mapping found for channel {channel_id}")
                return

            agent_room_id = row["agent_room_id"]

            # 대화방 삭제 (ChatService를 통해 삭제하면 메모리도 자동으로 삭제됨)
            chat_repo = ChatRepository(db)
            try:
                # 대화방 owner 조회 (삭제 권한 확인용)
                cursor = await db.execute(
                    "SELECT owner_id FROM chat_rooms WHERE id = ?",
                    (agent_room_id,)
                )
                owner_row = await cursor.fetchone()

                if owner_row:
                    owner_id = owner_row["owner_id"]
                    logger.info(f"Deleting chat room {agent_room_id[:8]} (owner: {owner_id[:8]})")
                    
                    # ChatService의 delete_chat_room을 직접 호출 (대화방 + 메모리 삭제)
                    await db.execute("DELETE FROM chat_rooms WHERE id = ?", (agent_room_id,))
                    await db.commit()

                    # Vector DB에서 메모리 삭제
                    try:
                        from src.shared.vector_store import delete_vectors_by_filter
                        await delete_vectors_by_filter({"chat_room_id": agent_room_id})
                        logger.info(f"Vector DB data deleted for room {agent_room_id[:8]}")
                    except Exception as e:
                        logger.warning(f"Vector DB deletion failed: {e}")

                # 매핑 정보 삭제
                await db.execute(
                    "DELETE FROM mchat_channel_mapping WHERE mchat_channel_id = ?",
                    (channel_id,)
                )
                await db.commit()

                # 캐시에서 제거
                if channel_id in _channel_cache:
                    del _channel_cache[channel_id]

                logger.info(f"Channel {channel_name} mapping deleted successfully")

            except Exception as e:
                logger.error(f"Failed to delete chat room {agent_room_id}: {e}")

        except Exception as e:
            logger.error(f"Failed to handle channel_deleted event: {e}", exc_info=True)

    @client.on("channel_left")
    async def handle_channel_left(event):
        """봇이 채널에서 나갔을 때 (메모리 보존)"""
        data = event.get("data", {})
        channel_id = data.get("channel_id", "")
        channel_name = data.get("channel_name", "")
        logger.info(f"Bot left channel: {channel_name} ({channel_id})")
        # 채널을 자발적으로 떠난 경우 메모리는 보존
        logger.info(f"Memories preserved for channel {channel_name}")

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
