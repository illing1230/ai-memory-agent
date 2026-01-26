"""Provider 추상 베이스 클래스"""

from abc import ABC, abstractmethod
from typing import Any


class BaseEmbeddingProvider(ABC):
    """Embedding Provider 추상 클래스"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """단일 텍스트 임베딩"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """배치 텍스트 임베딩"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """벡터 차원 반환"""
        pass


class BaseLLMProvider(ABC):
    """LLM Provider 추상 클래스"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """텍스트 생성"""
        pass

    @abstractmethod
    async def extract_memories(
        self,
        conversation: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """대화에서 메모리 추출"""
        pass
