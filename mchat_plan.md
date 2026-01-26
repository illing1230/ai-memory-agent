# Samsung Mchat 연동 계획 및 검토사항

## 1. 개요

Samsung Mchat은 Mattermost 기반의 사내 메신저로, Mattermost API v4를 활용하여 AI Memory Agent와 연동할 수 있습니다.

### 연동 목표
- Mchat 채팅방의 메시지를 AI Memory Agent로 전달
- AI가 메모리 기반으로 응답 생성
- `/remember`, `/search`, `@ai` 등 커맨드 지원

---

## 2. Mattermost 연동 방식 비교

| 방식 | 설명 | 장점 | 단점 | 권장 용도 |
|------|------|------|------|-----------|
| **Incoming Webhook** | 외부 → Mattermost 메시지 전송 | 간단한 설정, 코딩 불필요 | 단방향만 가능 | AI 응답 전송 |
| **Outgoing Webhook** | 특정 키워드 시 외부 서버 호출 | 트리거 기반 동작 | Public 채널만 지원 | 커맨드 트리거 |
| **Bot Account + REST API** | 양방향 메시지 처리 | 완전한 제어 가능 | 구현 복잡도 높음 | 완전한 봇 기능 |
| **WebSocket** | 실시간 이벤트 수신 | 즉각적인 반응 | 연결 유지 필요 | 실시간 모니터링 |
| **Slash Command** | `/명령어` 형태 | 사용자 친화적 | 응답 시간 제한 (5초) | 간단한 조회 |

### 권장 아키텍처: **Outgoing Webhook + Incoming Webhook 조합**

```
┌─────────────────────────────────────────────────────────────────┐
│                        Samsung Mchat                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   사용자: @ai 오늘 불량률 몇 %야?                                │
│                     │                                            │
│                     ▼                                            │
│            [Outgoing Webhook]                                    │
│            (트리거: @ai, /remember 등)                           │
│                     │                                            │
└─────────────────────│────────────────────────────────────────────┘
                      │ HTTP POST
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI Memory Agent                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. 메시지 파싱                                                 │
│   2. 메모리 검색 (Qdrant)                                        │
│   3. LLM 응답 생성                                               │
│   4. 메모리 추출 & 저장                                          │
│                     │                                            │
└─────────────────────│────────────────────────────────────────────┘
                      │ HTTP POST (Incoming Webhook)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Samsung Mchat                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   🤖 AI: 저장된 메모리에 따르면 오늘 X부품 불량률은 12%입니다.   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 연동 방식별 상세

### 3.1 Outgoing Webhook (메시지 수신)

Mchat에서 특정 트리거 발생 시 AI Memory Agent로 HTTP POST 요청

**트리거 설정:**
- 트리거 워드: `@ai`, `/remember`, `/search`, `/forget`
- 또는 특정 채널의 모든 메시지

**Webhook Payload (Mchat → AI Agent):**
```json
{
  "token": "webhook_token",
  "team_id": "team123",
  "team_domain": "quality-team",
  "channel_id": "channel456",
  "channel_name": "품질검사",
  "timestamp": 1706234567,
  "user_id": "user789",
  "user_name": "김과장",
  "post_id": "post_abc",
  "text": "@ai 오늘 X부품 불량률 어때?",
  "trigger_word": "@ai"
}
```

**AI Agent 응답 (즉시 응답 시):**
```json
{
  "text": "저장된 메모리에 따르면 오늘 X부품 불량률은 12%입니다.",
  "username": "AI Assistant",
  "icon_url": "https://example.com/ai-icon.png"
}
```

### 3.2 Incoming Webhook (AI 응답 전송)

AI가 처리 완료 후 Mchat으로 메시지 전송

**Webhook URL 형식:**
```
https://mchat.samsung.com/hooks/xxx-generated-key-xxx
```

**전송 Payload:**
```json
{
  "channel": "품질검사",
  "username": "AI Memory Bot",
  "icon_emoji": ":robot:",
  "text": "#### 🧠 메모리 저장됨\n\n- **내용:** X부품 불량률 12%\n- **범위:** 이 채팅방\n- **카테고리:** fact"
}
```

### 3.3 Bot Account + WebSocket (고급)

실시간으로 모든 채널 메시지를 모니터링하고 처리

```python
from mattermostdriver import Driver

driver = Driver({
    'url': 'mchat.samsung.com',
    'token': 'BOT_ACCESS_TOKEN',
    'scheme': 'https',
    'port': 443
})

