"""Anthropic LLM Provider"""

import json
from typing import Any, AsyncGenerator

import httpx

from src.shared.providers.base import BaseLLMProvider
from src.shared.exceptions import ProviderException


MEMORY_EXTRACTION_PROMPT = """다음 대화에서 장기적으로 기억할 가치가 있는 정보를 추출하세요.

중요 규칙:
- 대화에 명시적으로 언급된 정보만 추출하세요.
- 대화에 없는 내용을 추론하거나 가정하지 마세요.
- 불확실한 정보는 추출하지 마세요.

추출 기준:
- 사용자의 선호도, 습관, 특성
- 중요한 사실이나 결정 사항
- 프로젝트/업무 관련 정보
- 관계 정보 (사람, 조직 등)

응답 형식 (반드시 유효한 JSON 배열만 출력):
[
  {
    "content": "추출된 메모리 내용",
    "category": "preference|fact|decision|relationship",
    "importance": "high|medium|low"
  }
]

예시:
[
  {
    "content": "김과장은 오전 회의를 선호한다",
    "category": "preference",
    "importance": "medium"
  },
  {
    "content": "프로젝트 마감일은 3월 15일이다",
    "category": "fact",
    "importance": "high"
  }
]

중요:
- 추출할 메모리가 없으면 빈 배열 []만 반환하세요.
- JSON 배열 외에 다른 텍스트, 설명, 주석은 절대 포함하지 마세요.
- 코드 블록(```json) 없이 JSON 배열만 직접 출력하세요.

대화:
{conversation}"""


class AnthropicLLMProvider(BaseLLMProvider):
    """Anthropic Claude LLM Provider"""

    def __init__(
        self,
        api_key: str | None,
        model: str,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """텍스트 생성"""
        if not self.api_key:
            raise ProviderException("Anthropic LLM", "API 키가 설정되지 않았습니다")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]

        except httpx.HTTPStatusError as e:
            raise ProviderException("Anthropic LLM", f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            raise ProviderException("Anthropic LLM", str(e))

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """텍스트 스트리밍 생성"""
        if not self.api_key:
            raise ProviderException("Anthropic LLM", "API 키가 설정되지 않았습니다")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,  # 스트리밍 활성화
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # "data: " 제거
                            
                            try:
                                data = json.loads(data_str)
                                if data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})
                                    content = delta.get("text", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            raise ProviderException("Anthropic LLM", f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            raise ProviderException("Anthropic LLM", str(e))

    async def extract_memories(
        self,
        conversation: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출"""
        conv_text = "\n".join(
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation
        )

        prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conv_text)

        response = await self.generate(
            prompt=prompt,
            system_prompt="당신은 대화에서 중요한 정보를 추출하는 AI입니다. JSON 형식으로만 응답하세요.",
            temperature=0.1,
            max_tokens=2000,
        )

        try:
            response = response.strip()
            print(f"[JSON 파싱] 원본 응답 (길이: {len(response)}): {response[:300]}...")
            
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            print(f"[JSON 파싱] 코드 블록 제거 후: {response[:200]}...")

            memories = json.loads(response)
            if isinstance(memories, list):
                # 유효한 메모리만 필터링
                valid_memories = []
                for mem in memories:
                    if isinstance(mem, dict) and mem.get("content"):
                        valid_memories.append({
                            "content": str(mem.get("content", "")),
                            "category": str(mem.get("category", "fact")),
                            "importance": str(mem.get("importance", "medium")),
                        })
                print(f"[JSON 파싱] 성공: {len(valid_memories)}개의 메모리 추출")
                return valid_memories
            print(f"[JSON 파싱] 응답이 리스트가 아님: {type(memories)}")
            return []
        except json.JSONDecodeError as e:
            print(f"[JSON 파싱] JSON 파싱 실패: {e}")
            print(f"[JSON 파싱] 파싱 실패한 응답: {response}")
            return []
