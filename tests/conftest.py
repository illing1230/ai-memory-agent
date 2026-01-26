"""테스트 설정"""

import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path

from src.config import get_settings


@pytest_asyncio.fixture
async def db():
    """테스트용 인메모리 데이터베이스"""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    
    # 스키마 생성
    schema_path = Path(__file__).parent.parent / "src" / "shared" / "database.py"
    # 간단한 스키마만 생성
    await conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    yield conn
    await conn.close()
