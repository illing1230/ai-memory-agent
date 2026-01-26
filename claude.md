# AI Memory Agent

## 프로젝트 개요

AI Memory Agent는 멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템입니다.
Mem0.ai의 컨셉을 기반으로 하되, 멀티채팅 지원과 세분화된 권한 관리 기능을 추가합니다.
aa
## 핵심 기능

### 1. 멀티채팅 기반 메모리 저장
- 여러 채팅방(Room)에서 발생하는 대화를 통합 메모리로 저장
- 채팅방별 컨텍스트 분리 및 통합 검색 지원
- 실시간 메모리 추출 및 저장 (`@ai` 멘션 시 자동 추출)

### 2. 권한 기반 메모리 접근 제어
- **개인(Personal)**: 사용자 본인만 접근 가능한 메모리
- **채팅방(Chatroom)**: 해당 채팅방 멤버만 접근 가능한 메모리 ⭐ 신규
- **프로젝트(Project)**: 특정 프로젝트 참여자만 접근 가능한 메모리
- **부서(Department)**: 부서 전체가 공유하는 메모리

### 3. 하이브리드 저장소
- **SQLite**: 메타데이터, 권한, 관계 정보 저장
- **Qdrant**: 벡터 임베딩 저장 및 시맨틱 검색

### 4. 슬래시 커맨드 지원
- `/remember <내용>` - 채팅방 메모리 저장
- `/forget <검색어>` - 메모리 삭제
- `/search <검색어>` - 메모리 검색
- `/members` - 채팅방 멤버 목록
- `/invite <이메일>` - 멤버 초대
- `/help` - 도움말

---

## 기술 스택

| 구분 | 기술 | 비고 |
|------|------|------|
| Backend | FastAPI (Python 3.11+) | |
| Database | SQLite (개발) / PostgreSQL (운영) | |
| Vector DB | Qdrant | 내부망: 10.244.11.230:30011 |
| Embedding | HuggingFace (기본), OpenAI, Ollama | 내부망: smart-dna.sec.samsung.net |
| LLM | OpenAI Compatible (Qwen3-32B), Ollama, Anthropic | 내부망: 10.244.11.119:30434 |
| Frontend | Streamlit | 카카오톡 스타일 데모 UI |

---

## 프로젝트 구조 (Feature-Based)

```
ai-memory-agent/
├── claude.md                    # 프로젝트 정의서
├── pyproject.toml               # 의존성 관리
├── README.md                    # 프로젝트 설명
├── errors.md                    # 에러 트래킹
├── .env.example                 # 환경변수 템플릿
├── .env                         # 환경변수 (git 제외)
│
├── app/
│   └── streamlit_app.py         # Streamlit 데모 UI (카카오톡 스타일)
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 앱 엔트리포인트
│   ├── config.py                # 설정 관리 (pydantic-settings)
│   │
│   ├── memory/                  # ✅ 메모리 관리 기능
│   │   ├── __init__.py
│   │   ├── router.py            # API 라우터 (CRUD, 검색, 추출)
│   │   ├── service.py           # 비즈니스 로직
│   │   ├── repository.py        # 데이터 접근 계층
│   │   └── schemas.py           # Pydantic 스키마
│   │
│   ├── chat/                    # ✅ 채팅방 관리 기능
│   │   ├── __init__.py
│   │   ├── router.py            # API 라우터 (Room, Member, Message)
│   │   ├── service.py           # 비즈니스 로직 (AI 응답, 커맨드)
│   │   ├── repository.py        # 데이터 접근 계층
│   │   └── schemas.py           # Pydantic 스키마
│   │
│   ├── permission/              # ✅ 권한 관리 기능
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   ├── user/                    # ✅ 사용자/부서/프로젝트 관리
│   │   ├── __init__.py
│   │   ├── router.py            # User, Department, Project API
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   ├── scripts/                 # 유틸리티 스크립트
│   │   ├── __init__.py
│   │   └── seed_data.py         # 초기 데이터 시딩
│   │
│   └── shared/                  # 공유 모듈
│       ├── __init__.py
│       ├── database.py          # SQLite 연결 관리 + 스키마 정의
│       ├── vector_store.py      # Qdrant 연결 관리
│       ├── exceptions.py        # 커스텀 예외
│       │
│       └── providers/           # Provider 추상화
│           ├── __init__.py      # Factory 함수 export
│           ├── base.py          # 추상 베이스 클래스
│           ├── factory.py       # Provider Factory
│           ├── embedding/       # Embedding Providers
│           │   ├── __init__.py
│           │   ├── openai.py
│           │   ├── ollama.py
│           │   └── huggingface.py
│           └── llm/             # LLM Providers
│               ├── __init__.py
│               ├── openai.py    # OpenAI 호환 API (Qwen3 포함)
│               ├── ollama.py
│               └── anthropic.py
│
├── tests/                       # 테스트
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_memory/
│   ├── test_chat/
│   └── test_permission/
│
└── data/                        # 로컬 데이터 저장소
    └── sqlite/                  # SQLite DB 파일
        └── memory.db
```

