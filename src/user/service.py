"""User Service - 비즈니스 로직"""

from typing import Any

import aiosqlite

from src.user.repository import UserRepository
from src.shared.exceptions import NotFoundException, ValidationException, ForbiddenException


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
        existing = await self.repo.get_user_by_email(email)
        if existing:
            raise ValidationException(f"이미 사용 중인 이메일입니다: {email}")

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
        await self.get_user(user_id)

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

    async def get_user_department(self, user_id: str) -> dict[str, Any] | None:
        """사용자의 부서 조회"""
        user = await self.repo.get_user_with_department(user_id)
        if not user or not user.get("department_id"):
            return None
        return {
            "id": user["department_id"],
            "name": user.get("department_name"),
            "description": user.get("department_description"),
        }

    # ==================== Project ====================

    async def create_project(
        self,
        name: str,
        owner_id: str,
        description: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]:
        """프로젝트 생성 (생성자가 owner)"""
        project = await self.repo.create_project(name, description, department_id)
        
        # 생성자를 owner로 추가
        await self.repo.add_project_member(project["id"], owner_id, "owner")
        
        # member_role 포함해서 반환
        project["member_role"] = "owner"
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

    async def update_project(
        self,
        project_id: str,
        user_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """프로젝트 수정 (owner/admin만)"""
        await self._check_project_admin(project_id, user_id)
        return await self.repo.update_project(project_id, name, description)

    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """프로젝트 삭제 (owner만)"""
        await self._check_project_owner(project_id, user_id)
        return await self.repo.delete_project(project_id)

    # ==================== Project Member ====================

    async def add_project_member(
        self,
        project_id: str,
        user_id: str,
        target_user_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        """프로젝트 멤버 추가 (owner/admin만)"""
        await self._check_project_admin(project_id, user_id)
        await self.get_project(project_id)
        await self.get_user(target_user_id)

        if await self.repo.is_project_member(project_id, target_user_id):
            raise ValidationException("이미 프로젝트 멤버입니다")

        return await self.repo.add_project_member(project_id, target_user_id, role)

    async def list_project_members(self, project_id: str) -> list[dict[str, Any]]:
        """프로젝트 멤버 목록"""
        await self.get_project(project_id)
        return await self.repo.list_project_members(project_id)

    async def update_project_member_role(
        self,
        project_id: str,
        user_id: str,
        target_user_id: str,
        role: str,
    ) -> dict[str, Any]:
        """프로젝트 멤버 역할 변경 (owner만)"""
        await self._check_project_owner(project_id, user_id)
        
        if role == "owner":
            raise ForbiddenException("owner 역할은 부여할 수 없습니다")
        
        member = await self.repo.get_project_member_by_user(project_id, target_user_id)
        if not member:
            raise NotFoundException("프로젝트 멤버", target_user_id)
        
        if member["role"] == "owner":
            raise ForbiddenException("owner의 역할은 변경할 수 없습니다")
        
        return await self.repo.update_project_member_role(project_id, target_user_id, role)

    async def is_project_member(self, project_id: str, user_id: str) -> bool:
        """프로젝트 멤버 여부 확인"""
        return await self.repo.is_project_member(project_id, user_id)

    async def remove_project_member(
        self,
        project_id: str,
        user_id: str,
        target_user_id: str,
    ) -> bool:
        """프로젝트 멤버 제거 (owner/admin 또는 본인)"""
        member = await self.repo.get_project_member_by_user(project_id, user_id)
        if not member:
            raise ForbiddenException("프로젝트 멤버가 아닙니다")
        
        # 본인 탈퇴
        if user_id == target_user_id:
            if member["role"] == "owner":
                raise ForbiddenException("owner는 프로젝트를 나갈 수 없습니다. 프로젝트를 삭제하세요.")
            return await self.repo.remove_project_member(project_id, target_user_id)
        
        # 다른 사람 강퇴 (owner/admin만)
        if member["role"] not in ["owner", "admin"]:
            raise ForbiddenException("멤버를 제거할 권한이 없습니다")
        
        target_member = await self.repo.get_project_member_by_user(project_id, target_user_id)
        if not target_member:
            raise NotFoundException("프로젝트 멤버", target_user_id)
        
        if target_member["role"] == "owner":
            raise ForbiddenException("owner는 강퇴할 수 없습니다")
        
        if member["role"] == "admin" and target_member["role"] == "admin":
            raise ForbiddenException("admin은 다른 admin을 강퇴할 수 없습니다")
        
        return await self.repo.remove_project_member(project_id, target_user_id)

    # ==================== Permission Check ====================

    async def _check_project_member(self, project_id: str, user_id: str) -> dict[str, Any]:
        """프로젝트 멤버 권한 체크"""
        member = await self.repo.get_project_member_by_user(project_id, user_id)
        if not member:
            raise ForbiddenException("프로젝트 멤버가 아닙니다")
        return member

    async def _check_project_admin(self, project_id: str, user_id: str) -> dict[str, Any]:
        """프로젝트 admin 이상 권한 체크"""
        member = await self._check_project_member(project_id, user_id)
        if member["role"] not in ["owner", "admin"]:
            raise ForbiddenException("관리자 권한이 필요합니다")
        return member

    async def _check_project_owner(self, project_id: str, user_id: str) -> dict[str, Any]:
        """프로젝트 owner 권한 체크"""
        member = await self._check_project_member(project_id, user_id)
        if member["role"] != "owner":
            raise ForbiddenException("소유자 권한이 필요합니다")
        return member
