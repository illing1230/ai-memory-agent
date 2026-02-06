# Samsung Mchat 연동 계획

## 1. 개요

Samsung Mchat(Mattermost 기반 사내 메신저)을 AI Memory Agent의 **클라이언트**로 연동한다.
Agent SDK와 동일하게, **AI Memory Agent가 모든 메시지와 메모리를 통합 관리**하는 구조를 취한다.

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **Single Source of Truth** | 모든 메시지는 AI Memory Agent DB(chat_messages)에 저장. Mchat은 UI 채널일 뿐 |
| **통합 파이프라인** | Mchat 메시지도 `ChatService.send_message()`를 거쳐 동일한 AI 응답/메모리 추출 파이프라인 사용 |
| **클라이언트 동등성** | React SPA, Agent SDK, Mchat 모두 동일한 백엔드 서비스를 공유하는 클라이언트 |
| **양방향 동기화** | Mchat → Agent: 메시지 수신/저장, Agent → Mchat: AI 응답 전송 |

### 연동 목표

- Mchat 채널의 메시지를 AI Memory Agent에 저장하고 관리
- 동일한 AI 파이프라인으로 응답 생성 (컨텍스트 우선순위, 리랭킹 동일 적용)
- `@ai`, `/remember`, `/search`, `/memory` 등 기존 커맨드 그대로 지원
- Mchat 사용자/채널 ↔ Agent 사용자/대화방 자동 매핑

---

## 2. 아키텍처

### 2.1 통합 메시지 관리 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        클라이언트 계층                        │
│                                                             │
│  ┌───────────┐   ┌──────────────┐   ┌───────────────────┐   │
│  │ React SPA │   │ Samsung Mchat│   │ Agent SDK (Python)│   │
│  │ (웹 UI)   │   │ (사내 메신저)  │   │ (외부 에이전트)     │   │
│  └─────┬─────┘   └──────┬───────┘   └────────┬──────────┘   │
│        │                │                     │             │
│   REST/WS          WS/Polling             REST (API Key)    │
│        │                │                     │             │
└────────┼────────────────┼─────────────────────┼─────────────┘
         │                │                     │
         ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI 백엔드 (포트 8000)                   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              ChatService.send_message()              │   │
│  │    (공통 진입점: 메시지 저장, AI 응답, 메모리 추출)       │    │
│  └──────────────────────────────────────────────────────┘   │
│         │              │                  │                 │
│    ┌────▼────┐   ┌─────▼─────┐   ┌────────▼────────┐        │
│    │  Chat   │   │  Memory   │   │    Document     │        │
│    │ Service │   │  Service  │   │    Service      │        │
│    └────┬────┘   └─────┬─────┘   └────────┬────────┘        │
│         │              │                  │                 │
└─────────┼──────────────┼──────────────────┼─────────────────┘
          │              │                  │
     ┌────▼────┐    ┌────▼────┐        ┌────▼────┐
     │ SQLite  │    │ Qdrant  │        │   LLM   │
     │(메시지,  │    │(벡터DB)  │        │Provider │
     │ 메모리)  │    │         │        │         │
     └─────────┘    └─────────┘        └─────────┘
```

### 2.2 클라이언트별 역할 비교

| 항목 | React SPA | Mchat | Agent SDK |
|------|-----------|-------|-----------|
| **메시지 전송** | REST API / WebSocket | Worker가 중계 | REST API (API Key) |
| **메시지 저장** | chat_messages | chat_messages (동일) | agent_data + chat_messages |
| **AI 응답** | ChatService 직접 | ChatService 직접 (동일) | Agent API or Client API |
| **메모리 추출** | 자동 (동일 파이프라인) | 자동 (동일 파이프라인) | 수동 (POST /data) |
| **인증** | Base64+HMAC 토큰 | Bot Token + 사용자 매핑 | API Key |
| **실시간** | WebSocket | WebSocket/Polling | Polling |

### 2.3 메시지 흐름 (Mchat → Agent → Mchat)

```
[Mchat 사용자]
    │ "@ai 오늘 불량률 몇 %야?"
    ▼
[Mchat 서버] ──── WebSocket/Polling ────▶ [MchatWorker]
                                              │
                                    1. Mchat user → Agent user 매핑
                                    2. Mchat channel → Agent chatroom 매핑
                                    3. 자체 메시지(봇 응답) 필터링
                                              │
                                              ▼
                                    [ChatService.send_message()]
                                              │
                               ┌──────────────┼──────────────┐
                               │              │              │
                          chat_messages   AI 응답 생성    메모리 추출
                          테이블 저장     (Qdrant 검색     (자동)
                                          + LLM 호출)
                                              │
                                              ▼
                                    assistant_message 반환
                                              │
                                              ▼
                                    [MchatClient.create_post()]
                                              │
                                              ▼
