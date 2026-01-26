"""Anthropic LLM Provider"""

import json
from typing import Any

import httpx

from src.shared.providers.base import BaseLLMProvider
from src.shared.exceptions import ProviderException


MEMORY_EXTRACTION_PROMPT = """다음 대화에서 장기적으로 기억할 가치가 있는 정보를 추출하세요.

추출 기준:
- 사용자의 선호도, 습관, 특성
- 중요한 사실이나 결정 사항
- 프로젝트/업무 관련 정보
- 관계 정보 (사람, 조직 등)

응답 형식 (JSON만 출력):
[
  {
    "content": "추출된 메모리 내용",
    "category": "preference|fact|decision|relationship",
    "importance": "high|medium|low"
  }
]

추출할 메모리가 없으면 빈 배열 []을 반환하세요.

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
            temperature=0.3,
            max_tokens=2000,
        )

        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            memories = json.loads(response)
            if isinstance(memories, list):
                return memories
            return []
        except json.JSONDecodeError:
            return []
