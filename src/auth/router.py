"""인증 라우터"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
import aiosqlite

from src.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, UserInfo
from src.auth.service import AuthService
from src.shared.database import get_db
from src.shared.auth import verify_access_token
from src.shared.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


async def get_auth_service(db: aiosqlite.Connection = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> str:
    """현재 사용자 ID 추출 (토큰 또는 X-User-ID 헤더)"""
    # Bearer 토큰 확인
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        user_id = verify_access_token(token)
        if user_id:
            return user_id
    
    # X-User-ID 헤더 확인 (개발용 폴백)
    if x_user_id:
        return x_user_id
    
    raise HTTPException(status_code=401, detail="인증이 필요합니다")


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
