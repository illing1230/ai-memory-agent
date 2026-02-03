"""Agent Repository - 데이터베이스 접근"""
import json
import uuid
from typing import Any

import aiosqlite


class AgentRepository:
    """Agent 관련 데이터베이스 작업"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

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
        agent_type_id = str(uuid.uuid4())
                
        await self.db.execute(
            """
            INSERT INTO agent_types (id, name, description, developer_id, version, config_schema, capabilities, public_scope, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_type_id,
                name,
                description,
                developer_id,
                version,
                json.dumps(config_schema) if config_schema else None,
                json.dumps(capabilities) if capabilities else None,
                public_scope,
                project_id,
            ),
        )
        await self.db.commit()
                
        return await self.get_agent_type(agent_type_id)

    async def get_agent_type(self, agent_type_id: str) -> dict[str, Any] | None:
        """Agent Type 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM agent_types WHERE id = ?",
            (agent_type_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        
        agent_type = dict(row)
        # JSON 필드 파싱
        if agent_type.get("config_schema"):
            agent_type["config_schema"] = json.loads(agent_type["config_schema"])
        if agent_type.get("capabilities"):
            try:
                agent_type["capabilities"] = json.loads(agent_type["capabilities"])
            except (json.JSONDecodeError, TypeError):
                agent_type["capabilities"] = []
        else:
            agent_type["capabilities"] = []
        
        return agent_type

    async def list_agent_types(
        self,
        developer_id: str | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent Type 목록 조회"""
        query = "SELECT * FROM agent_types WHERE 1=1"
        params = []
        
        if developer_id:
            query += " AND developer_id = ?"
            params.append(developer_id)
        
        if is_public is not None:
            query += " AND is_public = ?"
            params.append(is_public)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        
        # JSON 필드 파싱
        agent_types = []
        for row in rows:
            agent_type = dict(row)
            if agent_type.get("config_schema"):
                agent_type["config_schema"] = json.loads(agent_type["config_schema"])
            if agent_type.get("capabilities"):
                try:
                    agent_type["capabilities"] = json.loads(agent_type["capabilities"])
                except (json.JSONDecodeError, TypeError):
                    agent_type["capabilities"] = []
            else:
                agent_type["capabilities"] = []
            agent_types.append(agent_type)
        
        return agent_types

    async def update_agent_type(
        self,
        agent_type_id: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Agent Type 수정"""
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if value is not None:
                if key in ["config_schema", "capabilities"]:
                    updates.append(f"{key} = ?")
                    params.append(json.dumps(value))
                else:
                    updates.append(f"{key} = ?")
                    params.append(value)
        
        if not updates:
            return await self.get_agent_type(agent_type_id)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(agent_type_id)
        
        query = f"UPDATE agent_types SET {', '.join(updates)} WHERE id = ?"
        await self.db.execute(query, params)
        await self.db.commit()
        
        return await self.get_agent_type(agent_type_id)

    async def delete_agent_type(self, agent_type_id: str) -> bool:
        """Agent Type 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM agent_types WHERE id = ?",
            (agent_type_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0

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
        instance_id = str(uuid.uuid4())
        api_key = f"sk_{uuid.uuid4().hex}"
        
        await self.db.execute(
            """
            INSERT INTO agent_instances (id, agent_type_id, name, owner_id, api_key, config, webhook_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                instance_id,
                agent_type_id,
                name,
                owner_id,
                api_key,
                json.dumps(config) if config else None,
                webhook_url,
            ),
        )
        await self.db.commit()
        
        return await self.get_agent_instance(instance_id)

    async def get_agent_instance(self, instance_id: str) -> dict[str, Any] | None:
        """Agent Instance 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM agent_instances WHERE id = ?",
            (instance_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        
        instance = dict(row)
        # JSON 필드 파싱
        if instance.get("config"):
            try:
                instance["config"] = json.loads(instance["config"])
            except (json.JSONDecodeError, TypeError):
                instance["config"] = None
        
        return instance

    async def get_agent_instance_by_api_key(self, api_key: str) -> dict[str, Any] | None:
        """API Key로 Agent Instance 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM agent_instances WHERE api_key = ?",
            (api_key,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        
        instance = dict(row)
        # JSON 필드 파싱
        if instance.get("config"):
            try:
                instance["config"] = json.loads(instance["config"])
            except (json.JSONDecodeError, TypeError):
                instance["config"] = None
        
        return instance

    async def list_agent_instances(
        self,
        owner_id: str | None = None,
        agent_type_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent Instance 목록 조회"""
        query = "SELECT * FROM agent_instances WHERE 1=1"
        params = []
        
        if owner_id:
            query += " AND owner_id = ?"
            params.append(owner_id)
        
        if agent_type_id:
            query += " AND agent_type_id = ?"
            params.append(agent_type_id)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        
        # JSON 필드 파싱
        instances = []
        for row in rows:
            instance = dict(row)
            if instance.get("config"):
                try:
                    instance["config"] = json.loads(instance["config"])
                except (json.JSONDecodeError, TypeError):
                    instance["config"] = None
            instances.append(instance)
        
        return instances

    async def update_agent_instance(
        self,
        instance_id: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Agent Instance 수정"""
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if value is not None:
                if key == "config":
                    updates.append(f"{key} = ?")
                    params.append(json.dumps(value))
                else:
                    updates.append(f"{key} = ?")
                    params.append(value)
        
        if not updates:
            return await self.get_agent_instance(instance_id)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(instance_id)
        
        query = f"UPDATE agent_instances SET {', '.join(updates)} WHERE id = ?"
        await self.db.execute(query, params)
        await self.db.commit()
        
        return await self.get_agent_instance(instance_id)

    async def regenerate_api_key(self, instance_id: str) -> str:
        """API Key 재발급"""
        new_api_key = f"sk_{uuid.uuid4().hex}"
        
        await self.db.execute(
            "UPDATE agent_instances SET api_key = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_api_key, instance_id),
        )
        await self.db.commit()
        
        return new_api_key

    async def delete_agent_instance(self, instance_id: str) -> bool:
        """Agent Instance 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM agent_instances WHERE id = ?",
            (instance_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ==================== Agent Data ====================

    async def create_agent_data(
        self,
        agent_instance_id: str,
        data_type: str,
        content: str,
        internal_user_id: str,
        external_user_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Agent 데이터 생성"""
        data_id = str(uuid.uuid4())
        
        await self.db.execute(
            """
            INSERT INTO agent_data (id, agent_instance_id, external_user_id, internal_user_id, data_type, content, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data_id,
                agent_instance_id,
                external_user_id,
                internal_user_id,
                data_type,
                content,
                json.dumps(metadata) if metadata else None,
            ),
        )
        await self.db.commit()
        
        return await self.get_agent_data(data_id)

    async def get_agent_data(self, data_id: str) -> dict[str, Any] | None:
        """Agent 데이터 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM agent_data WHERE id = ?",
            (data_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        
        data = dict(row)
        # JSON 필드 파싱
        if data.get("metadata"):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except (json.JSONDecodeError, TypeError):
                data["metadata"] = None
        
        return data

    async def list_agent_data(
        self,
        agent_instance_id: str,
        internal_user_id: str | None = None,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent 데이터 목록 조회"""
        query = "SELECT * FROM agent_data WHERE agent_instance_id = ?"
        params = [agent_instance_id]
        
        if internal_user_id:
            query += " AND internal_user_id = ?"
            params.append(internal_user_id)
        
        if data_type:
            query += " AND data_type = ?"
            params.append(data_type)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        
        # JSON 필드 파싱
        data_list = []
        for row in rows:
            data = dict(row)
            if data.get("metadata"):
                try:
                    data["metadata"] = json.loads(data["metadata"])
                except (json.JSONDecodeError, TypeError):
                    data["metadata"] = None
            data_list.append(data)
        
        return data_list

    # ==================== External User Mapping ====================

    async def create_external_user_mapping(
        self,
        agent_instance_id: str,
        external_user_id: str,
        internal_user_id: str,
        external_system_name: str | None = None,
    ) -> dict[str, Any]:
        """외부 사용자 매핑 생성"""
        mapping_id = str(uuid.uuid4())
        
        await self.db.execute(
            """
            INSERT INTO external_user_mappings (id, agent_instance_id, external_user_id, internal_user_id, external_system_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (mapping_id, agent_instance_id, external_user_id, internal_user_id, external_system_name),
        )
        await self.db.commit()
        
        return await self.get_external_user_mapping(mapping_id)

    async def get_external_user_mapping(self, mapping_id: str) -> dict[str, Any] | None:
        """외부 사용자 매핑 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM external_user_mappings WHERE id = ?",
            (mapping_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_external_user_mapping_by_external_id(
        self,
        agent_instance_id: str,
        external_user_id: str,
    ) -> dict[str, Any] | None:
        """외부 사용자 ID로 매핑 조회"""
        cursor = await self.db.execute(
            """
            SELECT * FROM external_user_mappings 
            WHERE agent_instance_id = ? AND external_user_id = ?
            """,
            (agent_instance_id, external_user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_external_user_mappings(
        self,
        agent_instance_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """외부 사용자 매핑 목록 조회"""
        cursor = await self.db.execute(
            """
            SELECT * FROM external_user_mappings 
            WHERE agent_instance_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (agent_instance_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def delete_external_user_mapping(self, mapping_id: str) -> bool:
        """외부 사용자 매핑 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM external_user_mappings WHERE id = ?",
            (mapping_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ==================== Agent Instance Share ====================

    async def create_agent_instance_share(
        self,
        agent_instance_id: str,
        shared_with_user_id: str | None = None,
        shared_with_project_id: str | None = None,
        shared_with_department_id: str | None = None,
        role: str = "viewer",
    ) -> dict[str, Any]:
        """Agent Instance 공유 생성"""
        share_id = str(uuid.uuid4())
        
        await self.db.execute(
            """
            INSERT INTO agent_instance_shares (id, agent_instance_id, shared_with_user_id, shared_with_project_id, shared_with_department_id, role)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (share_id, agent_instance_id, shared_with_user_id, shared_with_project_id, shared_with_department_id, role),
        )
        await self.db.commit()
        
        return await self.get_agent_instance_share(share_id)

    async def get_agent_instance_share(self, share_id: str) -> dict[str, Any] | None:
        """Agent Instance 공유 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM agent_instance_shares WHERE id = ?",
            (share_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_agent_instance_shares(
        self,
        agent_instance_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Agent Instance 공유 목록 조회"""
        cursor = await self.db.execute(
            """
            SELECT * FROM agent_instance_shares 
            WHERE agent_instance_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (agent_instance_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def delete_agent_instance_share(self, share_id: str) -> bool:
        """Agent Instance 공유 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM agent_instance_shares WHERE id = ?",
            (share_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0
