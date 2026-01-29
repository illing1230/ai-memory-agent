# AI Memory Agent

멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템입니다.

## 🎯 주요 기능

- **멀티채팅 기반 메모리**: 여러 채팅방의 대화를 통합 메모리로 저장
- **권한 기반 접근 제어**: 개인/프로젝트/부서 단위 메모리 접근 관리
- **시맨틱 검색**: 벡터 임베딩 기반 유사 메모리 검색
- **자동 메모리 추출**: LLM을 활용한 대화에서 메모리 자동 추출
- **실시간 채팅**: WebSocket 기반 실시간 메시지 전송
- **AI 응답**: `@ai` 멘션으로 AI 어시스턴트와 대화

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite (개발) / PostgreSQL (운영)
- **Vector DB**: Qdrant
- **Embedding**: HuggingFace, OpenAI, Ollama
- **LLM**: OpenAI Compatible (Qwen3), Ollama, Anthropic
- **WebSocket**: FastAPI WebSocket

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **상태 관리**: Zustand
- **서버 상태**: TanStack Query (React Query)
- **라우팅**: React Router v6
- **실시간 통신**: WebSocket (Native)

## 📁 프로젝트 구조

```
ai-memory-agent/
├── src/                        # Backend (FastAPI)
│   ├── main.py                 # FastAPI 엔트리포인트
│   ├── config.py               # 설정 관리
│   ├── auth/                   # 인증 모듈
│   │   ├── router.py           # 인증 API 라우터
│   │   ├── service.py          # 인증 비즈니스 로직
│   │   └── schemas.py          # Pydantic 스키마
│   ├── memory/                 # 메모리 모듈
│   │   ├── router.py           # 메모리 API 라우터
│   │   ├── service.py          # 메모리 비즈니스 로직
│   │   └── repository.py       # 데이터 접근 계층
│   ├── user/                   # 사용자/부서/프로젝트 모듈
│   ├── chat/                   # 채팅방 모듈
│   ├── permission/             # 권한 모듈
│   ├── websocket/              # WebSocket 모듈
│   │   ├── router.py           # WebSocket 엔드포인트
│   │   └── manager.py          # 연결 관리자
│   ├── shared/                 # 공유 모듈
│   │   ├── auth.py             # 공통 인증 유틸리티
│   │   ├── database.py         # SQLite 연결
│   │   ├── vector_store.py     # Qdrant 연결
│   │   └── providers/          # Embedding/LLM Providers
│   └── scripts/
│       └── seed_data.py        # 테스트 데이터 생성
│
├── frontend/                   # Frontend (React)
│   ├── src/
│   │   ├── App.tsx             # 라우팅 설정
│   │   ├── main.tsx            # 엔트리포인트
│   │   ├── components/         # 공용 컴포넌트
│   │   │   ├── ui/             # 기본 UI (Button, Input 등)
│   │   │   └── layout/         # 레이아웃 (Sidebar, MainLayout)
│   │   ├── features/           # 기능별 모듈
│   │   │   ├── auth/           # 인증 (로그인/회원가입)
│   │   │   ├── chat/           # 채팅 (채팅방, 메시지)
│   │   │   ├── memory/         # 메모리 (검색, 목록)
│   │   │   ├── project/        # 프로젝트 관리
│   │   │   └── workspace/      # 워크스페이스
│   │   ├── hooks/              # 커스텀 훅
│   │   │   └── useWebSocket.ts # WebSocket 훅
│   │   ├── lib/                # 유틸리티
│   │   │   └── api.ts          # API 클라이언트
│   │   ├── stores/             # Zustand 스토어
│   │   └── types/              # TypeScript 타입
│   ├── vite.config.ts          # Vite 설정 (프록시 포함)
│   └── package.json
│
├── tests/                      # 테스트
├── data/                       # 로컬 데이터 (SQLite, Qdrant)
├── docs/                       # 문서
├── pyproject.toml              # Python 의존성
└── .env.example                # 환경변수 템플릿
```

## 🚀 빠른 시작

### 1. Backend 설정

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

### 2. Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install
```

### 3. 서버 실행

```bash
# Terminal 1: Backend 실행
python -m src.main
# 또는: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend 실행
cd frontend
npm run dev
```

### 4. 접속

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend ReDoc**: http://localhost:8000/redoc

### 5. 테스트 데이터 생성 (선택)

```bash
python -m src.scripts.seed_data
```

## 🔐 인증 체계

### 인증 플로우

```
┌─────────────────┐                  ┌──────────────────────────────────┐
│    Frontend     │                  │            Backend               │
├─────────────────┤                  ├──────────────────────────────────┤
│ 1. Login 요청   │─────────────────▶│ POST /api/v1/auth/login          │
│                 │◀─────────────────│ → access_token + user 반환       │
├─────────────────┤                  ├──────────────────────────────────┤
│ 2. 토큰 저장    │                  │                                  │
│ - access_token  │                  │                                  │
│ - user_id       │                  │                                  │
├─────────────────┤                  ├──────────────────────────────────┤
│ 3. API 호출     │─────────────────▶│ get_current_user_id() 검증       │
│ Headers:        │                  │ 1. Authorization: Bearer 토큰    │
│ - Authorization │                  │ 2. X-User-ID 폴백 (개발용)       │
│ - X-User-ID     │                  │                                  │
└─────────────────┘                  └──────────────────────────────────┘
```

### 인증 헤더

모든 인증이 필요한 API 요청에는 다음 헤더가 포함됩니다:

```
Authorization: Bearer <access_token>
X-User-ID: <user_id>
```

- `Authorization`: JWT 토큰 기반 인증 (우선 적용)
- `X-User-ID`: 개발 환경용 폴백

## 🌐 API 엔드포인트

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

### Memory
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/memories` | 메모리 목록 |
| POST | `/api/v1/memories` | 메모리 생성 |
| GET | `/api/v1/memories/{id}` | 메모리 상세 |
| PUT | `/api/v1/memories/{id}` | 메모리 수정 |
| DELETE | `/api/v1/memories/{id}` | 메모리 삭제 |
| POST | `/api/v1/memories/search` | 시맨틱 검색 |
| POST | `/api/v1/memories/extract` | 메모리 자동 추출 |

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

## 🔒 권한 체계

| Scope | 설명 | 접근 조건 |
|-------|------|----------|
| `personal` | 개인 메모리 | 소유자만 접근 |
| `chatroom` | 채팅방 메모리 | 채팅방 멤버만 접근 |
| `project` | 프로젝트 메모리 | 프로젝트 멤버만 접근 |
| `department` | 부서 메모리 | 같은 부서원만 접근 |

## ⚙️ 환경 변수

`.env.example` 파일을 참조하여 `.env` 파일을 생성하세요:

```env
# App
APP_ENV=development

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

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

## 📱 Frontend 기능

### 채팅
- 채팅방 목록/생성/관리
- 실시간 메시지 전송 (WebSocket)
- `@ai` 멘션으로 AI 응답
- 타이핑 인디케이터
- 메시지 히스토리

### 메모리
- 시맨틱 검색
- Scope 필터링 (개인/채팅방/프로젝트/부서)
- 메모리 생성/삭제

### UI/UX
- Notion 스타일 사이드바
- 반응형 디자인
- 로딩 상태 표시
- 에러 처리

## 🧪 테스트

```bash
# Backend 테스트
pytest

# Frontend 린트
cd frontend
npm run lint
```

## 📄 라이선스

Internal Use Only - Samsung Electronics
