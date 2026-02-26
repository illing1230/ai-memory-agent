"""테스트 공통 설정 및 fixture"""

import os
import pytest
import pytest_asyncio
import aiosqlite
from unittest.mock import AsyncMock, MagicMock, patch

# 테스트 환경 설정 — Settings 로드 전에 환경변수를 설정해야 함
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["SQLITE_DB_PATH"] = ":memory:"

from src.shared.database import SCHEMA_SQL


# ──────────────────────────────────────────────
# Database Fixture
# ──────────────────────────────────────────────
@pytest_asyncio.fixture
async def db():
    """전체 스키마가 적용된 인메모리 SQLite 데이터베이스"""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.executescript(SCHEMA_SQL)
    await conn.commit()
    yield conn
    await conn.close()


# ──────────────────────────────────────────────
# Seed Data Fixtures
# ──────────────────────────────────────────────
@pytest_asyncio.fixture
async def seed_users(db):
    """테스트 사용자 생성: user-1 (admin), user-2 (member), user-3 (다른 부서)"""
    await db.execute(
        "INSERT INTO departments (id, name, description) VALUES (?, ?, ?)",
        ("dept-1", "개발팀", "개발 부서"),
    )
    await db.execute(
        "INSERT INTO departments (id, name, description) VALUES (?, ?, ?)",
        ("dept-2", "디자인팀", "디자인 부서"),
    )
    await db.execute(
        "INSERT INTO users (id, name, email, role, department_id) VALUES (?, ?, ?, ?, ?)",
        ("user-1", "관리자", "admin@test.com", "admin", "dept-1"),
    )
    await db.execute(
        "INSERT INTO users (id, name, email, role, department_id) VALUES (?, ?, ?, ?, ?)",
        ("user-2", "사용자2", "user2@test.com", "user", "dept-1"),
    )
    await db.execute(
        "INSERT INTO users (id, name, email, role, department_id) VALUES (?, ?, ?, ?, ?)",
        ("user-3", "사용자3", "user3@test.com", "user", "dept-2"),
    )
    await db.commit()
    return {
        "user-1": {"id": "user-1", "name": "관리자", "role": "admin", "department_id": "dept-1"},
        "user-2": {"id": "user-2", "name": "사용자2", "role": "user", "department_id": "dept-1"},
        "user-3": {"id": "user-3", "name": "사용자3", "role": "user", "department_id": "dept-2"},
    }


@pytest_asyncio.fixture
async def seed_chat_room(db, seed_users):
    """테스트 대화방 생성: user-1 소유, user-2 멤버"""
    await db.execute(
        "INSERT INTO chat_rooms (id, name, room_type, owner_id) VALUES (?, ?, ?, ?)",
        ("room-1", "테스트 대화방", "personal", "user-1"),
    )
    await db.execute(
        "INSERT INTO chat_room_members (id, chat_room_id, user_id, role) VALUES (?, ?, ?, ?)",
        ("member-1", "room-1", "user-1", "owner"),
    )
    await db.execute(
        "INSERT INTO chat_room_members (id, chat_room_id, user_id, role) VALUES (?, ?, ?, ?)",
        ("member-2", "room-1", "user-2", "member"),
    )
    await db.commit()
    return {"id": "room-1", "name": "테스트 대화방", "room_type": "personal", "owner_id": "user-1"}


@pytest_asyncio.fixture
async def seed_memories(db, seed_users, seed_chat_room):
    """테스트 메모리 생성: personal, chatroom, agent 각 1개씩"""
    await db.execute(
        """INSERT INTO memories (id, content, scope, owner_id, category, importance)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("mem-1", "개인 메모리 내용", "personal", "user-1", "fact", "medium"),
    )
    await db.execute(
        """INSERT INTO memories (id, content, scope, owner_id, chat_room_id, category, importance)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("mem-2", "대화방 메모리 내용", "chatroom", "user-1", "room-1", "decision", "high"),
    )
    await db.execute(
        """INSERT INTO memories (id, content, scope, owner_id, category, importance, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("mem-3", "에이전트 메모리 내용", "agent", "user-1", "fact", "low",
         '{"source": "agent", "agent_instance_id": "agent-inst-1"}'),
    )
    await db.commit()
    return [
        {"id": "mem-1", "scope": "personal", "owner_id": "user-1"},
        {"id": "mem-2", "scope": "chatroom", "owner_id": "user-1", "chat_room_id": "room-1"},
        {"id": "mem-3", "scope": "agent", "owner_id": "user-1"},
    ]


# ──────────────────────────────────────────────
# Mock Fixtures
# ──────────────────────────────────────────────
@pytest.fixture
def mock_embedding_provider():
    """임베딩 프로바이더 Mock"""
    provider = AsyncMock()
    provider.embed = AsyncMock(return_value=[0.1] * 1024)
    provider.embed_batch = AsyncMock(return_value=[[0.1] * 1024])
    provider.dimension = 1024
    return provider


@pytest.fixture
def mock_llm_provider():
    """LLM 프로바이더 Mock"""
    provider = AsyncMock()
    provider.generate = AsyncMock(return_value="테스트 응답")
    provider.extract_memories = AsyncMock(return_value=[])
    return provider


@pytest.fixture
def mock_reranker_provider():
    """Reranker 프로바이더 Mock"""
    provider = AsyncMock()
    provider.rerank = AsyncMock(return_value=[
        {"index": 0, "relevance_score": 0.9, "document": "test"}
    ])
    return provider


@pytest.fixture
def mock_vector_store():
    """Qdrant 벡터 스토어 Mock"""
    with patch("src.shared.vector_store.search_vectors", new_callable=AsyncMock) as mock_search, \
         patch("src.shared.vector_store.upsert_vector", new_callable=AsyncMock) as mock_upsert, \
         patch("src.shared.vector_store.delete_vector", new_callable=AsyncMock) as mock_delete, \
         patch("src.shared.vector_store.delete_vectors_by_filter", new_callable=AsyncMock) as mock_delete_filter:
        mock_search.return_value = []
        mock_delete_filter.return_value = 0
        yield {
            "search": mock_search,
            "upsert": mock_upsert,
            "delete": mock_delete,
            "delete_filter": mock_delete_filter,
        }


@pytest.fixture
def mock_mchat_client():
    """Mattermost 클라이언트 Mock"""
    client = AsyncMock()
    client.get_me = AsyncMock(return_value={"id": "bot-user-id", "username": "ai-memory-bot"})
    client.get_user = AsyncMock(return_value={
        "id": "mchat-user-1", "username": "testuser",
        "email": "test@example.com", "is_bot": False,
    })
    client.get_channel_members = AsyncMock(return_value=[])
    client.create_post = AsyncMock(return_value={"id": "post-1"})
    client.send_message = AsyncMock(return_value={"id": "post-1"})
    client.add_reaction = AsyncMock(return_value={})
    client.leave_channel = AsyncMock()
    return client
