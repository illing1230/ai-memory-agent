# CLAUDE.md

이 파일은 Claude Code가 이 프로젝트를 이해하고 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

AI Memory Agent - 멀티채팅 환경에서 권한 기반 메모리 관리를 제공하는 시스템.
사용자가 채팅을 하면 AI가 자동으로 메모리를 추출/저장하고, RAG 문서와 함께 컨텍스트로 활용하여 응답합니다.

## 기술 스택

### 백엔드
- **Python 3.11+**, FastAPI, Uvicorn
- **DB**: SQLite (aiosqlite) - 메인 데이터 저장
- **Vector DB**: Qdrant - 임베딩 벡터 검색 (메모리 + 문서 RAG)
- **LLM**: OpenAI 호환 API (Qwen3-32B), Anthropic, Ollama 지원
- **Embedding**: HuggingFace, OpenAI, Ollama 지원
- **인증**: Base64+HMAC 토큰, 개발 모드에서는 X-User-ID 헤더 허용

### 프론트엔드
- **React 18 + TypeScript**, Vite
- **상태관리**: Zustand (클라이언트), TanStack Query (서버)
- **스타일**: Tailwind CSS
- **라우팅**: React Router v6
- **실시간**: WebSocket (Native)
- **아이콘**: Lucide React

## 프로젝트 구조

```
ai-memory-agent/
├── src/                          # 백엔드 (Python/FastAPI)
│   ├── main.py                   # FastAPI 앱 엔트리포인트
│   ├── config.py                 # 설정 (pydantic-settings)
│   ├── admin/                    # 관리자 API
│   ├── auth/                     # 인증 (로그인/회원가입)
│   ├── chat/                     # 대화방 + AI 응답 생성
│   ├── document/                 # RAG 문서 업로드/관리
│   ├── mchat/                    # Mattermost(Mchat) 연동
│   ├── memory/                   # 메모리 CRUD + 검색
│   ├── permission/               # 권한 체크
│   ├── user/                     # 사용자/부서/프로젝트
│   ├── websocket/                # WebSocket 핸들러
│   ├── shared/                   # 공유 모듈
│   │   ├── database.py           # SQLite 초기화 + 스키마
│   │   ├── vector_store.py       # Qdrant 클라이언트
│   │   ├── providers.py          # LLM/Embedding 프로바이더
│   │   ├── auth.py               # 인증 미들웨어
│   │   └── exceptions.py         # 커스텀 예외
│   └── scripts/                  # 시드 데이터 등
├── frontend/                     # 프론트엔드 (React/TypeScript)
│   └── src/
│       ├── App.tsx               # 라우팅 설정
│       ├── components/           # 공용 UI 컴포넌트
│       ├── features/             # 기능별 모듈
│       │   ├── admin/            # 관리자 페이지
│       │   ├── auth/             # 인증
│       │   ├── chat/             # 채팅
│       │   ├── document/         # 문서 관리
│       │   ├── memory/           # 메모리 검색/목록
│       │   └── project/          # 프로젝트 관리
│       ├── hooks/                # 전역 훅 (useWebSocket 등)
│       ├── lib/                  # API 클라이언트, 유틸
│       ├── stores/               # Zustand 스토어
│       └── types/                # TypeScript 타입
├── data/sqlite/                  # SQLite DB 파일 (.gitignore)
├── .env                          # 환경변수 (.gitignore)
├── pyproject.toml                # Python 의존성
└── masterplan.md                 # 프로젝트 마스터플랜
```

## 개발 서버 실행

```bash
# 백엔드 (포트 8000)
PYTHONIOENCODING=utf-8 python -m src.main

# 프론트엔드 (포트 3000)
cd frontend && npm run dev
```

## 주요 커맨드

```bash
# 백엔드 의존성 설치
pip install -e .

# 프론트엔드 의존성 설치
cd frontend && npm install

# 프론트엔드 빌드
cd frontend && npx vite build

# 린트
ruff check src/
cd frontend && npm run lint
```

## 핵심 아키텍처 패턴

### 백엔드 모듈 구조
각 도메인 모듈(`chat/`, `memory/`, `document/` 등)은 동일한 패턴을 따릅니다:
- `router.py` - FastAPI 라우터 (엔드포인트 정의)
- `service.py` - 비즈니스 로직
- `repository.py` - DB 접근 레이어 (aiosqlite)
- `schemas.py` - Pydantic 모델 (요청/응답)

### AI 응답 컨텍스트 우선순위
`src/chat/service.py`의 `_generate_ai_response()`에서:
1. **대화 내용** (최우선) - 최근 20개 메시지
2. **RAG 문서** (높은 우선순위) - 대화방에 연결된 문서 청크
3. **저장된 메모리** (보조) - 컨텍스트 소스 설정 기반 검색

### 메모리 스코프
- `personal` - 개인 메모리
- `chatroom` - 대화방 메모리
- `project` - 프로젝트 메모리
- `department` - 부서 메모리

### 프론트엔드 패턴
- Feature-based 구조: `features/{domain}/api/`, `hooks/`, `components/`
- API 호출: `lib/api.ts`의 `get/post/put/del` 래퍼 사용
- 서버 상태: TanStack Query (`useQuery`, `useMutation`)
- 파일 업로드: FormData 직접 fetch (JSON 래퍼 미사용)

## DB 스키마 (주요 테이블)

- `users` - 사용자 (role: user/admin)
- `departments` - 부서
- `projects` / `project_members` - 프로젝트 + 멤버
- `chat_rooms` / `chat_room_members` - 대화방 + 멤버
- `chat_messages` - 채팅 메시지 (user/assistant 역할)
- `memories` - 메모리 (scope별 분류, vector_id로 Qdrant 연결)
- `documents` / `document_chunks` - RAG 문서 + 청크
- `document_chat_rooms` - 문서-대화방 다대다 연결

## API 엔드포인트 (주요)

| Prefix | 모듈 | 설명 |
|--------|------|------|
| `/api/v1/auth` | auth | 로그인/회원가입/토큰검증 |
| `/api/v1/users` | user | 사용자/부서/프로젝트 관리 |
| `/api/v1/chat-rooms` | chat | 대화방 CRUD + 메시지 |
| `/api/v1/memories` | memory | 메모리 CRUD + 검색 |
| `/api/v1/documents` | document | 문서 업로드/목록/삭제/연결 |
| `/api/v1/admin` | admin | 관리자 대시보드/관리 |
| `/api/v1/permissions` | permission | 권한 체크 |
| `/ws/chat/{room_id}` | websocket | 실시간 채팅 |

## 환경변수 (.env)

주요 설정:
- `SQLITE_DB_PATH` - SQLite 경로
- `QDRANT_URL` / `QDRANT_COLLECTION` - Qdrant 연결
- `EMBEDDING_PROVIDER` - 임베딩 프로바이더 (huggingface/openai/ollama)
- `LLM_PROVIDER` - LLM 프로바이더 (openai/ollama/anthropic)
- `APP_ENV` - 환경 (development/production)

## 주의사항

- Windows 환경에서 `PYTHONIOENCODING=utf-8`로 서버 실행 필요 (이모지 출력 때문)
- Qdrant 미연결 시에도 앱은 정상 동작 (벡터 검색만 비활성화)
- 개발 모드에서 `X-User-ID` 헤더로 인증 우회 가능
- SQLite DB는 자동 스키마 마이그레이션 (ALTER TABLE 시도 → 실패 시 무시)
- `.env` 파일은 `.gitignore`에 포함됨
