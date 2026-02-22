"""
Mchat 채널 대화 자동 요약 모듈

스케줄러가 주기적으로 채널 대화를 분석하여 요약을 포스팅하고,
팀 메모리로 저장한다.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

import aiosqlite

from src.config import get_settings
from src.mchat.client import MchatClient
from src.memory.pipeline import MemoryPipeline
from src.memory.repository import MemoryRepository
from src.shared.providers import get_llm_provider

logger = logging.getLogger("mchat.summary")

# 스케줄러 상태
_scheduler_task: asyncio.Task | None = None
_scheduler_running = False

# username 캐시
_username_cache: dict[str, str] = {}  # user_id -> username

SUMMARY_SYSTEM_PROMPT = """당신은 팀 채널 대화 요약 전문가입니다.
주어진 대화 내용을 분석하여 아래 형식으로 한국어 요약을 작성하세요.

출력 형식 (마크다운 없이 순수 텍스트):
**주요 논의 주제**
- (bullet points)

**결정 사항**
- (합의/결정 내용, 없으면 "없음")

**액션 아이템**
- (누가 무엇을, 없으면 "없음")

**주요 멘션**
- (사람, 프로젝트, 일정 등)

규칙:
- 봇/AI의 응답은 요약에서 제외하세요.
- 사용자들의 실제 논의 내용에 집중하세요.
- 간결하고 핵심적인 내용만 포함하세요.
- 대화가 거의 없거나 의미있는 논의가 없으면 "특별한 논의 사항 없음"으로 요약하세요.
"""

MERGE_SYSTEM_PROMPT = """당신은 여러 부분 요약을 하나의 통합 요약으로 합치는 전문가입니다.
중복을 제거하고 모든 고유한 정보를 포함하세요.

출력 형식:
**주요 논의 주제**
- (bullet points)

**결정 사항**
- (합의/결정 내용, 없으면 "없음")

**액션 아이템**
- (누가 무엇을, 없으면 "없음")

**주요 멘션**
- (사람, 프로젝트, 일정 등)
"""


async def get_posts_since(
    client: MchatClient,
    channel_id: str,
    since_ms: int,
) -> list[dict]:
    """Mattermost REST API로 시간 범위 내 포스트 조회"""
    all_posts = []
    page = 0
    per_page = 200

    while True:
        result = await client._request(
            "GET",
            f"/api/v4/channels/{channel_id}/posts",
            params={"since": since_ms, "page": page, "per_page": per_page},
        )

        posts = result.get("posts", {})
        order = result.get("order", [])

        if not order:
            break

        for post_id in order:
            post = posts.get(post_id)
            if post:
                all_posts.append(post)

        if len(order) < per_page:
            break
        page += 1

    # 시간순 정렬 (오래된 것 먼저)
    all_posts.sort(key=lambda p: p.get("create_at", 0))
    return all_posts


async def resolve_usernames(
    client: MchatClient,
    user_ids: set[str],
) -> dict[str, str]:
    """user_id -> username 변환 (캐시 사용)"""
    result = {}
    for uid in user_ids:
        if uid in _username_cache:
            result[uid] = _username_cache[uid]
        else:
            try:
                user_info = await client.get_user(uid)
                username = user_info.get("username", uid[:8])
                _username_cache[uid] = username
                result[uid] = username
            except Exception:
                result[uid] = uid[:8]
    return result


def format_posts_as_conversation(
    posts: list[dict],
    username_map: dict[str, str],
) -> str:
    """포스트 목록을 대화 텍스트로 변환"""
    lines = []
    for post in posts:
        user_id = post.get("user_id", "")
        username = username_map.get(user_id, user_id[:8])
        message = post.get("message", "").strip()
        if message:
            lines.append(f"@{username}: {message}")
    return "\n".join(lines)


def chunk_posts(posts: list[dict], chunk_size: int = 50) -> list[list[dict]]:
    """포스트를 청크로 분할"""
    return [posts[i:i + chunk_size] for i in range(0, len(posts), chunk_size)]


async def generate_summary(conversation_text: str) -> str:
    """LLM으로 단일 대화 텍스트 요약"""
    llm_provider = get_llm_provider()

    result = await llm_provider.generate(
        prompt=f"다음 팀 채널 대화를 요약해주세요:\n\n{conversation_text}",
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=1500,
    )
    return result.strip()


async def generate_chunked_summary(
    posts: list[dict],
    username_map: dict[str, str],
) -> str:
    """청크별 요약 -> 통합 요약"""
    chunks = chunk_posts(posts, chunk_size=50)

    if len(chunks) <= 1:
        text = format_posts_as_conversation(posts, username_map)
        return await generate_summary(text)

    # 각 청크 요약
    partial_summaries = []
    for i, chunk in enumerate(chunks):
        text = format_posts_as_conversation(chunk, username_map)
        summary = await generate_summary(text)
        partial_summaries.append(f"[파트 {i+1}]\n{summary}")
        logger.info(f"Chunk {i+1}/{len(chunks)} summarized")

    # 통합 요약
    llm_provider = get_llm_provider()
    merged = await llm_provider.generate(
        prompt=f"다음 부분 요약들을 하나로 통합해주세요:\n\n" + "\n\n".join(partial_summaries),
        system_prompt=MERGE_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=2000,
    )
    return merged.strip()


def format_summary_post(
    channel_name: str,
    period_start: datetime,
    period_end: datetime,
    message_count: int,
    participant_count: int,
    summary_content: str,
) -> str:
    """마크다운 포맷으로 요약 포스트 생성"""
    kst = timezone(timedelta(hours=9))
    start_str = period_start.astimezone(kst).strftime("%Y-%m-%d %H:%M")
    end_str = period_end.astimezone(kst).strftime("%Y-%m-%d %H:%M")

    return f"""## :memo: 채널 대화 요약
