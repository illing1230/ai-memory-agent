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
    role: str = "user"


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


class SSOLoginRequest(BaseModel):
    """SSO 로그인 요청"""
    email: str
    name: str
    sso_provider: str  # "saml", "oidc", "oauth2" 등
    sso_id: str  # SSO 시스템에서의 고유 ID
    department_id: Optional[str] = None
