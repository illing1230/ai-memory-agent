"""예외 클래스 테스트"""

from src.shared.exceptions import (
    AppException,
    NotFoundException,
    PermissionDeniedException,
    ForbiddenException,
    ValidationException,
    DatabaseException,
    VectorStoreException,
    ProviderException,
)


class TestAppException:
    def test_default_status_code(self):
        exc = AppException("에러 발생")
        assert exc.status_code == 500
        assert exc.message == "에러 발생"
        assert exc.details == {}

    def test_custom_status_and_details(self):
        exc = AppException("커스텀", status_code=418, details={"key": "val"})
        assert exc.status_code == 418
        assert exc.details["key"] == "val"


class TestNotFoundException:
    def test_without_id(self):
        exc = NotFoundException("메모리")
        assert exc.status_code == 404
        assert "메모리" in exc.message

    def test_with_id(self):
        exc = NotFoundException("메모리", "mem-123")
        assert "mem-123" in exc.message
        assert exc.status_code == 404


class TestPermissionDeniedException:
    def test_default_message(self):
        exc = PermissionDeniedException()
        assert exc.status_code == 403
        assert "권한" in exc.message

    def test_custom_message(self):
        exc = PermissionDeniedException("접근 불가")
        assert exc.message == "접근 불가"


class TestForbiddenExceptionAlias:
    def test_alias(self):
        assert ForbiddenException is PermissionDeniedException


class TestValidationException:
    def test_with_details(self):
        exc = ValidationException("유효하지 않음", details={"field": "name"})
        assert exc.status_code == 400
        assert exc.details["field"] == "name"


class TestDatabaseException:
    def test_default(self):
        exc = DatabaseException()
        assert exc.status_code == 500


class TestVectorStoreException:
    def test_default(self):
        exc = VectorStoreException()
        assert exc.status_code == 500


class TestProviderException:
    def test_provider_name_in_message(self):
        exc = ProviderException("OpenAI", "API 키 오류")
        assert exc.status_code == 502
        assert "OpenAI" in exc.message
        assert "API 키 오류" in exc.message
