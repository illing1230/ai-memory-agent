"""Memory API Router"""

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from src.shared.database import get_db
from src.shared.exceptions import NotFoundException, PermissionDeniedException
from src.shared.auth import get_current_user_id
from src.memory.service import MemoryService
from src.memory.schemas import (
    MemoryCreate,
    MemoryUpdate,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    MemoryListResult,
    MemoryExtractRequest,
)

router = APIRouter()


def get_memory_service(db: aiosqlite.Connection = Depends(get_db)) -> MemoryService:
    return MemoryService(db)


@router.post("", response_model=MemoryResponse)
async def create_memory(
    data: MemoryCreate,
    user_id: str = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    """메모리 생성"""
    return await service.create_memory(
        content=data.content,
        owner_id=user_id,
        scope=data.scope,
        project_id=data.project_id,
        department_id=data.department_id,
        chat_room_id=data.chat_room_id,
        source_message_id=data.source_message_id,
        category=data.category,
        importance=data.importance,
        metadata=data.metadata,
    )


@router.get("", response_model=list[MemoryListResult])
async def list_memories(
    scope: str | None = None,
    project_id: str | None = None,
    department_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    """메모리 목록 조회 (권한 기반 필터링)"""
    try:
        results = await service.list_memories(
            user_id=user_id,
            scope=scope,
            project_id=project_id,
            department_id=department_id,
            limit=limit,
            offset=offset,
        )
        return [
            MemoryListResult(
                memory=r["memory"],
                source_info=r.get("source_info")
            )
            for r in results
        ]
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    """메모리 상세 조회"""
    try:
        return await service.get_memory(memory_id, user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    data: MemoryUpdate,
    user_id: str = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    """메모리 수정"""
    try:
        return await service.update_memory(
            memory_id=memory_id,
            user_id=user_id,
            content=data.content,
            category=data.category,
            importance=data.importance,
            metadata=data.metadata,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    """메모리 삭제"""
    try:
        await service.delete_memory(memory_id, user_id)
        return {"message": "메모리가 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    data: MemorySearchRequest,
    user_id: str = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    """메모리 시맨틱 검색"""
    results = await service.search_memories(
        query=data.query,
        user_id=user_id,
        limit=data.limit,
        score_threshold=data.score_threshold,
        scope=data.scope,
        project_id=data.project_id,
        department_id=data.department_id,
    )

    return MemorySearchResponse(
        results=[
            MemorySearchResult(
                memory=r["memory"],
                score=r["score"],
                source_info=r.get("source_info")
            )
            for r in results
        ],
        total=len(results),
        query=data.query,
    )


@router.post("/extract", response_model=list[MemoryResponse])
async def extract_memories(
    data: MemoryExtractRequest,
    user_id: str = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    """대화에서 메모리 자동 추출"""
    return await service.extract_memories(
        conversation=data.conversation,
        owner_id=user_id,
        scope=data.scope,
        project_id=data.project_id,
        department_id=data.department_id,
        chat_room_id=data.chat_room_id,
    )
