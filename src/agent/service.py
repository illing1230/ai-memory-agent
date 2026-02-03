"""Agent Service - 비즈니스 로직"""
import json
from typing import Any

import aiosqlite

from src.agent.repository import AgentRepository
from src.memory.repository import MemoryRepository
from src.shared.exceptions import NotFoundException, PermissionDeniedException
from src.shared.vector_store import upsert_vector
from src.shared.providers import get_embedding_provider


class AgentService:
    """Agent 관련 비즈니스 로직"""
    
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.repo = AgentRepository(db)
        self.memory_repo = MemoryRepository(db)

    # ==================== Agent Type ====================

    async def create_agent_type(
        self,
        name: str,
        developer_id: str,
        description: str | None = None,
        version: str = "1.0.0",
        config_schema: dict | None = None,
        capabilities: list[str] | None = None,
        public_scope: str = "public",
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Agent Type 생성"""
        return await self.repo.create_agent_type(
            name=name,
            developer_id=developer_id,
            description=description,
            version=version,
            config_schema=config_schema,
            capabilities=capabilities,
            public_scope=public_scope,
            project_id=project_id,
        )

    async def get_agent_type(self, agent_type_id: str) -> dict[str, Any]:
        """Agent Type 조회"""
        agent_type = await self.repo.get_agent_type(agent_type_id)
        if not agent_type:
            raise NotFoundException("Agent Type", agent_type_id)
        return agent_type

    async def list_agent_types(
        self,
        developer_id: str | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent Type 목록 조회"""
        agent_types = await self.repo.list_agent_types(
            developer_id=developer_id,
            is_public=is_public,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        # 사용자 ID가 있으면 공개 범위에 따른 필터링
        if user_id:
            filtered_types = []
            for agent_type in agent_types:
                # 개발자 본인은 항상 볼 수 있음
                if agent_type["developer_id"] == user_id:
                    filtered_types.append(agent_type)
                    continue
                
                # 공개 범위에 따른 접근 권한 체크
                if agent_type["public_scope"] == "public":
                    # 전체 공개: 모든 사용자 접근 가능
                    filtered_types.append(agent_type)
                elif agent_type["public_scope"] == "department":
                    # 부서 공개: 같은 부서 사용자만 접근 가능
                    if await self._check_same_department(user_id, agent_type["developer_id"]):
                        filtered_types.append(agent_type)
                elif agent_type["public_scope"] == "project":
                    # 프로젝트 공개: 지정된 프로젝트 멤버만 접근 가능
                    if agent_type["project_id"]:
                        if await self._check_project_member(user_id, agent_type["project_id"]):
                            filtered_types.append(agent_type)
                    else:
                        # project_id가 없으면 같은 프로젝트 멤버 체크
                        if await self._check_shared_project(user_id, agent_type["developer_id"]):
                            filtered_types.append(agent_type)
                # private는 개발자만 접근 가능 (위에서 이미 처리)
            
            return filtered_types
        
        return agent_types

    async def update_agent_type(
        self,
        agent_type_id: str,
        developer_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Agent Type 수정"""
        agent_type = await self.get_agent_type(agent_type_id)
        
        # 개발자만 수정 가능
        if agent_type["developer_id"] != developer_id:
            raise PermissionDeniedException("Agent Type을 수정할 권한이 없습니다")
        
        return await self.repo.update_agent_type(agent_type_id, **kwargs)

    async def delete_agent_type(self, agent_type_id: str, developer_id: str) -> bool:
        """Agent Type 삭제"""
        agent_type = await self.get_agent_type(agent_type_id)
        
        # 개발자만 삭제 가능
        if agent_type["developer_id"] != developer_id:
            raise PermissionDeniedException("Agent Type을 삭제할 권한이 없습니다")
        
        return await self.repo.delete_agent_type(agent_type_id)

    # ==================== Agent Instance ====================

    async def create_agent_instance(
        self,
        agent_type_id: str,
        name: str,
        owner_id: str,
        config: dict | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """Agent Instance 생성"""
        # Agent Type 존재 확인
        agent_type = await self.repo.get_agent_type(agent_type_id)
        if not agent_type:
            raise NotFoundException("Agent Type", agent_type_id)
                
        # 공개 범위 확인 (비공개 Agent Type도 인스턴스 생성 허용)
        # TODO: 조직 내부 Agent Type의 경우 조직 멤버십 확인 필요
                
        return await self.repo.create_agent_instance(
            agent_type_id=agent_type_id,
            name=name,
            owner_id=owner_id,
            config=config,
            webhook_url=webhook_url,
        )

    async def get_agent_instance(self, instance_id: str, user_id: str) -> dict[str, Any]:
        """Agent Instance 조회"""
        instance = await self.repo.get_agent_instance(instance_id)
        if not instance:
            raise NotFoundException("Agent Instance", instance_id)
        
        # 소유자 또는 공유 대상만 접근 가능
        await self._check_agent_instance_access(instance, user_id)
        
        return instance

    async def list_agent_instances(
        self,
        user_id: str,
        agent_type_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent Instance 목록 조회"""
        # 내 Agent Instance + 공유받은 Agent Instance
        my_instances = await self.repo.list_agent_instances(
            owner_id=user_id,
            agent_type_id=agent_type_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        # TODO: 공유받은 Agent Instance도 포함
        
        return my_instances

    async def update_agent_instance(
        self,
        instance_id: str,
        user_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Agent Instance 수정"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자만 수정 가능
        if instance["owner_id"] != user_id:
            raise PermissionDeniedException("Agent Instance를 수정할 권한이 없습니다")
        
        return await self.repo.update_agent_instance(instance_id, **kwargs)

    async def regenerate_api_key(self, instance_id: str, user_id: str) -> str:
        """API Key 재발급"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자만 재발급 가능
        if instance["owner_id"] != user_id:
            raise PermissionDeniedException("API Key를 재발급할 권한이 없습니다")
        
        return await self.repo.regenerate_api_key(instance_id)

    async def delete_agent_instance(self, instance_id: str, user_id: str) -> bool:
        """Agent Instance 삭제"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자만 삭제 가능
        if instance["owner_id"] != user_id:
            raise PermissionDeniedException("Agent Instance를 삭제할 권한이 없습니다")
        
        return await self.repo.delete_agent_instance(instance_id)

    # ==================== Agent Data ====================

    async def receive_agent_data(
        self,
        api_key: str,
        data_type: str,
        content: str,
        external_user_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Agent 데이터 수신"""
        # API Key로 Agent Instance 조회
        instance = await self.repo.get_agent_instance_by_api_key(api_key)
        if not instance:
            raise PermissionDeniedException("유효하지 않은 API Key입니다")
        
        if instance["status"] != "active":
            raise PermissionDeniedException("비활성화된 Agent Instance입니다")
        
        # 사용자 ID 결정
        if external_user_id:
            # 외부 사용자 매핑 조회
            mapping = await self.repo.get_external_user_mapping_by_external_id(
                instance["id"],
                external_user_id,
            )
            if mapping:
                internal_user_id = mapping["internal_user_id"]
            else:
                # 매핑이 없으면 소유자 사용
                internal_user_id = instance["owner_id"]
        else:
            # 단일 사용자 Agent
            internal_user_id = instance["owner_id"]
        
        # 데이터 저장
        agent_data = await self.repo.create_agent_data(
            agent_instance_id=instance["id"],
            data_type=data_type,
            content=content,
            internal_user_id=internal_user_id,
            external_user_id=external_user_id,
            metadata=metadata,
        )
        
        # 메모리 타입이면 메모리로 변환
        if data_type == "memory":
            await self._convert_to_memory(
                content=content,
                owner_id=internal_user_id,
                agent_instance_id=instance["id"],
                metadata=metadata,
            )
        
        return agent_data

    async def list_agent_data(
        self,
        instance_id: str,
        user_id: str,
        internal_user_id: str | None = None,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent 데이터 목록 조회"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자 또는 공유 대상만 접근 가능
        await self._check_agent_instance_access(instance, user_id)
        
        return await self.repo.list_agent_data(
            agent_instance_id=instance_id,
            internal_user_id=internal_user_id,
            data_type=data_type,
            limit=limit,
            offset=offset,
        )

    async def _convert_to_memory(
        self,
        content: str,
        owner_id: str,
        agent_instance_id: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Agent 데이터를 메모리로 변환"""
        # 벡터 생성
        embedding_provider = get_embedding_provider()
        vector = await embedding_provider.embed(content)
        
        # 메모리 생성 (scope를 'agent'로 설정)
        memory = await self.memory_repo.create_memory(
            content=content,
            owner_id=owner_id,
            scope="agent",
            category=metadata.get("category") if metadata else None,
            importance=metadata.get("importance", "medium") if metadata else "medium",
            metadata={
                **(metadata or {}),
                "source": "agent",
                "agent_instance_id": agent_instance_id,
            },
        )
        
        # 벡터 저장
        if memory.get("vector_id"):
            await upsert_vector(
                vector_id=memory["vector_id"],
                vector=vector,
                payload={
                    "memory_id": memory["id"],
                    "scope": "agent",
                    "owner_id": owner_id,
                },
            )
        
        return memory

    # ==================== External User Mapping ====================

    async def create_external_user_mapping(
        self,
        instance_id: str,
        user_id: str,
        external_user_id: str,
        internal_user_id: str,
        external_system_name: str | None = None,
    ) -> dict[str, Any]:
        """외부 사용자 매핑 생성"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자만 매핑 생성 가능
        if instance["owner_id"] != user_id:
            raise PermissionDeniedException("사용자 매핑을 생성할 권한이 없습니다")
        
        return await self.repo.create_external_user_mapping(
            agent_instance_id=instance_id,
            external_user_id=external_user_id,
            internal_user_id=internal_user_id,
            external_system_name=external_system_name,
        )

    async def list_external_user_mappings(
        self,
        instance_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """외부 사용자 매핑 목록 조회"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자만 조회 가능
        if instance["owner_id"] != user_id:
            raise PermissionDeniedException("사용자 매핑을 조회할 권한이 없습니다")
        
        return await self.repo.list_external_user_mappings(
            agent_instance_id=instance_id,
            limit=limit,
            offset=offset,
        )

    async def delete_external_user_mapping(
        self,
        mapping_id: str,
        user_id: str,
    ) -> bool:
        """외부 사용자 매핑 삭제"""
        # 매핑 조회
        mapping = await self.repo.get_external_user_mapping(mapping_id)
        if not mapping:
            raise NotFoundException("사용자 매핑", mapping_id)
        
        # Agent Instance 소유자 확인
        instance = await self.repo.get_agent_instance(mapping["agent_instance_id"])
        if instance and instance["owner_id"] != user_id:
            raise PermissionDeniedException("사용자 매핑을 삭제할 권한이 없습니다")
        
        return await self.repo.delete_external_user_mapping(mapping_id)

    # ==================== Agent Instance Share ====================

    async def create_agent_instance_share(
        self,
        instance_id: str,
        user_id: str,
        shared_with_user_id: str | None = None,
        shared_with_project_id: str | None = None,
        shared_with_department_id: str | None = None,
        role: str = "viewer",
    ) -> dict[str, Any]:
        """Agent Instance 공유 생성"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자만 공유 가능
        if instance["owner_id"] != user_id:
            raise PermissionDeniedException("Agent Instance를 공유할 권한이 없습니다")
        
        return await self.repo.create_agent_instance_share(
            agent_instance_id=instance_id,
            shared_with_user_id=shared_with_user_id,
            shared_with_project_id=shared_with_project_id,
            shared_with_department_id=shared_with_department_id,
            role=role,
        )

    async def list_agent_instance_shares(
        self,
        instance_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent Instance 공유 목록 조회"""
        instance = await self.get_agent_instance(instance_id, user_id)
        
        # 소유자만 조회 가능
        if instance["owner_id"] != user_id:
            raise PermissionDeniedException("공유 목록을 조회할 권한이 없습니다")
        
        return await self.repo.list_agent_instance_shares(
            agent_instance_id=instance_id,
            limit=limit,
            offset=offset,
        )

    async def delete_agent_instance_share(
        self,
        share_id: str,
        user_id: str,
    ) -> bool:
        """Agent Instance 공유 삭제"""
        # 공유 조회
        share = await self.repo.get_agent_instance_share(share_id)
        if not share:
            raise NotFoundException("공유", share_id)
        
        # Agent Instance 소유자 확인
        instance = await self.repo.get_agent_instance(share["agent_instance_id"])
        if instance and instance["owner_id"] != user_id:
            raise PermissionDeniedException("공유를 삭제할 권한이 없습니다")
        
        return await self.repo.delete_agent_instance_share(share_id)

    async def _check_agent_instance_access(
        self,
        instance: dict[str, Any],
        user_id: str,
    ) -> bool:
        """Agent Instance 접근 권한 체크"""
        # 소유자
        if instance["owner_id"] == user_id:
            return True
        
        # TODO: 공유 대상 체크
        
        raise PermissionDeniedException("Agent Instance에 접근할 권한이 없습니다")

    async def _check_same_department(self, user_id: str, developer_id: str) -> bool:
        """같은 부서인지 확인"""
        cursor = await self.db.execute(
            """
            SELECT u1.department_id, u2.department_id
            FROM users u1, users u2
            WHERE u1.id = ? AND u2.id = ?
            """,
            (user_id, developer_id),
        )
        row = await cursor.fetchone()
        if row and row["u1.department_id"] and row["u2.department_id"]:
            return row["u1.department_id"] == row["u2.department_id"]
        return False

    async def _check_shared_project(self, user_id: str, developer_id: str) -> bool:
        """같은 프로젝트에 속해 있는지 확인"""
        cursor = await self.db.execute(
            """
            SELECT COUNT(*) as count
            FROM project_members pm1, project_members pm2
            WHERE pm1.user_id = ? AND pm2.user_id = ? AND pm1.project_id = pm2.project_id
            """,
            (user_id, developer_id),
        )
        row = await cursor.fetchone()
        return row["count"] > 0

    async def _check_project_member(self, user_id: str, project_id: str) -> bool:
        """프로젝트 멤버인지 확인"""
        cursor = await self.db.execute(
            """
            SELECT COUNT(*) as count
            FROM project_members
            WHERE user_id = ? AND project_id = ?
            """,
            (user_id, project_id),
        )
        row = await cursor.fetchone()
        return row["count"] > 0
