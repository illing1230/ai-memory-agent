"""커스텀 예외 정의"""

from typing import Any


class AppException(Exception):
    """애플리케이션 기본 예외"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """리소스를 찾을 수 없음"""

    def __init__(self, resource: str, resource_id: str | None = None):
        message = f"{resource}을(를) 찾을 수 없습니다"
        if resource_id:
            message = f"{resource} (ID: {resource_id})을(를) 찾을 수 없습니다"
        super().__init__(message=message, status_code=404)


class PermissionDeniedException(AppException):
    """권한 없음"""

    def __init__(self, message: str = "접근 권한이 없습니다"):
        super().__init__(message=message, status_code=403)


# ForbiddenException 별칭
ForbiddenException = PermissionDeniedException


class ValidationException(AppException):
    """유효성 검사 실패"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message=message, status_code=400, details=details)


class DatabaseException(AppException):
    """데이터베이스 오류"""

    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다"):
        super().__init__(message=message, status_code=500)


class VectorStoreException(AppException):
    """벡터 저장소 오류"""

    def __init__(self, message: str = "벡터 저장소 오류가 발생했습니다"):
        super().__init__(message=message, status_code=500)


class ProviderException(AppException):
    """Provider 오류 (Embedding/LLM)"""

    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"{provider} Provider 오류: {message}",
            status_code=502,
        )