---

## 데이터베이스 스키마

### SQLite 테이블 (src/shared/database.py에서 관리)

#### departments (부서)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| name | TEXT | 부서명 |
| description | TEXT | 설명 |
| created_at | DATETIME | 생성일시 |

#### users (사용자)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| name | TEXT | 사용자명 |
| email | TEXT | 이메일 (UNIQUE) |
| department_id | TEXT | FK → departments.id |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

#### projects (프로젝트)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| name | TEXT | 프로젝트명 |
| description | TEXT | 설명 |
| department_id | TEXT | FK → departments.id |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

#### project_members (프로젝트 멤버)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| project_id | TEXT | FK → projects.id |
| user_id | TEXT | FK → users.id |
| role | TEXT | 역할 (owner, admin, member) |
| joined_at | DATETIME | 참여일시 |

#### chat_rooms (채팅방)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| name | TEXT | 채팅방명 |
| room_type | TEXT | 유형 (personal, project, department) |
| owner_id | TEXT | FK → users.id |
| project_id | TEXT | FK → projects.id (nullable) |
| department_id | TEXT | FK → departments.id (nullable) |
| context_sources | TEXT (JSON) | 메모리 검색 범위 설정 |
| created_at | DATETIME | 생성일시 |

#### chat_room_members (채팅방 멤버)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| chat_room_id | TEXT | FK → chat_rooms.id |
| user_id | TEXT | FK → users.id |
| role | TEXT | 역할 (owner, admin, member) |
| joined_at | DATETIME | 참여일시 |

#### chat_messages (채팅 메시지)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| chat_room_id | TEXT | FK → chat_rooms.id |
| user_id | TEXT | 발신자 ID |
| role | TEXT | 역할 (user, assistant) |
| content | TEXT | 메시지 내용 |
| mentions | TEXT | 멘션 목록 (JSON) |
| created_at | DATETIME | 생성일시 |

#### memories (메모리)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| content | TEXT | 메모리 내용 |
| vector_id | TEXT | Qdrant 벡터 ID |
| scope | TEXT | 범위 (personal, chatroom, project, department) |
| owner_id | TEXT | FK → users.id (생성자) |
| project_id | TEXT | FK → projects.id (nullable) |
| department_id | TEXT | FK → departments.id (nullable) |
| chat_room_id | TEXT | FK → chat_rooms.id (nullable) |
| source_message_id | TEXT | 원본 메시지 ID |
| category | TEXT | 카테고리 (fact, preference, decision 등) |
| importance | TEXT | 중요도 (high, medium, low) |
| metadata | TEXT (JSON) | 추가 메타데이터 |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

