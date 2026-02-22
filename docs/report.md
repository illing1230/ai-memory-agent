# AI Memory Agent — 전사 AI 에이전트 지식 인프라 플랫폼

## 보고 자료

---

## 1. 개요

### 프로젝트 목적

사내 AI 에이전트 개발자들이 **메모리(지식) 기능을 쉽게 붙일 수 있는 중앙 인프라**를 제공하여, 전사 AI 에이전트의 지식을 한 곳에서 축적·관리·활용할 수 있는 플랫폼.

### 핵심 가치

| 대상 | 제공 가치 |
|------|----------|
| **AI 에이전트 개발자** | SDK + 문서 → 5줄 코드로 메모리 기능 연동 |
| **플랫폼 운영자** | 대시보드, 사용량 통계, 감사 로그, 지식 품질 관리 |
| **조직** | 전사 AI 지식 자산 축적, 에이전트 간 지식 공유 |

### 포지셔닝

> **"AI 에이전트용 사내 지식 인프라를 운영한다"**

- 각 팀이 개별적으로 메모리 시스템을 구축하는 것 대비 **중앙화된 관리와 교차 활용** 가능
- 개발자에게는 간편한 SDK, 운영자에게는 가시성 있는 대시보드 제공

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Memory Agent Platform                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Frontend │  │ SDK      │  │Mattermost│  │ REST API  │  │
│  │ (React)  │  │ (Python) │  │   Bot    │  │ (Swagger) │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │              │               │       │
│  ┌────▼──────────────▼──────────────▼───────────────▼────┐  │
│  │              FastAPI Backend (Python)                  │  │
│  │                                                       │  │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐  │  │
│  │  │  Auth   │ │  Memory  │ │  Agent  │ │   Admin   │  │  │
│  │  │ (JWT)   │ │ (CRUD+   │ │ (SDK    │ │ (Dashboard│  │  │
│  │  │         │ │  Search) │ │  API)   │ │  Report)  │  │  │
│  │  └─────────┘ └──────────┘ └─────────┘ └───────────┘  │  │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐  │  │
│  │  │  Chat   │ │ Document │ │ Webhook │ │   Rate    │  │  │
│  │  │(Room+WS)│ │  (RAG)   │ │         │ │  Limiter  │  │  │
│  │  └─────────┘ └──────────┘ └─────────┘ └───────────┘  │  │
│  └──────────────┬──────────────────────┬─────────────────┘  │
│                 │                      │                    │
│        ┌────────▼────────┐    ┌────────▼────────┐          │
│        │  SQLite (관계형) │    │  Qdrant (벡터)  │          │
│        │  - 사용자/채팅   │    │  - 메모리 임베딩 │          │
│        │  - 메모리 메타   │    │  - 문서 청크     │          │
│        │  - 감사 로그     │    │  - 시맨틱 검색   │          │
│        └─────────────────┘    └─────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 기술 스택

| 영역 | 기술 | 비고 |
|------|------|------|
| 백엔드 | Python 3.11+, FastAPI | 비동기 처리 |
| 관계형 DB | SQLite (aiosqlite) | 경량, 서버리스 |
| 벡터 DB | Qdrant | 시맨틱 검색 |
| LLM | OpenAI 호환 API, Anthropic, Ollama | 다중 프로바이더 |
| Embedding | HuggingFace, OpenAI, Ollama | 다중 프로바이더 |
| 프론트엔드 | React 18, TypeScript, Vite | SPA |
| 메신저 연동 | Mattermost (WebSocket + REST) | 실시간 봇 |
| 컨테이너 | Docker Compose | 원클릭 배포 |

---

## 3. 주요 기능

### 3-1. 개발자용 — Python SDK

AI 에이전트 개발자가 최소한의 코드로 메모리 기능을 연동할 수 있는 SDK.

```python
from ai_memory_agent_sdk import Agent

agent = Agent(
    api_key="sk_xxx",
    base_url="http://memory-server:8000",
    agent_id="my-bot",
    llm_provider="openai",
    llm_url="https://api.openai.com/v1",
    llm_api_key="sk-...",
    model="gpt-4o-mini",
)

# 대화 (자동으로 서버에서 관련 메모리 검색 → LLM 컨텍스트에 주입)
response = agent.message("프로젝트 마감일이 언제야?")

# 대화에서 중요 정보를 자동 추출하여 서버에 메모리로 저장
agent.memory()
```

**SDK 제공 기능:**

| 기능 | 설명 |
|------|------|
| `agent.message(text)` | 메모리 기반 AI 대화 |
| `agent.memory()` | 대화에서 메모리 자동 추출 + 서버 저장 |
| `agent.search(query)` | 서버 메모리 시맨틱 검색 |
| `agent.sources()` | 사용 가능한 메모리 소스 조회 |
| `agent.data()` | 에이전트가 저장한 데이터 조회 |
| `agent.health()` | 서버 연결 상태 확인 |

