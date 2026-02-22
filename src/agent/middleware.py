"""Agent API 감사 로그 미들웨어"""

import time
import logging
from typing import Any

import aiosqlite

from src.agent.repository import AgentRepository

logger = logging.getLogger(__name__)


class ApiLogRecorder:
    """API 호출 로그 기록 유틸리티

    미들웨어 대신 엔드포인트 내에서 직접 호출하여 사용.
    Agent API (X-API-Key 인증) 엔드포인트에서만 적용.
    """

    def __init__(self, db: aiosqlite.Connection):
        self.repo = AgentRepository(db)

    async def log(
        self,
        agent_instance_id: str,
        endpoint: str,
        method: str,
        status_code: int = 200,
        user_id: str | None = None,
        external_user_id: str | None = None,
        request_size: int | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        """API 호출 로그 기록"""
        try:
            await self.repo.create_api_log(
                agent_instance_id=agent_instance_id,
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                external_user_id=external_user_id,
                status_code=status_code,
                request_size=request_size,
                response_time_ms=response_time_ms,
            )
        except Exception as e:
            logger.warning(f"API 로그 기록 실패: {e}")
