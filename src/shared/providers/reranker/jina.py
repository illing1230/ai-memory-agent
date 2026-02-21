"""Jina Reranker Provider (로컬 배포)"""

from typing import Any

import httpx

from src.shared.providers.base import BaseRerankerProvider
from src.shared.exceptions import ProviderException


class JinaRerankerProvider(BaseRerankerProvider):
    """Jina Reranker Provider - 로컬 서버 (localhost:7998)"""

    def __init__(self, base_url: str, model: str = "jinaai/jina-reranker-v2-base-multilingual"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """문서 리랭킹"""
        if not documents:
            return []

        if top_n is None:
            top_n = len(documents)

        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": top_n,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/rerank",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    results.append({
                        "index": item["index"],
                        "relevance_score": item["relevance_score"],
                        "document": documents[item["index"]],
                    })

                # relevance_score 내림차순 정렬
                results.sort(key=lambda x: x["relevance_score"], reverse=True)
                return results

        except httpx.HTTPStatusError as e:
            raise ProviderException("Jina Reranker", f"HTTP 오류: {e.response.status_code}")
        except httpx.ConnectError:
            print("⚠️  Reranker 서버 연결 실패 - 리랭킹 건너뜀")
            # 연결 실패 시 원래 순서 유지 (graceful degradation)
            return [
                {"index": i, "relevance_score": 1.0 - (i * 0.01), "document": doc}
                for i, doc in enumerate(documents[:top_n])
            ]
        except Exception as e:
            raise ProviderException("Jina Reranker", str(e))
