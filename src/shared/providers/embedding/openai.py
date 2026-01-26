"""OpenAI Embedding Provider"""

import httpx

from src.shared.providers.base import BaseEmbeddingProvider
from src.shared.exceptions import ProviderException


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI 호환 Embedding Provider"""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str,
        dimension: int,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """단일 텍스트 임베딩"""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """배치 텍스트 임베딩"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            # Bearer 토큰 형식 처리
            if self.api_key.startswith("Bearer "):
                headers["Authorization"] = self.api_key
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # OpenAI 형식 응답 파싱
                embeddings = [item["embedding"] for item in data["data"]]
                return embeddings

        except httpx.HTTPStatusError as e:
            raise ProviderException("OpenAI Embedding", f"HTTP 오류: {e.response.status_code}")
        except Exception as e:
            raise ProviderException("OpenAI Embedding", str(e))