driver.login()

async def event_handler(event):
    data = json.loads(event)
    if data.get('event') == 'posted':
        post = json.loads(data['data']['post'])
        message = post['message']
        channel_id = post['channel_id']
        user_id = post['user_id']
        
        # AI Memory Agent 처리
        if message.startswith('@ai') or message.startswith('/remember'):
            response = await process_message(message, user_id, channel_id)
            driver.posts.create_post({
                'channel_id': channel_id,
                'message': response
            })

driver.init_websocket(event_handler)
```

---

## 4. 구현 계획

### Phase 1: 기본 연동 (2주)

**목표:** Outgoing + Incoming Webhook으로 기본 기능 구현

```
Week 1:
├── Mchat 관리자에게 Webhook 권한 요청
├── Outgoing Webhook 생성 (트리거: @ai, /remember, /search)
├── Incoming Webhook 생성 (AI 응답용)
└── AI Agent에 Mchat Webhook 엔드포인트 추가

Week 2:
├── 메시지 파싱 로직 구현
├── 채널/사용자 ID 매핑 테이블 구축
├── 기본 커맨드 연동 테스트
└── 에러 핸들링 및 로깅
```

### Phase 2: Bot Account 연동 (2주)

**목표:** Bot Account로 양방향 완전 연동

```
Week 3:
├── Mchat Bot Account 생성 요청
├── Bot Token 발급 및 권한 설정
├── REST API 클라이언트 구현
└── 메시지 읽기/쓰기 테스트

Week 4:
├── 채널 자동 참여 로직
├── 멘션 및 DM 처리
├── 메시지 편집/삭제 기능
└── 통합 테스트
```

### Phase 3: WebSocket 실시간 연동 (2주)

**목표:** 실시간 이벤트 기반 처리

```
Week 5:
├── WebSocket 연결 관리자 구현
├── 이벤트 핸들러 구현
├── 재연결 로직 (Connection Recovery)
└── 메시지 큐잉 시스템

Week 6:
├── 멀티 채널 동시 모니터링
├── 성능 최적화
├── 모니터링 대시보드
└── 운영 배포
```

---

## 5. 검토 사항

### 5.1 사전 확인 필요 (Mchat 관리자)

| 항목 | 질문 | 중요도 |
|------|------|--------|
| **API 버전** | Mchat이 Mattermost API v4를 지원하는지? | 🔴 필수 |
| **Webhook 활성화** | Outgoing/Incoming Webhook이 활성화되어 있는지? | 🔴 필수 |
| **Bot Account** | Bot Account 생성이 가능한지? | 🟡 권장 |
| **WebSocket** | WebSocket 연결이 허용되는지? | 🟢 선택 |
| **API 엔드포인트** | 내부 API URL (예: `mchat.samsung.com/api/v4/`) | 🔴 필수 |
| **인증 방식** | Personal Access Token vs Session Token | 🔴 필수 |
| **Rate Limit** | API 호출 제한이 있는지? (기본: 10req/sec) | 🟡 권장 |
| **Private 채널** | Private 채널 접근 권한 정책 | 🟡 권장 |

### 5.2 보안 검토

```
┌─────────────────────────────────────────────────────────────────┐
│                       보안 체크리스트                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ □ Webhook URL은 내부망에서만 접근 가능한지?                      │
│ □ Bot Token 저장 방식 (환경변수, Vault 등)                       │
│ □ 메시지 암호화 전송 (HTTPS)                                     │
│ □ 민감정보 필터링 (개인정보, 비밀번호 등)                        │
│ □ 로그에 토큰/민감정보 노출 방지                                 │
│ □ IP 화이트리스트 설정 가능 여부                                 │
│ □ 감사 로그 기록                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 네트워크 검토

```
AI Memory Agent Server          Samsung Mchat Server
    (10.244.14.73:8000)              (mchat.samsung.com)
           │                                │
           │◄──── Outgoing Webhook ─────────│
           │      (Mchat → Agent)           │
           │                                │
           │────── Incoming Webhook ───────►│
           │      (Agent → Mchat)           │
           │                                │
           │◄───── WebSocket (선택) ────────│
           │      (실시간 양방향)            │
           │                                │
           
확인사항:
- 방화벽 정책 (포트 오픈 필요)
- 프록시 설정 여부
- SSL 인증서 검증
```

### 5.4 기능 제약사항

| 기능 | Outgoing Webhook | Bot Account | WebSocket |
|------|-----------------|-------------|-----------|
| Public 채널 | ✅ | ✅ | ✅ |
| Private 채널 | ❌ | ✅ (초대 필요) | ✅ |
| DM | ❌ | ✅ | ✅ |
| 파일 업로드 | ❌ | ✅ | ✅ |
| 메시지 편집 | ❌ | ✅ | ✅ |
| Reaction | ❌ | ✅ | ✅ |
| Thread 응답 | ⚠️ (제한적) | ✅ | ✅ |
| 응답 시간 | 5초 제한 | 제한 없음 | 실시간 |

---

## 6. 코드 구조 (예상)

```
src/
├── mchat/
│   ├── __init__.py
│   ├── client.py          # Mchat API 클라이언트
│   ├── webhook_handler.py # Webhook 수신 처리
│   ├── bot.py             # Bot Account 로직
│   ├── websocket.py       # WebSocket 연결 관리
│   ├── models.py          # Mchat 데이터 모델
│   └── router.py          # FastAPI 라우터
```

### 6.1 Webhook Handler 예시

```python
# src/mchat/webhook_handler.py
from fastapi import APIRouter, Request, HTTPException
from src.chat.service import ChatService

router = APIRouter(prefix="/mchat", tags=["Mchat"])

@router.post("/webhook/outgoing")
async def handle_outgoing_webhook(request: Request):
    """Mchat Outgoing Webhook 수신"""
    payload = await request.json()
    
    # 토큰 검증
    if payload.get("token") != settings.MCHAT_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # 메시지 추출
    text = payload.get("text", "")
    user_id = payload.get("user_id")
    channel_id = payload.get("channel_id")
    user_name = payload.get("user_name")
    
    # AI Memory Agent 처리
    chat_service = ChatService(db)
    result = await chat_service.process_mchat_message(
        mchat_channel_id=channel_id,
        mchat_user_id=user_id,
        mchat_user_name=user_name,
        content=text,
    )
    
    # Outgoing Webhook 직접 응답 (5초 이내)
    if result.get("quick_response"):
        return {
            "text": result["response"],
            "username": "AI Memory Bot",
            "icon_emoji": ":robot:"
        }
    
    # 비동기 처리 후 Incoming Webhook으로 응답
    return {"text": ""}  # 빈 응답 (별도로 Incoming Webhook 사용)
```

### 6.2 Mchat Client 예시

```python
# src/mchat/client.py
import httpx
from typing import Optional

class MchatClient:
    """Mchat API 클라이언트"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def send_message(
        self,
        channel_id: str,
        message: str,
        root_id: Optional[str] = None,  # Thread 응답용
    ) -> dict:
        """채널에 메시지 전송"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v4/posts",
                headers=self.headers,
                json={
                    "channel_id": channel_id,
                    "message": message,
                    "root_id": root_id,
                }
            )
            return response.json()
    
    async def send_via_webhook(
        self,
        webhook_url: str,
        message: str,
        channel: Optional[str] = None,
        username: str = "AI Memory Bot",
    ) -> bool:
        """Incoming Webhook으로 메시지 전송"""
        async with httpx.AsyncClient() as client:
            payload = {
                "text": message,
                "username": username,
                "icon_emoji": ":robot:",
            }
            if channel:
                payload["channel"] = channel
            
            response = await client.post(webhook_url, json=payload)
            return response.status_code == 200
    
    async def get_user(self, user_id: str) -> dict:
        """사용자 정보 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v4/users/{user_id}",
                headers=self.headers,
            )
            return response.json()
    
    async def get_channel(self, channel_id: str) -> dict:
        """채널 정보 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v4/channels/{channel_id}",
                headers=self.headers,
            )
            return response.json()
```

---

## 7. 데이터 매핑

### 7.1 채널 매핑 테이블

```sql
-- Mchat 채널 ↔ AI Memory Agent 채팅방 매핑
CREATE TABLE mchat_channel_mapping (
    id TEXT PRIMARY KEY,
    mchat_channel_id TEXT UNIQUE NOT NULL,
    mchat_channel_name TEXT,
    mchat_team_id TEXT,
    agent_room_id TEXT REFERENCES chat_rooms(id),
    webhook_url TEXT,  -- Incoming Webhook URL (응답용)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_mchat_channel_id ON mchat_channel_mapping(mchat_channel_id);
```

### 7.2 사용자 매핑 테이블

