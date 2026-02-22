# Mattermost 로컬 설치 및 봇 설정 가이드

## 1. Mattermost 로컬 설치 (Docker)

### 사전 요구사항

- Docker Desktop 설치 완료
- Docker Compose 사용 가능

### 1-1. Docker Compose로 설치

```bash
mkdir mattermost-local && cd mattermost-local
```

`docker-compose.yml` 작성:

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: mmuser
      POSTGRES_PASSWORD: mmuser_password
      POSTGRES_DB: mattermost
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  mattermost:
    image: mattermost/mattermost-team-edition:latest
    ports:
      - "8065:8065"
    environment:
      MM_SQLSETTINGS_DRIVERNAME: postgres
      MM_SQLSETTINGS_DATASOURCE: "postgres://mmuser:mmuser_password@postgres:5432/mattermost?sslmode=disable&connect_timeout=10"
      MM_SERVICESETTINGS_SITEURL: "http://localhost:8065"
      # Bot 계정 생성 허용
      MM_SERVICESETTINGS_ENABLEBOTACCOUNTCREATION: "true"
      # Personal Access Token 허용
      MM_SERVICESETTINGS_ENABLEUSERACCESSTOKENS: "true"
      # WebSocket 설정
      MM_SERVICESETTINGS_ENABLEWEBSOCKETCONNECTIONS: "true"
    volumes:
      - mattermost_config:/mattermost/config
      - mattermost_data:/mattermost/data
      - mattermost_logs:/mattermost/logs
      - mattermost_plugins:/mattermost/plugins
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
  mattermost_config:
  mattermost_data:
  mattermost_logs:
  mattermost_plugins:
```

```bash
docker-compose up -d
```

### 1-2. 초기 설정

1. 브라우저에서 `http://localhost:8065` 접속
2. 관리자 계정 생성 (이메일, 사용자명, 비밀번호 설정)
3. 팀 생성 (예: `ai-team`)

---

## 2. Bot 계정 생성

### 방법 A: System Console에서 Bot 생성 (권장)

1. 좌측 상단 메뉴 > **System Console** 접속
2. **Integrations > Bot Accounts** 이동
   - "Enable Bot Account Creation" → **true** 확인
3. 좌측 상단 메뉴 > 팀으로 돌아가기
4. 상단 메뉴 > **Integrations** > **Bot Accounts** > **Add Bot Account**
   - Username: `ai-memory-bot`
   - Display Name: `AI Memory Bot`
   - Description: `AI Memory Agent 연동 봇`
   - Role: `System Admin` (모든 채널 접근 필요 시) 또는 `Member`
5. **Create Bot Account** 클릭
6. **Token** 이 표시됨 → 반드시 복사하여 저장 (다시 볼 수 없음)

### 방법 B: Personal Access Token 사용

Bot 계정 대신 일반 사용자 계정의 Personal Access Token을 사용할 수도 있음.

1. **System Console > Integrations > Integration Management**
   - "Enable Personal Access Tokens" → **true**
2. 봇으로 사용할 계정으로 로그인
3. 좌측 하단 프로필 > **Security** > **Personal Access Tokens**
4. **Create Token**
   - Description: `ai-memory-agent`
5. **Token ID**와 **Access Token** 복사

### 방법 C: mmctl CLI 사용

```bash
# Mattermost 컨테이너 내부에서 실행
docker exec -it mattermost-local-mattermost-1 bash

# 로그인
mmctl auth login http://localhost:8065 --name local --username admin --password <password>

# Bot 생성
mmctl bot create ai-memory-bot --display-name "AI Memory Bot" --description "AI Memory Agent 연동 봇"

# Token 생성
mmctl token generate ai-memory-bot "ai-memory-agent-token"
# → Access Token 출력됨. 복사하여 저장.
```

---

## 3. AI Memory Agent 서버 연결 설정

### 3-1. .env 파일 설정

프로젝트 루트의 `.env` 파일에 다음을 설정:

```bash
# ===========================================
# Mchat (Mattermost) Integration
# ===========================================
# 로컬 Mattermost 서버 URL (HTTP)
MCHAT_URL=http://localhost:8065

# Bot Access Token (위에서 복사한 토큰)
MCHAT_TOKEN=<여기에_토큰_붙여넣기>

# 연동 활성화
MCHAT_ENABLED=true

# 로컬 HTTP 서버이므로 SSL 검증 불필요
MCHAT_SSL_VERIFY=true

# Bot 이름 (Mattermost에서 생성한 Bot의 username)
MCHAT_BOT_NAME=ai-memory-bot

# DM에서 @ai 멘션 없이도 자동 응답
MCHAT_RESPOND_TO_ALL_DM=true
```

