# AI Memory Agent — 서버 검증 가이드

## 검증 스크립트 사용법

### 사전 요구사항

- 서버가 실행 중이어야 합니다
- Python 3.11+ 및 `httpx` 패키지가 필요합니다

### 서버 실행

```bash
cd ai-memory-agent

# 가상환경 활성화
source .venv/bin/activate

# 서버 실행
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 검증 스크립트 실행

```bash
# 기본 (localhost:8000)
python scripts/verify_server.py

# 다른 서버 지정
python scripts/verify_server.py --base-url http://192.168.1.100:8000
```

### 출력 예시

```
============================================================
  AI Memory Agent — Server Verification
  Target: http://localhost:8000
============================================================

1. Health Check
  [PASS] GET /health — status=healthy, qdrant=True

2. Authentication
  [PASS] POST /auth/register — user_id=abc123...
  [PASS] POST /auth/login — token received
  [PASS] GET /auth/me — name=Verify User
  [PASS] POST /auth/verify — token valid

3. Memory CRUD
  [PASS] POST /memories — id=def456...
  [PASS] GET /memories — count=15
  [PASS] GET /memories/{id} — content=검증 테스트 메모리...
  [PASS] PUT /memories/{id} — updated
  [PASS] POST /memories/search — results=3
  [PASS] DELETE /memories/{id} — deleted

4. Chat Room
  [PASS] POST /chat-rooms — id=ghi789...
  [PASS] GET /chat-rooms — count=5
  [PASS] POST /chat-rooms/{id}/messages — sent
  [PASS] GET /chat-rooms/{id}/messages — count=1

5. Agent SDK API
  [PASS] POST /agent-types — id=jkl012...
  [PASS] POST /agent-instances — api_key=sk_xxxxx...
  [PASS] POST /agents/{id}/data (memory) — saved
  [PASS] POST /agents/{id}/data (message) — saved
  [PASS] POST /agents/{id}/memories — id=mno345...
  [PASS] GET /agents/{id}/memory-sources — ok
  [PASS] POST /agents/{id}/memories/search — results=2
  [PASS] GET /agents/{id}/data — total=3
  [PASS] GET /agents/{id}/entities — ok
  [PASS] DELETE /agents/{id}/memories/{mid} — deleted

6. Agent Stats & Logs
  [PASS] GET /agent-instances/{id}/stats — memories=2, messages=1
  [PASS] GET /agent-instances/{id}/api-logs — total=3
  [PASS] GET /agent-instances/{id}/webhook-events — count=2

7. Admin API
  [PASS] Admin login — admin token acquired
  [PASS] GET /api/v1/admin/dashboard — Dashboard
  [PASS] GET /api/v1/admin/users — Users
  [PASS] GET /api/v1/admin/chat-rooms — Chat Rooms
  [PASS] GET /api/v1/admin/memories — Memories
  [PASS] GET /api/v1/admin/agent-dashboard — Agent Dashboard
  [PASS] GET /api/v1/admin/agent-api-logs — Agent API Logs
  [PASS] GET /api/v1/admin/knowledge-quality-report — Knowledge Quality Report

8. Rate Limiting
  [PASS] Rate Limiting — 429 at request #61, Retry-After=60

9. SSO Login
  [PASS] POST /auth/sso — user=SSO Test User, token received

Cleanup
  [PASS] Delete test agent instance — cleaned up
  [PASS] Delete test agent type — cleaned up

============================================================
  Results: 35 passed, 0 failed, 0 skipped / 35 total