**채널**: {channel_name}
**기간**: {start_str} ~ {end_str}
**메시지 수**: {message_count}건 | **참여자**: {participant_count}명

---

{summary_content}

---
_이 요약은 AI Memory Agent에 의해 자동 생성되었습니다._"""


async def summarize_channel(
    client: MchatClient,
    db: aiosqlite.Connection,
    mchat_channel_id: str,
    channel_name: str,
    agent_room_id: str,
    since_ms: int,
    until_ms: int | None = None,
    bot_user_id: str | None = None,
) -> dict | None:
    """채널 1개 요약 실행 (전체 파이프라인)

    Returns:
        요약 결과 dict 또는 None (메시지 없음/실패)
    """
    if until_ms is None:
        until_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # 1. 포스트 조회
    posts = await get_posts_since(client, mchat_channel_id, since_ms)

    # 봇 자신 메시지 필터링
    if bot_user_id:
        posts = [p for p in posts if p.get("user_id") != bot_user_id]

    # 시간 범위 필터 (since API는 since 이후 변경된 글도 포함하므로 create_at으로 재필터)
    posts = [p for p in posts if since_ms <= p.get("create_at", 0) <= until_ms]

    if not posts:
        logger.info(f"No messages to summarize for {channel_name}")
        return None

    # 2. 사용자명 조회
    user_ids = {p.get("user_id", "") for p in posts if p.get("user_id")}
    username_map = await resolve_usernames(client, user_ids)

    # 3. LLM 요약 생성
    summary_content = await generate_chunked_summary(posts, username_map)

    # 4. 포맷팅
    period_start = datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc)
    period_end = datetime.fromtimestamp(until_ms / 1000, tz=timezone.utc)
    participant_count = len(user_ids)
    message_count = len(posts)

    formatted_post = format_summary_post(
        channel_name=channel_name,
        period_start=period_start,
        period_end=period_end,
        message_count=message_count,
        participant_count=participant_count,
        summary_content=summary_content,
    )

    # 5. 채널에 포스팅
    await client.create_post(
        channel_id=mchat_channel_id,
        message=formatted_post,
    )
    logger.info(f"Summary posted to {channel_name} ({message_count} msgs, {participant_count} users)")

    # 6. 메모리 저장
    memory_id = None
    try:
        memory_repo = MemoryRepository(db)
        pipeline = MemoryPipeline(memory_repo)

        # 요약 내용을 챗룸 메모리로 저장 (대화방 관련 검색에 활용)
        # agent_room_id에 연결하여 chatroom scope로 저장
        # 먼저 매핑된 user 찾기 (봇 계정의 agent user)
        cursor = await db.execute(
            "SELECT agent_user_id FROM mchat_user_mapping LIMIT 1"
        )
        row = await cursor.fetchone()
        owner_id = row[0] if row else None

        if owner_id:
            memory_content = f"[채널 요약: {channel_name}] {summary_content}"
            memory = await pipeline.save(
                content=memory_content,
                user_id=owner_id,
                room_id=agent_room_id,
                scope="chatroom",
                category="fact",
                importance="medium",
                skip_if_duplicate=True,
            )
            if memory:
                memory_id = memory["id"]
                logger.info(f"Summary memory saved: {memory_id}")
    except Exception as e:
        logger.warning(f"Failed to save summary memory: {e}")

    # 7. 요약 로그 기록
    log_id = str(uuid.uuid4())
    try:
        await db.execute(
            """INSERT INTO mchat_summary_log
               (id, mchat_channel_id, channel_name, period_start_ms, period_end_ms,
                message_count, participant_count, summary_content, memory_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (log_id, mchat_channel_id, channel_name, since_ms, until_ms,
             message_count, participant_count, summary_content, memory_id),
        )
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save summary log: {e}")

    return {
        "log_id": log_id,
        "channel_name": channel_name,
        "message_count": message_count,
        "participant_count": participant_count,
        "memory_id": memory_id,
    }


