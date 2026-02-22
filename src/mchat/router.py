"""Mchat 관리 API 라우터"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import aiosqlite

from src.shared.database import get_db
from src.shared.auth import get_current_admin_user
from src.mchat.worker import get_mchat_client, get_mchat_bot_user_id, get_mchat_stats
from src.mchat.summary import is_scheduler_running, trigger_summary_now

router = APIRouter()


# ==================== 기존 API ====================


@router.get("/status")
async def get_status(
    admin_id: str = Depends(get_current_admin_user),
):
    """Mchat 연결 상태"""
    client = get_mchat_client()

    if client is None:
        return {
            "status": "disabled",
            "connected": False,
            "bot_user_id": None,
            "base_url": None,
            "last_error": None,
            "stats": get_mchat_stats(),
        }

    return {
        "status": "connected" if client.connected else "disconnected",
        "connected": client.connected,
        "bot_user_id": get_mchat_bot_user_id(),
        "base_url": client.base_url,
        "last_error": client.last_error,
        "stats": get_mchat_stats(),
    }


@router.get("/channels")
async def get_channels(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """매핑된 채널 목록 (요약 설정 포함)"""
    cursor = await db.execute(
        """SELECT m.id, m.mchat_channel_id, m.mchat_channel_name, m.mchat_team_id,
                  m.agent_room_id, m.sync_enabled, m.summary_enabled,
                  m.summary_interval_hours, m.created_at,
                  r.name as room_name
           FROM mchat_channel_mapping m
           LEFT JOIN chat_rooms r ON m.agent_room_id = r.id
           ORDER BY m.created_at DESC"""
    )
    rows = await cursor.fetchall()

    return [
        {
            "id": row["id"],
            "mchat_channel_id": row["mchat_channel_id"],
            "mchat_channel_name": row["mchat_channel_name"],
            "mchat_team_id": row["mchat_team_id"],
            "agent_room_id": row["agent_room_id"],
            "agent_room_name": row["room_name"],
            "sync_enabled": bool(row["sync_enabled"]),
            "summary_enabled": bool(row["summary_enabled"]) if row["summary_enabled"] is not None else False,
            "summary_interval_hours": row["summary_interval_hours"] or 24,
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@router.put("/channels/{mapping_id}/sync")
async def toggle_channel_sync(
    mapping_id: str,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """채널 동기화 on/off 토글"""
    # 현재 상태 조회
    cursor = await db.execute(
        "SELECT sync_enabled FROM mchat_channel_mapping WHERE id = ?",
        (mapping_id,)
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="채널 매핑을 찾을 수 없습니다")

    new_value = 0 if row["sync_enabled"] else 1
    await db.execute(
        "UPDATE mchat_channel_mapping SET sync_enabled = ? WHERE id = ?",
        (new_value, mapping_id)
    )
    await db.commit()

    return {"sync_enabled": bool(new_value)}


@router.get("/users")
async def get_users(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """매핑된 사용자 목록"""
    cursor = await db.execute(
        """SELECT m.id, m.mchat_user_id, m.mchat_username,
                  m.agent_user_id, m.created_at,
                  u.name as agent_user_name, u.email as agent_user_email
           FROM mchat_user_mapping m
           LEFT JOIN users u ON m.agent_user_id = u.id
           ORDER BY m.created_at DESC"""
    )
    rows = await cursor.fetchall()

    return [
        {
            "id": row["id"],
            "mchat_user_id": row["mchat_user_id"],
            "mchat_username": row["mchat_username"],
            "agent_user_id": row["agent_user_id"],
            "agent_user_name": row["agent_user_name"],
            "agent_user_email": row["agent_user_email"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


# ==================== 요약 관리 API ====================


@router.get("/summary/status")
async def get_summary_status(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """스케줄러 상태 + 통계"""
    # 총 요약 수
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM mchat_summary_log")
    row = await cursor.fetchone()
    total_summaries = row["cnt"] if row else 0

    # 최근 24시간 요약 수
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM mchat_summary_log
           WHERE created_at >= datetime('now', '-1 day')"""
    )
    row = await cursor.fetchone()
    recent_summaries = row["cnt"] if row else 0

    # 요약 활성화된 채널 수
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM mchat_channel_mapping WHERE summary_enabled = 1"
    )
    row = await cursor.fetchone()
    enabled_channels = row["cnt"] if row else 0

    return {
        "scheduler_running": is_scheduler_running(),
        "enabled_channels": enabled_channels,
        "total_summaries": total_summaries,
        "recent_summaries_24h": recent_summaries,
    }


