# AI Memory Agent

전사 AI 에이전트를 위한 **중앙 메모리(지식) 인프라 플랫폼**입니다.

사내 AI 에이전트 개발자에게 SDK를 제공하여 메모리 기능을 쉽게 연동하고, 모든 지식이 중앙 서버에 축적되어 플랫폼 운영자가 통계·모니터링·감사·품질 관리를 할 수 있는 구조입니다.

## 주요 기능

### 개발자용 — Python SDK
- **5줄 코드**로 AI 에이전트에 메모리 기능 연동
- Agent (고수준), SyncClient / AsyncClient (저수준) 제공
- 메모리 저장/검색, LLM 통합 대화, 메모리 자동 추출

### 채팅 & AI 응답
- 멀티 대화방 지원
- `@ai` 멘션으로 AI에게 질문
- WebSocket 기반 실시간 메시지
- 대화에서 자동 메모리 추출

### 메모리 관리
- 3단계 스코프: 개인, 대화방, 에이전트
- 시맨틱 벡터 검색 (Qdrant)
- 메모리 Supersede 체인 (버전 이력 관리)
- 메모리 감쇠 (30일 미접근 시 중요도 자동 하향)
- 엔티티 자동 추출 및 링크
- 슬래시 커맨드: `/remember`, `/memory`, `/forget`, `/search`
- 대화방별 컨텍스트 소스 설정 (다른 대화방, 개인 메모리 참조)

### RAG 문서
- PDF/TXT 파일 업로드
- **시맨틱 청킹** — 의미 단위 분할 (코사인 유사도 기반 경계 감지)
- **하이브리드 검색** — 벡터 검색(Qdrant) + 키워드 검색(SQLite FTS5) 결합
- **Reranker** — Jina Reranker로 최종 결과 정밀 재순위
- **엔티티 쿼리 확장** — 질문에서 추출한 엔티티로 검색 쿼리 보강
- 문서-대화방 연결/해제 (다대다)

### Mattermost 연동
- 사내 Mattermost 봇으로 AI 대화
- DM 자동 응답, `@ai` 멘션 호출
- 사용자/채널 자동 매핑 (이메일 기반)
- 채널 대화 요약 (`@ai 요약`)
- 설정 가이드: [docs/mattermost-setup.md](docs/mattermost-setup.md)

### 운영자 관리 기능
- **에이전트 대시보드** — 전체 인스턴스 현황, 일별 활동, Top 에이전트
- **API 감사 로그** — 에이전트별 API 호출 기록 자동 수집
- **지식 품질 리포트** — 오래된 메모리, 중복 후보, 스코프 분포, 엔티티 분석
- **Rate Limiting** — 에이전트별 분당 호출 제한 (기본 60회/분)
- **Webhook** — 메모리 생성/메시지 수신 시 개발자 서버로 알림 (3회 재시도)
- **팀 지식 대시보드** — 메모리 분포, 핫 토픽, 오래된 지식, 기여도 랭킹
- 사용자/대화방/메모리/부서/프로젝트 관리

### 멀티 에이전트 지식 공유
- A팀 에이전트 메모리를 B팀 에이전트가 검색 가능
- 에이전트 인스턴스 간 공유 설정 (viewer/member)
- 메모리 타임라인 — Supersede 체인으로 지식 발전 추적

## 기술 스택

| 영역 | 기술 |
|------|------|
| **백엔드** | Python 3.11+, FastAPI, Uvicorn |
| **DB** | SQLite (aiosqlite) |
| **벡터 DB** | Qdrant |
| **LLM** | OpenAI 호환 API (Qwen3-32B), Anthropic, Ollama |
| **Embedding** | HuggingFace, OpenAI, Ollama |
| **Reranker** | Jina Reranker API |
| **프론트엔드** | React 18, TypeScript, Vite |
| **상태관리** | Zustand (클라이언트), TanStack Query (서버) |
| **스타일** | Tailwind CSS |
| **실시간** | WebSocket (Native) |
| **메신저** | Mattermost (WebSocket + REST) |
| **컨테이너** | Docker Compose |

## 빠른 시작

### 요구사항

- Python 3.11+
- Node.js 18+
- (선택) Qdrant 서버 - 벡터 검색용, 없어도 기본 동작 가능

