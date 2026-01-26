"""User API Router"""

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from src.shared.database import get_db
from src.shared.exceptions import NotFoundException, ValidationException
from src.user.service import UserService
from src.user.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectMemberCreate,
    ProjectMemberResponse,
)

router = APIRouter()


def get_user_service(db: aiosqlite.Connection = Depends(get_db)) -> UserService:
    return UserService(db)


# ==================== Department ====================

@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    data: DepartmentCreate,
    service: UserService = Depends(get_user_service),
):
    """부서 생성"""
    return await service.create_department(data.name, data.description)


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(
    service: UserService = Depends(get_user_service),
):
    """부서 목록"""
    return await service.list_departments()


@router.get("/departments/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: str,
    service: UserService = Depends(get_user_service),
):
    """부서 조회"""
    try:
        return await service.get_department(dept_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


# ==================== Project (User보다 먼저!) ====================

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    owner_id: str | None = None,
    service: UserService = Depends(get_user_service),
):
    """프로젝트 생성"""
    return await service.create_project(
        data.name,
        data.description,
        data.department_id,
        owner_id,
    )


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    department_id: str | None = None,
    service: UserService = Depends(get_user_service),
):
    """프로젝트 목록"""
    return await service.list_projects(department_id)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    service: UserService = Depends(get_user_service),
):
    """프로젝트 조회"""
    try:
        return await service.get_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


# ==================== Project Member ====================

@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: str,
    data: ProjectMemberCreate,
    service: UserService = Depends(get_user_service),
):
    """프로젝트 멤버 추가"""
    try:
        return await service.add_project_member(project_id, data.user_id, data.role)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: str,
    service: UserService = Depends(get_user_service),
):
    """프로젝트 멤버 목록"""
    try:
        return await service.list_project_members(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: str,
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    """프로젝트 멤버 제거"""
    await service.remove_project_member(project_id, user_id)
    return {"message": "프로젝트 멤버가 제거되었습니다"}


# ==================== User ====================

@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """사용자 생성"""
    try:
        return await service.create_user(data.name, data.email, data.department_id)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("", response_model=list[UserResponse])
async def list_users(
    department_id: str | None = None,
    service: UserService = Depends(get_user_service),
):
    """사용자 목록"""
    return await service.list_users(department_id)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    """사용자 조회"""
    try:
        return await service.get_user(user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    """사용자 수정"""
    try:
        return await service.update_user(
            user_id,
            data.name,
            data.email,
            data.department_id,
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    """사용자 삭제"""
    try:
        await service.delete_user(user_id)
        return {"message": "사용자가 삭제되었습니다"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/{user_id}/projects", response_model=list[ProjectResponse])
async def get_user_projects(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    """사용자가 참여한 프로젝트 목록"""
    return await service.get_user_projects(user_id)
