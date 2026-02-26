"""Mchat Worker 테스트"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.mchat.worker import (
    get_or_create_agent_room,
    get_or_create_agent_user,
    sync_channel_members,
    _channel_cache,
)
from src.chat.repository import ChatRepository


class TestGetOrCreateAgentRoom:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """각 테스트 전에 캐시 클리어"""
        _channel_cache.clear()
        yield
        _channel_cache.clear()

    async def test_from_cache(self, db, seed_chat_room, mock_mchat_client):
        """캐시에 있으면 DB 조회 없이 바로 반환"""
        _channel_cache["ch-1"] = "room-1"
        result = await get_or_create_agent_room(
            db, mock_mchat_client, "ch-1", "테스트채널", "user-1", "bot-user-id"
        )
        assert result == "room-1"

    async def test_from_db(self, db, seed_chat_room, mock_mchat_client):
        """DB에 매핑이 있으면 그것을 반환하고 캐시"""
        await db.execute(
            "INSERT INTO mchat_channel_mapping (id, mchat_channel_id, agent_room_id) VALUES (?, ?, ?)",
            ("map-1", "ch-1", "room-1"),
        )
        await db.commit()

        result = await get_or_create_agent_room(
            db, mock_mchat_client, "ch-1", "테스트채널", "user-1", "bot-user-id"
        )
        assert result == "room-1"
        assert _channel_cache["ch-1"] == "room-1"

    async def test_stale_mapping(self, db, seed_users, mock_mchat_client):
        """매핑된 대화방이 삭제된 경우 새로 생성"""
        # 존재하지 않는 room에 대한 매핑 생성
        await db.execute(
            "INSERT INTO mchat_channel_mapping (id, mchat_channel_id, agent_room_id) VALUES (?, ?, ?)",
            ("map-1", "ch-1", "deleted-room"),
        )
        await db.commit()

        mock_mchat_client.get_channel_members = AsyncMock(return_value=[])

        result = await get_or_create_agent_room(
            db, mock_mchat_client, "ch-1", "새채널", "user-1", "bot-user-id"
        )
        # 새 대화방이 생성되어야 함
        assert result != "deleted-room"
        assert result is not None

    async def test_new_channel(self, db, seed_users, mock_mchat_client):
        """매핑이 없으면 새 대화방 생성"""
        mock_mchat_client.get_channel_members = AsyncMock(return_value=[])

        result = await get_or_create_agent_room(
            db, mock_mchat_client, "ch-new", "새로운채널", "user-1", "bot-user-id"
        )
        assert result is not None

        # 대화방 확인
        repo = ChatRepository(db)
        room = await repo.get_chat_room(result)
        assert room is not None
        assert "Mchat" in room["name"]


class TestGetOrCreateAgentUser:
    async def test_email_match(self, db, seed_users, mock_mchat_client):
        """Mattermost 이메일이 기존 사용자와 일치하면 매칭"""
        mock_mchat_client.get_user = AsyncMock(return_value={
            "id": "mchat-u1", "username": "admin", "email": "admin@test.com", "is_bot": False,
        })

        result = await get_or_create_agent_user(db, mock_mchat_client, "mchat-u1", "admin")
        assert result == "user-1"  # admin@test.com 매칭

    async def test_new_user_creation(self, db, seed_users, mock_mchat_client):
        """매칭 실패 시 새 사용자 생성"""
        mock_mchat_client.get_user = AsyncMock(return_value={
            "id": "mchat-u-new", "username": "newuser",
            "email": "newuser@company.com", "is_bot": False,
        })

        result = await get_or_create_agent_user(db, mock_mchat_client, "mchat-u-new", "newuser")
        assert result is not None

    async def test_stale_user_mapping(self, db, seed_users, mock_mchat_client):
        """매핑된 사용자가 삭제된 경우 재생성"""
        await db.execute(
            "INSERT INTO mchat_user_mapping (id, mchat_user_id, mchat_username, agent_user_id) VALUES (?, ?, ?, ?)",
            ("map-1", "mchat-stale", "stale", "deleted-user"),
        )
        await db.commit()

        mock_mchat_client.get_user = AsyncMock(return_value={
            "id": "mchat-stale", "username": "stale",
            "email": "stale@test.com", "is_bot": False,
        })

        result = await get_or_create_agent_user(db, mock_mchat_client, "mchat-stale", "stale")
        assert result is not None
        assert result != "deleted-user"


class TestSyncChannelMembers:
    async def test_adds_missing_members(self, db, seed_chat_room, mock_mchat_client):
        """채널에 있지만 대화방에 없는 멤버 추가"""
        mock_mchat_client.get_channel_members = AsyncMock(return_value=[
            {"user_id": "mchat-u3"},
        ])
        mock_mchat_client.get_user = AsyncMock(return_value={
            "id": "mchat-u3", "username": "user3",
            "email": "user3@test.com", "is_bot": False,
        })

        await sync_channel_members(
            db, mock_mchat_client, "ch-1", "room-1", "bot-user-id"
        )

    async def test_skips_bots(self, db, seed_chat_room, mock_mchat_client):
        """봇 사용자는 추가하지 않음"""
        mock_mchat_client.get_channel_members = AsyncMock(return_value=[
            {"user_id": "bot-user-id"},
        ])

        await sync_channel_members(
            db, mock_mchat_client, "ch-1", "room-1", "bot-user-id"
        )
        # 봇은 스킵되므로 멤버 수 변화 없음
        repo = ChatRepository(db)
        members = await repo.list_members("room-1")
        member_ids = [m["user_id"] for m in members]
        assert "bot-user-id" not in member_ids

    async def test_handles_api_failure(self, db, seed_chat_room, mock_mchat_client):
        """채널 멤버 조회 실패 시 graceful 처리"""
        mock_mchat_client.get_channel_members = AsyncMock(side_effect=Exception("API Error"))

        # 예외가 발생하지 않아야 함
        await sync_channel_members(
            db, mock_mchat_client, "ch-1", "room-1", "bot-user-id"
        )