============================================================
```

---

## 검증 항목 상세

### 1. Health Check

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| 서버 상태 | `GET /health` | status=healthy, SQLite/Qdrant 연결 |

### 2. Authentication

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| 회원가입 | `POST /auth/register` | 새 사용자 생성 + 토큰 발급 |
| 로그인 | `POST /auth/login` | 이메일/비밀번호 인증 + 토큰 발급 |
| 사용자 정보 | `GET /auth/me` | Bearer 토큰으로 현재 사용자 조회 |
| 토큰 검증 | `POST /auth/verify` | 토큰 유효성 확인 |

### 3. Memory CRUD

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| 생성 | `POST /memories` | 메모리 생성 + 벡터 임베딩 저장 |
| 목록 | `GET /memories` | 소유자 기반 메모리 목록 |
| 조회 | `GET /memories/{id}` | 개별 메모리 상세 |
| 수정 | `PUT /memories/{id}` | 내용/중요도 수정 |
| 검색 | `POST /memories/search` | 시맨틱 벡터 검색 |
| 삭제 | `DELETE /memories/{id}` | 메모리 삭제 |

### 4. Chat Room

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| 대화방 생성 | `POST /chat-rooms` | 대화방 생성 + 소유자 멤버 추가 |
| 대화방 목록 | `GET /chat-rooms` | 참여 중인 대화방 목록 |
| 메시지 전송 | `POST /chat-rooms/{id}/messages` | 메시지 저장 |
| 메시지 목록 | `GET /chat-rooms/{id}/messages` | 대화방 메시지 조회 |

### 5. Agent SDK API

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| 타입 생성 | `POST /agent-types` | 에이전트 타입 등록 |
| 인스턴스 생성 | `POST /agent-instances` | 인스턴스 생성 + API Key 발급 |
| 데이터 전송 (memory) | `POST /agents/{id}/data` | API Key 인증 + 메모리 저장 |
| 데이터 전송 (message) | `POST /agents/{id}/data` | 메시지 저장 |
| 메모리 생성 | `POST /agents/{id}/memories` | 전용 메모리 엔드포인트 |
| 메모리 소스 | `GET /agents/{id}/memory-sources` | 접근 가능한 메모리 소스 |
| 메모리 검색 | `POST /agents/{id}/memories/search` | 에이전트 메모리 시맨틱 검색 |
| 데이터 조회 | `GET /agents/{id}/data` | 에이전트 데이터 목록 |
| 엔티티 조회 | `GET /agents/{id}/entities` | 엔티티 그래프 |
| 메모리 삭제 | `DELETE /agents/{id}/memories/{mid}` | 에이전트 메모리 삭제 |

### 6. Agent Stats & Logs

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| 사용량 통계 | `GET /agent-instances/{id}/stats` | memory/message/log 카운트 |
| API 로그 | `GET /agent-instances/{id}/api-logs` | 호출 기록 목록 |
| Webhook 이벤트 | `GET /agent-instances/{id}/webhook-events` | 이벤트 발송 이력 |

### 7. Admin API

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| 대시보드 | `GET /admin/dashboard` | 전체 통계 |
| 사용자 목록 | `GET /admin/users` | 전체 사용자 |
| 대화방 목록 | `GET /admin/chat-rooms` | 전체 대화방 |
| 메모리 목록 | `GET /admin/memories` | 전체 메모리 (페이지네이션) |
| 에이전트 대시보드 | `GET /admin/agent-dashboard` | 에이전트 현황 |
| API 감사 로그 | `GET /admin/agent-api-logs` | 전사 API 호출 기록 |
| 지식 품질 리포트 | `GET /admin/knowledge-quality-report` | 지식 건강도 |

### 8. Rate Limiting

| 테스트 | 검증 내용 |
|--------|----------|
| 분당 호출 제한 | 61번째 요청에서 HTTP 429 반환 + Retry-After 헤더 |

### 9. SSO Login

| 테스트 | 엔드포인트 | 검증 내용 |
|--------|-----------|----------|
| SSO 로그인 | `POST /auth/sso` | 이메일 기반 매칭 또는 자동 생성 + 토큰 발급 |

---

## 수동 검증 방법

### curl로 개별 API 테스트

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. 회원가입
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test123"}'

# 3. 로그인 → 토큰 획득
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 4. 메모리 생성
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content":"테스트 메모리","scope":"personal"}'

# 5. 메모리 검색
curl -X POST http://localhost:8000/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"테스트","limit":5}'

# 6. SSO 로그인
curl -X POST http://localhost:8000/api/v1/auth/sso \
  -H "Content-Type: application/json" \
  -d '{"email":"sso@company.com","name":"SSO User","sso_provider":"saml","sso_id":"sso-123"}'

# 7. Agent SDK — API Key로 메모리 저장
curl -X POST http://localhost:8000/api/v1/agents/AGENT_ID/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_your_api_key" \
  -d '{"data_type":"memory","content":"에이전트 메모리 테스트"}'

# 8. Agent SDK — 메모리 검색
curl -X POST http://localhost:8000/api/v1/agents/AGENT_ID/memories/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_your_api_key" \
  -d '{"query":"테스트","limit":5}'

# 9. Admin — 대시보드 (admin 계정 필요)
curl http://localhost:8000/api/v1/admin/dashboard \
  -H "X-User-ID: dev-user-001"

# 10. Admin — 지식 품질 리포트
curl http://localhost:8000/api/v1/admin/knowledge-quality-report \
  -H "X-User-ID: dev-user-001"
```

### Swagger UI로 테스트

브라우저에서 `http://localhost:8000/docs` 접속하여 모든 API를 인터랙티브하게 테스트할 수 있습니다.

---

## 트러블슈팅

### 검증 스크립트 실행 실패

```bash
# httpx 미설치 시
pip install httpx

# 또는 프로젝트 가상환경 사용
.venv/bin/python scripts/verify_server.py
```

### 서버 연결 실패

```
[FAIL] GET /health — [Errno 61] Connection refused
```
→ 서버가 실행 중인지 확인: `curl http://localhost:8000/health`

### Admin API가 SKIP 되는 경우

```
[SKIP] Admin login — admin account not found
```
→ seed data를 실행하거나 X-User-ID 폴백이 admin 권한이 없을 때 발생합니다.

```bash
# seed data 실행
python -m src.scripts.seed_data
```

### Rate Limiting이 SKIP 되는 경우

```
[SKIP] Rate Limiting — no 429 after 65 requests
```
→ rate_limit_per_minute 설정이 65보다 높을 수 있습니다. 정상 동작입니다.
