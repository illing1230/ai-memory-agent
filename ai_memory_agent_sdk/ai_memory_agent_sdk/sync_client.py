"""AI Memory Agent SDK - Sync Client"""

from typing import Any

import httpx

from ai_memory_agent_sdk.exceptions import (
    AuthenticationError,
    APIError,
    ConnectionError,
)


class AIMemoryAgentSyncClient:
    """AI Memory Agent 동기 클라이언트 (httpx.Client 기반)"""

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
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._client.close()

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

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """HTTP 요청 실행"""
        try:
            response = self._client.request(method, path, **kwargs)
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {e}")
        except (AuthenticationError, APIError, ConnectionError):
            raise
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP 에러: {e}")

    # ==================== Agent Data ====================

    def send_memory(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """메모리 데이터 전송"""
        return self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/data",
            json={
                "data_type": "memory",
                "content": content,
                "metadata": metadata,
            },
        )

    def send_message(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """메시지 데이터 전송"""
        return self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/data",
            json={
                "data_type": "message",
                "content": content,
                "metadata": metadata,
            },
        )

    def send_log(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """로그 데이터 전송"""
        return self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/data",
            json={
                "data_type": "log",
                "content": content,
                "metadata": metadata,
            },
        )

    # ==================== Memory Search ====================

    def search_memories(
        self,
        query: str,
        context_sources: dict | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """메모리 검색"""
        body: dict[str, Any] = {"query": query, "limit": limit}
        if context_sources:
            body["context_sources"] = context_sources
        return self._request(
            "POST",
            f"/api/v1/agents/{self.agent_id}/memories/search",
            json=body,
        )

    # ==================== Memory Sources ====================

    def get_memory_sources(self) -> dict[str, Any]:
        """접근 가능한 메모리 소스 목록 조회"""
        return self._request(
            "GET",
            f"/api/v1/agents/{self.agent_id}/memory-sources",
        )

    # ==================== Agent Data Query ====================

    def get_agent_data(
        self,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """에이전트 데이터 조회"""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if data_type:
            params["data_type"] = data_type
        return self._request(
            "GET",
            f"/api/v1/agents/{self.agent_id}/data",
            params=params,
        )

    # ==================== Health Check ====================

    def health_check(self) -> dict[str, Any]:
        """서버 헬스 체크"""
        return self._request("GET", "/health")
