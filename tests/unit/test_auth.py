"""Auth 모듈 테스트"""

from datetime import timedelta
from unittest.mock import patch, MagicMock

from src.shared.auth import (
    create_access_token,
    verify_access_token,
    hash_password,
    verify_password,
)


def _mock_settings():
    s = MagicMock()
    s.jwt_secret_key = "test-secret-key-for-testing"
    s.jwt_access_token_expire_hours = 24
    return s


class TestAccessToken:
    """액세스 토큰 생성/검증 테스트"""

    @patch("src.shared.auth.get_settings", return_value=_mock_settings())
    def test_create_and_verify(self, _):
        token = create_access_token("user-1")
        user_id = verify_access_token(token)
        assert user_id == "user-1"

    @patch("src.shared.auth.get_settings", return_value=_mock_settings())
    def test_custom_expiry(self, _):
        token = create_access_token("user-2", expires_delta=timedelta(hours=1))
        assert verify_access_token(token) == "user-2"

    @patch("src.shared.auth.get_settings", return_value=_mock_settings())
    def test_expired_token(self, _):
        token = create_access_token("user-1", expires_delta=timedelta(seconds=-1))
        assert verify_access_token(token) is None

    @patch("src.shared.auth.get_settings", return_value=_mock_settings())
    def test_tampered_signature(self, _):
        token = create_access_token("user-1")
        # 토큰 마지막 문자를 변경하여 서명 변조
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        assert verify_access_token(tampered) is None

    @patch("src.shared.auth.get_settings", return_value=_mock_settings())
    def test_malformed_token(self, _):
        assert verify_access_token("not-a-valid-token") is None

    @patch("src.shared.auth.get_settings", return_value=_mock_settings())
    def test_empty_token(self, _):
        assert verify_access_token("") is None


class TestPassword:
    """비밀번호 해싱/검증 테스트"""

    def test_hash_and_verify(self):
        hashed = hash_password("my-password")
        assert verify_password("my-password", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_format(self):
        hashed = hash_password("test")
        # salt$hash 형태
        assert "$" in hashed
        salt, hash_val = hashed.split("$")
        assert len(salt) == 32  # hex(16 bytes)

    def test_verify_malformed_hash(self):
        assert verify_password("test", "no-dollar-sign") is False
