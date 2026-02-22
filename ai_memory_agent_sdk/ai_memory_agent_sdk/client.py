"""AI Memory Agent SDK - Async Client"""

from typing import Any

import httpx

from ai_memory_agent_sdk.exceptions import (
    AuthenticationError,
    APIError,
    ConnectionError,
)


class AIMemoryAgentClient:
    """AI Memory Agent 비동기 클라이언트 (httpx.AsyncClient 기반)"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        agent_id: str = "",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._client.aclose()

    def _handle_response(self, response: httpx.Response) -> Any:
        """HTTP 응답 처리 및 에러 변환"""
        if response.status_code in (401, 403):
            detail = ""
            try:
                detail = response.json().get("detail", "")
            except Exception:
                pass
            raise AuthenticationError(detail or "유효하지 않은 API Key입니다")
        if response.status_code >= 400:
            detail = ""
            try:
                detail = response.json().get("detail", "")
            except Exception:
                detail = response.text
            raise APIError(response.status_code, detail)
        return response.json()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """HTTP 요청 실행"""
        try:
            response = await self._client.request(method, path, **kwargs)
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {e}")
        except (AuthenticationError, APIError, ConnectionError):
            raise
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP 에러: {e}")

    # ==================== Agent Data ====================

    async def send_memory(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """메모리 데이터 전송"""
        return await self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/data",
            json={
                "data_type": "memory",
                "content": content,
                "metadata": metadata,
            },
        )

    async def send_message(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """메시지 데이터 전송"""
        return await self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/data",
            json={
                "data_type": "message",
                "content": content,
                "metadata": metadata,
            },
        )

    async def send_log(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """로그 데이터 전송"""
        return await self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/data",
            json={
                "data_type": "log",
                "content": content,
                "metadata": metadata,
            },
        )

    # ==================== Memory Search ====================

    async def search_memories(
        self,
        query: str,
        context_sources: dict | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """메모리 검색"""
        body: dict[str, Any] = {"query": query, "limit": limit}
        if context_sources:
            body["context_sources"] = context_sources
        return await self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/memories/search",
            json=body,
        )

    # ==================== Memory Sources ====================

    async def get_memory_sources(self) -> dict[str, Any]:
        """접근 가능한 메모리 소스 목록 조회"""
        return await self._request(
            "GET",
            f"/api/v1/agents/{self.agent_id}/memory-sources",
        )

    # ==================== Agent Data Query ====================

    async def get_agent_data(
        self,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """에이전트 데이터 조회"""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if data_type:
            params["data_type"] = data_type
        return await self._request(
            "GET",
            f"/api/v1/agents/{self.agent_id}/data",
            params=params,
        )

    # ==================== Health Check ====================

    async def health_check(self) -> dict[str, Any]:
        """서버 헬스 체크"""
        return await self._request("GET", "/health")
