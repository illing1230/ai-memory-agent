# Mchat (Mattermost) 연동 테스트 가이드

## 사전 조건

| 서비스 | URL | 상태 확인 |
|--------|-----|-----------|
| Mattermost | http://localhost:8065 | 브라우저에서 접속 |
| AI Memory Agent | http://localhost:8000 | `curl http://localhost:8000/health` |
| Qdrant | http://localhost:6333 | `curl http://localhost:6333` |
| Embedding Server | http://localhost:7997 | `curl http://localhost:7997/health` |

## 1. Mattermost 로그인

브라우저에서 http://localhost:8065 접속

```
이메일: admin@test.com
비밀번호: Testpass123
```

> 로그인하면 "Test Team" > "Town Square" 채널에 진입됩니다.

## 2. 서버 시작

```bash
# Mattermost (이미 실행 중이면 생략)
docker start mattermost-preview

# AI Memory Agent
source .venv/bin/activate
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

로그에 아래 메시지가 보이면 정상:
```
[mchat] INFO: WebSocket connected!
```

## 3. 계정 연결 구조

```
Mattermost admin (admin@test.com)
        ↓ 이메일 자동 매칭
Agent dev-user-001 (admin@test.com)
        ↓
기존 메모리 29개 접근 가능
```

Mattermost 이메일과 Agent 이메일이 같으면 자동으로 기존 계정에 연결됩니다.

## 4. 테스트 시나리오

### 4-1. 공개 채널에서 @ai 멘션

**Town Square** 채널에서:

```
@ai 안녕! 내 일정 알려줘
```

- `@ai` 또는 `@ai-memory-bot` 멘션 시 봇이 응답
- 멘션 없는 일반 메시지는 무시됨

### 4-2. DM (1:1 대화)

왼쪽 사이드바에서 `ai-memory-bot`을 찾아 DM 시작:

```
오늘 오후 5시에 팀 회의 있어. 기억해줘.
```

- DM에서는 `@ai` 멘션 없이도 자동 응답
- 메모리 자동 추출 (회의 일정 → 메모리 저장)

### 4-3. 메모리 활용 확인

DM에서:

```
내가 저장한 일정들 알려줘
```

- 이전에 저장된 메모리 (부산 출장, MemGate 프로젝트 등)를 기반으로 응답
- Mattermost에서 보낸 새 메모리도 포함

### 4-4. 메모리 저장 확인

DM에서:

```
다음주 금요일에 김품질 팀장이랑 점심 약속 있어
```

응답 후, Agent 웹 UI(http://localhost:8000)에서 로그인하여 메모리 목록 확인.

### 4-5. 연속 대화

DM에서 여러 메시지를 이어서 보내기:

```
1. 새 프로젝트 이름은 "ProjectX"야
2. ProjectX는 React + FastAPI 기술 스택이야
3. ProjectX 기술 스택 뭐라고 했지?
```

→ 3번에서 이전 대화 맥락을 활용해 응답하는지 확인.

## 5. 관리자 페이지 확인

브라우저에서 http://localhost:8000 접속 후 로그인:

```
이메일: admin@test.com
비밀번호: test123
```

**Admin > Mchat 탭**에서 확인 가능한 항목:
- 연결 상태 (Connected/Disconnected)
- 메시지 통계 (수신/응답/메모리추출/에러)
- 채널 매핑 목록 + Sync ON/OFF 토글
- 사용자 매핑 목록

## 6. 로그 확인

```bash
# 서버 로그 실시간 확인
tail -f /tmp/mchat-server.log

# 또는 foreground로 실행 중이면 콘솔에서 직접 확인
```

주요 로그 패턴:
```
[mchat.worker] INFO: Message from @admin: ...     # 메시지 수신
[mchat.worker] INFO: Email match: ... -> ...       # 이메일 매칭 (최초 1회)
[mchat.worker] INFO: Message saved to room=...     # 메시지 저장
[mchat.worker] INFO: AI response sent (N chars)    # AI 응답 전송
```

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 봇이 응답 안 함 | WebSocket 미연결 | 서버 로그에서 `WebSocket connected!` 확인 |
| `대화방 멤버가 아닙니다` | 계정 매핑 변경 후 기존 채널 매핑 불일치 | DB에서 `mchat_channel_mapping` 해당 행 삭제 후 서버 재시작 |
| DM에서 응답 안 함 | `MCHAT_RESPOND_TO_ALL_DM=false` | `.env`에서 `true`로 변경 |
| 메모리가 안 보임 | 이메일 불일치로 새 계정 생성됨 | Admin > Mchat > Users에서 매핑 확인 |

## 8. 환경 변수 (.env)

```env
MCHAT_URL=http://localhost:8065
MCHAT_TOKEN=3i44my51c3bxb8q1d753q79mnw
MCHAT_ENABLED=true
MCHAT_SSL_VERIFY=true
MCHAT_BOT_NAME=ai-memory-bot
MCHAT_RESPOND_TO_ALL_DM=true
```
