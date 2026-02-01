"""인증 관련 유틸리티"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import base64

from fastapi import Depends, Header, HTTPException

from src.config import get_settings


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    settings = get_settings()
    
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_access_token_expire_hours)
    
    expire = datetime.utcnow() + expires_delta
    
    # 페이로드 구성
    payload = f"{user_id}|{expire.isoformat()}"
    
    # 서명 생성 (HMAC-SHA256)
    secret = settings.jwt_secret_key
    signature = hashlib.sha256(f"{payload}|{secret}".encode()).hexdigest()[:32]
    
    # Base64 인코딩
    token_data = f"{payload}|{signature}"
    token = base64.urlsafe_b64encode(token_data.encode()).decode()
    
    return token


def verify_access_token(token: str) -> Optional[str]:
    """액세스 토큰 검증 및 user_id 반환"""
    settings = get_settings()
    
    try:
        # Base64 디코딩
        token_data = base64.urlsafe_b64decode(token.encode()).decode()
        parts = token_data.split("|")
        
        if len(parts) != 3:
            return None
        
        user_id, expire_str, signature = parts
        
        # 서명 검증
        secret = settings.jwt_secret_key
        expected_signature = hashlib.sha256(f"{user_id}|{expire_str}|{secret}".encode()).hexdigest()[:32]
        
        if signature != expected_signature:
            return None
        
        # 만료 검증
        expire = datetime.fromisoformat(expire_str)
        if datetime.utcnow() > expire:
            return None
        
        return user_id
        
    except Exception:
        return None


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """비밀번호 검증"""
    try:
        salt, hash_value = hashed.split("$")
        expected_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_value == expected_hash.hex()
    except Exception:
        return False


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> str:
    """
    현재 사용자 ID 추출
    - Bearer 토큰 우선 확인
    - X-User-ID 헤더 폴백 (개발 환경)
    """
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


async def get_current_admin_user(
    user_id: str = Depends(get_current_user_id),
) -> str:
    """관리자 권한 확인. admin role이 아니면 403 반환."""
    from src.shared.database import get_db_sync

    db = await get_db_sync()
    try:
        cursor = await db.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or row["role"] != "admin":
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
        return user_id
    finally:
        await db.close()