**클라이언트 모드:** 고수준 Agent 외에 저수준 SyncClient / AsyncClient도 제공하여 세밀한 제어 가능.

### 3-2. 운영자용 — 관리 대시보드 API

| API | 설명 |
|-----|------|
| `GET /admin/agent-dashboard` | 전체 에이전트 현황 (인스턴스 수, 활성 수, 메모리 수, 메시지 수, 일별 활동) |
| `GET /admin/agent-api-logs` | 전사 API 호출 감사 로그 |
| `GET /admin/knowledge-quality-report` | 지식 품질 리포트 (오래된 메모리, 중복 후보, 스코프 분포, 엔티티 분석) |
| `GET /agent-instances/{id}/stats` | 개별 에이전트 사용량 통계 |
| `GET /agent-instances/{id}/api-logs` | 개별 에이전트 API 호출 기록 |
| `GET /agent-instances/{id}/webhook-events` | Webhook 발송 이력 |

### 3-3. 메모리 시스템

**3단계 스코프:**

| 스코프 | 설명 | 예시 |
|--------|------|------|
| `personal` | 개인 메모리 | "사용자가 Python을 선호함" |
| `chatroom` | 대화방 공유 메모리 | "프로젝트 마감일은 3/15" |
| `agent` | 에이전트가 저장한 메모리 | "고객 문의: 결제 오류 해결" |

**핵심 메커니즘:**
- 시맨틱 벡터 검색 (Qdrant) — 의미 기반 메모리 검색
- 메모리 자동 추출 — LLM이 대화에서 사실/선호도/결정 사항 등을 자동 감지
- 중복 제거 — 유사도 임계값(0.85) 기반 중복 메모리 방지
- Supersede 체인 — 메모리 업데이트 시 이전 버전 이력 관리
- 메모리 감쇠 — 30일 미접근 시 중요도 자동 하향 (high→medium→low)
- 엔티티 추출 — 메모리에서 인물/장소/시간 등 엔티티 자동 추출 및 링크

### 3-4. RAG 문서 시스템

| 기능 | 설명 |
|------|------|
| 문서 업로드 | PDF, TXT 파일 업로드 |
| 시맨틱 청킹 | 의미 단위 분할 (코사인 유사도 기반 경계 감지) |
| 하이브리드 검색 | 벡터 검색(Qdrant) + 키워드 검색(SQLite FTS5) 결합 |
| Reranker | Jina Reranker로 최종 결과 정밀 재순위 |
| 문서-대화방 연결 | 다대다 관계로 특정 대화방에서 문서 컨텍스트 참조 |

### 3-5. Mattermost 연동

사내 Mattermost에서 바로 AI 봇과 대화 가능.

| 기능 | 설명 |
|------|------|
| DM 자동 응답 | Bot에게 DM 보내면 AI 응답 |
| @ai 멘션 | 채널에서 `@ai` 멘션으로 호출 |
| 메모리 자동 추출 | 대화에서 중요 정보 자동 저장 |
| 사용자 자동 매핑 | Mattermost 계정 ↔ AI Memory Agent 계정 (이메일 기반) |
| 채널 자동 매핑 | Mattermost 채널 ↔ AI Memory Agent 대화방 |
| 대화 요약 | `@ai 요약` 명령어로 채널 대화 요약 |

### 3-6. 보안 및 운영

| 기능 | 설명 |
|------|------|
| JWT 인증 | 사용자 로그인/회원가입 |
| API Key 인증 | 에이전트 SDK 인증 (X-API-Key) |
| Rate Limiting | 에이전트별 분당 호출 제한 (기본 60회/분, 429 응답) |
| API 감사 로그 | 에이전트 API 호출 기록 자동 저장 |
| Webhook | 메모리 생성/메시지 수신 시 개발자 서버로 알림 (3회 재시도) |
| 권한 기반 접근 | 메모리 스코프별 접근 제어 |

---

## 4. 에이전트 간 지식 공유

### 교차 에이전트 메모리 검색

A팀 에이전트의 메모리를 B팀 에이전트가 검색할 수 있는 기능.

```
┌──────────────┐                    ┌──────────────┐
│  A팀 에이전트 │─── 메모리 저장 ──▶│              │
│  (고객 응대)  │                    │   AI Memory  │
│              │                    │   Agent      │
│              │                    │   Server     │
│  B팀 에이전트 │◀── 메모리 검색 ───│              │
│  (기술 지원)  │                    │              │
└──────────────┘                    └──────────────┘
```

**사전 조건:** 에이전트 인스턴스 간 공유 설정 필요 (role: viewer/member)

**활용 예시:**
- 고객 응대 봇이 축적한 FAQ → 기술 지원 봇이 참조
- 영업 봇이 저장한 고객 정보 → 마케팅 봇이 참조
- 기획 봇이 저장한 프로젝트 일정 → 개발 봇이 참조

