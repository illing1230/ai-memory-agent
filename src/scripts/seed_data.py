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
    {"id": "dev-user-001", "name": "개발자", "email": "dev@test.local", "dept_idx": 1, "role": "admin"},
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
    # 개인 채팅방
    {"name": "개발자의 메모", "room_type": "personal", "owner_idx": 0},
    {"name": "김품질의 메모", "room_type": "personal", "owner_idx": 1},
    {"name": "최개발의 메모", "room_type": "personal", "owner_idx": 4},
    {"name": "한기획의 메모", "room_type": "personal", "owner_idx": 8},
    # 프로젝트 채팅방
    {"name": "PLM 개발 채팅", "room_type": "project", "owner_idx": 1, "project_idx": 0},
    {"name": "MemGate 개발 채팅", "room_type": "project", "owner_idx": 0, "project_idx": 1},
    {"name": "RAG 논의", "room_type": "project", "owner_idx": 5, "project_idx": 2},
    # 부서 채팅방
    {"name": "품질팀 공유", "room_type": "department", "owner_idx": 1, "dept_idx": 0},
    {"name": "개발팀 공유", "room_type": "department", "owner_idx": 0, "dept_idx": 1},
    {"name": "기획팀 공유", "room_type": "department", "owner_idx": 8, "dept_idx": 2},
]

# 채팅방 멤버 매핑 (chat_room_idx -> user_idx 리스트)
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
    # 프로젝트 메모리
    {
        "content": "PLM 시스템의 데이터베이스는 PostgreSQL을 사용한다",
        "scope": "project",
        "owner_idx": 1,
        "project_idx": 0,
        "category": "fact",
        "importance": "high",
        "topic_key": "PLM 데이터베이스",
    },
    {
        "content": "MemGate는 Qdrant 벡터 DB와 SQLite를 함께 사용한다",
        "scope": "project",
        "owner_idx": 0,
        "project_idx": 1,
        "category": "fact",
        "importance": "high",
        "topic_key": "MemGate 기술 스택",
    },
    {
        "content": "RAG 시스템에서 chunk 크기는 512 토큰으로 결정했다",
        "scope": "project",
        "owner_idx": 5,
        "project_idx": 2,
        "category": "decision",
        "importance": "high",
        "topic_key": "RAG chunk 크기",
    },
    {
        "content": "품질 대시보드는 Grafana로 구현하기로 했다",
        "scope": "project",
        "owner_idx": 1,
        "project_idx": 3,
        "category": "decision",
        "importance": "medium",
        "topic_key": "품질 대시보드 기술",
    },
    {
        "content": "신제품 출시일은 2025년 3월로 목표한다",
        "scope": "project",
        "owner_idx": 8,
        "project_idx": 4,
        "category": "decision",
        "importance": "high",
        "topic_key": "신제품 출시일",
    },
    # 부서 메모리
    {
        "content": "품질팀 회의는 매주 화요일 오전 10시에 진행한다",
        "scope": "department",
        "owner_idx": 1,
        "dept_idx": 0,
        "category": "fact",
        "importance": "medium",
        "topic_key": "품질팀 회의",
    },
    {
        "content": "개발팀은 GitFlow 브랜치 전략을 사용한다",
        "scope": "department",
        "owner_idx": 0,
        "dept_idx": 1,
        "category": "fact",
        "importance": "high",
        "topic_key": "개발팀 브랜치 전략",
    },
    {
        "content": "기획팀은 Notion을 공식 문서 도구로 사용한다",
        "scope": "department",
        "owner_idx": 8,
        "dept_idx": 2,
        "category": "fact",
        "importance": "medium",
        "topic_key": "기획팀 문서 도구",
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
    {
        "content": "MemGate API는 FastAPI로 구현한다",
        "scope": "project",
        "owner_idx": 5,
        "project_idx": 1,
        "category": "decision",
        "importance": "high",
        "topic_key": "MemGate API 프레임워크",
    },
    {
        "content": "RAG 시스템에서 HyDE 기법을 적용하기로 했다",
        "scope": "project",
        "owner_idx": 7,
        "project_idx": 2,
        "category": "decision",
        "importance": "high",
        "topic_key": "RAG HyDE 기법",
    },
    # UPDATE 예제 (같은 topic_key, superseded 관계)
    {
        "content": "신제품 출시일은 2025년 6월로 연기되었다",
        "scope": "project",
        "owner_idx": 8,
        "project_idx": 4,
        "category": "decision",
        "importance": "high",
        "topic_key": "신제품 출시일",
        "supersedes_idx": 7,  # 이전 메모리(2025년 3월)를 superseded
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
    
    # 채팅방 공유
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

        # 5. 채팅방 생성
        print("\n💬 채팅방 생성...")
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

        # 6. 채팅방 멤버 추가
        print("\n👥 채팅방 멤버 추가...")
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

        # 7. 메모리 생성 (벡터 포함)
        print("\n🧠 메모리 생성...")
        memory_ids = []
        embedding_failed = False  # 임베딩 한 번 실패하면 이후 스킵
        for mem in MEMORIES:
            memory_id = str(uuid.uuid4())
            vector_id = str(uuid.uuid4())
            now = (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()

            project_id = project_ids[mem["project_idx"]] if "project_idx" in mem else None
            department_id = dept_ids[mem["dept_idx"]] if "dept_idx" in mem else None

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

            # SQLite에 저장
            topic_key = mem.get("topic_key")
            await db.execute(
                """INSERT INTO memories
                    (id, content, vector_id, scope, owner_id, project_id, department_id,
                    category, importance, topic_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (memory_id, mem["content"], vector_id, mem["scope"], 
                 user_ids[mem["owner_idx"]], project_id, department_id, 
                 mem.get("category"), mem.get("importance", "medium"), topic_key, now, now),
            )

            # Qdrant에 저장
            if vector and vector_id:
                payload = {
                    "memory_id": memory_id,
                    "scope": mem["scope"],
                    "owner_id": user_ids[mem["owner_idx"]],
                    "project_id": project_id,
                    "department_id": department_id,
                }
                await upsert_vector(vector_id, vector, payload)

            memory_ids.append(memory_id)
            scope_icon = {"personal": "👤", "project": "📋", "department": "🏢"}
            print(f"  {scope_icon.get(mem['scope'], '❓')} {mem['content'][:40]}...")

        # 7.5. superseded 관계 설정
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

        # 8. 공유 설정 생성
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
        print(f"  💬 채팅방: {len(CHAT_ROOMS)}개")
        print(f"  🧠 메모리: {len(MEMORIES)}개")
        print(f"  🔗 공유 설정: {len(SHARES)}개")
        print("=" * 50)

        # 테스트용 사용자 ID 출력
        print("\n📌 테스트용 사용자 ID:")
        for i, user in enumerate(USERS[:4]):
            print(f"  {user['name']}: {user_ids[i]}")

    finally:
        await db.close()
        await close_database()
        await close_vector_store()


if __name__ == "__main__":
    asyncio.run(seed_data())
