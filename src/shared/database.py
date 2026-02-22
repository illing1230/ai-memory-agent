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

-- 대화방 테이블
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

-- 대화방 멤버 테이블
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
    sources TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE
);

-- 메모리 테이블
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    vector_id TEXT,
    scope TEXT NOT NULL CHECK (scope IN ('personal', 'project', 'department', 'chatroom', 'agent')),
    owner_id TEXT NOT NULL,
    project_id TEXT,
    department_id TEXT,
    chat_room_id TEXT,
    source_message_id TEXT,
    category TEXT,
    importance TEXT DEFAULT 'medium',
    metadata TEXT,
    topic_key TEXT,
    superseded BOOLEAN DEFAULT 0,
    superseded_by TEXT,
    superseded_at DATETIME,
    last_accessed_at DATETIME,
    access_count INTEGER DEFAULT 0,
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

-- 엔티티 테이블
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person','meeting','project','organization','topic','date')),
    owner_id TEXT NOT NULL,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    UNIQUE (name_normalized, entity_type, owner_id)
);

-- 메모리-엔티티 연결 테이블
CREATE TABLE IF NOT EXISTS memory_entities (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    relation_type TEXT DEFAULT 'mentioned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    UNIQUE (memory_id, entity_id)
);

-- 엔티티 관계 테이블
CREATE TABLE IF NOT EXISTS entity_relations (
    id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    UNIQUE (source_entity_id, target_entity_id, relation_type)
);

-- 문서 테이블
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'txt')),
    file_size INTEGER NOT NULL,
    owner_id TEXT NOT NULL,
    chat_room_id TEXT,
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    chunk_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE SET NULL
);

-- 문서 청크 테이블
CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    vector_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 문서-대화방 연결 테이블
CREATE TABLE IF NOT EXISTS document_chat_rooms (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chat_room_id TEXT NOT NULL,
    linked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    UNIQUE (document_id, chat_room_id)
);

