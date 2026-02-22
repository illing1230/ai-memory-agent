"""Webhook Service - 에이전트 이벤트 발행 및 재시도"""

import asyncio
import json
import logging
from typing import Any

import httpx
import aiosqlite

from src.agent.repository import AgentRepository

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BACKOFF_BASE = 2  # 지수 백오프 기본값 (초)


class WebhookService:
    """Webhook 이벤트 발행 서비스"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.repo = AgentRepository(db)

    async def fire_event(
        self,
        agent_instance_id: str,
        event_type: str,
        payload: dict[str, Any],
        webhook_url: str | None = None,
    ) -> dict | None:
        """이벤트 생성 후 webhook 전송 시도"""
        # 이벤트 저장
        event = await self.repo.create_webhook_event(
            agent_instance_id=agent_instance_id,
            event_type=event_type,
            payload=json.dumps(payload),
        )

        if not webhook_url:
            # webhook_url이 없으면 인스턴스에서 가져오기
            instance = await self.repo.get_agent_instance(agent_instance_id)
            webhook_url = instance.get("webhook_url") if instance else None

        if not webhook_url:
            return event

        # 비동기로 전송 시도 (백그라운드)
        asyncio.create_task(self._deliver(event["id"], webhook_url, payload))

        return event

    async def _deliver(
        self,
        event_id: str,
        webhook_url: str,
        payload: dict[str, Any],
    ) -> None:
        """Webhook 전송 (재시도 포함)"""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    status_code = response.status_code

                if 200 <= status_code < 300:
                    await self.repo.update_webhook_event(
                        event_id=event_id,
                        status="delivered",
                        attempts=attempt,
                        response_status=status_code,
                    )
                    logger.info(f"Webhook delivered: event={event_id}, status={status_code}")
                    return
                else:
                    await self.repo.update_webhook_event(
                        event_id=event_id,
                        status="failed",
                        attempts=attempt,
                        response_status=status_code,
                    )
                    logger.warning(
                        f"Webhook failed: event={event_id}, attempt={attempt}, status={status_code}"
                    )

            except Exception as e:
                await self.repo.update_webhook_event(
                    event_id=event_id,
                    status="failed",
                    attempts=attempt,
                )
                logger.warning(f"Webhook error: event={event_id}, attempt={attempt}, error={e}")

            # 지수 백오프
            if attempt < MAX_ATTEMPTS:
                delay = BACKOFF_BASE ** attempt
                await asyncio.sleep(delay)

        # 최대 시도 초과
        logger.error(f"Webhook exhausted: event={event_id}, max_attempts={MAX_ATTEMPTS}")