### 1. 환경 설정

```bash
cd ai-memory-agent

# 의존성 설치
pip install -e .

# 환경변수 설정
cp .env.example .env
# .env 파일을 환경에 맞게 수정
```

`.env` 주요 설정:

```env
# DB
SQLITE_DB_PATH=./data/sqlite/memory.db

# Qdrant (선택)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=ai-memory-agent

# Embedding 프로바이더 (huggingface / openai / ollama)
EMBEDDING_PROVIDER=huggingface
EMBEDDING_DIMENSION=1024

# LLM 프로바이더 (openai / ollama / anthropic)
LLM_PROVIDER=openai
OPENAI_LLM_URL=http://localhost:8080/v1
OPENAI_LLM_MODEL=your-model-name
OPENAI_API_KEY=your-api-key

# 환경
APP_ENV=development
```

### 2. 서버 실행

```bash
# Terminal 1: Backend (포트 8000)
PYTHONIOENCODING=utf-8 python -m src.main

# Terminal 2: Frontend (포트 3000)
cd frontend
npm install
npm run dev
```

### 3. 접속

- **Frontend**: http://localhost:3000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### 4. Docker로 실행

```bash
docker-compose up -d
# api (8000) + qdrant (6333) + frontend (3000)
```

### 5. 테스트 데이터 생성 (선택)

```bash
python -m src.scripts.seed_data
```

### 6. DB 초기화

```bash
rm data/sqlite/memory.db     # Linux/Mac
del data\sqlite\memory.db    # Windows
```

## For Agent Developers (SDK)

사내 AI 에이전트에 메모리 기능을 추가하려면 SDK를 사용하세요.

### SDK 설치

```bash
cd ai_memory_agent_sdk
pip install -e .
```

### 빠른 시작

```python
from ai_memory_agent_sdk import Agent

agent = Agent(
    api_key="sk_your_api_key",
    base_url="http://localhost:8000",
    agent_id="my-bot",
    llm_provider="openai",
    llm_url="https://api.openai.com/v1",
    llm_api_key="sk-...",
    model="gpt-4o-mini",
)

# 대화 (메모리 자동 검색 + LLM 호출)
response = agent.message("안녕하세요!")

# 메모리 추출 → 서버 저장
agent.memory()

# 메모리 검색
results = agent.search("검색어")
```

### 저수준 클라이언트

```python
from ai_memory_agent_sdk import SyncClient

client = SyncClient(
    api_key="sk_your_api_key",
    base_url="http://localhost:8000",
    agent_id="my-bot",
)

# 메모리 저장
client.send_memory("사용자가 Python을 선호합니다")

# 메모리 검색
results = client.search_memories("프로그래밍 언어 선호도")

# 에이전트 데이터 조회
data = client.get_agent_data(data_type="memory", limit=10)
```

자세한 내용: [Quickstart 가이드](docs/quickstart.md)

## 프로젝트 구조

```
ai-memory-agent/
├── src/                          # 백엔드 (FastAPI)
│   ├── main.py                   # 앱 엔트리포인트
│   ├── config.py                 # 환경설정 (pydantic-settings)
│   ├── admin/                    # 관리자 API (대시보드, 지식품질, CRUD)
│   ├── auth/                     # 인증 (로그인/회원가입/토큰)
│   ├── agent/                    # 에이전트 SDK API (타입/인스턴스/메모리/공유)
│   ├── chat/                     # 대화방 + AI 응답 + 슬래시 커맨드
│   ├── document/                 # RAG 문서 (업로드/청킹/임베딩/연결)
│   ├── mchat/                    # Mattermost(Mchat) 연동
│   ├── memory/                   # 메모리 CRUD + 시맨틱 검색 + 타임라인
│   ├── permission/               # 권한 체크
│   ├── user/                     # 사용자/부서/프로젝트
│   ├── websocket/                # WebSocket 핸들러
│   ├── shared/                   # DB, 벡터스토어, 프로바이더, 인증, Rate Limiter
│   └── scripts/                  # 시드 데이터
├── ai_memory_agent_sdk/          # Python SDK 패키지
│   ├── ai_memory_agent_sdk/
│   │   ├── agent.py              # Agent (고수준, LLM 통합)
│   │   ├── client.py             # AsyncClient
│   │   ├── sync_client.py        # SyncClient
│   │   └── exceptions.py         # 에러 클래스
│   └── pyproject.toml
├── frontend/                     # 프론트엔드 (React)
│   └── src/
│       ├── features/             # 기능별 모듈
│       ├── components/           # 공용 컴포넌트
│       ├── hooks/                # 커스텀 훅
│       ├── lib/                  # API 클라이언트
│       ├── stores/               # Zustand 스토어
│       └── types/                # TypeScript 타입
├── docs/                         # 문서
│   ├── quickstart.md             # SDK 빠른 시작 가이드
│   ├── mattermost-setup.md       # Mattermost 설치 및 봇 설정
│   └── report.md                 # 보고 자료
├── docker-compose.yml            # Docker Compose (api+qdrant+frontend)
├── Dockerfile                    # 백엔드 Docker 이미지
├── data/sqlite/                  # SQLite DB (자동 생성, .gitignore)
├── .env                          # 환경변수 (.gitignore)
├── pyproject.toml                # Python 의존성
└── CLAUDE.md                     # Claude Code 가이드
```

