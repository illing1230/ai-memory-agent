# AI Memory Agent - Master Plan

## 1. 프로젝트 비전

멀티채팅 환경에서 **권한 기반 메모리 관리**와 **RAG 문서 활용**을 통해
팀의 지식을 체계적으로 축적하고 AI가 이를 활용하여 맥락 있는 응답을 제공하는 시스템.

---

## 2. 현재 구현 완료 (v0.2.0)

### 2.1 핵심 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| 사용자 인증 | ✅ | 로그인/회원가입, Base64+HMAC 토큰 |
| 멀티 대화방 | ✅ | 대화방 CRUD, 멤버 관리, 공유 (멤버/뷰어 권한) |
| 실시간 메시지 | ✅ | WebSocket 기반, 자동 재연결 |
| AI 응답 | ✅ | @ai 멘션, 슬래시 커맨드 7종 |
| 메모리 관리 | ✅ | 2단계 스코프 (개인/대화방), 프로젝트/부서는 비활성화 |
| 자동 메모리 추출 | ✅ | @ai 응답 후 LLM으로 중요 정보 자동 추출 |
| 수동 메모리 추출 | ✅ | `/memory` 커맨드, 중복 체크 (벡터 유사도 0.85) |
| 시맨틱 검색 | ✅ | Qdrant 벡터 검색 + 리랭킹 (유사도 60% + 최신도 40%) |
| RAG 문서 업로드 | ✅ | PDF/TXT 업로드, 청킹, 임베딩 |
| 문서-대화방 연결 | ✅ | 다대다 연결, 대화방 설정에서 관리 |
| 문서 미리보기 | ✅ | 청크별 문서 내용 확인 |
| 컨텍스트 우선순위 | ✅ | 대화 > RAG 문서 > 메모리 |
| 컨텍스트 소스 설정 | ✅ | 대화방별 메모리 소스 (이 대화방/다른 대화방/개인) |
| Agent 시스템 | ✅ | Type 등록, Marketplace, Instance 관리, API Key 발급 |
| Agent SDK | ✅ | Python SDK (Agent API + Client API), 메모리 저장/검색/소스 조회 |
| LLM 프롬프트 강화 | ✅ | 환각 방지 규칙, temperature 0.1 |
| 관리자 페이지 | ✅ | 대시보드, 사용자/대화방/메모리/부서/프로젝트 관리 |
| 사용 가이드 | ✅ | React 가이드 패널 + HTML 전체 문서 보기 |
| 프론트엔드 | ✅ | React SPA, Notion 스타일 UI |

### 2.2 슬래시 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/remember <내용>` | 개인 + 대화방 메모리 저장 |
| `/memory` | 최근 대화에서 메모리 자동 추출 (중복 자동 건너뜀) |
| `/search <검색어>` | 메모리 검색 |
| `/forget <검색어>` | 메모리 삭제 |
| `/members` | 대화방 멤버 목록 |
| `/invite <이메일>` | 멤버 초대 (관리자) |
| `/help` | 도움말 |

### 2.3 백엔드 모듈

```
src/
├── admin/          # 관리자 (대시보드, CRUD, 페이지네이션)
├── agent/          # Agent (Type 등록, Instance, SDK API, 메모리 검색)
├── auth/           # 인증 (로그인, 회원가입, 토큰 검증)
├── chat/           # 채팅 (방 CRUD, 메시지, AI 응답, 슬래시 커맨드)
├── document/       # 문서 (업로드, 청킹, 임베딩, 연결)
├── mchat/          # Mattermost 연동 (부분 구현)
├── memory/         # 메모리 (CRUD, 시맨틱 검색)
├── permission/     # 권한 체크
├── user/           # 사용자/부서/프로젝트 관리
├── websocket/      # 실시간 채팅
└── shared/         # DB, 벡터스토어, LLM/Embedding 프로바이더
```

### 2.4 프론트엔드 모듈

```
frontend/src/features/
├── admin/          # 관리자 페이지 (대시보드, 탭별 관리)
├── agent/          # Agent (Marketplace, Instance 관리, Type 등록)
├── auth/           # 로그인 폼, 인증 스토어
├── chat/           # 대화방 UI, 메시지, 멤버, 컨텍스트 설정
├── document/       # 문서 업로드, 목록, 미리보기
├── memory/         # 메모리 검색, 목록
├── project/        # 프로젝트 관리
└── share/          # 대화방 공유 모달
```

