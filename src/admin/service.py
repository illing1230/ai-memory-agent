"""관리자 서비스"""

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
        """채팅방 목록 + 멤버/메시지 수"""
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
        """채팅방 삭제"""
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
