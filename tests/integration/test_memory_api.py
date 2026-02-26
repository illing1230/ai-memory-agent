"""Memory API 통합 테스트"""

import pytest


class TestCreateMemory:
    async def test_create(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/memories",
            json={"content": "통합 테스트 메모리", "scope": "personal"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "통합 테스트 메모리"
        assert data["scope"] == "personal"
        assert data["id"] is not None


class TestListMemories:
    async def test_list(self, client, auth_headers):
        # 먼저 메모리 생성
        await client.post(
            "/api/v1/memories",
            json={"content": "리스트 테스트", "scope": "personal"},
            headers=auth_headers,
        )
        resp = await client.get("/api/v1/memories", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_with_scope(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/memories", params={"scope": "personal"}, headers=auth_headers
        )
        assert resp.status_code == 200


class TestGetMemory:
    async def test_get(self, client, auth_headers):
        # 생성
        create_resp = await client.post(
            "/api/v1/memories",
            json={"content": "조회 테스트", "scope": "personal"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/memories/{memory_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == memory_id

    async def test_not_found(self, client, auth_headers):
        resp = await client.get("/api/v1/memories/non-existent", headers=auth_headers)
        assert resp.status_code == 404

    async def test_forbidden(self, client, auth_headers, auth_headers_user2):
        # user-1이 생성
        create_resp = await client.post(
            "/api/v1/memories",
            json={"content": "비밀 메모리", "scope": "personal"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        # user-2가 접근 시도
        resp = await client.get(f"/api/v1/memories/{memory_id}", headers=auth_headers_user2)
        assert resp.status_code == 403


class TestUpdateMemory:
    async def test_update(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memories",
            json={"content": "수정 전", "scope": "personal"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        resp = await client.put(
            f"/api/v1/memories/{memory_id}",
            json={"content": "수정 후"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "수정 후"


class TestDeleteMemory:
    async def test_delete(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memories",
            json={"content": "삭제 대상", "scope": "personal"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)
        assert resp.status_code == 200

        # 삭제 후 조회
        get_resp = await client.get(f"/api/v1/memories/{memory_id}", headers=auth_headers)
        assert get_resp.status_code == 404


class TestSearchMemories:
    async def test_search(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/memories/search",
            json={"query": "테스트 검색어", "limit": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "total" in data
        assert "query" in data
