"""Agent API Router"""
from fastapi import APIRouter, Depends, HTTPException, Header
import aiosqlite

from src.shared.database import get_db
from src.shared.exceptions import NotFoundException, PermissionDeniedException
from src.shared.auth import get_current_user_id
from src.agent.service import AgentService
from src.agent.schemas import (
    AgentTypeCreate,
    AgentTypeUpdate,
    AgentTypeResponse,
    AgentInstanceCreate,
    AgentInstanceUpdate,
    AgentInstanceResponse,
    AgentDataCreate,
    AgentDataResponse,
    AgentDataListResponse,
    AgentMemorySearchRequest,
    AgentMemorySearchResponse,
    MemorySourcesResponse,
    ExternalUserMappingCreate,
    ExternalUserMappingResponse,
    AgentInstanceShareCreate,
    AgentInstanceShareResponse,
    AgentInstanceStats,
    AgentApiLogList,
    AgentMemoryCreate,
    WebhookEventResponse,
)

router = APIRouter()


def get_agent_service(db: aiosqlite.Connection = Depends(get_db)) -> AgentService:
    return AgentService(db)


# ==================== Agent Type ====================

@router.post("/agent-types", response_model=AgentTypeResponse)
async def create_agent_type(
    data: AgentTypeCreate,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Type 생성"""
    return await service.create_agent_type(
        name=data.name,
        developer_id=user_id,
        description=data.description,
        version=data.version,
        config_schema=data.config_schema,
        capabilities=data.capabilities,
        public_scope=data.public_scope,
        project_id=data.project_id,
    )


@router.get("/agent-types", response_model=list[AgentTypeResponse])
async def list_agent_types(
    developer_id: str | None = None,
    is_public: bool | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Type 목록 조회"""
    return await service.list_agent_types(
        developer_id=developer_id,
        is_public=is_public,
        status=status,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/agent-types/{agent_type_id}", response_model=AgentTypeResponse)
async def get_agent_type(
    agent_type_id: str,
    service: AgentService = Depends(get_agent_service),
):
    """Agent Type 조회"""
    try:
        return await service.get_agent_type(agent_type_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.put("/agent-types/{agent_type_id}", response_model=AgentTypeResponse)
async def update_agent_type(
    agent_type_id: str,
    data: AgentTypeUpdate,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Type 수정"""
    try:
        return await service.update_agent_type(
            agent_type_id=agent_type_id,
            developer_id=user_id,
            name=data.name,
            description=data.description,
            version=data.version,
            config_schema=data.config_schema,
            capabilities=data.capabilities,
            public_scope=data.public_scope,
            project_id=data.project_id,
            status=data.status,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/agent-types/{agent_type_id}")
async def delete_agent_type(
    agent_type_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Type 삭제"""
    try:
        await service.delete_agent_type(agent_type_id, user_id)
        return {"message": "Agent가 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Agent Instance ====================

@router.post("/agent-instances", response_model=AgentInstanceResponse)
async def create_agent_instance(
    data: AgentInstanceCreate,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 생성"""
    try:
        return await service.create_agent_instance(
            agent_type_id=data.agent_type_id,
            name=data.name,
            owner_id=user_id,
            config=data.config,
            webhook_url=data.webhook_url,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/agent-instances", response_model=list[AgentInstanceResponse])
async def list_agent_instances(
    agent_type_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 목록 조회"""
    return await service.list_agent_instances(
        user_id=user_id,
        agent_type_id=agent_type_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/agent-instances/{instance_id}", response_model=AgentInstanceResponse)
async def get_agent_instance(
    instance_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 조회"""
    try:
        return await service.get_agent_instance(instance_id, user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.put("/agent-instances/{instance_id}", response_model=AgentInstanceResponse)
async def update_agent_instance(
    instance_id: str,
    data: AgentInstanceUpdate,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 수정"""
    try:
        return await service.update_agent_instance(
            instance_id=instance_id,
            user_id=user_id,
            name=data.name,
            config=data.config,
            webhook_url=data.webhook_url,
            status=data.status,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.post("/agent-instances/{instance_id}/regenerate-api-key")
async def regenerate_api_key(
    instance_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """API Key 재발급"""
    try:
        new_api_key = await service.regenerate_api_key(instance_id, user_id)
        return {"api_key": new_api_key}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/agent-instances/{instance_id}")
async def delete_agent_instance(
    instance_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 삭제"""
    try:
        await service.delete_agent_instance(instance_id, user_id)
        return {"message": "Agent Instance가 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Agent Data ====================

@router.post("/agents/{agent_id}/data", response_model=AgentDataResponse)
async def receive_agent_data(
    agent_id: str,
    data: AgentDataCreate,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: AgentService = Depends(get_agent_service),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Agent 데이터 수신 (API Key 인증)"""
    import time
    start = time.time()
    try:
        result = await service.receive_agent_data(
            api_key=x_api_key,
            data_type=data.data_type,
            content=data.content,
            external_user_id=data.external_user_id,
            metadata=data.metadata,
        )
        # API 로그 기록
        elapsed_ms = int((time.time() - start) * 1000)
        from src.agent.middleware import ApiLogRecorder
        recorder = ApiLogRecorder(db)
        await recorder.log(
            agent_instance_id=result["agent_instance_id"],
            endpoint=f"/agents/{agent_id}/data",
            method="POST",
            status_code=200,
            external_user_id=data.external_user_id,
            response_time_ms=elapsed_ms,
        )
        return result
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/agent-instances/{instance_id}/data", response_model=list[AgentDataResponse])
async def list_agent_data(
    instance_id: str,
    internal_user_id: str | None = None,
    data_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent 데이터 목록 조회"""
    try:
        return await service.list_agent_data(
            instance_id=instance_id,
            user_id=user_id,
            internal_user_id=internal_user_id,
            data_type=data_type,
            limit=limit,
            offset=offset,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Agent Memory Access (API Key Auth) ====================

@router.get("/agents/{agent_id}/memory-sources", response_model=MemorySourcesResponse)
async def get_memory_sources(
    agent_id: str,
    external_user_id: str | None = None,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: AgentService = Depends(get_agent_service),
):
    """에이전트가 접근 가능한 메모리 소스 목록 (API Key 인증)"""
    try:
        return await service.get_memory_sources(
            api_key=x_api_key,
            external_user_id=external_user_id,
        )
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.post("/agents/{agent_id}/memories/search", response_model=AgentMemorySearchResponse)
async def search_agent_memories(
    agent_id: str,
    data: AgentMemorySearchRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: AgentService = Depends(get_agent_service),
):
    """메모리 검색 (API Key 인증, context_sources 기반)"""
    try:
        return await service.search_memories(
            api_key=x_api_key,
            query=data.query,
            context_sources=data.context_sources.model_dump() if data.context_sources else None,
            limit=data.limit,
            external_user_id=data.external_user_id,
        )
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/agents/{agent_id}/data", response_model=AgentDataListResponse)
async def get_agent_data(
    agent_id: str,
    data_type: str | None = None,
    external_user_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: AgentService = Depends(get_agent_service),
):
    """에이전트 데이터 조회 (API Key 인증)"""
    try:
        return await service.get_agent_data_by_api_key(
            api_key=x_api_key,
            data_type=data_type,
            external_user_id=external_user_id,
            limit=limit,
            offset=offset,
        )
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== External User Mapping ====================

@router.post("/agent-instances/{instance_id}/user-mappings", response_model=ExternalUserMappingResponse)
async def create_external_user_mapping(
    instance_id: str,
    data: ExternalUserMappingCreate,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """외부 사용자 매핑 생성"""
    try:
        return await service.create_external_user_mapping(
            instance_id=instance_id,
            user_id=user_id,
            external_user_id=data.external_user_id,
            internal_user_id=data.internal_user_id,
            external_system_name=data.external_system_name,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/agent-instances/{instance_id}/user-mappings", response_model=list[ExternalUserMappingResponse])
async def list_external_user_mappings(
    instance_id: str,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """외부 사용자 매핑 목록 조회"""
    try:
        return await service.list_external_user_mappings(
            instance_id=instance_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/agent-instances/user-mappings/{mapping_id}")
async def delete_external_user_mapping(
    mapping_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """외부 사용자 매핑 삭제"""
    try:
        await service.delete_external_user_mapping(mapping_id, user_id)
        return {"message": "사용자 매핑이 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Agent Instance Share ====================

@router.post("/agent-instances/{instance_id}/shares", response_model=AgentInstanceShareResponse)
async def create_agent_instance_share(
    instance_id: str,
    data: AgentInstanceShareCreate,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 공유 생성"""
    try:
        return await service.create_agent_instance_share(
            instance_id=instance_id,
            user_id=user_id,
            shared_with_user_id=data.shared_with_user_id,
            shared_with_project_id=data.shared_with_project_id,
            shared_with_department_id=data.shared_with_department_id,
            role=data.role,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/agent-instances/{instance_id}/shares", response_model=list[AgentInstanceShareResponse])
async def list_agent_instance_shares(
    instance_id: str,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 공유 목록 조회"""
    try:
        return await service.list_agent_instance_shares(
            instance_id=instance_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/agent-instances/shares/{share_id}")
async def delete_agent_instance_share(
    share_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Agent Instance 공유 삭제"""
    try:
        await service.delete_agent_instance_share(share_id, user_id)
        return {"message": "공유가 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Phase 2-1: Agent Instance Stats ====================

@router.get("/agent-instances/{instance_id}/stats", response_model=AgentInstanceStats)
async def get_agent_instance_stats(
    instance_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """에이전트 인스턴스 사용량 통계"""
    try:
        await service.get_agent_instance(instance_id, user_id)
        return await service.get_instance_stats(instance_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Phase 2-2: API Audit Logs ====================

@router.get("/agent-instances/{instance_id}/api-logs", response_model=AgentApiLogList)
async def get_agent_api_logs(
    instance_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """에이전트 인스턴스 API 호출 로그"""
    try:
        await service.get_agent_instance(instance_id, user_id)
        logs, total = await service.list_api_logs(instance_id, limit, offset)
        return {"logs": logs, "total": total}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Phase 2-3: Memory Dedicated Endpoints ====================

@router.post("/agents/{agent_id}/memories", response_model=AgentDataResponse)
async def create_agent_memory(
    agent_id: str,
    data: AgentMemoryCreate,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: AgentService = Depends(get_agent_service),
    db: aiosqlite.Connection = Depends(get_db),
):
    """메모리 전용 생성 (API Key 인증)"""
    import time
    start = time.time()
    try:
        result = await service.create_agent_memory(
            api_key=x_api_key,
            content=data.content,
            metadata=data.metadata,
        )
        elapsed_ms = int((time.time() - start) * 1000)
        from src.agent.middleware import ApiLogRecorder
        recorder = ApiLogRecorder(db)
        await recorder.log(
            agent_instance_id=result["agent_instance_id"],
            endpoint=f"/agents/{agent_id}/memories",
            method="POST",
            status_code=200,
            response_time_ms=elapsed_ms,
        )
        return result
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/agents/{agent_id}/memories/{memory_id}")
async def delete_agent_memory(
    agent_id: str,
    memory_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: AgentService = Depends(get_agent_service),
):
    """메모리 삭제 (API Key 인증)"""
    try:
        await service.delete_agent_memory(api_key=x_api_key, memory_id=memory_id)
        return {"message": "메모리가 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/agents/{agent_id}/entities")
async def get_agent_entities(
    agent_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: AgentService = Depends(get_agent_service),
):
    """에이전트 소유자의 Entity 그래프 조회 (API Key 인증)"""
    try:
        return await service.get_agent_entities(api_key=x_api_key)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)


# ==================== Phase 2-4: Webhook Events ====================

@router.get("/agent-instances/{instance_id}/webhook-events", response_model=list[WebhookEventResponse])
async def list_webhook_events(
    instance_id: str,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    """Webhook 이벤트 목록 조회"""
    try:
        await service.get_agent_instance(instance_id, user_id)
        return await service.list_webhook_events(instance_id, limit, offset)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=e.message)
