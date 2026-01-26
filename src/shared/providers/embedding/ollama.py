"""Ollama Embedding Provider"""

import httpx

from src.shared.providers.base import BaseEmbeddingProvider
from src.shared.exceptions import ProviderException


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Ollama Embedding Provider (로컬용)"""

    def __init__(
        self,
        base_url: str,
        model: str,
        dimension: int,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """단일 텍스트 임베딩"""
        payload = {
            "model": self.model,
            "prompt": text,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["embedding"]

        except httpx.HTTPStatusError as e:
            raise ProviderException("Ollama Embedding", f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            raise ProviderException("Ollama Embedding", str(e))

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """배치 텍스트 임베딩 (Ollama는 개별 호출)"""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings
