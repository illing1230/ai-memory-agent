"""AI Memory Agent SDK - Agent (고수준 LLM 통합 클래스)"""

from typing import Any

import httpx

from ai_memory_agent_sdk.sync_client import AIMemoryAgentSyncClient


# LLM 호출에 사용할 시스템 프롬프트
SYSTEM_PROMPT = """You are a helpful AI assistant. Use the provided context from memory to give informed responses.
If memory context is provided, reference it naturally in your answers.
Always respond in the same language as the user's message."""

MEMORY_EXTRACTION_PROMPT = """다음 대화에서 나중에 기억해야 할 중요한 정보를 추출하세요.
사실(fact), 선호(preference), 결정(decision) 등을 간결한 문장으로 각각 추출하세요.
추출할 메모리가 없으면 빈 문자열을 반환하세요.
메모리만 반환하고 다른 설명은 하지 마세요.

대화:
{conversation}"""


class Agent:
    """LLM 통합 고수준 에이전트

    AI Memory Agent 서버와 통신하면서 LLM을 직접 호출하여
    메모리 기반 대화를 수행하는 올인원 클래스.

    지원 LLM 포맷: OpenAI compatible, Anthropic, Ollama
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        agent_id: str = "",
        llm_provider: str = "openai",
        llm_url: str | None = None,
        llm_api_key: str | None = None,
        model: str | None = None,
    ):
        self._client = AIMemoryAgentSyncClient(
            api_key=api_key,
            base_url=base_url,
            agent_id=agent_id,
        )
        self._llm_provider = llm_provider.lower()
        self._llm_url = llm_url
        self._llm_api_key = llm_api_key
        self._model = model
        self._conversation: list[dict[str, str]] = []
        self.context_sources: dict = {
            "include_agent": False,
            "include_document": False,
            "chat_rooms": [],
        }

        # LLM 기본값 설정
        if self._llm_provider == "openai":
            self._llm_url = self._llm_url or "https://api.openai.com/v1"
            self._model = self._model or "gpt-4o-mini"
        elif self._llm_provider == "anthropic":
            self._llm_url = self._llm_url or "https://api.anthropic.com"
            self._model = self._model or "claude-sonnet-4-20250514"
        elif self._llm_provider == "ollama":
            self._llm_url = self._llm_url or "http://localhost:11434"
            self._model = self._model or "llama3.1"

    def message(self, user_input: str) -> str:
        """사용자 메시지 처리: 메모리 검색 -> LLM 호출 -> 응답 + 서버 저장"""
        # 1. 메모리 검색
        memory_context = ""
        if any([
            self.context_sources.get("include_agent"),
            self.context_sources.get("include_document"),
            self.context_sources.get("chat_rooms"),
        ]):
            try:
                result = self._client.search_memories(
                    query=user_input,
                    context_sources=self.context_sources,
                    limit=5,
                )
                if result.get("results"):
                    memories = [
                        f"- {r['content']}" for r in result["results"]
                    ]
                    memory_context = "\n\n[관련 메모리]\n" + "\n".join(memories)
            except Exception:
                pass

        # 2. 대화 히스토리에 사용자 메시지 추가
        self._conversation.append({"role": "user", "content": user_input})

        # 3. LLM 호출
        system_msg = SYSTEM_PROMPT
        if memory_context:
            system_msg += memory_context

        response_text = self._call_llm(system_msg, self._conversation)

        # 4. 대화 히스토리에 어시스턴트 응답 추가
        self._conversation.append({"role": "assistant", "content": response_text})

        # 5. 서버에 메시지 저장
        try:
            self._client.send_message(
                content=f"User: {user_input}\nAssistant: {response_text}",
            )
        except Exception:
            pass

        return response_text

    def memory(self) -> str | None:
        """현재 대화에서 메모리 추출 후 서버에 저장"""
        if len(self._conversation) < 2:
            return None

        # 대화 텍스트 생성
        conv_text = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in self._conversation[-10:]
        )

        # LLM으로 메모리 추출
        prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conv_text)
        messages = [{"role": "user", "content": prompt}]
        extracted = self._call_llm("You are a memory extraction assistant.", messages)

        if not extracted or not extracted.strip():
            return None

        # 서버에 메모리 저장
        try:
            self._client.send_memory(content=extracted.strip())
        except Exception:
            pass

        return extracted.strip()

    def search(self, query: str) -> dict[str, Any]:
        """서버 메모리 검색"""
        return self._client.search_memories(
            query=query,
            context_sources=self.context_sources,
            limit=10,
        )

    def sources(self) -> dict[str, Any]:
        """메모리 소스 조회"""
        return self._client.get_memory_sources()

    def data(self, limit: int = 20) -> dict[str, Any]:
        """에이전트 데이터 조회"""
        return self._client.get_agent_data(limit=limit)

    def clear(self):
        """대화 히스토리 초기화"""
        self._conversation = []

    def health(self) -> bool:
        """서버 헬스 체크"""
        try:
            result = self._client.health_check()
            return result.get("status") == "healthy"
        except Exception:
            return False

    def _call_llm(self, system_msg: str, messages: list[dict[str, str]]) -> str:
        """LLM 직접 호출 (httpx)"""
        if self._llm_provider == "openai":
            return self._call_openai(system_msg, messages)
        elif self._llm_provider == "anthropic":
            return self._call_anthropic(system_msg, messages)
        elif self._llm_provider == "ollama":
            return self._call_ollama(system_msg, messages)
        else:
            raise ValueError(f"지원하지 않는 LLM 프로바이더: {self._llm_provider}")

    def _call_openai(self, system_msg: str, messages: list[dict[str, str]]) -> str:
        """OpenAI 호환 API 호출"""
        url = f"{self._llm_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self._llm_api_key:
            headers["Authorization"] = f"Bearer {self._llm_api_key}"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_msg},
                *messages,
            ],
            "temperature": 0.7,
        }

        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, system_msg: str, messages: list[dict[str, str]]) -> str:
        """Anthropic API 호출"""
        url = f"{self._llm_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._llm_api_key or "",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self._model,
            "system": system_msg,
            "messages": messages,
            "max_tokens": 4096,
        }

        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    def _call_ollama(self, system_msg: str, messages: list[dict[str, str]]) -> str:
        """Ollama API 호출"""
        url = f"{self._llm_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_msg},
                *messages,
            ],
            "stream": False,
        }

        response = httpx.post(url, json=payload, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