| 설정 | 설명 | 로컬 기본값 |
|------|------|-------------|
| `MCHAT_URL` | Mattermost 서버 URL | `http://localhost:8065` |
| `MCHAT_TOKEN` | Bot/Personal Access Token | (필수) |
| `MCHAT_ENABLED` | Mchat 연동 활성화 | `false` |
| `MCHAT_SSL_VERIFY` | SSL 인증서 검증 | `true` (HTTP는 무관) |
| `MCHAT_BOT_NAME` | Bot username (멘션 감지용) | `ai-memory-bot` |
| `MCHAT_RESPOND_TO_ALL_DM` | DM 자동 응답 | `true` |
| `MCHAT_SUMMARY_ENABLED` | 채널 대화 자동 요약 | `false` |
| `MCHAT_SUMMARY_DEFAULT_INTERVAL_HOURS` | 요약 주기 (시간) | `24` |

### 3-2. SSL 설정 참고

| 환경 | MCHAT_URL | MCHAT_SSL_VERIFY |
|------|-----------|------------------|
| 로컬 Docker (HTTP) | `http://localhost:8065` | `true` (영향 없음) |
| 사내 HTTPS (자체 인증서) | `https://mchat.example.com` | `false` |
| 외부 HTTPS (정상 인증서) | `https://mattermost.company.com` | `true` |

---

## 4. 서버 실행 및 테스트

### 4-1. AI Memory Agent 서버 시작

```bash
cd /path/to/ai-memory-agent

# 가상환경 활성화
source .venv/bin/activate

# 서버 실행 (Mchat worker 자동 시작)
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

서버 로그에서 Mchat 연결 상태 확인:

```
Mchat Worker starting
MCHAT_URL: http://localhost:8065
Bot ID: xxxxx, Username: ai-memory-bot
Starting WebSocket connection...
WebSocket connected!
```

### 4-2. 동작 테스트

1. Mattermost에서 Bot에게 DM 전송:
   ```
   안녕하세요! 저는 프론트엔드 개발자입니다.
   ```
   → Bot이 AI 응답을 보내면 정상 연결

2. 채널에서 @ai 멘션으로 호출:
   ```
   @ai 프로젝트 일정을 기억해줘. 다음 주 금요일이 마감이야.
   ```
   → Bot이 응답하고, 메모리가 자동 추출됨

3. 채널에서 요약 요청:
   ```
   @ai 요약
   @ai 요약 48시간
   ```
   → 채널 최근 대화를 요약하여 응답 (MCHAT_SUMMARY_ENABLED=true 필요)

### 4-3. 관리 API로 상태 확인

```bash
# 서버 헬스체크
curl http://localhost:8000/health

# Mchat 연결 상태 확인 (관리자 토큰 필요)
curl -H "Authorization: Bearer <JWT토큰>" \
     http://localhost:8000/api/v1/mchat/status
```

---

## 5. 봇 동작 방식

### 메시지 응답 조건

| 상황 | 응답 여부 |
|------|----------|
| Bot에게 DM | O (`MCHAT_RESPOND_TO_ALL_DM=true` 일 때) |
| 채널에서 `@ai` 멘션 | O |
| 채널에서 `@ai-memory-bot` 멘션 | O |
| 채널에서 일반 메시지 | X |
| 봇 자신의 메시지 | X (무한루프 방지) |
| sync_enabled=false 채널 | X |

### 사용자/채널 자동 매핑

- Mattermost 사용자 → AI Memory Agent 사용자 (이메일 기반 매칭, 없으면 자동 생성)
- Mattermost 채널 → AI Memory Agent 대화방 (자동 생성)
- 매핑 정보는 `mchat_user_mapping`, `mchat_channel_mapping` 테이블에 저장

### 메모리 자동 추출

대화에서 의미 있는 정보(사실, 선호도, 일정 등)가 감지되면 자동으로 메모리로 추출하여 저장. 이후 동일 사용자의 질문에 관련 메모리를 검색하여 맥락 있는 응답 제공.

---

## 6. 트러블슈팅

### Bot이 응답하지 않는 경우

1. **토큰 확인**: `.env`의 `MCHAT_TOKEN`이 올바른지 확인
2. **서버 로그 확인**: `Mchat Worker starting` 이후 에러 메시지 확인
3. **Bot 권한 확인**: Bot이 해당 채널에 참여되어 있는지 확인
4. **WebSocket 연결**: 로그에 `WebSocket connected!` 표시되는지 확인

### WebSocket 연결이 끊기는 경우

- 서버가 자동으로 재연결 시도 (Exponential backoff: 5초 → 10초 → 20초 → ... → 최대 60초)
- 로그에 `Reconnecting in Xs...` 메시지 확인

### Mattermost 설정 확인

System Console에서 다음 설정이 활성화되어 있는지 확인:

- **Integrations > Bot Accounts > Enable Bot Account Creation**: true
- **Integrations > Integration Management > Enable Personal Access Tokens**: true
- **Environment > WebSocket > Enable WebSocket Connections**: true (기본값 true)

### 로컬 Mattermost 재시작

```bash
cd mattermost-local
docker-compose restart mattermost
```