### 2.5 DB 스키마

```
users ──┬── departments
        ├── projects ── project_members
        ├── chat_rooms ── chat_room_members
        │                 chat_room_shares
        │                 chat_messages
        ├── memories (personal/chatroom)
        ├── documents ── document_chunks
        │                document_chat_rooms (다대다)
        └── agent_types ── agent_instances ── agent_data
                           agent_instance_shares
                           external_user_mappings
```

### 2.6 AI 파이프라인

```
사용자 메시지 (@ai 멘션)
    │
    ├─ 1. 최근 대화 20개 조회 (최우선 컨텍스트)
    │
    ├─ 2. RAG 문서 검색 (대화방 연결 문서 → Qdrant 벡터 검색)
    │      └─ scope="document" + document_id 필터
    │
    ├─ 3. 메모리 검색 (컨텍스트 소스 설정 기반)
    │      ├─ 이 대화방 메모리
    │      ├─ 다른 대화방 메모리 (설정 시)
    │      └─ 개인 메모리 (설정 시)
    │
    ├─ 4. 시스템 프롬프트 조립
    │      ├─ [참고 문서] (RAG, 높은 우선순위)
    │      └─ [저장된 메모리] (보조)
    │
    ├─ 5. LLM 응답 생성 (OpenAI 호환 / Anthropic / Ollama)
    │
    └─ 6. 대화에서 자동 메모리 추출 + 중복 체크 + 저장
```

### 2.7 Agent SDK 구조

```
ai_memory_agent_sdk/
├── agent.py        # Agent API (LLM + 메모리 통합, 대화 관리)
├── client.py       # Client API (동기/비동기, 메모리/메시지/로그/검색)
├── exceptions.py   # 커스텀 예외 (AuthenticationError, APIError 등)
└── __init__.py     # 패키지 export
```

---

## 2-B. v0.3.0 업데이트

### 문서 RAG 개선
| 기능 | 설명 |
|------|------|
| 시맨틱 청킹 | 의미 단위 분할 (코사인 유사도 기반 경계 감지) |
| 하이브리드 검색 | 벡터 검색(Qdrant) + 키워드 검색(SQLite FTS5) 결합 |
| Reranker | Jina Reranker로 검색 결과 정밀 재순위 |
| 엔티티 쿼리 확장 | 질문에서 추출한 엔티티로 검색 쿼리 보강 |

### 팀 지식 대시보드
| 기능 | 설명 |
|------|------|
| 메모리 통계 | scope/category/importance별 분포, 활성/대체됨 비율, 최근 7d/30d |
| 핫 토픽 TOP 15 | 자주 언급되는 엔티티 + 멘션 수 + 타입 |
| 오래된 지식 | 30d/60d/90d 미접근 메모리 수 |
| 기여도 랭킹 | 사용자별 메모리 생성 수 + 활용 수 |
| 문서 통계 | 타입별/상태별 분포, 전체 청크 수 |
| API 엔드포인트 | `GET /api/v1/admin/knowledge-dashboard` |
| 프론트엔드 | 관리자 페이지에 "지식 대시보드" 탭 추가 |

---

## 3. 향후 계획

### Phase 1: 테스트 및 안정성 (최우선)

| 항목 | 현재 상태 | 목표 | 상세 |
|------|----------|------|------|
| 단위 테스트 | 0개 | 80%+ 커버리지 | auth, chat, memory, agent, document 모듈별 테스트 |
| SDK 테스트 | 0개 | client.py, agent.py 테스트 | |
| 보안: JWT secret | 하드코딩 | 환경변수 필수화 | `config.py` 기본값 제거, production 시 에러 |
| 보안: debug 모드 | 기본 True | 기본 False | production 환경 안전성 |
| 보안: rate limiting | 없음 | API 엔드포인트별 적용 | 남용 방지 |
| Error Boundary | 없음 | React Error Boundary 추가 | 런타임 에러 시 앱 크래시 방지 |
| console.log 정리 | 37개 | 0개 | production 빌드 전 정리 |
| Agent TODO | 3건 미구현 | 구현 완료 | 공유 Instance 조회, 공유 대상 체크, 조직 멤버십 확인 |

### Phase 2: 배포 인프라