-- 문서 청크 전문검색 (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts
USING fts5(content, chunk_id UNINDEXED, document_id UNINDEXED);

-- 공유 설정 테이블
CREATE TABLE IF NOT EXISTS shares (
    id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL CHECK (resource_type IN ('project', 'document', 'chat_room')),
    resource_id TEXT NOT NULL,
    target_type TEXT NOT NULL CHECK (target_type IN ('user', 'project', 'department')),
    target_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'member', 'viewer')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,
    UNIQUE(resource_type, resource_id, target_type, target_id)
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
CREATE INDEX IF NOT EXISTS idx_memories_topic_key ON memories(topic_key);
CREATE INDEX IF NOT EXISTS idx_memories_superseded ON memories(superseded);
CREATE INDEX IF NOT EXISTS idx_memory_access_log_memory ON memory_access_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_access_log_user ON memory_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_room ON chat_messages(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_room_members_room ON chat_room_members(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_chat_room_members_user ON chat_room_members(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_chat_room ON documents(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chat_rooms_document ON document_chat_rooms(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chat_rooms_room ON document_chat_rooms(chat_room_id);
CREATE INDEX IF NOT EXISTS idx_shares_resource ON shares(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_shares_target ON shares(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_shares_created_by ON shares(created_by);

-- 엔티티 인덱스
CREATE INDEX IF NOT EXISTS idx_entities_name_normalized ON entities(name_normalized);
CREATE INDEX IF NOT EXISTS idx_entities_type_owner ON entities(entity_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_entities_owner ON entities(owner_id);
CREATE INDEX IF NOT EXISTS idx_memory_entities_memory ON memory_entities(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_entities_entity ON memory_entities(entity_id);

-- 엔티티 관계 인덱스
CREATE INDEX IF NOT EXISTS idx_entity_relations_source ON entity_relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relations_target ON entity_relations(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relations_owner ON entity_relations(owner_id);

-- Agent Type (에이전트 유형/템플릿)
CREATE TABLE IF NOT EXISTS agent_types (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    developer_id TEXT NOT NULL,
    version TEXT DEFAULT '1.0.0',
    config_schema TEXT,
    capabilities TEXT,
    public_scope TEXT DEFAULT 'private' CHECK (public_scope IN ('private', 'project', 'department', 'public')),
    project_id TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (developer_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Agent Instance (사용자가 생성한 에이전트 인스턴스)
CREATE TABLE IF NOT EXISTS agent_instances (
    id TEXT PRIMARY KEY,
    agent_type_id TEXT NOT NULL,
    name TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    config TEXT,
    webhook_url TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_type_id) REFERENCES agent_types(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

-- Agent 데이터 수신 테이블
CREATE TABLE IF NOT EXISTS agent_data (
    id TEXT PRIMARY KEY,
    agent_instance_id TEXT NOT NULL,
    external_user_id TEXT,
    internal_user_id TEXT NOT NULL,
    data_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_instance_id) REFERENCES agent_instances(id),
    FOREIGN KEY (internal_user_id) REFERENCES users(id)
);

-- 외부 시스템 사용자 매핑
CREATE TABLE IF NOT EXISTS external_user_mappings (
    id TEXT PRIMARY KEY,
    agent_instance_id TEXT NOT NULL,
    external_user_id TEXT NOT NULL,
    internal_user_id TEXT NOT NULL,
    external_system_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_instance_id) REFERENCES agent_instances(id),
    FOREIGN KEY (internal_user_id) REFERENCES users(id),
    UNIQUE(agent_instance_id, external_user_id)
);

-- Agent Instance 공유
CREATE TABLE IF NOT EXISTS agent_instance_shares (
    id TEXT PRIMARY KEY,
    agent_instance_id TEXT NOT NULL,
    shared_with_user_id TEXT,
    shared_with_project_id TEXT,
    shared_with_department_id TEXT,
    role TEXT DEFAULT 'viewer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_instance_id) REFERENCES agent_instances(id),
    FOREIGN KEY (shared_with_user_id) REFERENCES users(id),
    FOREIGN KEY (shared_with_project_id) REFERENCES projects(id),
    FOREIGN KEY (shared_with_department_id) REFERENCES departments(id)
);

-- Agent 인덱스
CREATE INDEX IF NOT EXISTS idx_agent_types_developer ON agent_types(developer_id);
CREATE INDEX IF NOT EXISTS idx_agent_types_status ON agent_types(status);
CREATE INDEX IF NOT EXISTS idx_agent_instances_owner ON agent_instances(owner_id);
CREATE INDEX IF NOT EXISTS idx_agent_instances_type ON agent_instances(agent_type_id);
CREATE INDEX IF NOT EXISTS idx_agent_instances_api_key ON agent_instances(api_key);
CREATE INDEX IF NOT EXISTS idx_agent_data_instance ON agent_data(agent_instance_id);
CREATE INDEX IF NOT EXISTS idx_agent_data_user ON agent_data(internal_user_id);
CREATE INDEX IF NOT EXISTS idx_agent_data_created ON agent_data(created_at);
CREATE INDEX IF NOT EXISTS idx_external_mappings_instance ON external_user_mappings(agent_instance_id);
CREATE INDEX IF NOT EXISTS idx_external_mappings_external ON external_user_mappings(external_user_id);
CREATE INDEX IF NOT EXISTS idx_agent_shares_instance ON agent_instance_shares(agent_instance_id);
CREATE INDEX IF NOT EXISTS idx_agent_shares_user ON agent_instance_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_agent_shares_project ON agent_instance_shares(shared_with_project_id);
CREATE INDEX IF NOT EXISTS idx_agent_shares_department ON agent_instance_shares(shared_with_department_id);

-- Mchat 사용자 매핑 테이블
CREATE TABLE IF NOT EXISTS mchat_user_mapping (
    id TEXT PRIMARY KEY,
    mchat_user_id TEXT UNIQUE NOT NULL,
    mchat_username TEXT,
    agent_user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_user_id) REFERENCES users(id)
);

-- Mchat 채널 매핑 테이블
CREATE TABLE IF NOT EXISTS mchat_channel_mapping (
    id TEXT PRIMARY KEY,
    mchat_channel_id TEXT UNIQUE NOT NULL,
    mchat_channel_name TEXT,
    mchat_team_id TEXT,
    agent_room_id TEXT NOT NULL,
    sync_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_room_id) REFERENCES chat_rooms(id)
);

-- Mchat 인덱스
CREATE INDEX IF NOT EXISTS idx_mchat_user_mapping_mchat_user ON mchat_user_mapping(mchat_user_id);
CREATE INDEX IF NOT EXISTS idx_mchat_user_mapping_agent_user ON mchat_user_mapping(agent_user_id);
CREATE INDEX IF NOT EXISTS idx_mchat_channel_mapping_mchat_channel ON mchat_channel_mapping(mchat_channel_id);
CREATE INDEX IF NOT EXISTS idx_mchat_channel_mapping_agent_room ON mchat_channel_mapping(agent_room_id);
CREATE INDEX IF NOT EXISTS idx_mchat_channel_mapping_sync ON mchat_channel_mapping(sync_enabled);

-- Mchat 채널 대화 요약 로그 테이블
CREATE TABLE IF NOT EXISTS mchat_summary_log (
    id TEXT PRIMARY KEY,
    mchat_channel_id TEXT NOT NULL,
    channel_name TEXT,
    period_start_ms INTEGER NOT NULL,
    period_end_ms INTEGER NOT NULL,
    message_count INTEGER DEFAULT 0,
    participant_count INTEGER DEFAULT 0,
    summary_content TEXT NOT NULL,
    memory_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

-- 요약 로그 인덱스
CREATE INDEX IF NOT EXISTS idx_mchat_summary_log_channel ON mchat_summary_log(mchat_channel_id);
CREATE INDEX IF NOT EXISTS idx_mchat_summary_log_created ON mchat_summary_log(created_at);
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

    # topic_key 컬럼 추가 (memories)
    try:
        await _db_connection.execute("ALTER TABLE memories ADD COLUMN topic_key TEXT")
        await _db_connection.commit()
    except Exception:
        pass

    # superseded 컬럼 추가 (memories)
    try:
        await _db_connection.execute("ALTER TABLE memories ADD COLUMN superseded BOOLEAN DEFAULT 0")
        await _db_connection.commit()
    except Exception:
        pass

    # superseded_by 컬럼 추가 (memories)
    try:
        await _db_connection.execute("ALTER TABLE memories ADD COLUMN superseded_by TEXT")
        await _db_connection.commit()
    except Exception:
        pass

    # superseded_at 컬럼 추가 (memories)
    try:
        await _db_connection.execute("ALTER TABLE memories ADD COLUMN superseded_at DATETIME")
        await _db_connection.commit()
    except Exception:
        pass

    # 인덱스 추가 (기존 DB 마이그레이션)
    try:
        await _db_connection.execute("CREATE INDEX IF NOT EXISTS idx_memories_topic_key ON memories(topic_key)")
        await _db_connection.commit()
    except Exception:
        pass

    try:
        await _db_connection.execute("CREATE INDEX IF NOT EXISTS idx_memories_superseded ON memories(superseded)")
        await _db_connection.commit()
    except Exception:
        pass

    # public_scope 컬럼 추가 (agent_types)
    try:
        await _db_connection.execute("ALTER TABLE agent_types ADD COLUMN public_scope TEXT DEFAULT 'public'")
        await _db_connection.commit()
    except Exception:
        pass

    # project_id 컬럼 추가 (agent_types)
    try:
        await _db_connection.execute("ALTER TABLE agent_types ADD COLUMN project_id TEXT")
        await _db_connection.commit()
    except Exception:
        pass

    # agent scope 추가 (memories) - CHECK 제약조건 재생성
    try:
        # 기존 CHECK 제약조건 삭제
        await _db_connection.execute("CREATE TABLE memories_new (id TEXT PRIMARY KEY, content TEXT NOT NULL, vector_id TEXT, scope TEXT NOT NULL CHECK (scope IN ('personal', 'project', 'department', 'chatroom', 'agent')), owner_id TEXT NOT NULL, project_id TEXT, department_id TEXT, chat_room_id TEXT, source_message_id TEXT, category TEXT, importance TEXT DEFAULT 'medium', metadata TEXT, topic_key TEXT, superseded BOOLEAN DEFAULT 0, superseded_by TEXT, superseded_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (owner_id) REFERENCES users(id), FOREIGN KEY (project_id) REFERENCES projects(id), FOREIGN KEY (department_id) REFERENCES departments(id), FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id))")
        await _db_connection.execute("INSERT INTO memories_new SELECT * FROM memories")
        await _db_connection.execute("DROP TABLE memories")
        await _db_connection.execute("ALTER TABLE memories_new RENAME TO memories")
        await _db_connection.commit()
    except Exception:
        pass  # 이미 존재하면 무시

    # sources 컬럼 추가 (chat_messages)
    try:
        await _db_connection.execute("ALTER TABLE chat_messages ADD COLUMN sources TEXT")
        await _db_connection.commit()
    except Exception:
        pass

    # last_accessed_at 컬럼 추가 (memories)
    try:
        await _db_connection.execute("ALTER TABLE memories ADD COLUMN last_accessed_at DATETIME")
        await _db_connection.commit()
    except Exception:
        pass

    # access_count 컬럼 추가 (memories)
    try:
        await _db_connection.execute("ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0")
        await _db_connection.commit()
    except Exception:
        pass

    # entities, memory_entities 테이블 마이그레이션 (기존 DB용)
    try:
        await _db_connection.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                name_normalized TEXT NOT NULL,
                entity_type TEXT NOT NULL CHECK (entity_type IN ('person','meeting','project','organization','topic','date')),
                owner_id TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id),
                UNIQUE (name_normalized, entity_type, owner_id)
            );
            CREATE TABLE IF NOT EXISTS memory_entities (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                relation_type TEXT DEFAULT 'mentioned',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE (memory_id, entity_id)
            );
            CREATE INDEX IF NOT EXISTS idx_entities_name_normalized ON entities(name_normalized);
            CREATE INDEX IF NOT EXISTS idx_entities_type_owner ON entities(entity_type, owner_id);
            CREATE INDEX IF NOT EXISTS idx_entities_owner ON entities(owner_id);
            CREATE INDEX IF NOT EXISTS idx_memory_entities_memory ON memory_entities(memory_id);
            CREATE INDEX IF NOT EXISTS idx_memory_entities_entity ON memory_entities(entity_id);
        """)
        await _db_connection.commit()
    except Exception:
        pass

    # entity_relations 테이블 마이그레이션 (기존 DB용)
    try:
        await _db_connection.executescript("""
            CREATE TABLE IF NOT EXISTS entity_relations (
                id TEXT PRIMARY KEY,
                source_entity_id TEXT NOT NULL,
                target_entity_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                FOREIGN KEY (owner_id) REFERENCES users(id),
                UNIQUE (source_entity_id, target_entity_id, relation_type)
            );
            CREATE INDEX IF NOT EXISTS idx_entity_relations_source ON entity_relations(source_entity_id);
            CREATE INDEX IF NOT EXISTS idx_entity_relations_target ON entity_relations(target_entity_id);
            CREATE INDEX IF NOT EXISTS idx_entity_relations_owner ON entity_relations(owner_id);
        """)
        await _db_connection.commit()
    except Exception:
        pass

    # document_chunks_fts FTS5 가상 테이블 마이그레이션 (기존 DB용)
    try:
        await _db_connection.execute(
            """CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts
               USING fts5(content, chunk_id UNINDEXED, document_id UNINDEXED)"""
        )
        await _db_connection.commit()
    except Exception:
        pass

    # mchat 매핑 테이블 마이그레이션 (기존 DB용)
    try:
        await _db_connection.executescript("""
            CREATE TABLE IF NOT EXISTS mchat_user_mapping (
                id TEXT PRIMARY KEY,
                mchat_user_id TEXT UNIQUE NOT NULL,
                mchat_username TEXT,
                agent_user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS mchat_channel_mapping (
                id TEXT PRIMARY KEY,
                mchat_channel_id TEXT UNIQUE NOT NULL,
                mchat_channel_name TEXT,
                mchat_team_id TEXT,
                agent_room_id TEXT NOT NULL,
                sync_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_room_id) REFERENCES chat_rooms(id)
            );
            CREATE INDEX IF NOT EXISTS idx_mchat_user_mapping_mchat_user ON mchat_user_mapping(mchat_user_id);
            CREATE INDEX IF NOT EXISTS idx_mchat_user_mapping_agent_user ON mchat_user_mapping(agent_user_id);
            CREATE INDEX IF NOT EXISTS idx_mchat_channel_mapping_mchat_channel ON mchat_channel_mapping(mchat_channel_id);
            CREATE INDEX IF NOT EXISTS idx_mchat_channel_mapping_agent_room ON mchat_channel_mapping(agent_room_id);
            CREATE INDEX IF NOT EXISTS idx_mchat_channel_mapping_sync ON mchat_channel_mapping(sync_enabled);
        """)
        await _db_connection.commit()
    except Exception:
        pass

    # mchat_channel_mapping에 summary 컬럼 추가 (기존 DB 마이그레이션)
    try:
        await _db_connection.execute("ALTER TABLE mchat_channel_mapping ADD COLUMN summary_enabled BOOLEAN DEFAULT 0")
        await _db_connection.commit()
    except Exception:
        pass

    try:
        await _db_connection.execute("ALTER TABLE mchat_channel_mapping ADD COLUMN summary_interval_hours INTEGER DEFAULT 24")
        await _db_connection.commit()
    except Exception:
        pass

    # mchat_summary_log 테이블 마이그레이션 (기존 DB용)
    try:
        await _db_connection.executescript("""
            CREATE TABLE IF NOT EXISTS mchat_summary_log (
                id TEXT PRIMARY KEY,
                mchat_channel_id TEXT NOT NULL,
                channel_name TEXT,
                period_start_ms INTEGER NOT NULL,
                period_end_ms INTEGER NOT NULL,
                message_count INTEGER DEFAULT 0,
                participant_count INTEGER DEFAULT 0,
                summary_content TEXT NOT NULL,
                memory_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            );
            CREATE INDEX IF NOT EXISTS idx_mchat_summary_log_channel ON mchat_summary_log(mchat_channel_id);
            CREATE INDEX IF NOT EXISTS idx_mchat_summary_log_created ON mchat_summary_log(created_at);
        """)
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
