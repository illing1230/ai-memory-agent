"""Chat API 통합 테스트"""

import pytest


class TestChatRoomCRUD:
    async def test_create_room(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/chat-rooms",
            json={"name": "통합 테스트 방", "room_type": "personal"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "통합 테스트 방"
        assert data["owner_id"] == "test-user-1"

    async def test_list_rooms(self, client, auth_headers):
        # 방 생성
        await client.post(
            "/api/v1/chat-rooms",
            json={"name": "리스트 방"},
            headers=auth_headers,
        )
        resp = await client.get("/api/v1/chat-rooms", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_room(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/chat-rooms",
            json={"name": "조회 방"},
            headers=auth_headers,
        )
        room_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/chat-rooms/{room_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == room_id

    async def test_delete_room(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/chat-rooms",
            json={"name": "삭제 방"},
            headers=auth_headers,
        )
        room_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/v1/chat-rooms/{room_id}", headers=auth_headers)
        assert resp.status_code == 200


class TestChatRoomMembers:
    async def test_add_and_list_members(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/chat-rooms",
            json={"name": "멤버 테스트 방"},
            headers=auth_headers,
        )
        room_id = create_resp.json()["id"]

        # 멤버 추가
        resp = await client.post(
            f"/api/v1/chat-rooms/{room_id}/members",
            json={"user_id": "test-user-2"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # 멤버 목록
        members_resp = await client.get(
            f"/api/v1/chat-rooms/{room_id}/members",
            headers=auth_headers,
        )
        assert members_resp.status_code == 200
        members = members_resp.json()
        user_ids = [m["user_id"] for m in members]
        assert "test-user-2" in user_ids


class TestChatMessages:
    async def test_send_message(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/chat-rooms",
            json={"name": "메시지 방"},
            headers=auth_headers,
        )
        room_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/chat-rooms/{room_id}/messages",
            json={"content": "안녕하세요"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    async def test_get_messages(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/chat-rooms",
            json={"name": "메시지 조회 방"},
            headers=auth_headers,
        )
        room_id = create_resp.json()["id"]

        # 메시지 전송
        await client.post(
            f"/api/v1/chat-rooms/{room_id}/messages",
            json={"content": "테스트 메시지"},
            headers=auth_headers,
        )

        resp = await client.get(
            f"/api/v1/chat-rooms/{room_id}/messages",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) >= 1
