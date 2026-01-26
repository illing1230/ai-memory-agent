"""User Service - 비즈니스 로직"""

from typing import Any

import aiosqlite

from src.user.repository import UserRepository
from src.shared.exceptions import NotFoundException, ValidationException


class UserService:
    """사용자 관련 비즈니스 로직"""

    def __init__(self, db: aiosqlite.Connection):
        self.repo = UserRepository(db)

    # ==================== Department ====================

    async def create_department(
        self,
        name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """부서 생성"""
        return await self.repo.create_department(name, description)

    async def get_department(self, dept_id: str) -> dict[str, Any]:
        """부서 조회"""
        dept = await self.repo.get_department(dept_id)
        if not dept:
            raise NotFoundException("부서", dept_id)
        return dept

    async def list_departments(self) -> list[dict[str, Any]]:
        """부서 목록"""
        return await self.repo.list_departments()

    # ==================== User ====================

    async def create_user(
        self,
        name: str,
        email: str,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """사용자 생성"""
        # 이메일 중복 체크
        existing = await self.repo.get_user_by_email(email)
        if existing:
            raise ValidationException(f"이미 사용 중인 이메일입니다: {email}")

        # 부서 존재 확인
        if department_id:
            dept = await self.repo.get_department(department_id)
            if not dept:
                raise NotFoundException("부서", department_id)

        return await self.repo.create_user(name, email, department_id)

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """사용자 조회"""
        user = await self.repo.get_user(user_id)
        if not user:
            raise NotFoundException("사용자", user_id)
        return user

    async def list_users(self, department_id: str | None = None) -> list[dict[str, Any]]:
        """사용자 목록"""
        return await self.repo.list_users(department_id)

    async def update_user(
        self,
        user_id: str,
        name: str | None = None,
        email: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """사용자 수정"""
        # 존재 확인
        await self.get_user(user_id)

        # 이메일 중복 체크
        if email:
            existing = await self.repo.get_user_by_email(email)
            if existing and existing["id"] != user_id:
                raise ValidationException(f"이미 사용 중인 이메일입니다: {email}")

        user = await self.repo.update_user(user_id, name, email, department_id)
        return user

    async def delete_user(self, user_id: str) -> bool:
        """사용자 삭제"""
        await self.get_user(user_id)
        return await self.repo.delete_user(user_id)

    # ==================== Project ====================

    async def create_project(
        self,
        name: str,
        description: str | None = None,
        department_id: str | None = None,
        owner_id: str | None = None,
    ) -> dict[str, Any]:
        """프로젝트 생성"""
        project = await self.repo.create_project(name, description, department_id)

        # 생성자를 owner로 추가
        if owner_id:
            await self.repo.add_project_member(project["id"], owner_id, "owner")

        return project

    async def get_project(self, project_id: str) -> dict[str, Any]:
        """프로젝트 조회"""
        project = await self.repo.get_project(project_id)
        if not project:
            raise NotFoundException("프로젝트", project_id)
        return project

    async def list_projects(self, department_id: str | None = None) -> list[dict[str, Any]]:
        """프로젝트 목록"""
        return await self.repo.list_projects(department_id)

    async def get_user_projects(self, user_id: str) -> list[dict[str, Any]]:
        """사용자가 참여한 프로젝트 목록"""
        return await self.repo.get_user_projects(user_id)

    # ==================== Project Member ====================

    async def add_project_member(
        self,
        project_id: str,
        user_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        """프로젝트 멤버 추가"""
        await self.get_project(project_id)
        await self.get_user(user_id)

        # 이미 멤버인지 확인
        if await self.repo.is_project_member(project_id, user_id):
            raise ValidationException("이미 프로젝트 멤버입니다")

        return await self.repo.add_project_member(project_id, user_id, role)

    async def list_project_members(self, project_id: str) -> list[dict[str, Any]]:
        """프로젝트 멤버 목록"""
        await self.get_project(project_id)
        return await self.repo.list_project_members(project_id)

    async def is_project_member(self, project_id: str, user_id: str) -> bool:
        """프로젝트 멤버 여부 확인"""
        return await self.repo.is_project_member(project_id, user_id)

    async def remove_project_member(self, project_id: str, user_id: str) -> bool:
        """프로젝트 멤버 제거"""
        return await self.repo.remove_project_member(project_id, user_id)
