"""AI Memory Agent SDK 예외 클래스"""


class AIMemoryAgentError(Exception):
    """AI Memory Agent SDK 기본 예외"""
    pass


class AuthenticationError(AIMemoryAgentError):
    """인증 실패 예외"""
    pass


class APIError(AIMemoryAgentError):
    """API 오류 예외"""
    
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class ConnectionError(AIMemoryAgentError):
    """연결 오류 예외"""
    pass


class ValidationError(AIMemoryAgentError):
    """데이터 검증 오류 예외"""
    pass
