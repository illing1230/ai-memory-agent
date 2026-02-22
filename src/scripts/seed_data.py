"""테스트용 가짜 데이터 생성 스크립트"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
import aiosqlite
from src.config import get_settings
from src.shared.database import init_database, close_database, get_db_sync
from src.shared.vector_store import init_vector_store, close_vector_store, upsert_vector
from src.shared.providers import get_embedding_provider
from src.shared.auth import hash_password

# ==================== 샘플 데이터 정의 ====================

DEPARTMENTS = [
    {"name": "품질팀", "description": "제품 품질 관리 및 검사 담당"},
    {"name": "개발팀", "description": "소프트웨어 개발 담당"},
    {"name": "기획팀", "description": "제품 기획 및 전략 수립"},
]

USERS = [
    # 개발자 테스트 계정 (프론트엔드 dev-user-001과 매칭)
    {"id": "dev-user-001", "name": "개발자", "email": "admin@test.com", "dept_idx": 1, "role": "admin"},
    # 품질팀
    {"name": "김품질", "email": "kim.quality@samsung.com", "dept_idx": 0},
    {"name": "이검사", "email": "lee.inspector@samsung.com", "dept_idx": 0},
    {"name": "박관리", "email": "park.manager@samsung.com", "dept_idx": 0},
    # 개발팀
    {"name": "최개발", "email": "choi.dev@samsung.com", "dept_idx": 1},
    {"name": "정백엔드", "email": "jung.backend@samsung.com", "dept_idx": 1},
    {"name": "강프론트", "email": "kang.frontend@samsung.com", "dept_idx": 1},
    {"name": "윤데이터", "email": "yoon.data@samsung.com", "dept_idx": 1},
    # 기획팀
    {"name": "한기획", "email": "han.planner@samsung.com", "dept_idx": 2},
    {"name": "서전략", "email": "seo.strategy@samsung.com", "dept_idx": 2},
    {"name": "임분석", "email": "lim.analyst@samsung.com", "dept_idx": 2},
]

PROJECTS = [
    {"name": "PLM 시스템", "description": "제품 생명주기 관리 시스템", "dept_idx": 0},
    {"name": "MemGate", "description": "AI 메모리 관리 플랫폼", "dept_idx": 1},
    {"name": "RAG 시스템", "description": "검색 증강 생성 시스템", "dept_idx": 1},
    {"name": "품질 대시보드", "description": "품질 지표 시각화", "dept_idx": 0},
    {"name": "신제품 기획", "description": "2025년 신제품 기획", "dept_idx": 2},
]

# 프로젝트 멤버 매핑 (project_idx -> user_idx 리스트)
# 인덱스: 0=개발자, 1=김품질, 2=이검사, 3=박관리, 4=최개발, 5=정백엔드, 6=강프론트, 7=윤데이터, 8=한기획, 9=서전략, 10=임분석
PROJECT_MEMBERS = {
    0: [1, 2, 3],  # PLM 시스템 - 품질팀 전원
    1: [0, 4, 5, 6, 7],  # MemGate - 개발자 + 개발팀 전원
    2: [4, 5, 7],  # RAG 시스템 - 개발팀 일부
    3: [1, 2, 8],  # 품질 대시보드 - 품질팀 + 기획팀
    4: [8, 9, 10],  # 신제품 기획 - 기획팀 전원
}

CHAT_ROOMS = [
    # 개인 대화방
    {"name": "개발자의 메모", "room_type": "personal", "owner_idx": 0},
    {"name": "김품질의 메모", "room_type": "personal", "owner_idx": 1},
    {"name": "최개발의 메모", "room_type": "personal", "owner_idx": 4},
    {"name": "한기획의 메모", "room_type": "personal", "owner_idx": 8},
    # 프로젝트 대화방
    {"name": "PLM 개발 채팅", "room_type": "project", "owner_idx": 1, "project_idx": 0},
    {"name": "MemGate 개발 채팅", "room_type": "project", "owner_idx": 0, "project_idx": 1},
    {"name": "RAG 논의", "room_type": "project", "owner_idx": 5, "project_idx": 2},
    # 부서 대화방
    {"name": "품질팀 공유", "room_type": "department", "owner_idx": 1, "dept_idx": 0},
    {"name": "개발팀 공유", "room_type": "department", "owner_idx": 0, "dept_idx": 1},
    {"name": "기획팀 공유", "room_type": "department", "owner_idx": 8, "dept_idx": 2},
]

# 대화방 멤버 매핑 (chat_room_idx -> user_idx 리스트)
# 인덱스: 0=개발자, 1=김품질, 2=이검사, 3=박관리, 4=최개발, 5=정백엔드, 6=강프론트, 7=윤데이터, 8=한기획, 9=서전략, 10=임분석
CHAT_ROOM_MEMBERS = {
    0: [0],  # 개발자의 메모 - 개발자만
    1: [1],  # 김품질의 메모 - 김품질만
    2: [4],  # 최개발의 메모 - 최개발만
    3: [8],  # 한기획의 메모 - 한기획만
    4: [1, 2, 3],  # PLM 개발 채팅 - 품질팀 전원
    5: [0, 4, 5, 6, 7],  # MemGate 개발 채팅 - 개발자 + 개발팀 전원
    6: [4, 5, 7],  # RAG 논의 - 개발팀 일부
    7: [1, 2, 8],  # 품질팀 공유 - 품질팀 + 기획팀
    8: [0, 4, 5, 6, 7],  # 개발팀 공유 - 개발팀 전원
    9: [8, 9, 10],  # 기획팀 공유 - 기획팀 전원
}

MEMORIES = [
    # 개인 메모리
    {
        "content": "김품질은 코드 리뷰를 오전에 하는 것을 선호한다",
        "scope": "personal",
        "owner_idx": 1,
        "category": "preference",
        "importance": "medium",
        "topic_key": "김품질 코드 리뷰 시간",
    },
    {
        "content": "최개발은 Python보다 Rust를 선호한다",
        "scope": "personal",
        "owner_idx": 4,
        "category": "preference",
        "importance": "high",
        "topic_key": "최개발 언어 선호",
    },
    {
        "content": "한기획은 매주 금요일에 주간 보고서를 작성한다",
        "scope": "personal",
        "owner_idx": 8,
        "category": "fact",
        "importance": "medium",
        "topic_key": "한기획 주간 보고서",
    },
    # 추가 메모리
    {
        "content": "김품질은 커피보다 녹차를 선호한다",
        "scope": "personal",
        "owner_idx": 1,
        "category": "preference",
        "importance": "low",
        "topic_key": "김품질 음료 선호",
    },
    {
        "content": "최개발의 업무 집중 시간은 오후 2시~5시이다",
        "scope": "personal",
        "owner_idx": 4,
        "category": "preference",
        "importance": "medium",
        "topic_key": "최개발 업무 시간",
    },
    # 엔티티 관계 테스트용 메모리
    {
        "content": "박관리가 PLM 시스템 프로젝트를 총괄 관리하고 있다",
        "scope": "chatroom",
        "owner_idx": 1,
        "chat_room_idx": 4,  # PLM 개발 채팅
        "category": "relationship",
        "importance": "high",
        "topic_key": "박관리 PLM 관리",
        "entities": [
            {"name": "박관리", "type": "person"},
            {"name": "PLM 시스템", "type": "project"},
        ],
    },
    {
        "content": "김품질이 매주 월요일 품질검사 미팅에 참석한다",
        "scope": "chatroom",
        "owner_idx": 1,
        "chat_room_idx": 4,  # PLM 개발 채팅
        "category": "fact",
        "importance": "high",
        "topic_key": "김품질 품질검사 미팅",
        "entities": [
            {"name": "김품질", "type": "person"},
            {"name": "품질검사 미팅", "type": "meeting"},
        ],
    },
    {
        "content": "품질검사 미팅은 PLM 시스템 프로젝트의 정기 회의이다",
        "scope": "chatroom",
        "owner_idx": 1,
        "chat_room_idx": 4,  # PLM 개발 채팅
        "category": "fact",
        "importance": "medium",
        "topic_key": "품질검사 미팅 PLM",
        "entities": [
            {"name": "품질검사 미팅", "type": "meeting"},
            {"name": "PLM 시스템", "type": "project"},
        ],
    },
    {
        "content": "이검사가 PLM 시스템의 테스트 자동화를 담당하고 있다",
        "scope": "chatroom",
        "owner_idx": 1,
        "chat_room_idx": 4,  # PLM 개발 채팅
        "category": "relationship",
        "importance": "high",
        "topic_key": "이검사 테스트 자동화",
        "entities": [
            {"name": "이검사", "type": "person"},
            {"name": "PLM 시스템", "type": "project"},
        ],
    },
    {
        "content": "최개발이 MemGate 프로젝트의 백엔드 아키텍처를 설계했다",
        "scope": "chatroom",
        "owner_idx": 0,
        "chat_room_idx": 5,  # MemGate 개발 채팅
        "category": "fact",
        "importance": "high",
        "topic_key": "최개발 MemGate 아키텍처",
        "entities": [
            {"name": "최개발", "type": "person"},
            {"name": "MemGate", "type": "project"},
        ],
    },
    {
        "content": "정백엔드가 MemGate 프로젝트의 RAG 파이프라인을 구현 중이다",
        "scope": "chatroom",
        "owner_idx": 0,
        "chat_room_idx": 5,  # MemGate 개발 채팅
        "category": "fact",
        "importance": "high",
        "topic_key": "정백엔드 RAG 구현",
        "entities": [
            {"name": "정백엔드", "type": "person"},
            {"name": "MemGate", "type": "project"},
        ],
    },
    {
        "content": "3월 릴리즈 일정이 MemGate 프로젝트의 첫 번째 마일스톤이다",
        "scope": "chatroom",
        "owner_idx": 0,
        "chat_room_idx": 5,  # MemGate 개발 채팅
        "category": "decision",
        "importance": "high",
        "topic_key": "MemGate 3월 릴리즈",
        "entities": [
            {"name": "3월 릴리즈", "type": "date"},
            {"name": "MemGate", "type": "project"},
        ],
    },
]

# 엔티티 관계 시드 데이터 (entities 자동 생성 후 relation 연결)
# owner_idx는 해당 관계를 생성한 사용자 인덱스
ENTITY_RELATIONS = [
    # PLM 프로젝트 관계
    {"source": "박관리", "source_type": "person", "target": "PLM 시스템", "target_type": "project", "relation": "MANAGES", "owner_idx": 1},
    {"source": "김품질", "source_type": "person", "target": "품질검사 미팅", "target_type": "meeting", "relation": "ATTENDS", "owner_idx": 1},
    {"source": "품질검사 미팅", "source_type": "meeting", "target": "PLM 시스템", "target_type": "project", "relation": "PART_OF", "owner_idx": 1},
    {"source": "이검사", "source_type": "person", "target": "PLM 시스템", "target_type": "project", "relation": "WORKS_ON", "owner_idx": 1},
    # MemGate 프로젝트 관계
    {"source": "최개발", "source_type": "person", "target": "MemGate", "target_type": "project", "relation": "WORKS_ON", "owner_idx": 0},
    {"source": "정백엔드", "source_type": "person", "target": "MemGate", "target_type": "project", "relation": "WORKS_ON", "owner_idx": 0},
    {"source": "3월 릴리즈", "source_type": "date", "target": "MemGate", "target_type": "project", "relation": "PART_OF", "owner_idx": 0},
]

# Agent Types (에이전트 유형/템플릿)
AGENT_TYPES = [
    {
        "name": "고객 지원 챗봇",
        "description": "고객 문의를 자동으로 처리하는 챗봇 템플릿",
        "developer_idx": 0,  # 개발자
        "version": "1.0.0",
        "capabilities": ["memory", "message", "log"],
        "public_scope": "public",
        "status": "active",
    },
    {
        "name": "문서 분석 에이전트",
        "description": "문서를 분석하고 요약하는 에이전트 템플릿",
        "developer_idx": 0,  # 개발자
        "version": "1.0.0",
        "capabilities": ["memory", "log"],
        "public_scope": "public",
        "status": "active",
    },
    {
        "name": "코드 리뷰 봇",
        "description": "코드를 자동으로 리뷰하는 봇 템플릿",
        "developer_idx": 4,  # 최개발
        "version": "1.0.0",
        "capabilities": ["memory", "message"],
        "public_scope": "project",
        "project_idx": 1,  # MemGate
        "status": "active",
    },
]

# Agent Instances (사용자가 생성한 에이전트 인스턴스)
AGENT_INSTANCES = [
    {
        "name": "My Bot",
        "agent_type_idx": 0,  # 고객 지원 챗봇
        "owner_idx": 0,  # 개발자
        "status": "active",
    },
    {
        "name": "품질팀 봇",
        "agent_type_idx": 0,  # 고객 지원 챗봇
        "owner_idx": 1,  # 김품질
        "status": "active",
    },
    {
        "name": "문서 분석기",
        "agent_type_idx": 1,  # 문서 분석 에이전트
        "owner_idx": 0,  # 개발자
        "status": "active",
    },
]

# Agent Data (에이전트가 수신한 데이터)
AGENT_DATA = [
    {
        "agent_instance_idx": 0,  # My Bot
        "external_user_id": "user123",
        "internal_user_idx": 0,  # 개발자
        "data_type": "memory",
        "content": "사용자는 Python과 JavaScript를 모두 사용할 수 있다",
        "metadata": {"source": "chat", "timestamp": "2025-01-15T10:30:00Z"},
    },
    {
        "agent_instance_idx": 0,  # My Bot
        "external_user_id": "user123",
        "internal_user_idx": 0,  # 개발자
        "data_type": "message",
        "content": "안녕하세요, 오늘 날씨가 어때요?",
        "metadata": {"source": "chat", "timestamp": "2025-01-15T10:31:00Z"},
    },
    {
        "agent_instance_idx": 0,  # My Bot
        "external_user_id": "user456",
        "internal_user_idx": 0,  # 개발자
        "data_type": "memory",
        "content": "사용자는 주말에 등산을 간다",
        "metadata": {"source": "chat", "timestamp": "2025-01-16T14:20:00Z"},
    },
    {
        "agent_instance_idx": 1,  # 품질팀 봇
        "external_user_id": "quality_user1",
        "internal_user_idx": 1,  # 김품질
        "data_type": "memory",
        "content": "품질 검사는 매주 월요일과 목요일에 진행된다",
        "metadata": {"source": "chat", "timestamp": "2025-01-17T09:00:00Z"},
    },
    {
        "agent_instance_idx": 1,  # 품질팀 봇
        "external_user_id": "quality_user1",
        "internal_user_idx": 1,  # 김품질
        "data_type": "log",
        "content": "품질 검사 완료: 100개 항목 통과",
        "metadata": {"source": "system", "timestamp": "2025-01-17T17:00:00Z"},
    },
    {
        "agent_instance_idx": 2,  # 문서 분석기
        "external_user_id": "doc_user1",
        "internal_user_idx": 0,  # 개발자
        "data_type": "memory",
        "content": "문서 분석 결과: 주요 키워드는 AI, 머신러닝, 딥러닝",
        "metadata": {"source": "document", "timestamp": "2025-01-18T11:00:00Z"},
    },
]

# External User Mappings (외부 시스템 사용자 매핑)
EXTERNAL_USER_MAPPINGS = [
    {
        "agent_instance_idx": 0,  # My Bot
        "external_user_id": "user123",
        "internal_user_idx": 0,  # 개발자
        "external_system_name": "external_chat_system",
    },
    {
        "agent_instance_idx": 0,  # My Bot
        "external_user_id": "user456",
        "internal_user_idx": 0,  # 개발자
        "external_system_name": "external_chat_system",
    },
    {
        "agent_instance_idx": 1,  # 품질팀 봇
        "external_user_id": "quality_user1",
        "internal_user_idx": 1,  # 김품질
        "external_system_name": "quality_system",
    },
    {
        "agent_instance_idx": 2,  # 문서 분석기
        "external_user_id": "doc_user1",
        "internal_user_idx": 0,  # 개발자
        "external_system_name": "document_system",
    },
]

# Agent Instance Shares (에이전트 인스턴스 공유)
AGENT_INSTANCE_SHARES = [
    {
        "agent_instance_idx": 0,  # My Bot
        "shared_with_user_idx": 4,  # 최개발
        "role": "viewer",
    },
    {
        "agent_instance_idx": 1,  # 품질팀 봇
        "shared_with_user_idx": 2,  # 이검사
        "role": "member",
    },
]

# 공유 설정 (resource_type, resource_idx, target_type, target_idx, role, created_by_idx)
# resource_idx: project_idx 또는 chat_room_idx
# target_idx: user_idx, project_idx, dept_idx
SHARES = [
    # 프로젝트 공유
    {"resource_type": "project", "resource_idx": 0, "target_type": "user", "target_idx": 4, "role": "member", "created_by_idx": 1},  # PLM 시스템 -> 최개발
    {"resource_type": "project", "resource_idx": 1, "target_type": "user", "target_idx": 1, "role": "viewer", "created_by_idx": 0},  # MemGate -> 김품질
    {"resource_type": "project", "resource_idx": 2, "target_type": "project", "target_idx": 1, "role": "member", "created_by_idx": 5},  # RAG 시스템 -> MemGate
    {"resource_type": "project", "resource_idx": 3, "target_type": "department", "target_idx": 1, "role": "viewer", "created_by_idx": 1},  # 품질 대시보드 -> 개발팀
    
    # 대화방 공유
    {"resource_type": "chat_room", "resource_idx": 4, "target_type": "user", "target_idx": 4, "role": "member", "created_by_idx": 1},  # PLM 개발 채팅 -> 최개발
    {"resource_type": "chat_room", "resource_idx": 5, "target_type": "user", "target_idx": 1, "role": "viewer", "created_by_idx": 0},  # MemGate 개발 채팅 -> 김품질
    {"resource_type": "chat_room", "resource_idx": 6, "target_type": "project", "target_idx": 1, "role": "member", "created_by_idx": 5},  # RAG 논의 -> MemGate
    {"resource_type": "chat_room", "resource_idx": 7, "target_type": "department", "target_idx": 1, "role": "viewer", "created_by_idx": 1},  # 품질팀 공유 -> 개발팀
]

async def seed_data():
    """가짜 데이터 생성"""
    print("🌱 가짜 데이터 생성 시작...")
    
    # 초기화
    await init_database()
    
    # Qdrant 연결 (타임아웃 10초, 실패해도 계속 진행)
    try:
        await asyncio.wait_for(init_vector_store(), timeout=10)
    except asyncio.TimeoutError:
        print("⚠️  Qdrant 연결 타임아웃 (벡터 검색 기능 비활성화)")
    except Exception as e:
        print(f"⚠️  Qdrant 연결 실패 (벡터 검색 기능 비활성화): {e}")
    
    db = await get_db_sync()
    
    # 임베딩 프로바이더 (연결 실패해도 계속 진행)
    embedding_provider = None
    try:
        embedding_provider = get_embedding_provider()
        print("✅ Embedding Provider 연결됨")
    except Exception as e:
        print(f"⚠️  Embedding Provider 연결 실패 (메모리 벡터 없이 진행): {e}")
    
    try:
        # 1. 부서 생성
        print("\n📁 부서 생성...")
        dept_ids = []
        for dept in DEPARTMENTS:
            dept_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO departments (id, name, description) VALUES (?, ?, ?)",
                (dept_id, dept["name"], dept["description"]),
            )
            dept_ids.append(dept_id)
            print(f"  ✓ {dept['name']}")
        
        # 2. 사용자 생성
        print("\n👤 사용자 생성...")
        user_ids = []
        
        # 테스트 사용자 비밀번호 설정
        settings = get_settings()
        test_password = getattr(settings, 'test_user_password', 'test123')
        test_password_hash = hash_password(test_password)
        
        for i, user in enumerate(USERS):
            # 미리 정의된 ID가 있으면 사용, 없으면 UUID 생성
            user_id = user.get("id", str(uuid.uuid4()))
            role = user.get("role", "user")
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            
            # admin 계정(dev-user-001)은 비밀번호 설정하지 않음
            # 나머지 테스트 사용자들에게 TEST_USER_PASSWORD 적용
            password_hash = None
            if user_id != "dev-user-001":
                password_hash = test_password_hash
            
            await db.execute(
                """INSERT INTO users (id, name, email, role, department_id, password_hash, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, user["name"], user["email"], role, dept_ids[user["dept_idx"]], password_hash, now, now),
            )
            user_ids.append(user_id)
            password_info = f" (비밀번호: {test_password})" if password_hash else " (비밀번호 없음)"
            print(f"  ✓ {user['name']} ({user['email']}) - {user_id}{password_info}")
        
        # 3. 프로젝트 생성
        print("\n📋 프로젝트 생성...")
        project_ids = []
        for project in PROJECTS:
            project_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            await db.execute(
                """INSERT INTO projects (id, name, description, department_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_id, project["name"], project["description"],
                  dept_ids[project["dept_idx"]], now, now),
            )
            project_ids.append(project_id)
            print(f"  ✓ {project['name']}")
        
        # 4. 프로젝트 멤버 추가
        print("\n👥 프로젝트 멤버 추가...")
        for proj_idx, member_indices in PROJECT_MEMBERS.items():
            for i, user_idx in enumerate(member_indices):
                member_id = str(uuid.uuid4())
                role = "owner" if i == 0 else "member"
                await db.execute(
                    """INSERT INTO project_members (id, project_id, user_id, role)
                       VALUES (?, ?, ?, ?)""",
                    (member_id, project_ids[proj_idx], user_ids[user_idx], role),
                )
            print(f"  ✓ {PROJECTS[proj_idx]['name']}: {len(member_indices)}명")
        
        # 5. 대화방 생성
        print("\n💬 대화방 생성...")
        chat_room_ids = []
        for room in CHAT_ROOMS:
            room_id = str(uuid.uuid4())
            project_id = project_ids[room["project_idx"]] if "project_idx" in room else None
            department_id = dept_ids[room["dept_idx"]] if "dept_idx" in room else None
            await db.execute(
                """INSERT INTO chat_rooms (id, name, room_type, owner_id, project_id, department_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (room_id, room["name"], room["room_type"],
                  user_ids[room["owner_idx"]], project_id, department_id),
            )
            chat_room_ids.append(room_id)
            print(f"  ✓ {room['name']} ({room['room_type']})")
        
        # 6. 대화방 멤버 추가
        print("\n👥 대화방 멤버 추가...")
        for room_idx, member_indices in CHAT_ROOM_MEMBERS.items():
            for i, user_idx in enumerate(member_indices):
                member_id = str(uuid.uuid4())
                role = "owner" if i == 0 else "member"
                await db.execute(
                    """INSERT INTO chat_room_members (id, chat_room_id, user_id, role)
                       VALUES (?, ?, ?, ?)""",
                    (member_id, chat_room_ids[room_idx], user_ids[user_idx], role),
                )
            print(f"  ✓ {CHAT_ROOMS[room_idx]['name']}: {len(member_indices)}명")
        
        # 7. Agent Types 생성
        print("\n🤖 Agent Types 생성...")
        agent_type_ids = []
        for agent_type in AGENT_TYPES:
            agent_type_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            project_id = project_ids[agent_type["project_idx"]] if "project_idx" in agent_type else None
            
            import json
            await db.execute(
                """INSERT INTO agent_types (id, name, description, developer_id, version, capabilities, public_scope, project_id, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (agent_type_id, agent_type["name"], agent_type["description"],
                  user_ids[agent_type["developer_idx"]], agent_type["version"],
                  json.dumps(agent_type["capabilities"]), agent_type["public_scope"],
                  project_id, agent_type["status"], now, now),
            )
            agent_type_ids.append(agent_type_id)
            print(f"  ✓ {agent_type['name']} ({agent_type['public_scope']})")
        
        # 8. Agent Instances 생성
        print("\n🤖 Agent Instances 생성...")
        agent_instance_ids = []
        for agent_instance in AGENT_INSTANCES:
            agent_instance_id = str(uuid.uuid4())
            api_key = f"sk_{uuid.uuid4().hex}"
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            
            await db.execute(
                """INSERT INTO agent_instances (id, agent_type_id, name, owner_id, api_key, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (agent_instance_id, agent_type_ids[agent_instance["agent_type_idx"]],
                  agent_instance["name"], user_ids[agent_instance["owner_idx"]],
                  api_key, agent_instance["status"], now, now),
            )
            agent_instance_ids.append(agent_instance_id)
            print(f"  ✓ {agent_instance['name']} (API Key: {api_key[:20]}...)")
        
        # 9. External User Mappings 생성
        print("\n🔗 External User Mappings 생성...")
        for mapping in EXTERNAL_USER_MAPPINGS:
            mapping_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            
            await db.execute(
                """INSERT INTO external_user_mappings (id, agent_instance_id, external_user_id, internal_user_id, external_system_name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (mapping_id, agent_instance_ids[mapping["agent_instance_idx"]],
                  mapping["external_user_id"], user_ids[mapping["internal_user_idx"]],
                  mapping["external_system_name"], now),
            )
            print(f"  ✓ {mapping['external_user_id']} -> {USERS[mapping['internal_user_idx']]['name']}")
        
        # 10. Agent Data 생성
        print("\n📊 Agent Data 생성...")
        for agent_data in AGENT_DATA:
            data_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            
            import json
            await db.execute(
                """INSERT INTO agent_data (id, agent_instance_id, external_user_id, internal_user_id, data_type, content, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (data_id, agent_instance_ids[agent_data["agent_instance_idx"]],
                  agent_data["external_user_id"], user_ids[agent_data["internal_user_idx"]],
                  agent_data["data_type"], agent_data["content"],
                  json.dumps(agent_data["metadata"]), now),
            )
            print(f"  ✓ {agent_data['data_type']}: {agent_data['content'][:40]}...")
        
        # 10.5. Agent 메모리 생성 (type="memory"인 Agent Data만)
        print("\n🤖 Agent 메모리 생성...")
        agent_memory_ids = []
        agent_embedding_failed = False  # Agent 메모리용 임베딩 실패 플래그
        for agent_data in AGENT_DATA:
            if agent_data["data_type"] == "memory":
                memory_id = str(uuid.uuid4())
                vector_id = str(uuid.uuid4())
                now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
                
                # 임베딩 생성
                vector = None
                if embedding_provider and not agent_embedding_failed:
                    try:
                        vector = await asyncio.wait_for(
                            embedding_provider.embed(agent_data["content"]), timeout=10
                        )
                    except Exception as e:
                        print(f"  ⚠ 임베딩 실패: {e}")
                        vector = None
                        vector_id = None
                        agent_embedding_failed = True
                else:
                    vector_id = None
                
                # SQLite에 저장 (scope='agent')
                import json
                metadata = agent_data["metadata"].copy()
                metadata["source"] = "agent"
                metadata["agent_instance_id"] = agent_instance_ids[agent_data["agent_instance_idx"]]
                metadata["agent_instance_name"] = AGENT_INSTANCES[agent_data["agent_instance_idx"]]["name"]
                
                await db.execute(
                    """INSERT INTO memories
                        (id, content, vector_id, scope, owner_id, category, importance, metadata, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (memory_id, agent_data["content"], vector_id, "agent",
                      user_ids[agent_data["internal_user_idx"]], "fact", "medium",
                      json.dumps(metadata), now, now),
                )
                
                # Qdrant에 저장
                if vector and vector_id:
                    payload = {
                        "memory_id": memory_id,
                        "scope": "agent",
                        "owner_id": user_ids[agent_data["internal_user_idx"]],
                        "agent_instance_id": agent_instance_ids[agent_data["agent_instance_idx"]],
                    }
                    await upsert_vector(vector_id, vector, payload)
                
                agent_memory_ids.append(memory_id)
                print(f"  🤖 {agent_data['content'][:40]}...")
        
        # 11. Agent Instance Shares 생성
        print("\n🔗 Agent Instance Shares 생성...")
        for share in AGENT_INSTANCE_SHARES:
            share_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            
            await db.execute(
                """INSERT INTO agent_instance_shares (id, agent_instance_id, shared_with_user_id, role, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (share_id, agent_instance_ids[share["agent_instance_idx"]],
                  user_ids[share["shared_with_user_idx"]], share["role"], now),
            )
            print(f"  ✓ {AGENT_INSTANCES[share['agent_instance_idx']]['name']} -> {USERS[share['shared_with_user_idx']]['name']} ({share['role']})")
        
        # 12. 메모리 생성 (벡터 포함)
        print("\n🧠 메모리 생성...")
        memory_ids = []
        embedding_failed = False  # 임베딩 한 번 실패하면 이후 스킵
        for mem in MEMORIES:
            memory_id = str(uuid.uuid4())
            vector_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()

            # 임베딩 생성 (프로바이더 있고, 이전에 실패하지 않았을 때만)
            vector = None
            if embedding_provider and not embedding_failed:
                try:
                    vector = await asyncio.wait_for(
                        embedding_provider.embed(mem["content"]), timeout=10
                    )
                except Exception as e:
                    print(f"  ⚠ 임베딩 실패 (이후 임베딩 스킵): {e}")
                    vector = None
                    vector_id = None
                    embedding_failed = True
            else:
                vector_id = None

            # chat_room_id 처리
            chat_room_id = None
            if "chat_room_idx" in mem:
                chat_room_id = chat_room_ids[mem["chat_room_idx"]]

            # SQLite에 저장
            topic_key = mem.get("topic_key")
            await db.execute(
                """INSERT INTO memories
                    (id, content, vector_id, scope, owner_id, chat_room_id,
                    category, importance, topic_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (memory_id, mem["content"], vector_id, mem["scope"],
                  user_ids[mem["owner_idx"]], chat_room_id,
                  mem.get("category"), mem.get("importance", "medium"), topic_key, now, now),
            )

            # Qdrant에 저장
            if vector and vector_id:
                payload = {
                    "memory_id": memory_id,
                    "scope": mem["scope"],
                    "owner_id": user_ids[mem["owner_idx"]],
                }
                if chat_room_id:
                    payload["chat_room_id"] = chat_room_id
                await upsert_vector(vector_id, vector, payload)

            # 엔티티 연결 (entities 필드가 있는 경우)
            if "entities" in mem:
                for ent in mem["entities"]:
                    ent_name = ent["name"]
                    ent_type = ent["type"]
                    owner_id = user_ids[mem["owner_idx"]]
                    name_normalized = ent_name.strip().lower()

                    # get_or_create entity
                    cursor = await db.execute(
                        "SELECT id FROM entities WHERE name_normalized = ? AND entity_type = ? AND owner_id = ?",
                        (name_normalized, ent_type, owner_id),
                    )
                    row = await cursor.fetchone()
                    if row:
                        entity_id = row[0]
                    else:
                        entity_id = str(uuid.uuid4())
                        await db.execute(
                            "INSERT INTO entities (id, name, name_normalized, entity_type, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (entity_id, ent_name, name_normalized, ent_type, owner_id, now, now),
                        )

                    # link memory <-> entity
                    link_id = str(uuid.uuid4())
                    await db.execute(
                        "INSERT OR IGNORE INTO memory_entities (id, memory_id, entity_id, relation_type) VALUES (?, ?, ?, ?)",
                        (link_id, memory_id, entity_id, "mentioned"),
                    )
                    print(f"    🔗 엔티티 연결: {ent_name} ({ent_type})")

            memory_ids.append(memory_id)
            print(f"  👤 {mem['content'][:40]}...")
        
        # 12.5. 엔티티 관계 생성
        print("\n🔗 엔티티 관계 생성...")
        for rel in ENTITY_RELATIONS:
            owner_id = user_ids[rel["owner_idx"]]
            src_norm = rel["source"].strip().lower()
            tgt_norm = rel["target"].strip().lower()

            # source entity 조회
            cursor = await db.execute(
                "SELECT id FROM entities WHERE name_normalized = ? AND entity_type = ? AND owner_id = ?",
                (src_norm, rel["source_type"], owner_id),
            )
            src_row = await cursor.fetchone()

            # target entity 조회
            cursor = await db.execute(
                "SELECT id FROM entities WHERE name_normalized = ? AND entity_type = ? AND owner_id = ?",
                (tgt_norm, rel["target_type"], owner_id),
            )
            tgt_row = await cursor.fetchone()

            if src_row and tgt_row:
                rel_id = str(uuid.uuid4())
                await db.execute(
                    "INSERT OR IGNORE INTO entity_relations (id, source_entity_id, target_entity_id, relation_type, owner_id) VALUES (?, ?, ?, ?, ?)",
                    (rel_id, src_row[0], tgt_row[0], rel["relation"], owner_id),
                )
                print(f"  ✓ {rel['source']} →{rel['relation']}→ {rel['target']}")
            else:
                missing = []
                if not src_row:
                    missing.append(f"source={rel['source']}")
                if not tgt_row:
                    missing.append(f"target={rel['target']}")
                print(f"  ⚠ 엔티티 없음: {', '.join(missing)}")

        # 12.6. superseded 관계 설정
        print("\n🔄 superseded 관계 설정...")
        for i, mem in enumerate(MEMORIES):
            if "supersedes_idx" in mem:
                superseded_memory_id = memory_ids[mem["supersedes_idx"]]
                new_memory_id = memory_ids[i]
                now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
                
                # 이전 메모리를 superseded로 표시
                await db.execute(
                    """UPDATE memories
                        SET superseded = 1, superseded_by = ?, superseded_at = ?
                       WHERE id = ?""",
                    (new_memory_id, now, superseded_memory_id)
                )
                
                print(f"  ✓ {MEMORIES[mem['supersedes_idx']]['content'][:30]}... -> {mem['content'][:30]}...")
        
        # 13. 공유 설정 생성
        print("\n🔗 공유 설정 생성...")
        for share in SHARES:
            share_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()
            
            # 리소스 ID 결정
            if share["resource_type"] == "project":
                resource_id = project_ids[share["resource_idx"]]
                resource_name = PROJECTS[share["resource_idx"]]["name"]
            else:  # chat_room
                resource_id = chat_room_ids[share["resource_idx"]]
                resource_name = CHAT_ROOMS[share["resource_idx"]]["name"]
            
            # 타겟 ID 결정
            if share["target_type"] == "user":
                target_id = user_ids[share["target_idx"]]
                target_name = USERS[share["target_idx"]]["name"]
            elif share["target_type"] == "project":
                target_id = project_ids[share["target_idx"]]
                target_name = PROJECTS[share["target_idx"]]["name"]
            else:  # department
                target_id = dept_ids[share["target_idx"]]
                target_name = DEPARTMENTS[share["target_idx"]]["name"]
            
            await db.execute(
                """INSERT INTO shares (id, resource_type, resource_id, target_type, target_id, role, created_at, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (share_id, share["resource_type"], resource_id, share["target_type"], target_id,
                  share["role"], now, user_ids[share["created_by_idx"]]),
            )
            
            target_icon = {"user": "👤", "project": "📋", "department": "🏢"}
            print(f"  ✓ {resource_name} -> {target_icon[share['target_type']]} {target_name} ({share['role']})")
        
        await db.commit()
        
        # 요약 출력
        print("\n" + "=" * 50)
        print("✅ 가짜 데이터 생성 완료!")
        print("=" * 50)
        print(f"  📁 부서: {len(DEPARTMENTS)}개")
        print(f"  👤 사용자: {len(USERS)}명")
        print(f"  📋 프로젝트: {len(PROJECTS)}개")
        print(f"  💬 대화방: {len(CHAT_ROOMS)}개")
        print(f"  🤖 Agent Types: {len(AGENT_TYPES)}개")
        print(f"  🤖 Agent Instances: {len(AGENT_INSTANCES)}개")
        print(f"  📊 Agent Data: {len(AGENT_DATA)}개")
        print(f"  🔗 External User Mappings: {len(EXTERNAL_USER_MAPPINGS)}개")
        print(f"  🔗 Agent Instance Shares: {len(AGENT_INSTANCE_SHARES)}개")
        print(f"  🧠 메모리: {len(MEMORIES)}개")
        print(f"  🔗 엔티티 관계: {len(ENTITY_RELATIONS)}개")
        print(f"  🔗 공유 설정: {len(SHARES)}개")
        print("=" * 50)
        
        # 테스트용 사용자 ID 출력
        print("\n📌 테스트용 사용자 ID:")
        for i, user in enumerate(USERS[:4]):
            print(f"  {user['name']}: {user_ids[i]}")
        
        # Agent Instance API Key 출력
        print("\n📌 Agent Instance API Keys:")
        for i, agent_instance in enumerate(AGENT_INSTANCES):
            print(f"  {agent_instance['name']}: {agent_instance_ids[i]}")
    
    finally:
        await db.close()
        await close_database()
        await close_vector_store()

if __name__ == "__main__":
    asyncio.run(seed_data())
