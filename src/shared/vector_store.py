"""Qdrant 벡터 저장소 관리"""

from typing import Any
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.config import get_settings

# 전역 Qdrant 클라이언트
_qdrant_client: AsyncQdrantClient | None = None


async def init_vector_store() -> None:
    """Qdrant 벡터 저장소 초기화"""
    global _qdrant_client

    settings = get_settings()

    # 클라이언트 생성
    _qdrant_client = AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
    )

    # Collection 존재 확인 및 생성
    try:
        await _qdrant_client.get_collection(settings.qdrant_collection)
        print(f"✅ Qdrant Collection 확인됨: {settings.qdrant_collection}")
    except (UnexpectedResponse, Exception):
        # Collection 생성
        await _qdrant_client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=settings.embedding_dimension,
                distance=models.Distance.COSINE,
            ),
        )
        
        # 인덱스 생성 (payload 필드)
        await _qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="memory_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        await _qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="scope",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        await _qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="owner_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        await _qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="project_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        await _qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="department_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        print(f"✅ Qdrant Collection 생성됨: {settings.qdrant_collection} (dimension: {settings.embedding_dimension})")


async def close_vector_store() -> None:
    """Qdrant 연결 종료"""
    global _qdrant_client

    if _qdrant_client:
        await _qdrant_client.close()
        _qdrant_client = None
        print("✅ Qdrant 연결 종료")


def get_vector_store() -> AsyncQdrantClient:
    """Qdrant 클라이언트 반환"""
    if _qdrant_client is None:
        raise RuntimeError("Qdrant가 초기화되지 않았습니다")
    return _qdrant_client


async def upsert_vector(
    vector_id: str,
    vector: list[float],
    payload: dict[str, Any],
) -> None:
    """벡터 저장/업데이트"""
    settings = get_settings()
    client = get_vector_store()

    await client.upsert(
        collection_name=settings.qdrant_collection,
        points=[
            models.PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload,
            )
        ],
    )


async def search_vectors(
    query_vector: list[float],
    limit: int = 10,
    score_threshold: float | None = None,
    filter_conditions: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """벡터 검색"""
    settings = get_settings()
    client = get_vector_store()

    # 필터 조건 구성
    query_filter = None
    if filter_conditions:
        must_conditions = []
        for key, value in filter_conditions.items():
            if value is not None:
                if isinstance(value, list):
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value),
                        )
                    )
                else:
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        )
                    )
        if must_conditions:
            query_filter = models.Filter(must=must_conditions)

    results = await client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=query_filter,
    )

    return [
        {
            "id": str(result.id),
            "score": result.score,
            "payload": result.payload,
        }
        for result in results
    ]


async def delete_vector(vector_id: str) -> None:
    """벡터 삭제"""
    settings = get_settings()
    client = get_vector_store()

    await client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.PointIdsList(points=[vector_id]),
    )


async def get_vector(vector_id: str) -> dict[str, Any] | None:
    """벡터 조회"""
    settings = get_settings()
    client = get_vector_store()

    results = await client.retrieve(
        collection_name=settings.qdrant_collection,
        ids=[vector_id],
        with_vectors=True,
    )

    if results:
        point = results[0]
        return {
            "id": str(point.id),
            "vector": point.vector,
            "payload": point.payload,
        }
    return None
