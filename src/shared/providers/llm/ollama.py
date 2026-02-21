"""Ollama LLM Provider"""

import json
from typing import Any, AsyncGenerator

import httpx

from src.shared.providers.base import BaseLLMProvider
from src.shared.exceptions import ProviderException


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

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """스트리밍 텍스트 생성"""
        full_prompt = ""
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break

        except httpx.HTTPStatusError as e:
            raise ProviderException("Ollama LLM", f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            raise ProviderException("Ollama LLM", str(e))

    async def extract_memories(
        self,
        conversation: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출 (프롬프트는 memory/pipeline.py에서 관리)"""
        from src.memory.pipeline import MEMORY_EXTRACTION_PROMPT

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
