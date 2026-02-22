"""인증 라우터"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
import aiosqlite

from src.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, UserInfo, SSOLoginRequest
from src.auth.service import AuthService
from src.shared.database import get_db
from src.shared.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


async def get_auth_service(db: aiosqlite.Connection = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """로그인"""
    try:
        result = await auth_service.login(request.email, request.password)
        return result
    except ForbiddenException as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register", response_model=LoginResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """회원가입"""
    try:
        result = await auth_service.register(
            name=request.name,
            email=request.email,
            password=request.password,
            department_id=request.department_id,
        )
        return result
    except ForbiddenException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserInfo)
async def get_me(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """현재 로그인한 사용자 정보"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    token = authorization[7:]
    try:
        user = await auth_service.get_current_user(token)
        return user
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/sso", response_model=LoginResponse)
async def sso_login(
    request: SSOLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """SSO 로그인 (SAML/OIDC/OAuth2)

    SSO 인증 완료 후 사용자 정보를 전달하면,
    기존 사용자를 매칭하거나 자동 생성하여 토큰을 발급합니다.
    """
    try:
        result = await auth_service.sso_login(
            email=request.email,
            name=request.name,
            sso_provider=request.sso_provider,
            sso_id=request.sso_id,
            department_id=request.department_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify")
async def verify_token_endpoint(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """토큰 검증"""
    if not authorization or not authorization.startswith("Bearer "):
        return {"valid": False, "user_id": None}
    
    token = authorization[7:]
    user_id = auth_service.verify_token(token)
    
    return {"valid": user_id is not None, "user_id": user_id}
