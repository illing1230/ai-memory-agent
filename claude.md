# AI Memory Agent

## 프로젝트 개요

AI Memory Agent는 멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템입니다.
Mem0.ai의 컨셉을 기반으로 하되, 멀티채팅 지원과 세분화된 권한 관리 기능을 추가합니다.

## 핵심 기능

### 1. 멀티채팅 기반 메모리 저장
- 여러 채팅방(Room)에서 발생하는 대화를 통합 메모리로 저장
- 채팅방별 컨텍스트 분리 및 통합 검색 지원
- 실시간 메모리 추출 및 저장

### 2. 권한 기반 메모리 접근 제어
- **개인(Personal)**: 사용자 본인만 접근 가능한 메모리
- **프로젝트(Project)**: 특정 프로젝트 참여자만 접근 가능한 메모리
- **부서(Department)**: 부서 전체가 공유하는 메모리

### 3. 하이브리드 저장소
- **SQLite**: 메타데이터, 권한, 관계 정보 저장
- **Qdrant**: 벡터 임베딩 저장 및 시맨틱 검색

---

## 기술 스택

| 구분 | 기술 | 비고 |
|------|------|------|
| Backend | FastAPI (Python 3.11+) | |
| Database | SQLite (개발) / PostgreSQL (운영) | |
| Vector DB | Qdrant | 내부망: 10.244.11.230:30011 |
| Embedding | HuggingFace (기본), OpenAI, Ollama | 내부망: smart-dna.sec.samsung.net |
| LLM | OpenAI Compatible (Qwen3-32B), Ollama, Anthropic | 내부망: 10.244.11.119:30434 |

---

## 프로젝트 구조 (Feature-Based)

```
ai-memory-agent/
├── claude.md                    # 프로젝트 정의서
├── pyproject.toml               # 의존성 관리
├── .env.example                 # 환경변수 템플릿
├── .env                         # 환경변수 (git 제외)
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 앱 엔트리포인트
│   ├── config.py                # 설정 관리
│   │
│   ├── memory/                  # 메모리 관리 기능
│   │   ├── __init__.py
│   │   ├── router.py            # API 라우터
│   │   ├── service.py           # 비즈니스 로직
│   │   ├── repository.py        # 데이터 접근 계층
│   │   └── schemas.py           # Pydantic 스키마
│   │
│   ├── chat/                    # 채팅방 관리 기능
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   ├── permission/              # 권한 관리 기능
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   ├── user/                    # 사용자 관리 기능
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   └── shared/                  # 공유 모듈
│       ├── __init__.py
│       ├── database.py          # SQLite 연결 관리
│       ├── vector_store.py      # Qdrant 연결 관리
│       ├── exceptions.py        # 커스텀 예외
│       │
│       └── providers/           # Provider 추상화
│           ├── __init__.py
│           ├── base.py          # 추상 베이스 클래스
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
    ├── sqlite/                  # SQLite DB 파일
    └── qdrant/                  # Qdrant 로컬 데이터 (외부망용)
```

---

## 데이터베이스 스키마

### SQLite 테이블

#### users (사용자)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| name | TEXT | 사용자명 |
| email | TEXT | 이메일 (UNIQUE) |
| department_id | TEXT | FK → departments.id |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

#### departments (부서)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| name | TEXT | 부서명 |
| description | TEXT | 설명 |
| created_at | DATETIME | 생성일시 |

#### projects (프로젝트)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| name | TEXT | 프로젝트명 |
| description | TEXT | 설명 |
| department_id | TEXT | FK → departments.id (소속 부서) |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

#### project_members (프로젝트 멤버)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| project_id | TEXT | FK → projects.id |
| user_id | TEXT | FK → users.id |
| role | TEXT | 역할 (owner, member) |
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
| created_at | DATETIME | 생성일시 |

