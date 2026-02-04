"""AI Memory Agent SDK - 고수준 Agent 클래스

개발자가 최소한의 코드로 LLM + 메모리 연동 챗봇을 만들 수 있는 고수준 API.

사용법:
    # 내부 LLM 서버 (OpenAI 호환)
    agent = Agent(
        api_key="sk_...",
        agent_id="my-agent",
        llm_url="http://10.244.14.73:8080/v1",
        llm_api_key="your-llm-key",
        model="Qwen3-32B",
    )

    # 외부 OpenAI
    agent = Agent(
        api_key="sk_...",
        agent_id="my-agent",
        llm_provider="openai",
        llm_api_key="sk-openai-key",
        model="gpt-4o-mini",
    )

    response = agent.message("안녕하세요!")
    agent.memory()  # 대화에서 메모리 추출/저장
"""

import os
from typing import Any, Callable

from ai_memory_agent_sdk.client import AIMemoryAgentSyncClient
from ai_memory_agent_sdk.exceptions import ConnectionError as SDKConnectionError


def _create_llm_client(
    provider: str,
    llm_url: str | None = None,
    llm_api_key: str | None = None,
) -> Any:
    """LLM 클라이언트 생성

    Args:
        provider: "openai", "anthropic", "ollama"
        llm_url: LLM API URL (직접 지정, 환경변수보다 우선)
        llm_api_key: LLM API Key (직접 지정, 환경변수보다 우선)
    """
    if provider in ("openai", "ollama"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai 패키지가 필요합니다: pip install openai")

        if provider == "ollama":
            url = llm_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            if not url.endswith("/v1"):
                url = f"{url}/v1"
            return OpenAI(api_key=llm_api_key or "ollama", base_url=url)

        # openai
        api_key = llm_api_key or os.getenv("OPENAI_API_KEY")
        base_url = llm_url or os.getenv("OPENAI_API_BASE")
        if not api_key:
            raise ValueError("llm_api_key 또는 OPENAI_API_KEY 환경 변수를 설정해주세요.")

        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs)

    elif provider == "anthropic":
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic 패키지가 필요합니다: pip install anthropic")

        api_key = llm_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("llm_api_key 또는 ANTHROPIC_API_KEY 환경 변수를 설정해주세요.")

        kwargs_anthropic: dict[str, Any] = {"api_key": api_key}
        if llm_url:
            kwargs_anthropic["base_url"] = llm_url
        return Anthropic(**kwargs_anthropic)

    else:
        raise ValueError(f"지원하지 않는 LLM 프로바이더: {provider}")


def _get_default_model(provider: str) -> str:
    """프로바이더별 기본 모델"""
    defaults = {
        "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        "ollama": os.getenv("OLLAMA_MODEL", "qwen3:32b"),
    }
    return defaults.get(provider, "gpt-4o-mini")


