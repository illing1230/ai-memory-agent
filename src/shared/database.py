"""SQLite 데이터베이스 관리"""

import aiosqlite
from pathlib import Path
from typing import AsyncGenerator

from src.config import get_settings

# 전역 데이터베이스 연결
_db_connection: aiosqlite.Connection | None = None


# SQL 스키마 정의
SCHEMA_SQL = """
-- 부서 테이블
CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    role TEXT DEFAULT 'user',
    department_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- 프로젝트 테이블
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    department_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- 프로젝트 멤버 테이블
CREATE TABLE IF NOT EXISTS project_members (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT DEFAULT 'member',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (project_id, user_id)
);

-- 채팅방 테이블
CREATE TABLE IF NOT EXISTS chat_rooms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    room_type TEXT NOT NULL CHECK (room_type IN ('personal', 'project', 'department')),
    owner_id TEXT NOT NULL,
    project_id TEXT,
    department_id TEXT,
    context_sources TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- 채팅방 멤버 테이블
CREATE TABLE IF NOT EXISTS chat_room_members (
    id TEXT PRIMARY KEY,
    chat_room_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (chat_room_id, user_id)
);

-- 채팅 메시지 테이블
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    chat_room_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    mentions TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE
);

-- 메모리 테이블
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    vector_id TEXT,
    scope TEXT NOT NULL CHECK (scope IN ('personal', 'project', 'department', 'chatroom')),
    owner_id TEXT NOT NULL,
    project_id TEXT,
    department_id TEXT,
    chat_room_id TEXT,
    source_message_id TEXT,
    category TEXT,
    importance TEXT DEFAULT 'medium',
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id)
);

-- 메모리 접근 로그 테이블
CREATE TABLE IF NOT EXISTS memory_access_log (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('read', 'update', 'delete')),
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_department ON projects(department_id);
CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user ON project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_rooms_owner ON chat_rooms(owner_id);
CREATE INDEX IF NOT EXISTS idx_chat_rooms_type ON chat_rooms(room_type);
CREATE INDEX IF NOT EXISTS idx_memories_owner ON memories(owner_id);
CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope);
CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);
CREATE INDEX IF NOT EXISTS idx_memories_department ON memories(department_id);
CREATE INDEX IF NOT EXISTS idx_memories_chat_room ON memories(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_memory_access_log_memory ON memory_access_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_access_log_user ON memory_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_room ON chat_messages(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_room_members_room ON chat_room_members(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_chat_room_members_user ON chat_room_members(user_id);
"""


async def init_database() -> None:
    """데이터베이스 초기화"""
    global _db_connection

    settings = get_settings()
    db_path = Path(settings.sqlite_db_path)

    # 디렉토리 생성
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 연결 생성
    _db_connection = await aiosqlite.connect(db_path)
    _db_connection.row_factory = aiosqlite.Row

    # 외래 키 활성화
    await _db_connection.execute("PRAGMA foreign_keys = ON")

    # 스키마 생성
    await _db_connection.executescript(SCHEMA_SQL)
    await _db_connection.commit()
    
    # password_hash 컬럼 추가 (기존 DB 마이그레이션)
    try:
        await _db_connection.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        await _db_connection.commit()
    except Exception:
        pass  # 이미 존재하면 무시
    
    # updated_at 컬럼 추가 (chat_rooms)
    try:
        await _db_connection.execute("ALTER TABLE chat_rooms ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        await _db_connection.commit()
    except Exception:
        pass

    # role 컬럼 추가 (users)
    try:
        await _db_connection.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        await _db_connection.commit()
    except Exception:
        pass

    print(f"✅ SQLite 데이터베이스 초기화 완료: {db_path}")


async def close_database() -> None:
    """데이터베이스 연결 종료"""
    global _db_connection

    if _db_connection:
        await _db_connection.close()
        _db_connection = None
        print("✅ SQLite 데이터베이스 연결 종료")


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """데이터베이스 연결 반환 (의존성 주입용)"""
    if _db_connection is None:
        raise RuntimeError("데이터베이스가 초기화되지 않았습니다")
    yield _db_connection


async def get_db_sync() -> aiosqlite.Connection:
    """데이터베이스 연결 반환 (WebSocket용)"""
    settings = get_settings()
    db_path = Path(settings.sqlite_db_path)
    
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    
    return conn
