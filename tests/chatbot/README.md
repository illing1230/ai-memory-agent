# AI Memory Agent 테스트 챗봇

간단한 LLM 질문 답변형 챗봇으로 AI Memory Agent SDK를 테스트할 수 있습니다.

## 기능

- LLM과 대화
- 모든 대화 내용을 AI Memory Agent로 자동 전송
- 대화에서 중요한 메모리 추출 및 전송
- 대화 기록 관리

## 사전 요구사항

1. **AI Memory Agent 서버 실행**
   ```bash
   # 프로젝트 루트 디렉토리에서
   python -m uvicorn src.main:app --reload --port 8000
   ```

2. **Agent Instance 생성**
   - 웹 UI 접속: http://localhost:3000 (프론트엔드)
   - 백엔드 API: http://localhost:8000
   - 사이드바 → Agent → Marketplace
   - Agent Type 선택 → Instance 생성
   - API Key 복사
   - Instance ID 복사 (agent_id로 사용)

3. **LLM Provider 설정**
   - `.env` 파일에 LLM API Key 설정
   - 예: `OPENAI_API_KEY=sk-...`

## 사용 방법

### 1. API Key 설정

```bash
# 환경 변수로 설정
export AI_MEMORY_AGENT_API_KEY='sk_your_api_key_here'

# 또는 한 줄로 실행
AI_MEMORY_AGENT_API_KEY='sk_your_api_key_here' python tests/chatbot/test_chatbot.py
```

### 2. 챗봇 실행

```bash
# 기본 실행 (OpenAI 사용)
python tests/chatbot/test_chatbot.py

# 다른 LLM Provider 사용
LLM_PROVIDER=anthropic python tests/chatbot/test_chatbot.py
LLM_PROVIDER=ollama python tests/chatbot/test_chatbot.py
```

### 3. 대화 시작

```
============================================================
🤖 AI Memory Agent 테스트 챗봇
============================================================

명령어:
  /exit  - 챗봇 종료
  /clear - 대화 기록 초기화
  /memory - 대화에서 메모리 추출
  /help  - 도움말
============================================================

🔍 AI Memory Agent 서버 연결 확인 중...
✅ 서버 연결 성공

💬 대화를 시작합니다. 메시지를 입력하세요.

👤 You: 안녕하세요!

📤 사용자 메시지를 메모리로 전송 중...
✅ 메모리 전송 성공: abc123

🤖 LLM 응답 생성 중...

📤 어시스턴트 응답을 메모리로 전송 중...
✅ 메모리 전송 성공: def456

🤖 Assistant: 안녕하세요! 무엇을 도와드릴까요?
```

## 명령어

| 명령어 | 설명 |
|--------|------|
| `/exit` | 챗봇 종료 |
| `/clear` | 대화 기록 초기화 |
| `/memory` | 대화에서 중요한 메모리 추출 |
| `/help` | 도움말 표시 |

## 메모리 추출 예시

```
👤 You: 제 이름은 김철수이고, 파이썬 프로그래밍을 좋아해요

📤 사용자 메시지를 메모리로 전송 중...
✅ 메모리 전송 성공: abc123

🤖 LLM 응답 생성 중...

📤 어시스턴트 응답을 메모리로 전송 중...
✅ 메모리 전송 성공: def456

🤖 Assistant: 안녕하세요 김철수님! 파이썬 프로그래밍을 좋아하시는군요. 어떤 프로젝트를 진행하고 계신가요?

👤 You: /memory

🧠 대화에서 메모리 추출 중...

📤 추출된 메모리를 전송 중...
✅ 메모리 전송 성공: ghi789

📝 추출된 메모리:
사용자 이름은 김철수이며, 파이썬 프로그래밍에 관심이 있습니다.
```

## 데이터 전송

챗봇은 다음 데이터를 AI Memory Agent로 자동 전송합니다:

1. **사용자 메시지**: `data_type="message"`
2. **어시스턴트 응답**: `data_type="message"`
3. **추출된 메모리**: `data_type="memory"`

모든 데이터는 `source="test_chatbot"` 메타데이터와 함께 전송됩니다.

## 전송된 데이터 확인

전송된 데이터는 웹 UI에서 확인할 수 있습니다:

1. 웹 UI 접속: http://localhost:3030
2. 사이드바 → 지식 센터 → 대화방
3. 전송된 메모리 확인

## 오류 처리