## 인증 체계

```
Frontend / SDK                    Backend
┌─────────────────┐               ┌──────────────────────┐
│ Frontend:       │               │                      │
│ - JWT 토큰 인증  │──────────────▶│ Authorization:       │
│ - X-User-ID     │               │   Bearer <JWT>       │
│                 │               │                      │
│ SDK (에이전트):  │               │                      │
│ - API Key 인증   │──────────────▶│ X-API-Key:           │
│                 │               │   sk_xxxxx           │
└─────────────────┘               └──────────────────────┘
```

- **Frontend/사용자**: `Authorization: Bearer <JWT>` 또는 `X-User-ID` (개발 환경)
- **SDK/에이전트**: `X-API-Key: <api_key>` — 에이전트 인스턴스별 발급

## API 엔드포인트

### Auth
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/auth/login` | 로그인 |
| POST | `/api/v1/auth/register` | 회원가입 |
| GET | `/api/v1/auth/me` | 현재 사용자 정보 |
| POST | `/api/v1/auth/verify` | 토큰 검증 |

### Chat Rooms
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/chat-rooms` | 대화방 목록 |
| POST | `/api/v1/chat-rooms` | 대화방 생성 |
| GET | `/api/v1/chat-rooms/{id}` | 대화방 상세 |
| PUT | `/api/v1/chat-rooms/{id}` | 대화방 수정 |
| DELETE | `/api/v1/chat-rooms/{id}` | 대화방 삭제 |
| GET | `/api/v1/chat-rooms/{id}/messages` | 메시지 목록 |
| POST | `/api/v1/chat-rooms/{id}/messages` | 메시지 전송 |
| GET | `/api/v1/chat-rooms/{id}/members` | 멤버 목록 |
| POST | `/api/v1/chat-rooms/{id}/members` | 멤버 추가 |

### Memory
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/memories` | 메모리 목록 |
| POST | `/api/v1/memories` | 메모리 생성 |
| GET | `/api/v1/memories/{id}` | 메모리 상세 |
| PUT | `/api/v1/memories/{id}` | 메모리 수정 |
| DELETE | `/api/v1/memories/{id}` | 메모리 삭제 |
| POST | `/api/v1/memories/search` | 시맨틱 검색 |
| POST | `/api/v1/memories/extract` | 자동 추출 |
| GET | `/api/v1/memories/{id}/history` | 메모리 타임라인 (Supersede 체인) |

### Documents
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/documents/upload` | 문서 업로드 (multipart) |
| GET | `/api/v1/documents` | 문서 목록 |
| GET | `/api/v1/documents/{id}` | 문서 상세 (청크 포함) |
| DELETE | `/api/v1/documents/{id}` | 문서 삭제 |
| POST | `/api/v1/documents/{id}/link/{room_id}` | 문서-대화방 연결 |
| DELETE | `/api/v1/documents/{id}/link/{room_id}` | 문서-대화방 해제 |