#### memory_access_log (접근 로그)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| memory_id | TEXT | FK → memories.id |
| user_id | TEXT | FK → users.id |
| action | TEXT | 액션 (read, update, delete) |
| accessed_at | DATETIME | 접근일시 |

### Qdrant Collection

#### Collection: `ai-memory-agent`
```json
{
  "vectors": {
    "size": "${EMBEDDING_DIMENSION}",
    "distance": "Cosine"
  },
  "payload_schema": {
    "memory_id": "keyword",
    "scope": "keyword",
    "owner_id": "keyword",
    "project_id": "keyword",
    "department_id": "keyword",
    "chat_room_id": "keyword"
  }
}
```

**Embedding 차원 참고:**
| Provider | Model | Dimension |
|----------|-------|-----------|
| 삼성 내부 (HuggingFace) | magi/embeddings | 1024 |
| OpenAI | text-embedding-3-small | 1536 |
| OpenAI | text-embedding-3-large | 3072 |
| Ollama | nomic-embed-text | 768 |

---

## API 엔드포인트 (구현 완료)

### Memory API (`/api/v1/memories`)
| Method | Endpoint | 설명 | 상태 |
|--------|----------|------|------|
| POST | `/memories` | 메모리 생성 | ✅ |
| GET | `/memories` | 메모리 목록 조회 (권한 필터링) | ✅ |
| GET | `/memories/{id}` | 메모리 상세 조회 | ✅ |
| PUT | `/memories/{id}` | 메모리 수정 | ✅ |
| DELETE | `/memories/{id}` | 메모리 삭제 | ✅ |
| POST | `/memories/search` | 시맨틱 검색 | ✅ |
| POST | `/memories/extract` | 대화에서 메모리 추출 | ✅ |

### Chat Room API (`/api/v1/chat-rooms`)
| Method | Endpoint | 설명 | 상태 |
|--------|----------|------|------|
| POST | `/chat-rooms` | 채팅방 생성 | ✅ |
| GET | `/chat-rooms` | 내가 속한 채팅방 목록 | ✅ |
| GET | `/chat-rooms/{id}` | 채팅방 상세 | ✅ |
| PUT | `/chat-rooms/{id}` | 채팅방 수정 | ✅ |
| DELETE | `/chat-rooms/{id}` | 채팅방 삭제 | ✅ |
| POST | `/chat-rooms/{id}/members` | 멤버 추가 | ✅ |
| GET | `/chat-rooms/{id}/members` | 멤버 목록 | ✅ |
| PUT | `/chat-rooms/{id}/members/{user_id}` | 멤버 역할 변경 | ✅ |
| DELETE | `/chat-rooms/{id}/members/{user_id}` | 멤버 제거 | ✅ |
| GET | `/chat-rooms/{id}/messages` | 메시지 목록 | ✅ |
| POST | `/chat-rooms/{id}/messages` | 메시지 전송 + AI 응답 | ✅ |

### User API (`/api/v1/users`)
| Method | Endpoint | 설명 | 상태 |
|--------|----------|------|------|
| POST | `/users` | 사용자 생성 | ✅ |
| GET | `/users` | 사용자 목록 | ✅ |
| GET | `/users/{id}` | 사용자 조회 | ✅ |
| PUT | `/users/{id}` | 사용자 수정 | ✅ |
| DELETE | `/users/{id}` | 사용자 삭제 | ✅ |
| GET | `/users/{id}/projects` | 사용자 프로젝트 목록 | ✅ |
| GET | `/users/{id}/department` | 사용자 부서 조회 | ✅ |
| POST | `/users/departments` | 부서 생성 | ✅ |
| GET | `/users/departments` | 부서 목록 | ✅ |
| POST | `/users/projects` | 프로젝트 생성 | ✅ |
| GET | `/users/projects` | 프로젝트 목록 | ✅ |
| POST | `/users/projects/{id}/members` | 프로젝트 멤버 추가 | ✅ |

