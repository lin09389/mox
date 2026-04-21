import os

from mox.infrastructure.auth import AuthManager, PasswordManager
from mox.infrastructure.config import Settings


class TestSecurityDefaults:
    def test_require_auth_default_true(self):
        settings = Settings(_env_file=None)
        assert settings.REQUIRE_AUTH is True

    def test_default_users_empty(self):
        settings = Settings(_env_file=None)
        assert settings.DEFAULT_USERS == []

    def test_custom_default_users(self):
        settings = Settings(
            _env_file=None,
            DEFAULT_USERS=["admin:secret123:admin@test.com:admin,read"],
        )
        assert len(settings.DEFAULT_USERS) == 1
        assert settings.DEFAULT_USERS[0] == "admin:secret123:admin@test.com:admin,read"


class TestPasswordManager:
    def test_password_hash_and_verify(self):
        password = "secure_test_password_123"
        hashed = PasswordManager.get_password_hash(password)

        assert hashed != password
        assert PasswordManager.verify_password(password, hashed) is True
        assert PasswordManager.verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        password = "test_password"
        hash1 = PasswordManager.get_password_hash(password)
        hash2 = PasswordManager.get_password_hash(password)

        assert hash1 != hash2
        assert PasswordManager.verify_password(password, hash1) is True
        assert PasswordManager.verify_password(password, hash2) is True


class TestAuthManager:
    def test_no_default_users_by_default(self):
        env_backup = os.environ.get("MOX_DEFAULT_USERS")
        try:
            os.environ.pop("MOX_DEFAULT_USERS", None)
            manager = AuthManager()
            assert len(manager.users_db) == 0
        finally:
            if env_backup is not None:
                os.environ["MOX_DEFAULT_USERS"] = env_backup

    def test_authenticate_no_user(self):
        manager = AuthManager()
        result = manager.authenticate_user("nonexistent_user", "any_password")
        assert result is None

    def test_get_user_not_exists(self):
        manager = AuthManager()
        result = manager.get_user("nonexistent")
        assert result is None


class TestLoginAttemptsLimit:
    def test_login_lockout_config(self):
        settings = Settings(_env_file=None)
        assert settings.MAX_LOGIN_ATTEMPTS == 5
        assert settings.LOGIN_LOCKOUT_DURATION_MINUTES == 15


class TestCORSConfiguration:
    def test_cors_origins_restricted(self):
        settings = Settings(_env_file=None)
        assert settings.CORS_ORIGINS is not None
        assert len(settings.CORS_ORIGINS) > 0
        for origin in settings.CORS_ORIGINS:
            assert origin != "*"

    def test_cors_allow_credentials(self):
        settings = Settings(_env_file=None)
        assert settings.CORS_ALLOW_CREDENTIALS is True