async def summary_scheduler_loop(
    client: MchatClient,
    db: aiosqlite.Connection,
    bot_user_id: str | None = None,
):
    """10분 간격 폴링, 주기 도래 시 요약 실행"""
    global _scheduler_running
    _scheduler_running = True
    logger.info("Summary scheduler started")

    while _scheduler_running:
        try:
            await asyncio.sleep(600)  # 10분 간격

            if not _scheduler_running:
                break

            # summary_enabled된 채널 조회
            cursor = await db.execute(
                """SELECT m.mchat_channel_id, m.mchat_channel_name, m.agent_room_id,
                          m.summary_interval_hours
                   FROM mchat_channel_mapping m
                   WHERE m.sync_enabled = 1 AND m.summary_enabled = 1"""
            )
            channels = await cursor.fetchall()

            for ch in channels:
                if not _scheduler_running:
                    break

                mchat_channel_id = ch["mchat_channel_id"]
                channel_name = ch["mchat_channel_name"] or mchat_channel_id[:8]
                agent_room_id = ch["agent_room_id"]
                interval_hours = ch["summary_interval_hours"] or 24

                # 마지막 요약 시점 조회
                cursor2 = await db.execute(
                    """SELECT MAX(period_end_ms) as last_end
                       FROM mchat_summary_log
                       WHERE mchat_channel_id = ?""",
                    (mchat_channel_id,)
                )
                row = await cursor2.fetchone()
                last_end_ms = row["last_end"] if row and row["last_end"] else None

                now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

                if last_end_ms:
                    elapsed_hours = (now_ms - last_end_ms) / (1000 * 60 * 60)
                    if elapsed_hours < interval_hours:
                        continue
                    since_ms = last_end_ms
                else:
                    # 첫 요약: 24시간 전부터
                    since_ms = now_ms - (24 * 60 * 60 * 1000)

                try:
                    result = await summarize_channel(
                        client=client,
                        db=db,
                        mchat_channel_id=mchat_channel_id,
                        channel_name=channel_name,
                        agent_room_id=agent_room_id,
                        since_ms=since_ms,
                        until_ms=now_ms,
                        bot_user_id=bot_user_id,
                    )
                    if result:
                        logger.info(f"Scheduled summary completed: {channel_name}")
                except Exception as e:
                    logger.error(f"Scheduled summary failed for {channel_name}: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Summary scheduler error: {e}", exc_info=True)

    _scheduler_running = False
    logger.info("Summary scheduler stopped")


async def trigger_summary_now(
    client: MchatClient,
    db: aiosqlite.Connection,
    mchat_channel_id: str,
    hours: int = 24,
    bot_user_id: str | None = None,
) -> dict | None:
    """수동 트리거로 즉시 요약 실행"""
    # 채널 정보 조회
    cursor = await db.execute(
        """SELECT mchat_channel_name, agent_room_id
           FROM mchat_channel_mapping
           WHERE mchat_channel_id = ?""",
        (mchat_channel_id,)
    )
    row = await cursor.fetchone()

    if not row:
        logger.warning(f"Channel not found: {mchat_channel_id}")
        return None

    channel_name = row["mchat_channel_name"] or mchat_channel_id[:8]
    agent_room_id = row["agent_room_id"]

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    since_ms = now_ms - (hours * 60 * 60 * 1000)

    return await summarize_channel(
        client=client,
        db=db,
        mchat_channel_id=mchat_channel_id,
        channel_name=channel_name,
        agent_room_id=agent_room_id,
        since_ms=since_ms,
        until_ms=now_ms,
        bot_user_id=bot_user_id,
    )


def start_summary_scheduler(
    client: MchatClient,
    db: aiosqlite.Connection,
    bot_user_id: str | None = None,
) -> asyncio.Task:
    """요약 스케줄러 시작"""
    global _scheduler_task
    _scheduler_task = asyncio.create_task(
        summary_scheduler_loop(client, db, bot_user_id)
    )
    return _scheduler_task


async def stop_summary_scheduler():
    """요약 스케줄러 종료"""
    global _scheduler_task, _scheduler_running
    _scheduler_running = False

    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None

    logger.info("Summary scheduler stopped")


def is_scheduler_running() -> bool:
    """스케줄러 실행 중 여부"""
    return _scheduler_running
