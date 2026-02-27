"""관리자 서비스"""

from datetime import datetime, timedelta

import aiosqlite


class AdminService:
    """관리자 비즈니스 로직"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def get_dashboard_stats(self) -> dict:
        """대시보드 통계 조회"""
        stats = {}
        for table, key in [
            ("users", "total_users"),
            ("chat_rooms", "total_chat_rooms"),
            ("memories", "total_memories"),
            ("chat_messages", "total_messages"),
            ("departments", "total_departments"),
            ("projects", "total_projects"),
        ]:
            cursor = await self.db.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            row = await cursor.fetchone()
            stats[key] = row["cnt"] if row else 0
        return stats

    async def get_users(self) -> list[dict]:
        """전체 사용자 목록"""
        cursor = await self.db.execute(
            """SELECT u.id, u.name, u.email, u.role, u.department_id, u.created_at,
                      d.name as department_name
               FROM users u
               LEFT JOIN departments d ON u.department_id = d.id
               ORDER BY u.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_user_role(self, user_id: str, role: str) -> None:
        """사용자 역할 변경"""
        await self.db.execute(
            "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (role, user_id),
        )
        await self.db.commit()

    async def delete_user(self, user_id: str) -> None:
        """사용자 삭제"""
        await self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await self.db.commit()

    async def get_departments(self) -> list[dict]:
        """부서 목록 + 멤버 수"""
        cursor = await self.db.execute(
            """SELECT d.id, d.name, d.description, d.created_at,
                      COUNT(u.id) as member_count
               FROM departments d
               LEFT JOIN users u ON u.department_id = d.id
               GROUP BY d.id
               ORDER BY d.name"""
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_projects(self) -> list[dict]:
        """프로젝트 목록 + 멤버 수"""
        cursor = await self.db.execute(
            """SELECT p.id, p.name, p.description, p.department_id, p.created_at,
                      d.name as department_name,
                      COUNT(pm.id) as member_count
               FROM projects p
               LEFT JOIN departments d ON p.department_id = d.id
               LEFT JOIN project_members pm ON pm.project_id = p.id
               GROUP BY p.id
               ORDER BY p.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_chat_rooms(self) -> list[dict]:
        """대화방 목록 + 멤버/메시지 수"""
        cursor = await self.db.execute(
            """SELECT cr.id, cr.name, cr.room_type, cr.owner_id, cr.created_at,
                      u.name as owner_name,
                      (SELECT COUNT(*) FROM chat_room_members WHERE chat_room_id = cr.id) as member_count,
                      (SELECT COUNT(*) FROM chat_messages WHERE chat_room_id = cr.id) as message_count
               FROM chat_rooms cr
               LEFT JOIN users u ON cr.owner_id = u.id
               ORDER BY cr.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def delete_chat_room(self, room_id: str) -> None:
        """대화방 삭제"""
        await self.db.execute("DELETE FROM chat_rooms WHERE id = ?", (room_id,))
        await self.db.commit()

    async def get_memories(self, limit: int = 20, offset: int = 0) -> dict:
        """전체 메모리 목록 (페이지네이션)"""
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM memories")
        row = await cursor.fetchone()
        total = row["cnt"] if row else 0

        cursor = await self.db.execute(
            """SELECT m.id, m.content, m.scope, m.owner_id, m.category, m.importance, m.created_at,
                      u.name as owner_name
               FROM memories m
               LEFT JOIN users u ON m.owner_id = u.id
               ORDER BY m.created_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def delete_memory(self, memory_id: str) -> None:
        """메모리 삭제"""
        await self.db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        await self.db.commit()

    # === 지식 대시보드 ===

    async def get_knowledge_dashboard(self) -> dict:
        """팀 지식 대시보드 전체 조회"""
        memory_stats = await self._get_memory_stats()
        hot_topics = await self._get_hot_topics()
        stale_knowledge = await self._get_stale_knowledge()
        contributions = await self._get_contributions()
        document_stats = await self._get_document_stats()
        return {
            "memory_stats": memory_stats,
            "hot_topics": hot_topics,
            "stale_knowledge": stale_knowledge,
            "contributions": contributions,
            "document_stats": document_stats,
        }

    async def _get_memory_stats(self) -> dict:
        """메모리 통계 집계"""
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM memories")
        total = (await cursor.fetchone())["cnt"]

        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM memories WHERE superseded = 0"
        )
        active = (await cursor.fetchone())["cnt"]

        superseded = total - active

        # scope별
        cursor = await self.db.execute(
            "SELECT COALESCE(scope, 'unknown') as scope, COUNT(*) as cnt FROM memories GROUP BY scope"
        )
        by_scope = {row["scope"]: row["cnt"] for row in await cursor.fetchall()}

        # category별
        cursor = await self.db.execute(
            "SELECT COALESCE(category, 'uncategorized') as category, COUNT(*) as cnt FROM memories GROUP BY category"
        )
        by_category = {row["category"]: row["cnt"] for row in await cursor.fetchall()}

        # importance별
        cursor = await self.db.execute(
            "SELECT COALESCE(importance, 'medium') as importance, COUNT(*) as cnt FROM memories GROUP BY importance"
        )
        by_importance = {row["importance"]: row["cnt"] for row in await cursor.fetchall()}

        # 최근 7일/30일
        now = datetime.utcnow()
        d7 = (now - timedelta(days=7)).isoformat()
        d30 = (now - timedelta(days=30)).isoformat()

        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM memories WHERE created_at >= ?", (d7,)
        )
        recent_7d = (await cursor.fetchone())["cnt"]

        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM memories WHERE created_at >= ?", (d30,)
        )
        recent_30d = (await cursor.fetchone())["cnt"]

        return {
            "total": total,
            "active": active,
            "superseded": superseded,
            "by_scope": by_scope,
            "by_category": by_category,
            "by_importance": by_importance,
            "recent_7d": recent_7d,
            "recent_30d": recent_30d,
        }

    async def _get_hot_topics(self, limit: int = 15) -> list[dict]:
        """핫 토픽: 자주 언급되는 엔티티 TOP N"""
        cursor = await self.db.execute(
            """SELECT e.name as entity_name, e.entity_type,
                      COUNT(me.id) as mention_count
               FROM entities e
               JOIN memory_entities me ON me.entity_id = e.id
               GROUP BY e.id
               ORDER BY mention_count DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def _get_stale_knowledge(self) -> dict:
        """오래된 지식 통계 (30/60/90일 미접근)"""
        now = datetime.utcnow()
        d30 = (now - timedelta(days=30)).isoformat()
        d60 = (now - timedelta(days=60)).isoformat()
        d90 = (now - timedelta(days=90)).isoformat()

        results = {}
        for label, threshold in [("no_access_30d", d30), ("no_access_60d", d60), ("no_access_90d", d90)]:
            cursor = await self.db.execute(
                """SELECT COUNT(*) as cnt FROM memories
                   WHERE superseded = 0
                     AND (last_accessed_at IS NULL OR last_accessed_at < ?)""",
                (threshold,),
            )
            results[label] = (await cursor.fetchone())["cnt"]

        # 중요도 낮은 + 30일 미접근
        cursor = await self.db.execute(
            """SELECT COUNT(*) as cnt FROM memories
               WHERE superseded = 0
                 AND importance = 'low'
                 AND (last_accessed_at IS NULL OR last_accessed_at < ?)""",
            (d30,),
        )
        results["low_importance_stale"] = (await cursor.fetchone())["cnt"]

        return results

    async def _get_contributions(self, limit: int = 10) -> list[dict]:
        """사용자별 기여도 (생성 수 + 총 접근 수)"""
        cursor = await self.db.execute(
            """SELECT m.owner_id as user_id,
                      COALESCE(u.name, m.owner_id) as user_name,
                      COUNT(m.id) as memories_created,
                      COALESCE(SUM(m.access_count), 0) as memories_accessed
               FROM memories m
               LEFT JOIN users u ON m.owner_id = u.id
               GROUP BY m.owner_id
               ORDER BY memories_created DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def _get_document_stats(self) -> dict:
        """문서 통계"""
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM documents")
        total = (await cursor.fetchone())["cnt"]

        cursor = await self.db.execute(
            "SELECT COALESCE(file_type, 'unknown') as file_type, COUNT(*) as cnt FROM documents GROUP BY file_type"
        )
        by_type = {row["file_type"]: row["cnt"] for row in await cursor.fetchall()}

        cursor = await self.db.execute(
            "SELECT COALESCE(status, 'unknown') as status, COUNT(*) as cnt FROM documents GROUP BY status"
        )
        by_status = {row["status"]: row["cnt"] for row in await cursor.fetchall()}

        cursor = await self.db.execute(
            "SELECT COALESCE(SUM(chunk_count), 0) as total_chunks FROM documents"
        )
        total_chunks = (await cursor.fetchone())["total_chunks"]

        return {
            "total": total,
            "by_type": by_type,
            "by_status": by_status,
            "total_chunks": total_chunks,
        }

    # === Phase 2-1: Agent Dashboard ===

    async def get_agent_dashboard(self) -> dict:
        """에이전트 대시보드 통계"""
        from src.agent.repository import AgentRepository
        repo = AgentRepository(self.db)
        return await repo.get_all_instances_stats()

    # === Phase 2-2: Admin API Logs ===

    async def get_admin_api_logs(
        self,
        instance_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """관리자용 전체 API 로그"""
        from src.agent.repository import AgentRepository
        repo = AgentRepository(self.db)
        return await repo.list_api_logs(
            agent_instance_id=instance_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )

    # === Phase 3-3: Knowledge Quality Report ===

    async def get_knowledge_quality_report(self) -> dict:
        """전사 지식 품질 리포트"""
        now = datetime.utcnow()
        d30 = (now - timedelta(days=30)).isoformat()

        # 총 메모리
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM memories WHERE superseded = 0")
        total_memories = (await cursor.fetchone())["cnt"]

        # 30일 미접근 (stale)
        cursor = await self.db.execute(
            """SELECT COUNT(*) as cnt FROM memories
               WHERE superseded = 0
                 AND (last_accessed_at IS NULL OR last_accessed_at < ?)""",
            (d30,),
        )
        stale_memories_count = (await cursor.fetchone())["cnt"]

        # 유사 메모리 후보 수 (supersede 관계가 있는 것)
        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM memories WHERE superseded_by IS NOT NULL"
        )
        duplicate_candidates_count = (await cursor.fetchone())["cnt"]

        # Supersede 체인 수
        cursor = await self.db.execute(
            "SELECT COUNT(DISTINCT superseded_by) as cnt FROM memories WHERE superseded_by IS NOT NULL"
        )
        superseded_chain_count = (await cursor.fetchone())["cnt"]

        # Scope 분포
        cursor = await self.db.execute(
            """SELECT COALESCE(scope, 'unknown') as scope, COUNT(*) as cnt
               FROM memories WHERE superseded = 0 GROUP BY scope"""
        )
        scope_distribution = {row["scope"]: row["cnt"] for row in await cursor.fetchall()}

        # Category 분포
        cursor = await self.db.execute(
            """SELECT COALESCE(category, 'uncategorized') as category, COUNT(*) as cnt
               FROM memories WHERE superseded = 0 GROUP BY category"""
        )
        category_distribution = {row["category"]: row["cnt"] for row in await cursor.fetchall()}

        # Top 엔티티
        cursor = await self.db.execute(
            """SELECT e.name, e.entity_type, COUNT(me.id) as mention_count
               FROM entities e
               JOIN memory_entities me ON me.entity_id = e.id
               GROUP BY e.id
               ORDER BY mention_count DESC
               LIMIT 20"""
        )
        top_entities = [dict(row) for row in await cursor.fetchall()]

        # Agent별 기여
        cursor = await self.db.execute(
            """SELECT ai.id as agent_id, ai.name as agent_name,
                      COUNT(CASE WHEN ad.data_type = 'memory' THEN 1 END) as memory_count,
                      MAX(ad.created_at) as last_active
               FROM agent_instances ai
               LEFT JOIN agent_data ad ON ad.agent_instance_id = ai.id
               GROUP BY ai.id
               ORDER BY memory_count DESC
               LIMIT 20"""
        )
        agent_contribution = [dict(row) for row in await cursor.fetchall()]

        return {
            "total_memories": total_memories,
            "stale_memories_count": stale_memories_count,
            "duplicate_candidates_count": duplicate_candidates_count,
            "superseded_chain_count": superseded_chain_count,
            "scope_distribution": scope_distribution,
            "category_distribution": category_distribution,
            "top_entities": top_entities,
            "agent_contribution": agent_contribution,
        }

    # === Department Management ===
    
    async def update_department(self, department_id: str, name: str, description: str | None = None) -> None:
        """부서 수정"""
        await self.db.execute(
            "UPDATE departments SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name, description, department_id),
        )
        await self.db.commit()

    async def delete_department(self, department_id: str) -> None:
        """부서 삭제 - 소속 사용자의 department_id를 NULL로 설정 후 삭제"""
        # 소속 사용자의 department_id를 NULL로 설정
        await self.db.execute(
            "UPDATE users SET department_id = NULL WHERE department_id = ?",
            (department_id,)
        )
        # 부서 삭제
        await self.db.execute("DELETE FROM departments WHERE id = ?", (department_id,))
        await self.db.commit()

    # === Project Management ===
    
    async def update_project(
        self, 
        project_id: str, 
        name: str, 
        description: str | None = None, 
        department_id: str | None = None
    ) -> None:
        """프로젝트 수정"""
        await self.db.execute(
            "UPDATE projects SET name = ?, description = ?, department_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name, description, department_id, project_id),
        )
        await self.db.commit()

    async def delete_project(self, project_id: str) -> None:
        """프로젝트 삭제 - project_members 먼저 삭제 후 프로젝트 삭제"""
        # 프로젝트 멤버 먼저 삭제
        await self.db.execute("DELETE FROM project_members WHERE project_id = ?", (project_id,))
        # 프로젝트 삭제
        await self.db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await self.db.commit()