### Permission API (`/api/v1/permissions`)
| Method | Endpoint | 설명 | 상태 |
|--------|----------|------|------|
| GET | `/permissions/check` | 권한 확인 | ✅ |

### Health Check
| Method | Endpoint | 설명 | 상태 |
|--------|----------|------|------|
| GET | `/health` | 서버 상태 확인 | ✅ |

---

## Context Sources 구조

채팅방별로 AI가 참조할 메모리 범위를 설정합니다:

```json
{
  "memory": {
    "include_this_room": true,           // 이 채팅방 메모리 포함
    "other_chat_rooms": ["room-id-1"],   // 다른 채팅방 메모리 포함
    "include_personal": false,           // 내 개인 메모리 포함
    "projects": ["project-id-1"],        // 프로젝트 메모리 포함
    "departments": ["dept-id-1"]         // 부서 메모리 포함
  },
  "rag": {
    "collections": [],                   // RAG 컬렉션 (향후 확장)
    "filters": {}
  }
}
```

---

## 권한 로직

### 메모리 접근 권한 체크 Flow
```
1. 요청 사용자 확인
2. 메모리의 scope 확인
3. scope별 권한 체크:
   - personal: owner_id == 요청 사용자 ID
   - chatroom: 요청 사용자가 해당 chat_room의 member인지 확인
   - project: 요청 사용자가 해당 project의 member인지 확인
   - department: 요청 사용자가 해당 department 소속인지 확인
4. 접근 허용/거부
```

### 채팅방 권한 체계
- **owner**: 모든 권한 (삭제, 멤버 관리, 설정 변경)
- **admin**: 멤버 추가/제거, 설정 변경
- **member**: 메시지 전송, 조회

---

## 개발 진행 상황

### Phase 1: 기본 구조 ✅ 완료
- [x] 프로젝트 구조 설계 (Feature-based)
- [x] SQLite 스키마 구현
- [x] Qdrant 연결 설정
- [x] 기본 CRUD API

### Phase 2: 핵심 기능 ✅ 완료
- [x] 메모리 저장/검색 구현
- [x] 권한 체크 로직 구현
- [x] 채팅방 멤버 관리
- [x] 슬래시 커맨드 구현

### Phase 3: AI 연동 ✅ 완료
- [x] `@ai` 멘션 AI 응답
- [x] 메모리 자동 추출 (LLM 연동)
- [x] 컨텍스트 소스 기반 메모리 검색
- [x] Streamlit 데모 UI

### Phase 4: 고도화 🔄 진행 중
- [ ] 메모리 중복 제거/병합 최적화
- [ ] 성능 최적화
- [ ] PostgreSQL 마이그레이션
- [ ] RAG 컬렉션 연동

---

## 환경 변수

### 삼성 내부망 기본 설정 (권장)

```env
# ===========================================
# Database Configuration
# ===========================================
SQLITE_DB_PATH=./data/sqlite/memory.db

# ===========================================
# Vector Database (Qdrant)
# ===========================================
QDRANT_URL=http://10.244.11.230:30011
QDRANT_COLLECTION=ai-memory-agent
QDRANT_API_KEY=

# ===========================================
# Embedding Provider Configuration
# ===========================================
EMBEDDING_PROVIDER=huggingface
EMBEDDING_DIMENSION=1024

# HuggingFace Embedding (삼성 내부 서버)
HUGGINGFACE_API_KEY=Bearer ghu_xxxxx
HUGGINGFACE_EMBEDDING_MODEL_URL=https://smart-dna.sec.samsung.net/k8s/magi/embeddings

# ===========================================
# LLM Provider Configuration
# ===========================================
LLM_PROVIDER=openai

# SAMSUNG OpenAI Compatible LLM (Qwen3-32B)
OPENAI_LLM_URL=http://10.244.11.119:30434/v1
OPENAI_LLM_MODEL=/data/Qwen3-32B
OPENAI_API_KEY=Bearer ghu_xxxxx

# ===========================================
# Application Settings
# ===========================================
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# ===========================================
# Memory Extraction Settings
# ===========================================
AUTO_EXTRACT_MEMORY=true
MIN_MESSAGE_LENGTH_FOR_EXTRACTION=10
DUPLICATE_THRESHOLD=0.85
```