| 항목 | 현재 상태 | 목표 |
|------|----------|------|
| Docker | 없음 | Dockerfile + docker-compose.yml (백엔드 + 프론트엔드 + Qdrant) |
| CI/CD | 없음 | GitHub Actions (테스트, 린트, 빌드, 배포) |
| SDK 배포 | 로컬만 | PyPI 게시 (repository URL placeholder 수정) |
| SDK export | ValidationError 미export | `__init__.py`에서 export 추가 |

### Phase 3: Samsung Mchat 연동

Samsung 사내 메신저(Mattermost 기반)와 연동.

| 항목 | 현재 상태 | 남은 작업 |
|------|----------|----------|
| REST/WebSocket 클라이언트 | ✅ 구현 | |
| 폴링 워커 | ✅ 구현 | |
| DB 메시지 저장 | ❌ TODO | `example.py` Line 76 |
| 채널 매핑 | ⚠️ 인메모리 | DB 기반으로 변경 (재시작 시 손실 방지) |
| 에러 복구 | ❌ 미구현 | 재연결, 재시도 로직 |
| SSL 인증서 | ⚠️ 검증 비활성화 | 설정으로 분리 (내부망/외부망) |

### Phase 4: 고급 RAG 기능

| 기능 | 설명 |
|------|------|
| 추가 파일 형식 | DOCX, XLSX, PPT, Markdown 지원 |
| ~~청킹 전략 개선~~ | ✅ v0.3.0 완료 — 시맨틱 청킹 |
| ~~하이브리드 검색~~ | ✅ v0.3.0 완료 — 벡터 + FTS5 키워드 검색 |
| ~~Reranker~~ | ✅ v0.3.0 완료 — Jina Reranker |
| 문서 버전 관리 | 동일 문서 재업로드 시 버전 추적 |
| 문서 요약 | 업로드 시 자동 요약 생성 |

### Phase 5: 메모리 고도화

| 기능 | 설명 |
|------|------|
| 메모리 충돌 감지 | 상반되는 정보 저장 시 알림 |
| 메모리 만료 | TTL 기반 자동 정리 |
| 메모리 그래프 | 관련 메모리 간 연결 시각화 |
| 중복 메모리 병합 | 유사 메모리 자동 병합 (현재는 스킵만) |
| 메모리 공유 | 특정 메모리를 다른 대화방에 공유 |

### Phase 6: 성능 및 코드 품질

| 항목 | 상세 |
|------|------|
| 캐싱 레이어 | 사용자/대화방/벡터 검색 결과 캐싱 |
| 리랭킹 로직 중복 제거 | `chat/service.py`와 `agent/service.py`에 동일 로직 → 공통 모듈로 추출 |
| DB 쿼리 최적화 | N+1 쿼리 점검, 인덱스 추가 |
| 로깅/모니터링 | 구조화된 로깅, 메트릭 수집 |
| 에러 핸들링 강화 | 재시도, 서킷 브레이커, Qdrant 연결 실패 graceful degradation |
| 접근성 | ARIA label, 키보드 네비게이션, focus trap |

### Phase 7: 확장 기능

| 기능 | 설명 |
|------|------|
| 멀티 LLM 라우팅 | 질문 유형별 최적 모델 선택 |
| 스트리밍 응답 | SSE 기반 점진적 응답 |
| 음성 인터페이스 | STT/TTS 연동 |
| 모바일 앱 | React Native 또는 PWA |
| 플러그인 시스템 | 외부 도구 연동 (캘린더, JIRA 등) |

---

## 4. 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────┐
│                        클라이언트                              │
│  ┌─────────────┐  ┌───────────────┐  ┌─────────────────┐    │
│  │  React SPA  │  │  Samsung Mchat │  │  Agent SDK      │    │
│  │  (포트 3000) │  │  (Webhook)     │  │  (Python)       │    │
│  └──────┬──────┘  └───────┬───────┘  └────────┬────────┘    │
└─────────┼─────────────────┼───────────────────┼──────────────┘
          │ REST/WS         │ HTTP              │ REST (API Key)
          ▼                 ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI 백엔드 (포트 8000)                    │