```sql
-- Mchat 사용자 ↔ AI Memory Agent 사용자 매핑
CREATE TABLE mchat_user_mapping (
    id TEXT PRIMARY KEY,
    mchat_user_id TEXT UNIQUE NOT NULL,
    mchat_username TEXT,
    agent_user_id TEXT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_mchat_user_id ON mchat_user_mapping(mchat_user_id);
```

---

## 8. 테스트 계획

### 8.1 단위 테스트

```python
# tests/test_mchat_webhook.py
import pytest
from fastapi.testclient import TestClient

def test_outgoing_webhook_valid_token():
    """유효한 토큰으로 Webhook 호출"""
    response = client.post("/mchat/webhook/outgoing", json={
        "token": "valid_token",
        "text": "@ai 테스트",
        "user_id": "user123",
        "channel_id": "channel456",
    })
    assert response.status_code == 200

def test_outgoing_webhook_invalid_token():
    """유효하지 않은 토큰"""
    response = client.post("/mchat/webhook/outgoing", json={
        "token": "invalid_token",
        "text": "@ai 테스트",
    })
    assert response.status_code == 401

def test_remember_command():
    """/remember 커맨드 테스트"""
    response = client.post("/mchat/webhook/outgoing", json={
        "token": "valid_token",
        "text": "/remember X부품 불량률 12%",
        "user_id": "user123",
        "channel_id": "channel456",
        "trigger_word": "/remember"
    })
    assert "저장" in response.json()["text"]
```

### 8.2 통합 테스트

```
1. Mchat 테스트 채널 생성
2. Outgoing Webhook 설정 (→ AI Agent)
3. Incoming Webhook 설정 (← AI Agent)
4. 테스트 시나리오 실행:
   - @ai 질문 → AI 응답 확인
   - /remember 저장 → 토스트 확인
   - /search 검색 → 결과 확인
5. 성능 측정 (응답 시간, 처리량)
```

---

## 9. 운영 고려사항

### 9.1 모니터링

```yaml
# 메트릭 수집 항목
metrics:
  - mchat_webhook_requests_total       # Webhook 호출 수
  - mchat_webhook_latency_seconds      # 처리 시간
  - mchat_webhook_errors_total         # 에러 수
  - mchat_messages_processed_total     # 처리된 메시지 수
  - mchat_ai_responses_total           # AI 응답 수
  - mchat_memory_saved_total           # 저장된 메모리 수
```

### 9.2 에러 처리

```python
# 재시도 정책
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 2,
    "retry_status_codes": [429, 500, 502, 503, 504],
}

# 타임아웃 설정
TIMEOUT_CONFIG = {
    "webhook_response": 4.5,  # Outgoing Webhook 응답 (5초 제한)
    "api_request": 10.0,
    "websocket_ping": 30.0,
}
```

### 9.3 로깅

```python
# 로그 포맷
LOG_FORMAT = {
    "timestamp": "2025-01-26T12:00:00Z",
    "level": "INFO",
    "service": "mchat-integration",
    "mchat_channel_id": "channel456",
    "mchat_user_id": "user123",
    "action": "message_processed",
    "latency_ms": 150,
    "memory_count": 2,
}
```

---

## 10. 다음 단계

1. **Mchat 관리자 미팅** - API 접근 권한 및 정책 확인
2. **테스트 환경 구축** - 개발용 Webhook 설정
3. **PoC 개발** - 기본 Webhook 연동 구현
4. **보안 검토** - 정보보안팀 검토 요청
5. **파일럿 운영** - 품질팀 일부 채널에서 테스트
6. **확대 적용** - 전체 품질팀 롤아웃

---

## 부록: 유용한 API 엔드포인트

| 용도 | 엔드포인트 | 메서드 |
|------|-----------|--------|
| 로그인 | `/api/v4/users/login` | POST |
| 내 정보 | `/api/v4/users/me` | GET |
| 사용자 조회 | `/api/v4/users/{user_id}` | GET |
| 채널 조회 | `/api/v4/channels/{channel_id}` | GET |
| 메시지 전송 | `/api/v4/posts` | POST |
| 메시지 조회 | `/api/v4/channels/{channel_id}/posts` | GET |
| 팀 목록 | `/api/v4/teams` | GET |
| 채널 목록 | `/api/v4/users/{user_id}/teams/{team_id}/channels` | GET |
| WebSocket | `/api/v4/websocket` | WS |