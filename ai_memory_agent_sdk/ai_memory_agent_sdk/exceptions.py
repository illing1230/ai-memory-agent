"""AI Memory Agent SDK 예외 클래스"""


class AIMemoryAgentError(Exception):
    """Base exception for AI Memory Agent SDK"""

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(AIMemoryAgentError):
    """API Key가 유효하지 않거나 권한이 없는 경우 (401/403)"""

    def __init__(self, message: str = "유효하지 않은 API Key입니다"):
        super().__init__(message)


class APIError(AIMemoryAgentError):
    """서버 API 에러"""

    def __init__(self, status_code: int, message: str = ""):
        self.status_code = status_code
        super().__init__(f"API Error ({status_code}): {message}")


class ConnectionError(AIMemoryAgentError):
    """서버 연결 실패"""

    def __init__(self, message: str = "서버에 연결할 수 없습니다"):
        super().__init__(message)