@router.get("/summary/logs")
async def get_summary_logs(
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """요약 실행 이력"""
    cursor = await db.execute(
        """SELECT id, mchat_channel_id, channel_name, period_start_ms, period_end_ms,
                  message_count, participant_count, summary_content, memory_id, created_at
           FROM mchat_summary_log
           ORDER BY created_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    )
    rows = await cursor.fetchall()

    return [
        {
            "id": row["id"],
            "mchat_channel_id": row["mchat_channel_id"],
            "channel_name": row["channel_name"],
            "period_start_ms": row["period_start_ms"],
            "period_end_ms": row["period_end_ms"],
            "message_count": row["message_count"],
            "participant_count": row["participant_count"],
            "summary_content": row["summary_content"],
            "memory_id": row["memory_id"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@router.post("/summary/trigger/{channel_id}")
async def trigger_channel_summary(
    channel_id: str,
    background_tasks: BackgroundTasks,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
    hours: int = 24,
):
    """수동 요약 트리거"""
    client = get_mchat_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Mchat이 연결되지 않았습니다")

    # 채널 매핑 확인 (mchat_channel_id로 조회)
    cursor = await db.execute(
        "SELECT mchat_channel_id FROM mchat_channel_mapping WHERE mchat_channel_id = ?",
        (channel_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")

    bot_user_id = get_mchat_bot_user_id()

    # 비동기 백그라운드로 실행
    async def run_summary():
        try:
            await trigger_summary_now(
                client=client,
                db=db,
                mchat_channel_id=channel_id,
                hours=hours,
                bot_user_id=bot_user_id,
            )
        except Exception as e:
            import logging
            logging.getLogger("mchat.summary").error(f"API trigger failed: {e}")

    background_tasks.add_task(run_summary)

    return {"message": f"요약 트리거됨 (최근 {hours}시간)", "channel_id": channel_id}


class SummaryToggleRequest(BaseModel):
    enabled: bool


@router.put("/channels/{mapping_id}/summary")
async def toggle_channel_summary(
    mapping_id: str,
    request: SummaryToggleRequest,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """채널 요약 on/off 설정"""
    cursor = await db.execute(
        "SELECT id FROM mchat_channel_mapping WHERE id = ?",
        (mapping_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="채널 매핑을 찾을 수 없습니다")

    await db.execute(
        "UPDATE mchat_channel_mapping SET summary_enabled = ? WHERE id = ?",
        (1 if request.enabled else 0, mapping_id),
    )
    await db.commit()

    return {"summary_enabled": request.enabled}


class SummaryIntervalRequest(BaseModel):
    interval_hours: int


@router.put("/channels/{mapping_id}/summary-interval")
async def set_channel_summary_interval(
    mapping_id: str,
    request: SummaryIntervalRequest,
    admin_id: str = Depends(get_current_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """요약 주기 설정"""
    if request.interval_hours < 1:
        raise HTTPException(status_code=400, detail="요약 주기는 최소 1시간이어야 합니다")

    cursor = await db.execute(
        "SELECT id FROM mchat_channel_mapping WHERE id = ?",
        (mapping_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="채널 매핑을 찾을 수 없습니다")

    await db.execute(
        "UPDATE mchat_channel_mapping SET summary_interval_hours = ? WHERE id = ?",
        (request.interval_hours, mapping_id),
    )
    await db.commit()

    return {"summary_interval_hours": request.interval_hours}