│                                                                │
│  ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐  │
│  │  Auth  │ │  Chat  │ │ Document │ │Agent │ │  Admin   │  │
│  └────────┘ └───┬────┘ └────┬─────┘ └──┬───┘ └──────────┘  │
│                 │            │           │                     │
│           ┌─────▼────────────▼───────────▼───┐                │
│           │      AI Response Engine          │                │
│           │   (우선순위 컨텍스트 + 리랭킹)     │                │
│           └─────┬──────────┬─────────────────┘                │
│                 │          │                                   │
│           ┌─────▼───┐ ┌───▼──────┐                            │
│           │ Memory  │ │ Document │                            │
│           │ Service │ │ Service  │                            │
│           └────┬────┘ └────┬─────┘                            │
└────────────────┼───────────┼──────────────────────────────────┘
                 │           │
        ┌────────▼───┐  ┌───▼────────┐
        │   SQLite   │  │   Qdrant   │
        │ (메인 DB)   │  │ (벡터 DB)  │
        └────────────┘  └────────────┘

        ┌────────────────────────────┐
        │   LLM / Embedding API      │
        │  (OpenAI호환, Anthropic,   │
        │   Ollama, HuggingFace)     │
        └────────────────────────────┘
```

---

## 5. 데이터 흐름

### 메모리 저장 흐름
```
사용자: /remember 김과장은 오전 회의 선호
  → 텍스트 임베딩 생성
  → 개인 메모리 저장 (SQLite + Qdrant)
  → 대화방 메모리 저장 (SQLite + Qdrant)

사용자: /memory
  → 최근 대화 20개 조회
  → LLM으로 메모리 추출 (환각 방지 프롬프트, temperature 0.1)
  → 각 항목 벡터 유사도 중복 체크 (threshold 0.85)
  → 신규 항목만 저장, 중복은 스킵 + 사용자 알림
```

### 문서 업로드 흐름
```
사용자: PDF 파일 업로드
  → 텍스트 추출 (PyPDF2)
  → 청킹 (800자, 100자 오버랩)
  → 각 청크 임베딩 → Qdrant 저장 (scope=document)
  → 문서 메타데이터 SQLite 저장
  → (선택) 대화방에 연결
```

### AI 응답 흐름
```
사용자: @ai 오늘 회의 몇 시야?
  → 최근 대화 20개 조회
  → 연결 문서 벡터 검색 (Qdrant, scope=document)
  → 메모리 벡터 검색 (Qdrant, 컨텍스트 소스 기반)
  → 리랭킹 (유사도 60% + 최신도 40%, 30일 decay)
  → 시스템 프롬프트 조립 (문서 > 메모리 우선순위)
  → LLM 응답 생성
  → 대화에서 자동 메모리 추출 + 중복 체크
  → 응답 반환 + WebSocket 브로드캐스트
```

### Agent SDK 흐름
```
외부 챗봇: agent.message("안녕하세요!")
  → 사용자 메시지 서버에 저장 (send_message)
  → 메모리 소스에서 관련 메모리 검색 (search_memories)
  → 검색 결과를 LLM 컨텍스트에 포함
  → LLM 응답 생성
  → AI 응답 서버에 저장 (send_message)
  → 응답 반환
```

---

## 6. 기술 결정 기록

| 결정 | 선택 | 이유 |
|------|------|------|
| 메인 DB | SQLite | 설치 불필요, 단일 파일, 개발 편의성 |
| 벡터 DB | Qdrant | 오픈소스, 필터링 지원, payload 저장 |
| 백엔드 | FastAPI | 비동기, 자동 문서화, 타입 안전 |
| 프론트엔드 | React + Vite | 생태계, 빌드 속도 |
| 상태관리 | Zustand + TanStack Query | 간결함, 서버 상태 분리 |
| 인증 | Base64+HMAC | 외부 의존성 없이 간단한 토큰 인증 |
| 청킹 | 800자 + 100자 오버랩 | 일반적인 RAG 권장 사이즈 |
| 컨텍스트 우선순위 | 대화 > 문서 > 메모리 | 현재 맥락 최우선, 문서는 사실 기반, 메모리는 보조 |
| 리랭킹 가중치 | 유사도 60% + 최신도 40% | 관련성과 최신성 균형, 30일 decay |
| 중복 체크 | 벡터 유사도 0.85 | `/memory` 재실행 시 중복 저장 방지 |
| 메모리 추출 temperature | 0.1 | 환각 최소화, 대화에 명시된 정보만 추출 |
| Agent SDK | Agent API + Client API 이중 구조 | Agent API는 LLM 통합 빠른 구축, Client API는 세밀한 제어 |
| 프로젝트/부서 스코프 | 코드 유지, 사용 비활성화 | 대화방 공유로 동일 효과 달성, 복잡성 제거 |
| LLM 프로바이더 | 3종 (OpenAI호환, Anthropic, Ollama) | 다양한 환경 지원, 벤더 종속 방지 |
