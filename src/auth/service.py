"""인증 서비스"""

from typing import Optional
import aiosqlite

from src.user.repository import UserRepository
from src.shared.auth import create_access_token, verify_access_token, hash_password, verify_password
from src.shared.exceptions import NotFoundException, ForbiddenException


class AuthService:
    """인증 관련 비즈니스 로직"""

    def __init__(self, db: aiosqlite.Connection):
        self.user_repo = UserRepository(db)
        self.db = db

    async def login(self, email: str, password: str) -> dict:
        """로그인"""
        # 사용자 조회
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise ForbiddenException("이메일 또는 비밀번호가 올바르지 않습니다")
        
        # 비밀번호 검증 (password_hash 컬럼이 있는 경우)
        stored_password = user.get("password_hash")
        if stored_password:
            if not verify_password(password, stored_password):
                raise ForbiddenException("이메일 또는 비밀번호가 올바르지 않습니다")
        # password_hash가 없으면 개발모드로 통과
        
        # 토큰 생성
        access_token = create_access_token(user["id"])
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "department_id": user.get("department_id"),
                "role": user.get("role", "user"),
            }
        }

    async def register(
        self,
        name: str,
        email: str,
        password: str,
        department_id: Optional[str] = None,
    ) -> dict:
        """회원가입"""
        # 이메일 중복 체크
        existing = await self.user_repo.get_user_by_email(email)
        if existing:
            raise ForbiddenException("이미 사용 중인 이메일입니다")
        
        # 비밀번호 해싱
        password_hash = hash_password(password)
        
        # 사용자 생성
        user = await self.user_repo.create_user(
            name=name,
            email=email,
            department_id=department_id,
        )
        
        # password_hash 업데이트
        await self.db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user["id"])
        )
        await self.db.commit()
        
        # 토큰 생성
        access_token = create_access_token(user["id"])
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "department_id": department_id,
                "role": "user",
            }
        }

    async def get_current_user(self, token: str) -> dict:
        """현재 로그인한 사용자 정보"""
        user_id = verify_access_token(token)
        if not user_id:
            raise ForbiddenException("유효하지 않은 토큰입니다")
        
        user = await self.user_repo.get_user(user_id)
        if not user:
            raise NotFoundException("사용자", user_id)
        
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "department_id": user.get("department_id"),
            "role": user.get("role", "user"),
        }

    def verify_token(self, token: str) -> Optional[str]:
        """토큰 검증"""
        return verify_access_token(token)
