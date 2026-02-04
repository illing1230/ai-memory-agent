"""AI Memory Agent SDK 클라이언트"""

import httpx
from typing import Any, Literal

from ai_memory_agent_sdk.exceptions import (
    AuthenticationError,
    APIError,
    ConnectionError,
    ValidationError,
)


class AIMemoryAgentClient:
    """AI Memory Agent SDK 클라이언트
    
    외부 Agent에서 AI Memory Agent 시스템으로 데이터를 전송하기 위한 클라이언트
    
    Args:
        api_key: Agent Instance API Key
        base_url: AI Memory Agent API 기본 URL (기본값: http://localhost:8000)
        timeout: 요청 타임아웃 (초)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        agent_id: str = "test",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.agent_id = agent_id
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=timeout,
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """클라이언트 리소스 정리"""
        await self._client.aclose()
    
    def _handle_error(self, response: httpx.Response):
        """API 오류 처리"""
        if response.status_code == 401:
            raise AuthenticationError("유효하지 않은 API Key입니다")
        elif response.status_code == 403:
            raise AuthenticationError("접근 권한이 없습니다")
        elif response.status_code == 422:
            raise ValidationError("데이터 검증 실패")
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("detail", "알 수 없는 오류")
            except Exception:
                message = response.text or "알 수 없는 오류"
            raise APIError(message, status_code=response.status_code)
    
    async def send_memory(
        self,
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """메모리 데이터 전송
        
        Args:
            content: 메모리 내용
            external_user_id: 외부 시스템 사용자 ID (선택사항)
            metadata: 추가 메타데이터 (선택사항)
        
        Returns:
            전송된 데이터 정보
        
        Raises:
            AuthenticationError: 인증 실패
            APIError: API 오류
            ConnectionError: 연결 오류
        """
        return await self._send_data(
            data_type="memory",
            content=content,
            external_user_id=external_user_id,
            metadata=metadata,
        )
    
    async def send_message(
        self,
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """메시지 데이터 전송
        
        Args:
            content: 메시지 내용
            external_user_id: 외부 시스템 사용자 ID (선택사항)
            metadata: 추가 메타데이터 (선택사항)
        
        Returns:
            전송된 데이터 정보
        
        Raises:
            AuthenticationError: 인증 실패
            APIError: API 오류
            ConnectionError: 연결 오류
        """
        return await self._send_data(
            data_type="message",
            content=content,
            external_user_id=external_user_id,
            metadata=metadata,
        )
    
    async def send_log(
        self,
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """로그 데이터 전송
        
        Args:
            content: 로그 내용
            external_user_id: 외부 시스템 사용자 ID (선택사항)
            metadata: 추가 메타데이터 (선택사항)
        
        Returns:
            전송된 데이터 정보
        
        Raises:
            AuthenticationError: 인증 실패
            APIError: API 오류
            ConnectionError: 연결 오류
        """
        return await self._send_data(
            data_type="log",
            content=content,
            external_user_id=external_user_id,
            metadata=metadata,
        )
    
    async def _send_data(
        self,
        data_type: Literal["memory", "message", "log"],
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """데이터 전송 (내부 메서드)"""
        if not content or not content.strip():
            raise ValidationError("content는 비어있을 수 없습니다")
                
        payload = {
            "data_type": data_type,
            "content": content,
            "external_user_id": external_user_id,
            "metadata": metadata,
        }
                
        try:
            response = await self._client.post(
                f"/api/v1/agents/{self.agent_id}/data",
                json=payload,
            )
            
            if response.status_code >= 400:
                self._handle_error(response)
            
            return response.json()
        
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP 오류: {str(e)}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")
    
    async def health_check(self) -> bool:
        """서버 헬스 체크

        Returns:
            서버가 정상이면 True, 아니면 False
        """
        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def get_memory_sources(
        self,
        external_user_id: str | None = None,
    ) -> dict[str, Any]:
        """접근 가능한 메모리 소스 목록 조회"""
        params = {}
        if external_user_id:
            params["external_user_id"] = external_user_id
        try:
            response = await self._client.get(
                f"/api/v1/agents/{self.agent_id}/memory-sources",
                params=params,
            )
            if response.status_code >= 400:
                self._handle_error(response)
            return response.json()
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")

    async def search_memories(
        self,
        query: str,
        context_sources: dict[str, Any] | None = None,
        limit: int = 10,
        external_user_id: str | None = None,
    ) -> dict[str, Any]:
        """메모리 검색"""
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if context_sources:
            payload["context_sources"] = context_sources
        if external_user_id:
            payload["external_user_id"] = external_user_id
        try:
            response = await self._client.post(
                f"/api/v1/agents/{self.agent_id}/memories/search",
                json=payload,
            )
            if response.status_code >= 400:
                self._handle_error(response)
            return response.json()
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")

    async def get_data(
        self,
        data_type: str | None = None,
        external_user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """에이전트 데이터 조회"""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if data_type:
            params["data_type"] = data_type
        if external_user_id:
            params["external_user_id"] = external_user_id
        try:
            response = await self._client.get(
                f"/api/v1/agents/{self.agent_id}/data",
                params=params,
            )
            if response.status_code >= 400:
                self._handle_error(response)
            return response.json()
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")


# 동기 클라이언트 (선택사항)
class AIMemoryAgentSyncClient:
    """AI Memory Agent SDK 동기 클라이언트
    
    외부 Agent에서 AI Memory Agent 시스템으로 데이터를 전송하기 위한 동기 클라이언트
    
    Args:
        api_key: Agent Instance API Key
        base_url: AI Memory Agent API 기본 URL (기본값: http://localhost:8000)
        timeout: 요청 타임아웃 (초)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        agent_id: str = "test",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.agent_id = agent_id
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=timeout,
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """클라이언트 리소스 정리"""
        self._client.close()
    
    def _handle_error(self, response: httpx.Response):
        """API 오류 처리"""
        if response.status_code == 401:
            raise AuthenticationError("유효하지 않은 API Key입니다")
        elif response.status_code == 403:
            raise AuthenticationError("접근 권한이 없습니다")
        elif response.status_code == 422:
            raise ValidationError("데이터 검증 실패")
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("detail", "알 수 없는 오류")
            except Exception:
                message = response.text or "알 수 없는 오류"
            raise APIError(message, status_code=response.status_code)
    
    def send_memory(
        self,
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """메모리 데이터 전송 (동기)"""
        return self._send_data(
            data_type="memory",
            content=content,
            external_user_id=external_user_id,
            metadata=metadata,
        )
    
    def send_message(
        self,
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """메시지 데이터 전송 (동기)"""
        return self._send_data(
            data_type="message",
            content=content,
            external_user_id=external_user_id,
            metadata=metadata,
        )
    
    def send_log(
        self,
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """로그 데이터 전송 (동기)"""
        return self._send_data(
            data_type="log",
            content=content,
            external_user_id=external_user_id,
            metadata=metadata,
        )
    
    def _send_data(
        self,
        data_type: Literal["memory", "message", "log"],
        content: str,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """데이터 전송 (내부 메서드, 동기)"""
        if not content or not content.strip():
            raise ValidationError("content는 비어있을 수 없습니다")
                
        payload = {
            "data_type": data_type,
            "content": content,
            "external_user_id": external_user_id,
            "metadata": metadata,
        }
                
        try:
            response = self._client.post(
                f"/api/v1/agents/{self.agent_id}/data",
                json=payload,
            )
            
            if response.status_code >= 400:
                self._handle_error(response)
            
            return response.json()
        
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP 오류: {str(e)}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")
    
    def health_check(self) -> bool:
        """서버 헬스 체크 (동기)"""
        try:
            response = self._client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    def get_memory_sources(
        self,
        external_user_id: str | None = None,
    ) -> dict[str, Any]:
        """접근 가능한 메모리 소스 목록 조회 (동기)"""
        params = {}
        if external_user_id:
            params["external_user_id"] = external_user_id
        try:
            response = self._client.get(
                f"/api/v1/agents/{self.agent_id}/memory-sources",
                params=params,
            )
            if response.status_code >= 400:
                self._handle_error(response)
            return response.json()
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")

    def search_memories(
        self,
        query: str,
        context_sources: dict[str, Any] | None = None,
        limit: int = 10,
        external_user_id: str | None = None,
    ) -> dict[str, Any]:
        """메모리 검색 (동기)"""
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if context_sources:
            payload["context_sources"] = context_sources
        if external_user_id:
            payload["external_user_id"] = external_user_id
        try:
            response = self._client.post(
                f"/api/v1/agents/{self.agent_id}/memories/search",
                json=payload,
            )
            if response.status_code >= 400:
                self._handle_error(response)
            return response.json()
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")

    def get_data(
        self,
        data_type: str | None = None,
        external_user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """에이전트 데이터 조회 (동기)"""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if data_type:
            params["data_type"] = data_type
        if external_user_id:
            params["external_user_id"] = external_user_id
        try:
            response = self._client.get(
                f"/api/v1/agents/{self.agent_id}/data",
                params=params,
            )
            if response.status_code >= 400:
                self._handle_error(response)
            return response.json()
        except httpx.TimeoutException:
            raise ConnectionError("요청 타임아웃")
        except httpx.ConnectError:
            raise ConnectionError(f"서버에 연결할 수 없습니다: {self.base_url}")
        except (AuthenticationError, APIError, ValidationError):
            raise
        except Exception as e:
            raise ConnectionError(f"알 수 없는 오류: {str(e)}")
