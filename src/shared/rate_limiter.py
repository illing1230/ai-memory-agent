"""인메모리 슬라이딩 윈도우 Rate Limiter"""

import time
from collections import defaultdict
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SlidingWindowRateLimiter:
    """인메모리 슬라이딩 윈도우 카운터 기반 Rate Limiter"""

    def __init__(self):
        # key -> list of timestamps
        self._windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """요청이 허용되는지 확인"""
        now = time.time()
        window_start = now - window_seconds

        # 윈도우 밖의 오래된 타임스탬프 제거
        timestamps = self._windows[key]
        self._windows[key] = [t for t in timestamps if t > window_start]

        if len(self._windows[key]) >= limit:
            return False

        self._windows[key].append(now)
        return True

    def get_retry_after(self, key: str, window_seconds: int = 60) -> int:
        """Retry-After 값 계산 (초)"""
        if not self._windows[key]:
            return 0
        oldest = min(self._windows[key])
        retry_after = int(oldest + window_seconds - time.time()) + 1
        return max(1, retry_after)


# 전역 인스턴스
_rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """X-API-Key 기반 Rate Limiting 미들웨어

    Agent API 엔드포인트 (/api/v1/agents/) 에만 적용.
    rate_limit_per_minute는 기본 60으로, 에이전트 인스턴스별로 설정 가능.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Agent API 경로에만 적용
        path = request.url.path
        if not path.startswith("/api/v1/agents/"):
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return await call_next(request)

        # 기본 rate limit (에이전트 인스턴스별 설정은 DB 조회 필요 → 기본값 사용)
        default_limit = 60

        if not _rate_limiter.is_allowed(api_key, default_limit):
            retry_after = _rate_limiter.get_retry_after(api_key)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Too many requests."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
