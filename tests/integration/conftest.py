"""Integration test fixtures"""

import os
import pytest
import pytest_asyncio
import aiosqlite
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport

from src.shared.database import SCHEMA_SQL
from src.shared.auth import create_access_token, hash_password


@pytest_asyncio.fixture
async def test_db():
    """Integration 테스트용 인메모리 DB"""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.executescript(SCHEMA_SQL)
    await conn.commit()

    # 테스트 사용자 seed
    hashed = hash_password("test123")
    await conn.execute(
        "INSERT INTO users (id, name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        ("test-user-1", "테스트유저", "test@test.com", hashed, "admin"),
    )
    await conn.execute(
        "INSERT INTO users (id, name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        ("test-user-2", "유저2", "user2@test.com", hash_password("test123"), "user"),
    )
    await conn.commit()
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def app(test_db):
    """Mock된 외부 의존성을 가진 FastAPI 앱"""
    mock_embed = AsyncMock()
    mock_embed.embed = AsyncMock(return_value=[0.1] * 1024)
    mock_embed.dimension = 1024

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value="테스트 응답")
    mock_llm.extract_memories = AsyncMock(return_value=[])

    with patch("src.shared.vector_store.init_vector_store", new_callable=AsyncMock), \
         patch("src.shared.vector_store.close_vector_store", new_callable=AsyncMock), \
         patch("src.shared.vector_store.is_vector_store_available", return_value=False), \
         patch("src.shared.vector_store.upsert_vector", new_callable=AsyncMock), \
         patch("src.shared.vector_store.search_vectors", new_callable=AsyncMock, return_value=[]), \
         patch("src.shared.vector_store.delete_vector", new_callable=AsyncMock), \
         patch("src.shared.providers.get_embedding_provider", return_value=mock_embed), \
         patch("src.shared.providers.get_llm_provider", return_value=mock_llm), \
         patch("src.shared.providers.get_reranker_provider", return_value=None), \
         patch("src.memory.service.get_embedding_provider", return_value=mock_embed), \
         patch("src.memory.service.get_llm_provider", return_value=mock_llm):

        from src.main import create_app

        application = create_app()

        # DB dependency override
        async def override_get_db():
            yield test_db

        from src.shared.database import get_db
        application.dependency_overrides[get_db] = override_get_db

        yield application
        application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP 테스트 클라이언트"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """인증 헤더 (test-user-1)"""
    return {"X-User-ID": "test-user-1"}


@pytest.fixture
def auth_headers_user2():
    """인증 헤더 (test-user-2)"""
    return {"X-User-ID": "test-user-2"}