### 메모리 타임라인

메모리가 시간에 따라 어떻게 변화했는지 추적:

```
[v1] "프로젝트 마감일: 3/15"
  └── superseded by ──▶ [v2] "프로젝트 마감일: 3/22로 연장"
                           └── superseded by ──▶ [v3] "프로젝트 마감일: 3/29 (최종)"
```

`GET /api/v1/memories/{id}/history` → 전체 supersede 체인 반환

---

## 5. 지식 품질 리포트

운영자가 **전사 AI 지식의 건강도**를 한눈에 파악할 수 있는 API.

`GET /api/v1/admin/knowledge-quality-report` 응답 예시:

```json
{
  "total_memories": 76,
  "stale_memories_count": 28,
  "duplicate_candidates_count": 5,
  "superseded_chain_count": 3,
  "scope_distribution": {
    "personal": 11,
    "chatroom": 61,
    "agent": 4
  },
  "category_distribution": {
    "fact": 25,
    "preference": 12,
    "task": 8,
    "decision": 5
  },
  "top_entities": [
    {"name": "Qwen3-32B", "type": "technology", "mention_count": 5},
    {"name": "Python", "type": "technology", "mention_count": 4}
  ],
  "agent_contribution": [
    {"agent_name": "My Bot", "memory_count": 4, "last_active": "2025-06-10T..."}
  ]
}
```

**리포트 항목:**

| 항목 | 설명 | 활용 |
|------|------|------|
| `stale_memories_count` | 30일 이상 미접근 메모리 | 정리 대상 파악 |
| `duplicate_candidates_count` | 높은 유사도 메모리 쌍 | 중복 정리 |
| `superseded_chain_count` | 업데이트 체인 수 | 지식 발전 추적 |
| `scope_distribution` | 스코프별 메모리 분포 | 활용 패턴 분석 |
| `top_entities` | 자주 언급되는 엔티티 | 핵심 주제 파악 |
| `agent_contribution` | 에이전트별 기여도 | 활성도 모니터링 |

---

## 6. 배포

### Docker Compose (원클릭 배포)

```bash
docker-compose up -d
```

| 서비스 | 포트 | 역할 |
|--------|------|------|
| api | 8000 | FastAPI 백엔드 |
| qdrant | 6333 | 벡터 DB |
| frontend | 3000 | React SPA (nginx) |

### 환경 구성

| 환경 | DB | 벡터 DB | LLM | Embedding |
|------|-----|---------|-----|-----------|
| 로컬 개발 | SQLite (파일) | Qdrant (Docker) | Ollama (로컬) | Ollama (로컬) |
| 사내 서버 | SQLite (파일) | Qdrant (K8s) | Qwen3-32B (내부) | HuggingFace (내부) |
| 외부 클라우드 | SQLite (파일) | Qdrant Cloud | OpenAI API | OpenAI API |

---

## 7. 로드맵

### 완료

- [x] 채팅 + AI 응답 + 메모리 자동 추출
- [x] RAG 문서 시스템 (하이브리드 검색 + Reranker)
- [x] 관리자 대시보드
- [x] Mattermost 봇 연동
- [x] Python SDK (Agent + SyncClient + AsyncClient)
- [x] Docker Compose 배포
- [x] 에이전트 사용량 통계 API
- [x] API 감사 로그
- [x] Webhook 시스템
- [x] Rate Limiting
- [x] 멀티 에이전트 메모리 공유
- [x] 메모리 타임라인 (Supersede 체인)
- [x] 지식 품질 리포트 API

### 향후 계획

- [ ] 프론트엔드 관리자 대시보드 UI (에이전트 관리, 지식 품질 시각화)
- [ ] SDK npm 패키지 (JavaScript/TypeScript 지원)
- [ ] 멀티테넌시 지원 (부서/프로젝트 격리)
- [ ] 메모리 임포트/익스포트 기능
- [ ] 에이전트 성능 벤치마크 도구
- [ ] Slack 연동

---

## 8. 기대 효과

### 정량적

| 항목 | 기대 효과 |
|------|----------|
| 에이전트 개발 시간 | 메모리 시스템 직접 구축 대비 **80% 단축** (SDK 5줄 연동) |
| 지식 활용율 | 에이전트 간 지식 공유로 **중복 지식 축적 50% 감소** |
| 운영 가시성 | 실시간 통계 + 감사 로그로 **이상 탐지 시간 90% 단축** |

### 정성적

- **전사 AI 지식 자산화**: 각 팀의 AI 에이전트 지식이 중앙 서버에 축적
- **플랫폼 표준화**: 에이전트마다 다른 메모리 구현 대신 통일된 인프라
- **운영 거버넌스**: 누가, 언제, 어떤 지식을 축적했는지 추적 가능
- **확장성**: 새로운 에이전트 추가 시 SDK 연동만으로 즉시 메모리 기능 사용