[Mchat 서버] ◀──── REST API ─────── AI 응답 메시지 전송
    │
    ▼
[Mchat 사용자]
    "🤖 저장된 메모리에 따르면 오늘 X부품 불량률은 12%입니다."
```

---

## 3. 현재 구현 상태

### 3.1 구현 완료

| 구성요소 | 파일 | 상태 | 설명 |
|----------|------|------|------|
| REST/WS 클라이언트 | `mchat/client.py` | ✅ | Mattermost API v4 + WebSocket |
| WebSocket 워커 | `mchat/worker.py` | ✅ | 실시간 이벤트 수신, 메시지 중계 |
| Polling 워커 | `mchat/polling_worker.py` | ✅ | REST API 폴링 방식 (대안) |
| 사용자 매핑 | `worker.py` 내부 | ✅ | Mchat user_id → Agent user_id (이메일 기반) |
| 채널 매핑 | `worker.py` 내부 | ✅ | Mchat channel_id → Agent chat_room_id |
| 봇 메시지 필터 | `worker.py` 내부 | ✅ | 이모지 접두사(🤖, ✅ 등)로 자체 응답 무시 |
| ChatService 연동 | `worker.py` 내부 | ✅ | `send_message()` 호출로 통합 파이프라인 사용 |

### 3.2 미구현 / 보완 필요

| 항목 | 현재 상태 | 필요 작업 | 우선순위 |
|------|----------|----------|----------|
| DB 기반 채널 매핑 | 인메모리 dict | `mchat_channel_mapping` 테이블 사용 | 🔴 높음 |
| DB 기반 사용자 매핑 | 인메모리 dict | `mchat_user_mapping` 테이블 사용 | 🔴 높음 |
| 에러 복구 | 없음 | WebSocket 재연결, 메시지 재시도 로직 | 🔴 높음 |
| SSL 인증서 | 검증 비활성화 | 설정으로 분리 (내부망/외부망) | 🟡 중간 |
| 라우터 통합 | 없음 | FastAPI 라우터로 관리 API 제공 | 🟡 중간 |
| 매핑 관리 UI | 없음 | 프론트엔드에서 채널/사용자 매핑 관리 | 🟢 낮음 |

---

## 4. 데이터 매핑

### 4.1 채널 매핑 테이블

```sql
-- Mchat 채널 ↔ AI Memory Agent 대화방 매핑
CREATE TABLE IF NOT EXISTS mchat_channel_mapping (
    id TEXT PRIMARY KEY,
    mchat_channel_id TEXT UNIQUE NOT NULL,
    mchat_channel_name TEXT,
    mchat_team_id TEXT,
    agent_room_id TEXT REFERENCES chat_rooms(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 사용자 매핑 테이블

```sql
-- Mchat 사용자 ↔ AI Memory Agent 사용자 매핑
CREATE TABLE IF NOT EXISTS mchat_user_mapping (
    id TEXT PRIMARY KEY,
    mchat_user_id TEXT UNIQUE NOT NULL,
    mchat_username TEXT,
    agent_user_id TEXT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 매핑 로직

```
매핑 우선순위:
1. DB 매핑 테이블 조회 (mchat_user_mapping)
2. 이메일 기반 자동 매핑 (Mchat 이메일 → Agent users 테이블 이메일 조회)
3. 자동 생성 (새 Agent 사용자 + 매핑 레코드 생성)

채널 매핑:
1. DB 매핑 테이블 조회 (mchat_channel_mapping)
2. 자동 생성 (새 Agent 대화방 + 매핑 레코드 생성)
```

---

## 5. 구현 계획

### Phase 1: DB 기반 매핑 전환

**목표:** 인메모리 매핑을 DB 기반으로 전환하여 재시작 시에도 매핑 유지

- DB 스키마에 `mchat_channel_mapping`, `mchat_user_mapping` 테이블 추가
- `MchatRepository` 클래스 생성 (매핑 CRUD)
- Worker에서 인메모리 dict 대신 DB 조회/저장으로 변경
- 기존 인메모리 매핑을 캐시로 활용 (DB 조회 → 메모리 캐시 → 반환)

### Phase 2: 에러 복구 및 안정성

**목표:** 운영 환경에서의 안정적 동작 보장

- WebSocket 재연결 로직 (exponential backoff)
- 메시지 전송 실패 시 재시도 (최대 3회, backoff_factor=2)
- Mchat 서버 다운 시 메시지 큐잉 (SQLite 큐)
- 헬스체크 엔드포인트 (`/mchat/health`)

### Phase 3: 관리 API 및 모니터링

**목표:** Mchat 연동 상태를 관리하고 모니터링

- FastAPI 라우터 (`/api/v1/mchat/`)
  - `GET /mappings/channels` - 채널 매핑 목록
  - `POST /mappings/channels` - 채널 매핑 수동 생성
  - `GET /mappings/users` - 사용자 매핑 목록
  - `GET /status` - 워커 연결 상태
- 관리자 페이지에 Mchat 연동 현황 탭 추가

### Phase 4: SSL 및 보안 강화

**목표:** 운영 환경 보안 요건 충족

- SSL 인증서 검증 설정 분리 (`MCHAT_VERIFY_SSL=true/false`)
- Bot Token 환경변수 관리
- Webhook 토큰 검증
- 민감정보 필터링 (개인정보, 비밀번호 등 마스킹)

---

## 6. Mattermost 연동 방식

### 6.1 수신 방식 비교

| 방식 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **WebSocket** (현재 기본) | 실시간 이벤트 구독 | 즉각 반응, 모든 채널 | 연결 유지 필요 |
| **REST Polling** (현재 대안) | 주기적 메시지 조회 | 단순, 안정적 | 지연 (2초), API 부하 |
| **Outgoing Webhook** | 트리거 기반 | 설정 간단 | Public 채널만, 5초 제한 |

**선택: WebSocket 기본 + Polling 폴백**
- WebSocket 연결 실패 시 자동으로 Polling 모드 전환
- 두 방식 모두 동일한 `ChatService.send_message()` 호출

### 6.2 응답 전송 방식

| 방식 | 설명 | 사용 시점 |
|------|------|----------|
| **REST API** (`create_post`) | Bot Account로 메시지 전송 | AI 응답 전송 (기본) |
| **Incoming Webhook** | Webhook URL로 전송 | Bot Account 미지원 시 대안 |

---

## 7. 사전 확인 사항 (Mchat 관리자)

| 항목 | 질문 | 중요도 |
|------|------|--------|
| API 버전 | Mattermost API v4 지원 여부 | 🔴 필수 |
| Bot Account | Bot Account 생성 가능 여부 | 🔴 필수 |
| WebSocket | WebSocket 연결 허용 여부 | 🔴 필수 |
| API 엔드포인트 | 내부 API URL 확인 | 🔴 필수 |
| 인증 방식 | Personal Access Token vs Bot Token | 🔴 필수 |
| Rate Limit | API 호출 제한 (기본 10req/sec) | 🟡 권장 |
| Private 채널 | Private 채널 접근 정책 | 🟡 권장 |
| 방화벽 | Agent 서버 ↔ Mchat 서버 간 포트 오픈 | 🔴 필수 |
| SSL 인증서 | 내부 CA 인증서 필요 여부 | 🟡 권장 |

---

## 8. 보안 체크리스트

- [ ] Bot Token 환경변수 관리 (코드에 하드코딩 금지)
- [ ] HTTPS 통신 (내부망이라도 TLS 권장)
- [ ] Webhook 토큰 검증 (Outgoing Webhook 사용 시)
- [ ] 민감정보 필터링 (개인정보, 비밀번호 마스킹)
- [ ] 로그에 토큰/민감정보 노출 방지
- [ ] IP 화이트리스트 (가능 시)
- [ ] 감사 로그 기록

---

## 9. 기존 Agent 시스템과의 차이점

Agent SDK와 Mchat 모두 "외부 클라이언트 → AI Memory Agent 통합 관리" 구조이지만 차이가 있다:

| 항목 | Agent SDK | Mchat 연동 |
|------|-----------|------------|
| **연결 방식** | 외부 → Agent REST API | Agent → Mchat WebSocket/Polling |
| **연결 주체** | 외부 시스템이 연결 | AI Memory Agent가 연결 |
| **메시지 저장** | `agent_data` + 선택적 `chat_messages` | `chat_messages` 직접 저장 |
| **사용자 매핑** | `external_user_mappings` (API 기반) | `mchat_user_mapping` (이메일 기반) |
| **인증** | API Key (외부 → 내부) | Bot Token (내부 → Mchat) |
| **커맨드 지원** | SDK에서 직접 구현 | `@ai`, `/remember` 등 파싱 후 ChatService 위임 |

**공통점:**
- 모든 메시지가 AI Memory Agent DB에 저장됨 (Single Source of Truth)
- 동일한 AI 응답 파이프라인 (컨텍스트 우선순위, 리랭킹)
- 동일한 메모리 추출/검색 로직
- 사용자/채널 매핑 테이블로 외부 ID ↔ 내부 ID 변환

---

## 10. 다음 단계

1. **Mchat 관리자 미팅** - API 접근 권한, Bot Account 생성, 네트워크 정책 확인
2. **Phase 1 구현** - DB 기반 매핑으로 전환 (현재 코드 리팩토링)
3. **통합 테스트** - 테스트 채널에서 메시지 수신 → AI 응답 → 메모리 추출 검증
4. **Phase 2 구현** - 에러 복구, 안정성 확보
5. **파일럿 운영** - 특정 채널에서 시범 운영
6. **확대 적용** - 전체 롤아웃
