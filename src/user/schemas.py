"""User Pydantic 스키마"""

from datetime import datetime
from pydantic import BaseModel, EmailStr


# ==================== Department ====================

class DepartmentBase(BaseModel):
    name: str
    description: str | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== User ====================

class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    department_id: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    department_id: str | None = None


class UserResponse(UserBase):
    id: str
    department_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserWithDepartment(UserResponse):
    department: DepartmentResponse | None = None


# ==================== Project ====================

class ProjectBase(BaseModel):
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    department_id: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    department_id: str | None = None


class ProjectResponse(ProjectBase):
    id: str
    department_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Project Member ====================

class ProjectMemberCreate(BaseModel):
    user_id: str
    role: str = "member"


class ProjectMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True
