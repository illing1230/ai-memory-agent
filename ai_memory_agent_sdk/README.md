# AI Memory Agent SDK

사내 AI 에이전트에 메모리 기능을 추가하기 위한 Python SDK.

## 설치

```bash
cd ai_memory_agent_sdk
pip install -e .
```

## 빠른 시작

### Agent 클래스 (LLM 통합, 권장)

```python
from ai_memory_agent_sdk import Agent

agent = Agent(
    api_key="sk_your_api_key",
    base_url="http://localhost:8000",
    agent_id="my-bot",
    llm_provider="openai",       # openai, anthropic, ollama
    llm_url="https://api.openai.com/v1",
    llm_api_key="your-llm-key",
    model="gpt-4o-mini",
)

# 대화 (메모리 자동 검색 + LLM 호출 + 서버 저장)
response = agent.message("안녕하세요!")

# 메모리 추출
agent.memory()

# 메모리 검색
results = agent.search("프로젝트 일정")
```

### SyncClient (저수준)

```python
from ai_memory_agent_sdk import SyncClient

client = SyncClient(
    api_key="sk_your_api_key",
    base_url="http://localhost:8000",
    agent_id="my-bot",
)

# 메모리 저장
client.send_memory("사용자가 Python을 선호함")

# 메모리 검색
results = client.search_memories("프로그래밍 언어 선호도")

# 메모리 소스 조회
sources = client.get_memory_sources()
```

### AsyncClient (비동기)

```python
from ai_memory_agent_sdk import AsyncClient

async with AsyncClient(
    api_key="sk_your_api_key",
    base_url="http://localhost:8000",
    agent_id="my-bot",
) as client:
    await client.send_memory("중요한 정보")
    results = await client.search_memories("검색어")
```

## API 레퍼런스

### 데이터 전송
- `send_memory(content, metadata?)` - 메모리 저장
- `send_message(content, metadata?)` - 메시지 저장
- `send_log(content, metadata?)` - 로그 저장

### 검색
- `search_memories(query, context_sources?, limit?)` - 메모리 검색
- `get_memory_sources()` - 접근 가능한 메모리 소스 조회

### 조회
- `get_agent_data(data_type?, limit?, offset?)` - 에이전트 데이터 조회
- `health_check()` - 서버 상태 확인
