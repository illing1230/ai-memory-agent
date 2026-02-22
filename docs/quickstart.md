# Quickstart: AI Memory Agent SDK

이 가이드는 사내 AI 에이전트에 메모리 기능을 추가하는 방법을 설명합니다.

## 사전 준비

1. AI Memory Agent 서버가 실행 중이어야 합니다
2. Agent Instance를 생성하고 API Key를 발급받아야 합니다

### 서버 실행 (Docker)

```bash
cd ai-memory-agent
docker-compose up -d
```

또는 로컬 실행:

```bash
cd ai-memory-agent
pip install -e .
python -m src.main
```

### Agent Instance 생성

1. `http://localhost:8000/docs`에서 Swagger UI 접속
2. `/api/v1/auth/register`로 계정 생성
3. `/api/v1/auth/login`으로 로그인 (토큰 발급)
4. `/api/v1/agent-types`로 Agent Type 생성
5. `/api/v1/agent-instances`로 Agent Instance 생성 → `api_key` 확인

## SDK 설치

```bash
cd ai_memory_agent_sdk
pip install -e .
```

## 1분 만에 시작하기

### 방법 1: Agent 클래스 (LLM 통합)

가장 쉬운 방법. LLM 호출 + 메모리 저장/검색을 한번에 처리합니다.

```python
from ai_memory_agent_sdk import Agent

agent = Agent(
    api_key="sk_your_api_key_here",
    base_url="http://localhost:8000",
    agent_id="my-bot",
    llm_provider="openai",
    llm_url="https://api.openai.com/v1",
    llm_api_key="sk-...",
    model="gpt-4o-mini",
)

# 서버 연결 확인
if agent.health():
    print("서버 연결 OK")

# 대화 (자동으로 메모리 검색 + LLM 호출 + 서버 저장)
response = agent.message("나는 Python을 가장 좋아해")
print(response)

response = agent.message("내가 좋아하는 언어가 뭐였지?")
print(response)

# 대화에서 메모리 추출 → 서버에 저장
memory = agent.memory()
print(f"추출된 메모리: {memory}")

# 메모리 검색
results = agent.search("프로그래밍 언어")
for r in results["results"]:
    print(f"  [{r['score']:.3f}] {r['content']}")
```

### 방법 2: SyncClient (직접 LLM 호출)

기존 LLM 파이프라인이 있을 때. 메모리 저장/검색만 SDK로 처리합니다.

```python
from ai_memory_agent_sdk import SyncClient

client = SyncClient(
    api_key="sk_your_api_key_here",
    base_url="http://localhost:8000",
    agent_id="my-bot",
)

# 메모리 저장
client.send_memory("사용자 김철수는 Python 개발자이다")
client.send_memory("프로젝트 A의 마감일은 3월 15일")

# 메모리 검색
results = client.search_memories("김철수 정보")
for r in results["results"]:
    print(f"  [{r['score']:.3f}] {r['content']}")

# 메시지/로그 저장
client.send_message("사용자와의 대화 내용...")
client.send_log("에이전트 동작 로그")
```

### 방법 3: AsyncClient (비동기)

FastAPI 등 비동기 환경에서 사용합니다.

```python
from ai_memory_agent_sdk import AsyncClient

async def main():
    async with AsyncClient(
        api_key="sk_your_api_key_here",
        base_url="http://localhost:8000",
        agent_id="my-bot",
    ) as client:
        # 메모리 저장
        await client.send_memory("중요한 정보")

        # 메모리 검색
        results = await client.search_memories(
            query="검색어",
            context_sources={
                "include_agent": True,
                "include_document": True,
            },
        )
```

## 메모리 소스 설정

에이전트가 검색할 때 어떤 소스를 참조할지 설정할 수 있습니다.

```python
# 사용 가능한 소스 확인
sources = agent.sources()
print(sources)  # chat_rooms, agent, document

# 컨텍스트 소스 설정
agent.context_sources = {
    "include_agent": True,      # 에이전트 자체 메모리
    "include_document": True,   # RAG 문서
    "chat_rooms": ["room-id-1", "room-id-2"],  # 특정 채팅방 메모리
}
```

## 환경 변수로 설정

```bash
export AI_MEMORY_AGENT_API_KEY=sk_your_api_key
export AI_MEMORY_AGENT_URL=http://localhost:8000
export AGENT_ID=my-bot
export LLM_PROVIDER=openai
export LLM_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
```

```python
import os
from ai_memory_agent_sdk import Agent

agent = Agent(
    api_key=os.getenv("AI_MEMORY_AGENT_API_KEY"),
    base_url=os.getenv("AI_MEMORY_AGENT_URL", "http://localhost:8000"),
    agent_id=os.getenv("AGENT_ID", "my-bot"),
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_url=os.getenv("LLM_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
    model=os.getenv("LLM_MODEL"),
)
```

## 테스트 챗봇 실행

SDK에 포함된 대화형 테스트 챗봇으로 기능을 체험할 수 있습니다.

```bash
export AI_MEMORY_AGENT_API_KEY=sk_your_api_key
python -m tests.chatbot.external_chatbot_test
```

명령어:
- `/memory` - 대화에서 메모리 추출
- `/search <검색어>` - 메모리 검색
- `/sources` - 접근 가능한 메모리 소스 목록
- `/setup` - 메모리 소스 설정
- `/data` - 에이전트 저장 데이터 조회
- `/clear` - 대화 초기화
- `/exit` - 종료

## 다음 단계

- [SDK API 레퍼런스](../ai_memory_agent_sdk/README.md)
- [서버 API 문서](http://localhost:8000/docs) (Swagger UI)
