# AI Memory Agent

멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템입니다.

## 주요 기능

- **멀티채팅 기반 메모리**: 여러 채팅방의 대화를 통합 메모리로 저장
- **권한 기반 접근 제어**: 개인/프로젝트/부서 단위 메모리 접근 관리
- **시맨틱 검색**: 벡터 임베딩 기반 유사 메모리 검색
- **자동 메모리 추출**: LLM을 활용한 대화에서 메모리 자동 추출

## 기술 스택

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite (개발) / PostgreSQL (운영)
- **Vector DB**: Qdrant
- **Embedding**: HuggingFace, OpenAI, Ollama
- **LLM**: OpenAI Compatible (Qwen3), Ollama, Anthropic

## 빠른 시작

### 1. 환경 설정

```bash
# 프로젝트 클론
cd ai-memory-agent

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -e .

# 환경변수 설정
cp .env.example .env
# .env 파일 수정
```

### 2. 서버 실행

```bash
# 개발 서버 실행
python -m src.main

# 또는
uvicorn src.main:app --reload
```

### 3. 가짜 데이터 생성 (선택)

```bash
python -m src.scripts.seed_data
```

### 4. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 사용 예시

### 메모리 생성

```bash
curl -X POST "http://localhost:8000/api/v1/memories" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: your-user-id" \
  -d '{
    "content": "프로젝트 회의는 매주 월요일 10시에 진행한다",
    "scope": "project",
    "project_id": "your-project-id"
  }'
```

### 메모리 검색

```bash
curl -X POST "http://localhost:8000/api/v1/memories/search" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: your-user-id" \
  -d '{
    "query": "회의 일정",
    "limit": 10
  }'
```

## 프로젝트 구조

```
ai-memory-agent/
├── src/
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── config.py            # 설정 관리
│   ├── memory/              # 메모리 기능
│   ├── user/                # 사용자/부서/프로젝트 기능
│   ├── chat/                # 채팅방 기능
│   ├── permission/          # 권한 기능
│   ├── shared/              # 공유 모듈
│   │   ├── database.py      # SQLite
│   │   ├── vector_store.py  # Qdrant
│   │   └── providers/       # Embedding/LLM Providers
│   └── scripts/
│       └── seed_data.py     # 가짜 데이터 생성
├── tests/                   # 테스트
├── data/                    # 로컬 데이터
├── claude.md                # 프로젝트 정의서
├── pyproject.toml           # 의존성
└── .env.example             # 환경변수 템플릿
```

## 권한 체계

| Scope | 설명 | 접근 조건 |
|-------|------|----------|
| personal | 개인 메모리 | 소유자만 접근 |
| project | 프로젝트 메모리 | 프로젝트 멤버만 접근 |
| department | 부서 메모리 | 같은 부서원만 접근 |

## 환경 변수

주요 환경 변수 (`.env.example` 참조):

```env
# Database
SQLITE_DB_PATH=./data/sqlite/memory.db

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=ai-memory-agent

# Embedding
EMBEDDING_PROVIDER=huggingface
EMBEDDING_DIMENSION=1024
HUGGINGFACE_API_KEY=Bearer xxx
HUGGINGFACE_EMBEDDING_MODEL_URL=https://...

# LLM
LLM_PROVIDER=openai
OPENAI_LLM_URL=http://...
OPENAI_LLM_MODEL=/data/Qwen3-32B
OPENAI_API_KEY=Bearer xxx
```

## 라이선스

Internal Use Only - Samsung Electronics
