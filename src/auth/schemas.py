"""인증 스키마"""

from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: str
    password: str


class UserInfo(BaseModel):
    """사용자 정보"""
    id: str
    name: str
    email: str
    department_id: Optional[str] = None


class LoginResponse(BaseModel):
    """로그인 응답"""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class RegisterRequest(BaseModel):
    """회원가입 요청"""
    name: str
    email: str
    password: str
    department_id: Optional[str] = None