#### memories (메모리)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | TEXT (UUID) | PK |
| content | TEXT | 메모리 내용 (원문) |
| vector_id | TEXT | Qdrant 벡터 ID |
| scope | TEXT | 권한 범위 (personal, project, department) |
| owner_id | TEXT | FK → users.id (생성자) |
| project_id | TEXT | FK → projects.id (nullable) |
| department_id | TEXT | FK → departments.id (nullable) |
| chat_room_id | TEXT | FK → chat_rooms.id (출처 채팅방) |
| source_message_id | TEXT | 원본 메시지 ID |
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
    "size": "${EMBEDDING_DIMENSION}",  // Provider에 따라 동적 설정
    "distance": "Cosine"
  },
  "payload_schema": {
    "memory_id": "keyword",
    "scope": "keyword",
    "owner_id": "keyword",
    "project_id": "keyword",
    "department_id": "keyword",
    "created_at": "datetime"
  }
}
```

**Embedding 차원 참고:**
| Provider | Model | Dimension |
|----------|-------|-----------|
| 삼성 내부 (HuggingFace) | magi/embeddings | 1024 (확인 필요) |
| OpenAI | text-embedding-3-small | 1536 |
| OpenAI | text-embedding-3-large | 3072 |
| Ollama | nomic-embed-text | 768 |

---

## API 엔드포인트 설계

### Memory API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/memories` | 메모리 생성 |
| GET | `/api/v1/memories` | 메모리 목록 조회 (권한 필터링) |
| GET | `/api/v1/memories/{id}` | 메모리 상세 조회 |
| PUT | `/api/v1/memories/{id}` | 메모리 수정 |
| DELETE | `/api/v1/memories/{id}` | 메모리 삭제 |
| POST | `/api/v1/memories/search` | 시맨틱 검색 |

### Chat Room API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/chat-rooms` | 채팅방 생성 |
| GET | `/api/v1/chat-rooms` | 채팅방 목록 |
| GET | `/api/v1/chat-rooms/{id}` | 채팅방 상세 |
| POST | `/api/v1/chat-rooms/{id}/messages` | 메시지 전송 (메모리 추출 트리거) |

### User API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/users` | 사용자 생성 |
| GET | `/api/v1/users/me` | 현재 사용자 정보 |
| GET | `/api/v1/users/{id}/memories` | 사용자의 접근 가능한 메모리 |

### Permission API
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/permissions/check` | 권한 확인 |
| POST | `/api/v1/permissions/grant` | 권한 부여 |
| DELETE | `/api/v1/permissions/revoke` | 권한 회수 |

---

## 권한 로직

### 메모리 접근 권한 체크 Flow
```
1. 요청 사용자 확인
2. 메모리의 scope 확인
3. scope별 권한 체크:
   - personal: owner_id == 요청 사용자 ID
   - project: 요청 사용자가 해당 project의 member인지 확인
   - department: 요청 사용자가 해당 department 소속인지 확인
4. 접근 허용/거부
```

---

## 개발 우선순위

### Phase 1: 기본 구조 (현재)
- [x] 프로젝트 구조 설계
- [ ] SQLite 스키마 구현
- [ ] Qdrant 연결 설정
- [ ] 기본 CRUD API

### Phase 2: 핵심 기능
- [ ] 메모리 저장/검색 구현
- [ ] 권한 체크 로직 구현
- [ ] 멀티채팅 연동

### Phase 3: 고도화
- [ ] 메모리 자동 추출 (LLM 연동)
- [ ] 메모리 중복 제거/병합
- [ ] 성능 최적화

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
# Provider 선택: openai, ollama, huggingface
EMBEDDING_PROVIDER=huggingface
EMBEDDING_DIMENSION=1024

# HuggingFace Embedding (삼성 내부 서버)
HUGGINGFACE_API_KEY=Bearer ghu_xxxxx
HUGGINGFACE_EMBEDDING_MODEL_URL=https://smart-dna.sec.samsung.net/k8s/magi/embeddings

# ===========================================
# LLM Provider Configuration (메모리 추출용)
# ===========================================
# Provider 선택: openai, ollama, anthropic
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

## Provider 아키텍처

Mem0.ai와 유사하게, 다양한 Embedding/LLM Provider를 지원하는 플러가블 구조를 채택합니다.

### Embedding Provider Interface

```python
from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingProvider(ABC):
    """Embedding Provider 추상 클래스"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """단일 텍스트 임베딩"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 텍스트 임베딩"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """벡터 차원 반환"""
        pass
```

### LLM Provider Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """LLM Provider 추상 클래스"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    async def extract_memories(
        self,
        conversation: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """대화에서 메모리 추출"""
        pass
```

### Provider Factory