### 외부망/범용 설정 (옵션)

```env
# ===========================================
# Database Configuration
# ===========================================
SQLITE_DB_PATH=./data/sqlite/memory.db

# ===========================================
# Vector Database (Qdrant)
# ===========================================
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=ai-memory-agent
QDRANT_API_KEY=

# ===========================================
# Embedding Provider Configuration
# ===========================================
EMBEDDING_PROVIDER=openai
EMBEDDING_DIMENSION=1536

# OpenAI Embedding
OPENAI_API_KEY=sk-xxxxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_URL=https://api.openai.com/v1/embeddings

# ===========================================
# LLM Provider Configuration
# ===========================================
LLM_PROVIDER=openai

# OpenAI LLM
OPENAI_LLM_URL=https://api.openai.com/v1
OPENAI_LLM_MODEL=gpt-4o-mini

# Ollama (로컬)
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_LLM_MODEL=llama3.2
# OLLAMA_EMBEDDING_MODEL=nomic-embed-text
# EMBEDDING_DIMENSION=768

# Anthropic Claude
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

---

## 실행 방법

### 1. 의존성 설치
```bash
pip install -e .
# 또는
pip install -e ".[dev]"  # 개발 의존성 포함
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 수정
```

### 3. FastAPI 서버 실행
```bash
python -m src.main
# 또는
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Streamlit UI 실행
```bash
streamlit run app/streamlit_app.py
```

### 5. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Provider 아키텍처

### Embedding Provider Interface

```python
from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass
```

### LLM Provider Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        pass
    
    @abstractmethod
    async def extract_memories(
        self,
        conversation: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        pass
```

### Provider Factory

```python
# src/shared/providers/__init__.py
from src.shared.providers.factory import get_embedding_provider, get_llm_provider
```

---

## Mem0.ai 비교 분석

### 기능 비교

| 기능 | Mem0.ai | AI Memory Agent | 비고 |
|------|---------|-----------------|------|
| **메모리 저장** | ✅ 단일 사용자/세션 | ✅ 멀티채팅 + 권한 기반 | 확장 |
| **권한 관리** | ❌ 없음 | ✅ Personal/Chatroom/Project/Department | 신규 |
| **멀티 채팅방** | ❌ 없음 | ✅ 지원 | 신규 |
| **채팅방 멤버 관리** | ❌ 없음 | ✅ owner/admin/member | 신규 |
| **슬래시 커맨드** | ❌ 없음 | ✅ /remember, /search, /forget 등 | 신규 |
| **Vector DB** | ✅ Qdrant, Chroma, etc | ✅ Qdrant | 동일 |
| **Embedding** | ✅ 다양한 Provider | ✅ HuggingFace, OpenAI, Ollama | 동일 |
| **LLM** | ✅ 다양한 Provider | ✅ OpenAI Compatible, Ollama, Anthropic | 동일 |
| **메모리 자동 추출** | ✅ LLM 기반 | ✅ LLM 기반 | 동일 |
| **Graph Memory** | ✅ Neo4j 지원 | ❌ 미지원 (추후 고려) | Mem0 우위 |
| **기업용 기능** | ✅ 유료 | ✅ 자체 구축 | 자체 |

---

## 참고 사항

- Mem0.ai 참고: https://github.com/mem0ai/mem0
- Feature-based 폴더 구조 적용
- 개발 단계에서는 SQLite + Qdrant 사용
- 운영 환경에서는 PostgreSQL + Qdrant 클라우드 전환 고려
- 삼성 내부망 환경에서는 외부 API 의존 없이 자체 인프라로 운영
