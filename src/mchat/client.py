"""Mchat (Mattermost) API Client - WebSocket + REST API"""

import asyncio
import json
import logging
import ssl
from typing import Any, Callable, Optional

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from src.config import get_settings

logger = logging.getLogger("mchat")


def _get_ssl_context() -> ssl.SSLContext | bool:
    """SSL 컨텍스트 반환 (설정에 따라 분기)"""
    settings = get_settings()

    if settings.mchat_url.startswith("http://"):
        # 로컬 Mattermost: HTTP → SSL 불필요
        return False

    if not settings.mchat_ssl_verify:
        # Samsung 내부망: HTTPS + 자체 서명 인증서 → 검증 비활성화
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # 일반 HTTPS: 기본 SSL 검증
    return True


class MchatClient:
    """
    Mchat (Mattermost) 클라이언트

    WebSocket으로 실시간 메시지 수신, REST API로 메시지 전송
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.mchat_url).rstrip("/")
        self.token = token or settings.mchat_token

        # REST API 헤더
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        # SSL 설정
        self._ssl_context = _get_ssl_context()
        self._http_verify = self._ssl_context if isinstance(self._ssl_context, bool) else False

        # WebSocket 상태
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._ws_task: Optional[asyncio.Task] = None
        self._event_handlers: dict[str, list[Callable]] = {}
        self._running = False

        # Exponential backoff 설정
        self._reconnect_delay = 5
        self._reconnect_delay_max = 60
        self._current_reconnect_delay = self._reconnect_delay

        # 연결 상태
        self.connected = False
        self.last_error: Optional[str] = None

    # ==================== REST API ====================

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        """REST API 요청"""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0, verify=self._http_verify) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
            )

            if response.status_code >= 400:
                raise MchatAPIError(
                    status_code=response.status_code,
                    message=response.text,
                )

            return response.json() if response.text else {}

    async def get_me(self) -> dict[str, Any]:
        """현재 로그인한 사용자 (Bot) 정보 조회"""
        return await self._request("GET", "/api/v4/users/me")

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """사용자 정보 조회"""
        return await self._request("GET", f"/api/v4/users/{user_id}")

    async def get_user_by_username(self, username: str) -> dict[str, Any]:
        """사용자명으로 사용자 조회"""
        return await self._request("GET", f"/api/v4/users/username/{username}")

    async def get_channel(self, channel_id: str) -> dict[str, Any]:
        """채널 정보 조회"""
        return await self._request("GET", f"/api/v4/channels/{channel_id}")

    async def get_channel_members(self, channel_id: str) -> list[dict[str, Any]]:
        """채널 멤버 목록"""
        return await self._request("GET", f"/api/v4/channels/{channel_id}/members")

    async def get_teams(self) -> list[dict[str, Any]]:
        """내가 속한 팀 목록"""
        return await self._request("GET", "/api/v4/users/me/teams")

    async def get_channels_for_team(self, team_id: str) -> list[dict[str, Any]]:
        """팀의 채널 목록"""
        return await self._request("GET", f"/api/v4/users/me/teams/{team_id}/channels")

    async def create_post(
        self,
        channel_id: str,
        message: str,
        root_id: Optional[str] = None,
        file_ids: Optional[list[str]] = None,
        props: Optional[dict] = None,
    ) -> dict[str, Any]:
        """메시지 전송"""
        data = {
            "channel_id": channel_id,
            "message": message,
        }

        if root_id:
            data["root_id"] = root_id
        if file_ids:
            data["file_ids"] = file_ids
        if props:
            data["props"] = props

        return await self._request("POST", "/api/v4/posts", data=data)

    async def update_post(self, post_id: str, message: str) -> dict[str, Any]:
        """메시지 수정"""
        return await self._request("PUT", f"/api/v4/posts/{post_id}", data={
            "id": post_id,
            "message": message,
        })

    async def delete_post(self, post_id: str) -> dict[str, Any]:
        """메시지 삭제"""
        return await self._request("DELETE", f"/api/v4/posts/{post_id}")

    async def get_posts_for_channel(
        self,
        channel_id: str,
        page: int = 0,
        per_page: int = 60,
    ) -> dict[str, Any]:
        """채널의 메시지 목록 조회"""
        return await self._request(
            "GET",
            f"/api/v4/channels/{channel_id}/posts",
            params={"page": page, "per_page": per_page},
        )

    async def add_reaction(self, post_id: str, emoji_name: str) -> dict[str, Any]:
        """메시지에 리액션 추가"""
        user = await self.get_me()
        return await self._request("POST", "/api/v4/reactions", data={
            "user_id": user["id"],
            "post_id": post_id,
            "emoji_name": emoji_name,
        })

    async def create_direct_channel(self, user_ids: list[str]) -> dict[str, Any]:
        """DM 채널 생성 (1:1 또는 그룹)"""
        return await self._request("POST", "/api/v4/channels/direct", data=user_ids)

    async def ping(self) -> bool:
        """서버 헬스 체크"""
        try:
            result = await self._request("GET", "/api/v4/system/ping")
            return result.get("status") == "OK"
        except Exception:
            return False

    # ==================== WebSocket ====================

    def on(self, event_type: str):
        """이벤트 핸들러 등록 (데코레이터)"""
        def decorator(handler: Callable):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler
        return decorator

    async def _emit(self, event_type: str, data: dict):
        """이벤트 핸들러 호출"""
        handlers = self._event_handlers.get(event_type, [])
        handlers.extend(self._event_handlers.get("*", []))

        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Event handler error ({event_type}): {e}")

    async def connect_websocket(self):
        """WebSocket 연결 시작 (exponential backoff 재연결)"""
        self._running = True

        # WebSocket URL 구성
        ws_scheme = "wss" if self.base_url.startswith("https") else "ws"
        ws_url = f"{ws_scheme}://{self.base_url.split('://', 1)[1]}/api/v4/websocket"

        while self._running:
            try:
                logger.info(f"Connecting to WebSocket: {ws_url}")

                # SSL 설정 분기
                ws_ssl = self._ssl_context if ws_scheme == "wss" else None

                async with websockets.connect(
                    ws_url,
                    additional_headers={"Authorization": f"Bearer {self.token}"},
                    ping_interval=30,
                    ping_timeout=10,
                    ssl=ws_ssl,
                ) as ws:
                    self._ws = ws
                    self.connected = True
                    self.last_error = None
                    self._current_reconnect_delay = self._reconnect_delay  # 성공 시 리셋
                    logger.info("WebSocket connected!")

                    # 인증
                    auth_challenge = {
                        "seq": 1,
                        "action": "authentication_challenge",
                        "data": {"token": self.token},
                    }
                    await ws.send(json.dumps(auth_challenge))

                    # 이벤트 수신 루프
                    async for message in ws:
                        try:
                            event = json.loads(message)
                            event_type = event.get("event", "unknown")

                            if event_type == "posted" and "data" in event:
                                if "post" in event["data"]:
                                    event["data"]["post"] = json.loads(event["data"]["post"])

                            await self._emit(event_type, event)

                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON received: {message[:100]}")
                        except Exception as e:
                            logger.error(f"Event processing error: {e}")

            except ConnectionClosed as e:
                self.connected = False
                self.last_error = f"WebSocket closed: {e}"
                logger.warning(self.last_error)
            except Exception as e:
                self.connected = False
                self.last_error = f"WebSocket error: {e}"
                logger.error(self.last_error)

            if self._running:
                logger.info(f"Reconnecting in {self._current_reconnect_delay}s...")
                await asyncio.sleep(self._current_reconnect_delay)
                # Exponential backoff
                self._current_reconnect_delay = min(
                    self._current_reconnect_delay * 2,
                    self._reconnect_delay_max,
                )

        self.connected = False
        logger.info("WebSocket stopped")

    async def disconnect_websocket(self):
        """WebSocket 연결 종료"""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        self.connected = False

    def start(self) -> asyncio.Task:
        """WebSocket 연결을 백그라운드 태스크로 시작"""
        self._ws_task = asyncio.create_task(self.connect_websocket())
        return self._ws_task

    async def stop(self):
        """WebSocket 연결 종료"""
        await self.disconnect_websocket()
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass


class MchatAPIError(Exception):
    """Mchat API 오류"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Mchat API Error ({status_code}): {message}")