```python
# config.py
import os

def get_embedding_provider() -> BaseEmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "huggingface")
    dimension = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    
    if provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_EMBEDDING_MODEL"),
            base_url=os.getenv("OPENAI_EMBEDDING_URL"),
            dimension=dimension
        )
    elif provider == "huggingface":
        # 삼성 내부 HuggingFace 호환 서버
        return HuggingFaceEmbeddingProvider(
            api_key=os.getenv("HUGGINGFACE_API_KEY"),
            model_url=os.getenv("HUGGINGFACE_EMBEDDING_MODEL_URL"),
            dimension=dimension
        )
    elif provider == "ollama":
        return OllamaEmbeddingProvider(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            model=os.getenv("OLLAMA_EMBEDDING_MODEL"),
            dimension=dimension
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")

def get_llm_provider() -> BaseLLMProvider:
    provider = os.getenv("LLM_PROVIDER", "openai")
    
    if provider == "openai":
        # OpenAI 호환 API (삼성 내부 Qwen3 포함)
        return OpenAILLMProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_LLM_MODEL"),
            base_url=os.getenv("OPENAI_LLM_URL")
        )
    elif provider == "ollama":
        return OllamaLLMProvider(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            model=os.getenv("OLLAMA_LLM_MODEL")
        )
    elif provider == "anthropic":
        return AnthropicLLMProvider(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("ANTHROPIC_MODEL")
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
```

---

## Mem0.ai 비교 분석

### 기능 비교

| 기능 | Mem0.ai | AI Memory Agent | 비고 |
|------|---------|-----------------|------|
| **메모리 저장** | ✅ 단일 사용자/세션 | ✅ 멀티채팅 + 권한 기반 | 확장 |
| **권한 관리** | ❌ 없음 | ✅ Personal/Project/Department | 신규 |
| **멀티 채팅방** | ❌ 없음 | ✅ 지원 | 신규 |
| **Vector DB** | ✅ Qdrant, Chroma, etc | ✅ Qdrant | 동일 |
| **Embedding** | ✅ 다양한 Provider | ✅ HuggingFace, OpenAI, Ollama | 동일 |
| **LLM** | ✅ 다양한 Provider | ✅ OpenAI Compatible, Ollama, Anthropic | 동일 |
| **메모리 자동 추출** | ✅ LLM 기반 | ✅ LLM 기반 | 동일 |
| **메모리 중복 제거** | ✅ 지원 | ✅ 지원 (DUPLICATE_THRESHOLD) | 동일 |
| **Graph Memory** | ✅ Neo4j 지원 | ❌ 미지원 (추후 고려) | Mem0 우위 |
| **기업용 기능** | ✅ 유료 | ✅ 자체 구축 | 자체 |

### 핵심 차별화 포인트

1. **권한 기반 메모리 공유**
   - Mem0: 단순한 user_id/agent_id 기반 분리
   - AI Memory Agent: 조직 계층 구조 (개인 → 프로젝트 → 부서) 반영

2. **멀티 채팅방 통합**
   - Mem0: 단일 채팅 컨텍스트
   - AI Memory Agent: 여러 채팅방의 메모리를 통합 관리

3. **내부망 운영**
   - Mem0: 외부 서비스 의존 (API 키 필요)
   - AI Memory Agent: 삼성 내부 리소스만으로 운영 가능

---

## 메모리 추출 프로세스

Mem0.ai와 동일한 방식으로 LLM을 활용한 메모리 자동 추출을 지원합니다.

### 추출 Flow

```
[새 메시지 입력]
     ↓
[최소 길이 체크] → MIN_MESSAGE_LENGTH_FOR_EXTRACTION
     ↓
[LLM 메모리 추출] → 구조화된 메모리 생성
     ↓
[중복 체크] → DUPLICATE_THRESHOLD 기반 유사도 비교
     ↓
[메모리 저장] → SQLite (metadata) + Qdrant (vector)
```

### 메모리 추출 프롬프트 (예시)

```python
MEMORY_EXTRACTION_PROMPT = """
다음 대화에서 장기적으로 기억할 가치가 있는 정보를 추출하세요.

추출 기준:
- 사용자의 선호도, 습관, 특성
- 중요한 사실이나 결정 사항
- 프로젝트/업무 관련 정보
- 관계 정보 (사람, 조직 등)

응답 형식 (JSON):
[
  {
    "content": "추출된 메모리 내용",
    "category": "preference|fact|decision|relationship",
    "importance": "high|medium|low"
  }
]

대화:
{conversation}
"""
```

---

## 참고 사항

- Mem0.ai 참고: https://github.com/mem0ai/mem0
- Feature-based 폴더 구조 적용
- 개발 단계에서는 SQLite + Qdrant (내부망 또는 로컬) 사용
- 운영 환경에서는 PostgreSQL + Qdrant 클라우드 전환 고려
- 삼성 내부망 환경에서는 외부 API 의존 없이 자체 인프라로 운영