### Agent (SDK API)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/agent-types` | 에이전트 타입 등록 |
| GET | `/api/v1/agent-types` | 에이전트 타입 목록 |
| POST | `/api/v1/agent-types/{id}/instances` | 인스턴스 생성 (API Key 발급) |
| GET | `/api/v1/agent-instances` | 인스턴스 목록 |
| POST | `/api/v1/agents/{id}/data` | 데이터 전송 (memory/message/log) |
| GET | `/api/v1/agents/{id}/data` | 데이터 조회 |
| POST | `/api/v1/agents/{id}/memories` | 메모리 전용 생성 |
| DELETE | `/api/v1/agents/{id}/memories/{mid}` | 메모리 삭제 |
| POST | `/api/v1/agents/{id}/memories/search` | 메모리 검색 |
| GET | `/api/v1/agents/{id}/memory-sources` | 메모리 소스 조회 |
| GET | `/api/v1/agents/{id}/entities` | 엔티티 그래프 |
| GET | `/api/v1/agent-instances/{id}/stats` | 사용량 통계 |
| GET | `/api/v1/agent-instances/{id}/api-logs` | API 호출 로그 |
| GET | `/api/v1/agent-instances/{id}/webhook-events` | Webhook 이벤트 |

### Admin
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/admin/dashboard` | 대시보드 통계 |
| GET | `/api/v1/admin/knowledge-dashboard` | 팀 지식 대시보드 |
| GET | `/api/v1/admin/agent-dashboard` | 에이전트 대시보드 |
| GET | `/api/v1/admin/agent-api-logs` | 전사 API 감사 로그 |
| GET | `/api/v1/admin/knowledge-quality-report` | 지식 품질 리포트 |
| GET | `/api/v1/admin/users` | 사용자 목록 |
| GET | `/api/v1/admin/chat-rooms` | 대화방 목록 |
| GET | `/api/v1/admin/memories` | 메모리 목록 (페이지네이션) |
| GET | `/api/v1/admin/departments` | 부서 목록 |
| GET | `/api/v1/admin/projects` | 프로젝트 목록 |

### Mattermost
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/mchat/status` | Mchat 연결 상태 |
| GET | `/api/v1/mchat/channels` | 채널 매핑 목록 |
| GET | `/api/v1/mchat/users` | 사용자 매핑 목록 |

### WebSocket
| Endpoint | 설명 |
|----------|------|
| `ws://localhost:8000/ws/chat/{room_id}?token={token}` | 실시간 채팅 |

## AI 컨텍스트 우선순위

AI가 응답할 때 다음 순서로 컨텍스트를 참조합니다:

1. **대화 내용** (최우선) - 최근 20개 메시지
2. **RAG 문서** (높은 우선순위) - 하이브리드 검색(벡터+FTS5)으로 연결 문서 청크 조회 → Reranker로 정밀 재순위
3. **저장된 메모리** (보조) - 설정된 컨텍스트 소스 기반, 엔티티 쿼리 확장 적용

## 권한 체계

| Scope | 설명 | 접근 조건 |
|-------|------|----------|
| `personal` | 개인 메모리 | 소유자만 접근 |
| `chatroom` | 대화방 메모리 | 대화방 멤버만 접근 |
| `agent` | 에이전트 메모리 | 인스턴스 소유자/공유 대상 |

## 슬래시 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/remember <내용>` | 개인 + 대화방 메모리 저장 |
| `/memory` | 최근 대화에서 메모리 자동 추출 |
| `/forget <검색어>` | 메모리 삭제 |
| `/search <검색어>` | 메모리 검색 |
| `/members` | 멤버 목록 |
| `/invite <이메일>` | 멤버 초대 (관리자만) |
| `/help` | 도움말 |

## 문서

| 문서 | 설명 |
|------|------|
| [docs/quickstart.md](docs/quickstart.md) | SDK 빠른 시작 가이드 |
| [docs/mattermost-setup.md](docs/mattermost-setup.md) | Mattermost 로컬 설치 및 봇 설정 |
| [docs/report.md](docs/report.md) | 프로젝트 보고 자료 |

---

## 개발

```bash
# 린트
ruff check src/
cd frontend && npm run lint

# 타입 체크
mypy src/

# 테스트
pytest

# 프론트엔드 빌드
cd frontend && npx vite build
```

## 라이선스

Internal Use Only - Samsung Electronics