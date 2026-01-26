"""OpenAI LLM Provider (OpenAI 호환 API 포함 - Qwen3 등)"""

import json
import re
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

응답 형식 (JSON만 출력, 다른 텍스트 없이):
[
  {
    "content": "추출된 메모리 내용",
    "category": "preference|fact|decision|relationship",
    "importance": "high|medium|low"
  }
]

추출할 메모리가 없으면 빈 배열 []만 반환하세요.
반드시 유효한 JSON 배열만 출력하세요.

대화:
{conversation}"""


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI 호환 LLM Provider (Qwen3-32B 등 지원)"""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """텍스트 생성"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if self.api_key.startswith("Bearer "):
                headers["Authorization"] = self.api_key
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            # SSL 검증 비활성화 (내부망 대응)
            async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            raise ProviderException("OpenAI LLM", f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            raise ProviderException("OpenAI LLM", str(e))

    async def extract_memories(
        self,
        conversation: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출"""
        # 대화 포맷팅
        conv_text = "\n".join(
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation
        )

        prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conv_text)

        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt="당신은 대화에서 중요한 정보를 추출하는 AI입니다. 반드시 유효한 JSON 배열만 응답하세요. 다른 텍스트는 포함하지 마세요.",
                temperature=0.3,
                max_tokens=2000,
            )
        except Exception as e:
            # LLM 호출 실패 시 빈 리스트 반환
            print(f"메모리 추출 LLM 호출 실패: {e}")
            return []

        # JSON 파싱
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> list[dict[str, Any]]:
        """LLM 응답에서 JSON 파싱"""
        if not response:
            return []
        
        response = response.strip()
        
        # 코드 블록 제거
        if "```" in response:
            # ```json ... ``` 또는 ``` ... ``` 형식 처리
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
            if match:
                response = match.group(1).strip()
        
        # JSON 배열 찾기
        # [ 로 시작하고 ] 로 끝나는 부분 추출
        match = re.search(r"\[[\s\S]*\]", response)
        if match:
            response = match.group(0)
        
        try:
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
                return valid_memories
            return []
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}, 응답: {response[:200]}")
            return []
