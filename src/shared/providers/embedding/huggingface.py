"""HuggingFace Embedding Provider (삼성 내부 서버 호환)"""

import httpx

from src.shared.providers.base import BaseEmbeddingProvider
from src.shared.exceptions import ProviderException


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """HuggingFace 호환 Embedding Provider (삼성 내부 서버용)"""

    def __init__(
        self,
        api_key: str | None,
        model_url: str | None,
        dimension: int,
    ):
        self.api_key = api_key
        self.model_url = model_url
        self._dimension = dimension

        if not model_url:
            raise ValueError("HuggingFace Embedding URL이 설정되지 않았습니다")

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

        # HuggingFace TEI 형식
        payload = {"inputs": texts}

        try:
            # 내부망 직접 접속: 프록시 완전 비활성화
            # trust_env=False로 환경변수 프록시 설정 무시
            async with httpx.AsyncClient(
                timeout=60.0,
                verify=False,
                trust_env=False,  # 환경변수 HTTP_PROXY/HTTPS_PROXY 무시
            ) as client:
                response = await client.post(
                    self.model_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # 응답 형식에 따라 파싱
                # 형식 1: [[...], [...]] - 직접 임베딩 리스트
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], list):
                        return data
                    # 형식 2: [{"embedding": [...]}, ...]
                    elif isinstance(data[0], dict) and "embedding" in data[0]:
                        return [item["embedding"] for item in data]

                # 형식 3: {"embeddings": [[...], [...]]}
                if isinstance(data, dict) and "embeddings" in data:
                    return data["embeddings"]

                raise ProviderException("HuggingFace Embedding", f"알 수 없는 응답 형식: {type(data)}")

        except httpx.HTTPStatusError as e:
            raise ProviderException("HuggingFace Embedding", f"HTTP 오류: {e.response.status_code}")
        except ProviderException:
            raise
        except Exception as e:
            raise ProviderException("HuggingFace Embedding", str(e))