| 오류 | 원인 | 해결 방법 |
|------|------|-----------|
| 인증 오류 | API Key가 유효하지 않음 | 올바른 API Key 확인 |
| 연결 오류 | 서버에 연결 실패 | 서버 실행 상태 확인 |
| API 오류 | API 요청 실패 | 서버 로그 확인 |

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `AI_MEMORY_AGENT_API_KEY` | Agent Instance API Key | 필수 |
| `AGENT_ID` | Agent Instance ID | `test` |
| `LLM_PROVIDER` | LLM 제공자 | `openai` |
| `OPENAI_API_KEY` | OpenAI API Key | 필수 (OpenAI 사용 시) |
| `ANTHROPIC_API_KEY` | Anthropic API Key | 필수 (Anthropic 사용 시) |

## 예제 시나리오

### 시나리오 1: 사용자 정보 수집

```
👤 You: 저는 서울에 살고 있고, AI 개발에 관심이 있어요
👤 You: 최근에 머신러닝 프로젝트를 완료했어요
👤 You: /memory
```

결과: 사용자의 거주지, 관심사, 최근 활동이 메모리로 추출됨

### 시나리오 2: 선호도 파악

```
👤 You: 저는 커피를 좋아해요. 특히 아메리카노를 선호해요
👤 You: 아침에는 항상 커피를 마셔요
👤 You: /memory
```

결과: 커피 선호도, 좋아하는 종류, 습관이 메모리로 추출됨

## 팁

1. **대화 기록 초기화**: `/clear` 명령어로 대화 맥락을 초기화
2. **메모리 추출 타이밍**: 중요한 정보를 나눈 후 `/memory` 명령어 실행
3. **서버 상태 확인**: 챗봇 시작 시 자동으로 서버 연결 확인

## 문제 해결

### SDK 임포트 오류

```bash
# SDK 설치
pip install -e ai_memory_agent_sdk
```

### LLM Provider 오류

```bash
# .env 파일에 API Key 설정
echo "OPENAI_API_KEY=sk-..." >> .env
```

### 서버 연결 실패

```bash
# 서버 실행 확인
curl http://localhost:8000/health
```

## 추가 기능

챗봇을 확장하여 다음 기능을 추가할 수 있습니다:

- 대화 내용을 파일로 저장
- 여러 사용자 지원
- 웹훅 통합
- 로그 레벨 설정

## External Chatbot Test (`external_chatbot_test.py`)

`external_chatbot_test.py`는 Agent 클래스를 사용하여 LLM 호출, 메시지 저장, 메모리 검색/추출을 모두 처리하는 고급 챗봇입니다.

### 기능

- **LLM과 대화**: OpenAI, Anthropic, Ollama 등 다양한 LLM 제공자 지원
- **자동 메모리 저장**: 모든 대화 내용을 자동으로 메모리로 저장
- **메모리 검색**: 저장된 메모리에서 관련 정보 검색
- **메모리 추출**: 대화에서 중요한 정보를 추출하여 저장
- **메모리 소스 설정**: 대화 시 자동으로 검색할 메모리 소스 설정
- **데이터 조회**: 에이전트에 저장된 데이터 조회

### 사용 방법

```bash
# 기본 실행
python tests/chatbot/external_chatbot_test.py

# 다른 LLM Provider 사용
LLM_PROVIDER=anthropic python tests/chatbot/external_chatbot_test.py
LLM_PROVIDER=ollama python tests/chatbot/external_chatbot_test.py
```

### 명령어

| 명령어 | 설명 |
|--------|------|
| `/exit` | 챗봇 종료 |
| `/clear` | 대화 기록 초기화 |
| `/memory` | 대화에서 메모리 추출/저장 |
| `/sources` | 접근 가능한 메모리 소스 목록 |
| `/search <검색어>` | 메모리 검색 |
| `/data` | 에이전트 저장 데이터 조회 |
| `/setup` | 메모리 소스 설정 (대화 시 자동 검색) |
| `/help` | 도움말 표시 |

### 메모리 소스 설정

`/setup` 명령어를 사용하여 대화 시 자동으로 검색할 메모리 소스를 설정할 수 있습니다:

```
/setup
  개인 메모리 포함? (y/N): y
  채팅방 (3개):
    1. 프로젝트 A
    2. 팀 회의
    3. 개인 노트
  포함할 번호 (콤마 구분, 없으면 Enter): 1,2
  설정 완료: 개인, 채팅방(2)
```