def _llm_chat(
    client: Any,
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> str:
    """동기 LLM chat completions 호출"""
    if provider == "anthropic":
        system_msg = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_msg:
            kwargs["system"] = system_msg

        response = client.messages.create(**kwargs)
        return response.content[0].text
    else:
        # OpenAI / Ollama (OpenAI-compatible)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


class Agent:
    """고수준 AI Memory Agent

    LLM 호출, 메시지 저장, 메모리 검색/추출을 모두 내장한 올인원 에이전트.

    Args:
        api_key: AI Memory Agent API Key
        base_url: AI Memory Agent 서버 URL
        agent_id: Agent Instance ID
        llm_provider: LLM 프로바이더 ("openai", "anthropic", "ollama")
        llm_url: LLM API URL (직접 지정, 환경변수보다 우선)
        llm_api_key: LLM API Key (직접 지정, 환경변수보다 우선)
        model: LLM 모델명 (미지정 시 프로바이더 기본값)
        llm_func: 커스텀 LLM 함수 (지정하면 provider 무시)
            시그니처: (messages: list[dict]) -> str
        system_prompt: 시스템 프롬프트
        context_sources: 메모리 검색 소스 설정 (None이면 검색 안 함)

    Examples:
        # 내부 OpenAI 호환 서버
        agent = Agent(
            api_key="sk_...",
            agent_id="my-agent",
            llm_url="http://10.244.14.73:8080/v1",
            llm_api_key="your-key",
            model="Qwen3-32B",
        )

        # 외부 OpenAI
        agent = Agent(
            api_key="sk_...",
            llm_api_key="sk-openai-...",
            model="gpt-4o-mini",
        )

        # 완전 커스텀 LLM
        agent = Agent(
            api_key="sk_...",
            llm_func=lambda messages: my_custom_llm(messages),
        )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        agent_id: str = "test",
        llm_provider: str = "openai",
        llm_url: str | None = None,
        llm_api_key: str | None = None,
        model: str | None = None,
        llm_func: Callable[[list[dict[str, str]]], str] | None = None,
        system_prompt: str = "당신은 친절한 AI 어시스턴트입니다.",
        context_sources: dict[str, Any] | None = None,
    ):
        self._api_client = AIMemoryAgentSyncClient(
            api_key=api_key,
            base_url=base_url,
            agent_id=agent_id,
        )
        self._system_prompt = system_prompt
        self._context_sources = context_sources
        self._history: list[dict[str, str]] = []

        # LLM 설정
        if llm_func:
            # 커스텀 LLM 함수 사용
            self._llm_func = llm_func
            self._llm_provider = "custom"
            self._llm_client = None
            self._model = model or "custom"
        else:
            # 내장 프로바이더 사용
            self._llm_func = None
            self._llm_provider = llm_provider
            self._llm_client = _create_llm_client(
                llm_provider, llm_url=llm_url, llm_api_key=llm_api_key,
            )
            self._model = model or _get_default_model(llm_provider)

    @property
    def history(self) -> list[dict[str, str]]:
        """대화 기록"""
        return list(self._history)

    @property
    def context_sources(self) -> dict[str, Any] | None:
        """현재 메모리 소스 설정"""
        return self._context_sources

    @context_sources.setter
    def context_sources(self, value: dict[str, Any] | None) -> None:
        self._context_sources = value

    def _call_llm(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """LLM 호출 (내장 프로바이더 또는 커스텀 함수)"""
        if self._llm_func:
            return self._llm_func(messages)
        return _llm_chat(
            client=self._llm_client,
            provider=self._llm_provider,
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def message(self, content: str) -> str:
        """메시지 전송 → 메모리 검색 → LLM 응답 → 저장

        Args:
            content: 사용자 메시지

        Returns:
            LLM 응답 텍스트
        """
        # 1. 대화 기록에 추가
        self._history.append({"role": "user", "content": content})

        # 2. 사용자 메시지 저장
        self._safe_send("message", f"[user] {content}")

        # 3. 메모리 검색
        memory_context = self._search_memories(content)

        # 4. LLM 호출
        system = self._system_prompt
        if memory_context:
            system += f"\n\n[관련 메모리]\n{memory_context}"

        messages = [{"role": "system", "content": system}]
        messages.extend(self._history)

        response = self._call_llm(messages)

        # 5. 응답 저장 + 기록
        self._safe_send("message", f"[assistant] {response}")
        self._history.append({"role": "assistant", "content": response})

        return response

    def memory(self) -> str | None:
        """현재 대화에서 메모리 추출 → 저장

        Returns:
            추출된 메모리 텍스트, 대화가 부족하면 None
        """
        if len(self._history) < 2:
            return None

        recent = self._history[-10:]
        conversation_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in recent
        )

        messages = [
            {
                "role": "system",
                "content": "대화에서 사용자의 중요한 정보, 선호도, 관심사를 추출하여 간결하게 요약해주세요.",
            },
            {"role": "user", "content": f"다음 대화를 분석해주세요:\n\n{conversation_text}"},
        ]

        extracted = self._call_llm(messages, temperature=0.3, max_tokens=300).strip()

        self._safe_send("memory", extracted)
        return extracted

    def clear(self) -> None:
        """대화 기록 초기화"""
        self._history.clear()

    def sources(self) -> dict[str, Any]:
        """접근 가능한 메모리 소스 목록 조회"""
        return self._api_client.get_memory_sources()

    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """메모리 검색

        Args:
            query: 검색어
            limit: 최대 결과 수

        Returns:
            검색 결과 dict (results, total, query)
        """
        return self._api_client.search_memories(
            query=query,
            context_sources=self._context_sources,
            limit=limit,
        )

    def data(self, data_type: str | None = None, limit: int = 100) -> dict[str, Any]:
        """에이전트 저장 데이터 조회"""
        return self._api_client.get_data(data_type=data_type, limit=limit)

    def health(self) -> bool:
        """서버 헬스 체크"""
        return self._api_client.health_check()

    def _search_memories(self, query: str) -> str:
        """메모리 검색하여 컨텍스트 문자열 반환 (내부)"""
        if not self._context_sources:
            return ""
        try:
            result = self._api_client.search_memories(
                query=query,
                context_sources=self._context_sources,
                limit=5,
            )
            if not result.get("results"):
                return ""
            return "\n".join(
                f"- [{r['scope']}] {r['content']}" for r in result["results"]
            )
        except (SDKConnectionError, Exception):
            return ""

    def _safe_send(self, data_type: str, content: str) -> None:
        """에러 무시하고 데이터 전송 (내부)"""
        try:
            if data_type == "memory":
                self._api_client.send_memory(content=content)
            elif data_type == "message":
                self._api_client.send_message(content=content)
            else:
                self._api_client.send_log(content=content)
        except Exception:
            pass
