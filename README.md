# AI Memory Agent

멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 AI 시스템입니다.

채팅 대화에서 중요한 정보를 자동으로 추출하여 메모리로 저장하고, RAG 문서와 함께 AI 응답의 컨텍스트로 활용합니다.

## 주요 기능

### 채팅 & AI 응답
- 멀티 채팅방 지원 (개인/프로젝트/부서)
- `@ai` 멘션으로 AI에게 질문
- WebSocket 기반 실시간 메시지
- 대화에서 자동 메모리 추출

### 메모리 관리
- 4단계 스코프: 개인, 채팅방, 프로젝트, 부서
- 시맨틱 벡터 검색 (Qdrant)
- 슬래시 커맨드: `/remember`, `/forget`, `/search`
- 채팅방별 컨텍스트 소스 설정 (다른 채팅방, 프로젝트, 부서 메모리 참조)

### RAG 문서
- PDF/TXT 파일 업로드
- 자동 텍스트 추출 + 청킹(800자, 100자 오버랩) + 임베딩
- 문서-채팅방 연결/해제 (다대다)
- AI 응답 시 문서 컨텍스트 우선 참조

### 관리자
- 대시보드 (전체 통계)
- 사용자/채팅방/메모리/부서/프로젝트 관리
- 메모리 페이지네이션

## 기술 스택

| 영역 | 기술 |
|------|------|
| **백엔드** | Python 3.11+, FastAPI, Uvicorn |
| **DB** | SQLite (aiosqlite) |
| **벡터 DB** | Qdrant |
| **LLM** | OpenAI 호환 API (Qwen3-32B), Anthropic, Ollama |
| **Embedding** | HuggingFace, OpenAI, Ollama |
| **프론트엔드** | React 18, TypeScript, Vite |
| **상태관리** | Zustand (클라이언트), TanStack Query (서버) |
| **스타일** | Tailwind CSS |
| **실시간** | WebSocket (Native) |

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

### 4. 테스트 데이터 생성 (선택)

```bash
python -m src.scripts.seed_data
```

### 5. DB 초기화

```bash
del data\sqlite\memory.db    # Windows
rm data/sqlite/memory.db     # Linux/Mac
```

## 프로젝트 구조

```
ai-memory-agent/
├── src/                          # 백엔드 (FastAPI)
│   ├── main.py                   # 앱 엔트리포인트
│   ├── config.py                 # 환경설정 (pydantic-settings)
│   ├── admin/                    # 관리자 API (대시보드, CRUD)
│   ├── auth/                     # 인증 (로그인/회원가입/토큰)
│   ├── chat/                     # 채팅방 + AI 응답 + 슬래시 커맨드
│   ├── document/                 # RAG 문서 (업로드/청킹/임베딩/연결)
│   ├── mchat/                    # Mattermost(Mchat) 연동
│   ├── memory/                   # 메모리 CRUD + 시맨틱 검색
│   ├── permission/               # 권한 체크
│   ├── user/                     # 사용자/부서/프로젝트
│   ├── websocket/                # WebSocket 핸들러
│   ├── shared/                   # DB, 벡터스토어, 프로바이더, 인증
│   └── scripts/                  # 시드 데이터
├── frontend/                     # 프론트엔드 (React)
│   └── src/
│       ├── features/             # 기능별 모듈
│       │   ├── admin/            # 관리자 페이지
│       │   ├── auth/             # 인증 (로그인)
│       │   ├── chat/             # 채팅 (방, 메시지, 설정)
│       │   ├── document/         # 문서 관리 (업로드, 목록)
│       │   ├── memory/           # 메모리 (검색, 목록)
│       │   └── project/          # 프로젝트 관리
│       ├── components/           # 공용 컴포넌트 (UI, 레이아웃)
│       ├── hooks/                # 커스텀 훅 (useWebSocket)
│       ├── lib/                  # API 클라이언트, 유틸
│       ├── stores/               # Zustand 스토어
│       └── types/                # TypeScript 타입
├── data/sqlite/                  # SQLite DB (자동 생성, .gitignore)
├── .env                          # 환경변수 (.gitignore)
├── pyproject.toml                # Python 의존성
├── CLAUDE.md                     # Claude Code 가이드
└── masterplan.md                 # 프로젝트 마스터플랜
```

