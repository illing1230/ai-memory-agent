"""User Repository - 데이터 접근 계층"""

import uuid
from datetime import datetime
from typing import Any

import aiosqlite


class UserRepository:
    """사용자 관련 데이터베이스 작업"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    # ==================== Department ====================

    async def create_department(self, name: str, description: str | None = None) -> dict[str, Any]:
        """부서 생성"""
        dept_id = str(uuid.uuid4())
        await self.db.execute(
            "INSERT INTO departments (id, name, description) VALUES (?, ?, ?)",
            (dept_id, name, description),
        )
        await self.db.commit()
        return await self.get_department(dept_id)

    async def get_department(self, dept_id: str) -> dict[str, Any] | None:
        """부서 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM departments WHERE id = ?", (dept_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_departments(self) -> list[dict[str, Any]]:
        """부서 목록 조회"""
        cursor = await self.db.execute("SELECT * FROM departments ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ==================== User ====================

    async def create_user(
        self,
        name: str,
        email: str,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """사용자 생성"""
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self.db.execute(
            """INSERT INTO users (id, name, email, department_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, name, email, department_id, now, now),
        )
        await self.db.commit()
        return await self.get_user(user_id)

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """사용자 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_with_department(self, user_id: str) -> dict[str, Any] | None:
        """사용자 조회 (부서 정보 포함)"""
        cursor = await self.db.execute(
            """SELECT u.*, d.name as department_name, d.description as department_description
               FROM users u
               LEFT JOIN departments d ON u.department_id = d.id
               WHERE u.id = ?""",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """이메일로 사용자 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_users(self, department_id: str | None = None) -> list[dict[str, Any]]:
        """사용자 목록 조회"""
        if department_id:
            cursor = await self.db.execute(
                "SELECT * FROM users WHERE department_id = ? ORDER BY name",
                (department_id,),
            )
        else:
            cursor = await self.db.execute("SELECT * FROM users ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_user(
        self,
        user_id: str,
        name: str | None = None,
        email: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any] | None:
        """사용자 수정"""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if department_id is not None:
            updates.append("department_id = ?")
            params.append(department_id)

        if not updates:
            return await self.get_user(user_id)

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(user_id)

        await self.db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await self.db.commit()
        return await self.get_user(user_id)

    async def delete_user(self, user_id: str) -> bool:
        """사용자 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM users WHERE id = ?", (user_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ==================== Project ====================

    async def create_project(
        self,
        name: str,
        description: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """프로젝트 생성"""
        project_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await self.db.execute(
            """INSERT INTO projects (id, name, description, department_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, name, description, department_id, now, now),
        )
        await self.db.commit()
        return await self.get_project(project_id)

    async def get_project(self, project_id: str) -> dict[str, Any] | None:
        """프로젝트 조회"""
        cursor = await self.db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def update_project(
        self,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any] | None:
        """프로젝트 수정"""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return await self.get_project(project_id)

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(project_id)

        await self.db.execute(
            f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await self.db.commit()
        return await self.get_project(project_id)

    async def delete_project(self, project_id: str) -> bool:
        """프로젝트 삭제"""
        cursor = await self.db.execute(
            "DELETE FROM projects WHERE id = ?", (project_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def list_projects(self, department_id: str | None = None) -> list[dict[str, Any]]:
        """프로젝트 목록 조회"""
        if department_id:
            cursor = await self.db.execute(
                "SELECT * FROM projects WHERE department_id = ? ORDER BY name",
                (department_id,),
            )
        else:
            cursor = await self.db.execute("SELECT * FROM projects ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ==================== Project Member ====================

    async def add_project_member(
        self,
        project_id: str,
        user_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        """프로젝트 멤버 추가"""
        member_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO project_members (id, project_id, user_id, role)
               VALUES (?, ?, ?, ?)""",
            (member_id, project_id, user_id, role),
        )
        await self.db.commit()
        return await self.get_project_member_by_user(project_id, user_id)

    async def get_project_member(self, member_id: str) -> dict[str, Any] | None:
        """프로젝트 멤버 조회 (ID로)"""
        cursor = await self.db.execute(
            """SELECT pm.*, u.name as user_name, u.email as user_email
               FROM project_members pm
               LEFT JOIN users u ON pm.user_id = u.id
               WHERE pm.id = ?""",
            (member_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_project_member_by_user(
        self,
        project_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        """프로젝트 멤버 조회 (project_id, user_id로)"""
        cursor = await self.db.execute(
            """SELECT pm.*, u.name as user_name, u.email as user_email
               FROM project_members pm
               LEFT JOIN users u ON pm.user_id = u.id
               WHERE pm.project_id = ? AND pm.user_id = ?""",
            (project_id, user_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_project_members(self, project_id: str) -> list[dict[str, Any]]:
        """프로젝트 멤버 목록 조회"""
        cursor = await self.db.execute(
            """SELECT pm.*, u.name as user_name, u.email as user_email
               FROM project_members pm
               LEFT JOIN users u ON pm.user_id = u.id
               WHERE pm.project_id = ?
               ORDER BY pm.role, pm.joined_at""",
            (project_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_project_member_role(
        self,
        project_id: str,
        user_id: str,
        role: str,
    ) -> dict[str, Any] | None:
        """프로젝트 멤버 역할 변경"""
        await self.db.execute(
            """UPDATE project_members SET role = ?
               WHERE project_id = ? AND user_id = ?""",
            (role, project_id, user_id),
        )
        await self.db.commit()
        return await self.get_project_member_by_user(project_id, user_id)

    async def get_user_projects(self, user_id: str) -> list[dict[str, Any]]:
        """사용자가 참여한 프로젝트 목록 (역할 포함)"""
        cursor = await self.db.execute(
            """SELECT p.*, pm.role as member_role
               FROM projects p
               JOIN project_members pm ON p.id = pm.project_id
               WHERE pm.user_id = ?
               ORDER BY p.name""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def is_project_member(self, project_id: str, user_id: str) -> bool:
        """사용자가 프로젝트 멤버인지 확인"""
        cursor = await self.db.execute(
            "SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, user_id),
        )
        row = await cursor.fetchone()
        return row is not None

    async def remove_project_member(self, project_id: str, user_id: str) -> bool:
        """프로젝트 멤버 제거"""
        cursor = await self.db.execute(
            "DELETE FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, user_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0
