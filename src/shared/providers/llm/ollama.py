"""Ollama LLM Provider"""

import json
from typing import Any

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


class OllamaLLMProvider(BaseLLMProvider):
    """Ollama LLM Provider (로컬용)"""

    def __init__(
        self,
        base_url: str,
        model: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """텍스트 생성"""
        full_prompt = ""
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["response"]

        except httpx.HTTPStatusError as e:
            raise ProviderException("Ollama LLM", f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            raise ProviderException("Ollama LLM", str(e))

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