## 인증 체계

```
Frontend                          Backend
┌─────────────────┐               ┌──────────────────────┐
│ 1. Login 요청    │──────────────▶│ POST /auth/login     │
│                  │◀──────────────│ → token + user 반환   │
│ 2. 토큰 저장     │               │                      │
│ - access_token   │               │                      │
│ - user_id        │               │                      │
│ 3. API 호출      │──────────────▶│ 토큰 검증             │
│ - Authorization  │               │ 1. Bearer 토큰       │
│ - X-User-ID      │               │ 2. X-User-ID (개발용) │
└─────────────────┘               └──────────────────────┘
```

- `Authorization: Bearer <token>` - 토큰 기반 인증 (우선)
- `X-User-ID: <user_id>` - 개발 환경 폴백

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
| GET | `/api/v1/chat-rooms` | 채팅방 목록 |
| POST | `/api/v1/chat-rooms` | 채팅방 생성 |
| GET | `/api/v1/chat-rooms/{id}` | 채팅방 상세 |
| PUT | `/api/v1/chat-rooms/{id}` | 채팅방 수정 |
| DELETE | `/api/v1/chat-rooms/{id}` | 채팅방 삭제 |
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

### Documents
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/documents/upload` | 문서 업로드 (multipart) |
| GET | `/api/v1/documents` | 문서 목록 |
| GET | `/api/v1/documents/{id}` | 문서 상세 (청크 포함) |
| DELETE | `/api/v1/documents/{id}` | 문서 삭제 |
| POST | `/api/v1/documents/{id}/link/{room_id}` | 문서-채팅방 연결 |
| DELETE | `/api/v1/documents/{id}/link/{room_id}` | 문서-채팅방 해제 |

### Admin
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/admin/dashboard` | 대시보드 통계 |
| GET | `/api/v1/admin/users` | 사용자 목록 |
| GET | `/api/v1/admin/chat-rooms` | 채팅방 목록 |
| GET | `/api/v1/admin/memories` | 메모리 목록 (페이지네이션) |
| GET | `/api/v1/admin/departments` | 부서 목록 |
| GET | `/api/v1/admin/projects` | 프로젝트 목록 |

### WebSocket
| Endpoint | 설명 |
|----------|------|
| `ws://localhost:8000/ws/chat/{room_id}?token={token}` | 실시간 채팅 |

#### WebSocket 메시지 타입
```typescript
// 클라이언트 → 서버
{ type: "message:send", data: { content: "메시지 내용" } }
{ type: "typing:start", data: {} }
{ type: "typing:stop", data: {} }
{ type: "ping", data: {} }

// 서버 → 클라이언트
{ type: "message:new", data: { id, content, user_id, ... } }
{ type: "member:join", data: { user_id, user_name } }
{ type: "member:leave", data: { user_id } }
{ type: "memory:extracted", data: { count, memories: [...] } }
{ type: "room:info", data: { room_id, online_users: [...] } }
{ type: "pong", data: {} }
```

## AI 컨텍스트 우선순위

AI가 응답할 때 다음 순서로 컨텍스트를 참조합니다:

1. **대화 내용** (최우선) - 최근 20개 메시지
2. **RAG 문서** (높은 우선순위) - 채팅방에 연결된 문서 청크
3. **저장된 메모리** (보조) - 설정된 컨텍스트 소스 기반

## 권한 체계

| Scope | 설명 | 접근 조건 |
|-------|------|----------|
| `personal` | 개인 메모리 | 소유자만 접근 |
| `chatroom` | 채팅방 메모리 | 채팅방 멤버만 접근 |
| `project` | 프로젝트 메모리 | 프로젝트 멤버만 접근 |
| `department` | 부서 메모리 | 같은 부서원만 접근 |

## 슬래시 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/remember <내용>` | 개인 + 채팅방 메모리 저장 |
| `/remember -d <내용>` | + 부서 메모리 저장 |
| `/remember -p <프로젝트명> <내용>` | + 프로젝트 메모리 저장 |
| `/forget <검색어>` | 메모리 삭제 |
| `/search <검색어>` | 메모리 검색 |
| `/members` | 멤버 목록 |
| `/invite <이메일>` | 멤버 초대 (관리자만) |
| `/help` | 도움말 |

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
