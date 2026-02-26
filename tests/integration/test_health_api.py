"""Health API 테스트"""


class TestHealthCheck:
    async def test_basic(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    async def test_services_info(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert "services" in data
        assert "database" in data["services"]
        assert "vector_store" in data["services"]