### 메모리 검색 예시

```
👤 You: /search 파이썬

검색 결과: 5건
  [0.892] (personal) 사용자는 파이썬 프로그래밍을 좋아합니다
  [0.845] (chatroom) 프로젝트 A에서 파이썬을 사용했습니다
  [0.789] (personal) 파이썬으로 머신러닝 모델을 개발했습니다
  [0.723] (chatroom) 팀 회의에서 파이썬 라이브러리를 논의했습니다
  [0.678] (personal) 파이썬 3.9+를 사용하고 있습니다
```

### 데이터 조회 예시

```
👤 You: /data

에이전트 데이터 (150건 중 최근 20건)
  [message] 안녕하세요, 오늘 날씨가 좋네요
  [message] 네, 산책하기 딱 좋은 날씨입니다
  [memory] 사용자는 산책을 좋아합니다
  [message] 프로젝트 진행 상황은 어떤가요?
  [message] 잘 진행되고 있습니다
  ...
```

### 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `AI_MEMORY_AGENT_API_KEY` | Agent Instance API Key | 필수 |
| `AGENT_ID` | Agent Instance ID | `test` |
| `AI_MEMORY_AGENT_URL` | AI Memory Agent 서버 URL | `http://localhost:8000` |
| `LLM_PROVIDER` | LLM 제공자 | `openai` |
| `LLM_URL` | LLM 서버 URL (Ollama 등) | - |
| `LLM_API_KEY` | LLM API Key | - |
| `LLM_MODEL` | LLM 모델 이름 | - |

### 차이점

| 기능 | `test_chatbot.py` | `external_chatbot_test.py` |
|------|-------------------|---------------------------|
| LLM 호출 | 직접 구현 | Agent 클래스 사용 |
| 메모리 저장 | 수동 (`/memory` 명령어) | 자동 |
| 메모리 검색 | 지원 안 함 | 지원 (`/search` 명령어) |
| 메모리 소스 설정 | 지원 안 함 | 지원 (`/setup` 명령어) |
| 데이터 조회 | 지원 안 함 | 지원 (`/data` 명령어) |
| Agent 클래스 | 사용 안 함 | 사용 |

### 대화 예시

```
External LLM Chatbot + AI Memory Agent

명령어: /exit /clear /memory /sources /search /data /setup /help

서버 연결 성공

You: 안녕하세요!

Assistant: 안녕하세요! 무엇을 도와드릴까요?

You: 제 이름은 김철수이고, 파이썬 프로그래밍을 좋아해요

Assistant: 안녕하세요 김철수님! 파이썬 프로그래밍에 관심이 있으시군요. 어떤 프로젝트를 진행하고 계신가요?

You: /memory

추출된 메모리:
사용자 이름은 김철수이며, 파이썬 프로그래밍에 관심이 있습니다.

You: /search 파이썬

검색 결과: 2건
  [0.892] (personal) 사용자는 파이썬 프로그래밍을 좋아합니다
  [0.845] (personal) 파이썬으로 머신러닝 모델을 개발했습니다

Assistant: 파이썬 프로그래밍과 머신러닝에 관심이 있으시군요! 어떤 도움이 필요하신가요?
```

### 예제 시나리오

#### 시나리오 1: 메모리 검색 활용

```
👤 You: /search 커피

검색 결과: 3건
  [0.912] (personal) 사용자는 커피를 좋아합니다
  [0.856] (personal) 아메리카노를 선호합니다
  [0.789] (personal) 아침에는 항상 커피를 마십니다

👤 You: 커피 좋아하시는군요! 아메리카노를 드시나요?

Assistant: 네, 맞습니다! 특히 아메리카노를 좋아해요. 아침에는 항상 커피 한 잔으로 하루를 시작합니다.
```

#### 시나리오 2: 메모리 소스 설정 활용

```
👤 You: /setup
  개인 메모리 포함? (y/N): y
  채팅방 (2개):
    1. 프로젝트 A
    2. 팀 회의
  포함할 번호 (콤마 구분, 없으면 Enter): 1
  설정 완료: 개인, 채팅방(1)

👤 You: 프로젝트 A에서 어떤 기술을 사용했나요?

Assistant: (개인 및 프로젝트 A의 메모리에서 검색하여 답변)
```

## 라이선스

MIT License
