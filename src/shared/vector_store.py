"""Qdrant 벡터 저장소 관리"""

from typing import Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.config import get_settings

# 전역 Qdrant 클라이언트
_qdrant_client: AsyncQdrantClient | None = None
_qdrant_available: bool = False


def is_vector_store_available() -> bool:
    """Qdrant 사용 가능 여부 반환"""
    return _qdrant_available


async def init_vector_store() -> None:
    """Qdrant 벡터 저장소 초기화 (연결 실패해도 서버는 계속 실행)"""
    global _qdrant_client, _qdrant_available

    settings = get_settings()

    try:
        # 내부망 직접 접속: 프록시 완전 비활성화
        import httpx
        transport = httpx.AsyncHTTPTransport(retries=2)
        http_client = httpx.AsyncClient(
            timeout=30.0,
            verify=False,
            mounts={"all://": transport},
        )
        
        _qdrant_client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
            timeout=30,
            https=False,  # 내부망 HTTP 사용
        )

        # Collection 존재 확인 및 생성
        try:
            await _qdrant_client.get_collection(settings.qdrant_collection)
            print(f"✅ Qdrant Collection 확인됨: {settings.qdrant_collection}")

            # 기존 Collection에 chat_room_id 인덱스 추가 시도
            try:
                await _qdrant_client.create_payload_index(
                    collection_name=settings.qdrant_collection,
                    field_name="chat_room_id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                print(f"✅ chat_room_id 인덱스 추가됨")
            except Exception:
                pass  # 이미 존재하면 무시

        except UnexpectedResponse:
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
            await _qdrant_client.create_payload_index(
                collection_name=settings.qdrant_collection,
                field_name="chat_room_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            print(f"✅ Qdrant Collection 생성됨: {settings.qdrant_collection} (dimension: {settings.embedding_dimension})")

        _qdrant_available = True

    except Exception as e:
        print(f"⚠️  Qdrant 연결 실패 (벡터 검색 기능 비활성화): {e}")
        _qdrant_client = None
        _qdrant_available = False


async def close_vector_store() -> None:
    """Qdrant 연결 종료"""
    global _qdrant_client

    if _qdrant_client:
        await _qdrant_client.close()
        _qdrant_client = None
        print("✅ Qdrant 연결 종료")


def get_vector_store() -> AsyncQdrantClient | None:
    """Qdrant 클라이언트 반환 (연결 안됐으면 None)"""
    return _qdrant_client


async def upsert_vector(
    vector_id: str,
    vector: list[float],
    payload: dict[str, Any],
) -> None:
    """벡터 저장/업데이트"""
    client = get_vector_store()
    if client is None:
        print("⚠️  Qdrant 미연결: 벡터 저장 건너뜀")
        return

    settings = get_settings()
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
    client = get_vector_store()
    if client is None:
        print("⚠️  Qdrant 미연결: 벡터 검색 불가")
        return []

    settings = get_settings()

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

    # query_points 사용 (최신 qdrant-client API)
    results = await client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=query_filter,
    )

    return [
        {
            "id": str(point.id),
            "score": point.score,
            "payload": point.payload,
        }
        for point in results.points
    ]


async def delete_vector(vector_id: str) -> None:
    """벡터 삭제"""
    client = get_vector_store()
    if client is None:
        print("⚠️  Qdrant 미연결: 벡터 삭제 건너뜀")
        return

    settings = get_settings()
    await client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.PointIdsList(points=[vector_id]),
    )


async def get_vector(vector_id: str) -> dict[str, Any] | None:
    """벡터 조회"""
    client = get_vector_store()
    if client is None:
        print("⚠️  Qdrant 미연결: 벡터 조회 불가")
        return None

    settings = get_settings()
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
