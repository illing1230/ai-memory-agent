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
2. 사이드바 → 지식 관리 → 대화방
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

## 라이선스

MIT License
