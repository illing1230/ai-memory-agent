# AI Memory Agent SDK

외부 Agent에서 AI Memory Agent 시스템으로 데이터를 전송하기 위한 Python SDK

## 설치

### uv로 설치 (권장)

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 방법 1: pyproject.toml로 개발 (ai-memory-agent 내부)
cd ai-memory-agent/ai_memory_agent_sdk
uv sync  # 기본 의존성
uv sync --extra agent  # Agent 의존성 포함

# 방법 2: PyPI에서 설치
uv pip install ai-memory-agent-sdk

# 방법 3: 개발 버전 설치
uv pip install git+https://github.sec.samsung.net/work/ai-memory-agent-sdk.git
```

### pip로 설치

```bash
pip install ai-memory-agent-sdk
```

또는 개발 버전 설치:

```bash
pip install git+https://github.sec.samsung.net/work/ai-memory-agent-sdk.git
```

## 빠른 시작

### 동기 클라이언트 사용

```python
from ai_memory_agent_sdk import AIMemoryAgentSyncClient

# 클라이언트 초기화
client = AIMemoryAgentSyncClient(
    api_key="sk_your_api_key_here",
    base_url="http://localhost:8000",
)

# 메모리 전송
result = client.send_memory(
    content="사용자가 프로젝트 A에 관심을 보였습니다",
    metadata={
        "category": "interest",
        "importance": "high",
    }
)
print(f"전송 완료: {result}")

# 클라이언트 종료
client.close()
```

### 비동기 클라이언트 사용

```python
import asyncio
from ai_memory_agent_sdk import AIMemoryAgentClient

async def main():
    # 클라이언트 초기화
    async with AIMemoryAgentClient(
        api_key="sk_your_api_key_here",
        base_url="http://localhost:8000",
    ) as client:
        # 메모리 전송
        result = await client.send_memory(
            content="사용자가 프로젝트 A에 관심을 보였습니다",
            metadata={
                "category": "interest",
                "importance": "high",
            }
        )
        print(f"전송 완료: {result}")

asyncio.run(main())
```

## 기능

### 데이터 타입

SDK는 세 가지 데이터 타입을 지원합니다:

1. **Memory**: 사용자의 중요한 정보, 선호도, 관심사 등
2. **Message**: 사용자와의 대화 내용
3. **Log**: 시스템 로그, 이벤트 등

### 메서드

#### send_memory()

메모리 데이터를 전송합니다. 메모리 타입 데이터는 자동으로 시스템의 메모리로 변환되어 저장됩니다.

```python
result = client.send_memory(
    content="사용자가 Python 프로그래밍에 관심이 있습니다",
    external_user_id="user_123",  # 선택사항
    metadata={
        "category": "interest",
        "importance": "high",
    }
)
```

#### send_message()

메시지 데이터를 전송합니다.

```python
result = client.send_message(
    content="안녕하세요, 오늘 날씨가 좋네요",
    external_user_id="user_123",  # 선택사항
    metadata={
        "timestamp": "2024-01-01T12:00:00Z",
    }
)
```

#### send_log()

로그 데이터를 전송합니다.

```python
result = client.send_log(
    content="사용자가 로그인했습니다",
    external_user_id="user_123",  # 선택사항
    metadata={
        "level": "info",
        "action": "login",
    }
)
```

#### health_check()

서버 헬스 체크를 수행합니다.

```python
is_healthy = client.health_check()
print(f"서버 상태: {'정상' if is_healthy else '비정상'}")
```

## 다중 사용자 Agent

외부 시스템에서 다중 사용자를 지원하는 Agent의 경우, `external_user_id`를 사용하여 각 사용자를 식별할 수 있습니다.

```python
# 사용자 A의 데이터 전송
client.send_memory(
    content="사용자 A가 프로젝트에 관심이 있습니다",
    external_user_id="user_a",
)

# 사용자 B의 데이터 전송
client.send_memory(
    content="사용자 B가 다른 주제에 관심이 있습니다",
    external_user_id="user_b",
)
```

**중요**: 외부 사용자 ID를 사용하려면 AI Memory Agent 시스템에서 사용자 매핑이 설정되어 있어야 합니다. 매핑이 없는 경우 Agent Instance 소유자의 ID가 사용됩니다.

## 예외 처리

SDK는 다음과 같은 예외를 발생시킵니다:

- `AuthenticationError`: API Key가 유효하지 않거나 권한이 없는 경우
- `APIError`: API 요청이 실패한 경우
- `ConnectionError`: 서버 연결 실패
- `ValidationError`: 데이터 검증 실패

```python
from ai_memory_agent_sdk import (
    AIMemoryAgentSyncClient,
    AuthenticationError,
    APIError,
    ConnectionError,
    ValidationError,
)

client = AIMemoryAgentSyncClient(api_key="sk_your_api_key")

try:
    result = client.send_memory(content="테스트 메모리")
    print(f"전송 완료: {result}")
except AuthenticationError as e:
    print(f"인증 실패: {e}")
except APIError as e:
    print(f"API 오류: {e} (상태 코드: {e.status_code})")
except ConnectionError as e:
    print(f"연결 오류: {e}")
except ValidationError as e:
    print(f"검증 오류: {e}")
finally:
    client.close()
```

## 설정

### API Key

AI Memory Agent 시스템에서 Agent Instance를 생성하면 API Key가 발급됩니다. 이 API Key를 사용하여 SDK를 초기화합니다.

### Base URL

기본값은 `http://localhost:8000`입니다. 다른 URL을 사용하는 경우:

```python
client = AIMemoryAgentSyncClient(
    api_key="sk_your_api_key",
    base_url="https://your-api-server.com",
)
```

### Timeout

기본 타임아웃은 30초입니다. 변경하려면:

```python
client = AIMemoryAgentSyncClient(
    api_key="sk_your_api_key",
    timeout=60.0,  # 60초
)
```

## 예제

### 완전한 예제

```python
import asyncio
from ai_memory_agent_sdk import AIMemoryAgentClient, AuthenticationError

async def main():
    api_key = "sk_your_api_key_here"
    
    async with AIMemoryAgentClient(api_key=api_key) as client:
        # 헬스 체크
        if not await client.health_check():
            print("서버에 연결할 수 없습니다")
            return
        
        print("서버에 연결되었습니다")
        
        # 여러 데이터 전송
        try:
            # 메모리
            await client.send_memory(
                content="사용자가 AI 기술에 깊은 관심을 가지고 있습니다",
                metadata={
                    "category": "interest",
                    "importance": "high",
                    "tags": ["AI", "기술"],
                }
            )
            
            # 메시지
            await client.send_message(
                content="최근에 어떤 프로젝트를 진행하고 계신가요?",
                external_user_id="user_123",
            )
            
            # 로그
            await client.send_log(
                content="사용자가 대화를 시작했습니다",
                external_user_id="user_123",
                metadata={
                    "level": "info",
                    "action": "conversation_start",
                }
            )
            
            print("모든 데이터가 성공적으로 전송되었습니다")
            
        except AuthenticationError:
            print("API Key가 유효하지 않습니다")
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 지원

문제가 있거나 기능 요청이 있으시면 [Knox email](hy.joo@samsung.com)를 통해 알려주세요.
