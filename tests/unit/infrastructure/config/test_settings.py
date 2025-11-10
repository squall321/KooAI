"""
Tests for Infrastructure Config Settings

Tests Settings class and configuration loading.
"""

import os
from unittest.mock import patch
import pytest


class TestSettings:
    """Test Settings class"""

    def test_settings_can_be_created(self):
        """Test Settings can be instantiated"""
        from src.infrastructure.config.settings import Settings

        settings = Settings()

        assert settings is not None
        assert settings.app_name == "KooAI"

    def test_settings_default_values(self):
        """Test Settings has correct default values"""
        from src.infrastructure.config.settings import Settings

        settings = Settings()

        assert settings.kooai_env == "development"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_settings_allowed_origins_list(self):
        """Test allowed_origins_list property"""
        from src.infrastructure.config.settings import Settings

        settings = Settings()

        origins = settings.allowed_origins_list

        assert isinstance(origins, list)
        assert len(origins) > 0

    def test_settings_database_url_property(self):
        """Test get_database_url property"""
        from src.infrastructure.config.settings import Settings

        settings = Settings()

        db_url = settings.get_database_url

        assert isinstance(db_url, str)
        assert len(db_url) > 0

    def test_settings_from_env(self):
        """Test Settings loads from environment variables"""
        from src.infrastructure.config.settings import Settings

        with patch.dict(os.environ, {
            "APP_NAME": "TestApp",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        }):
            settings = Settings()

            assert settings.app_name == "TestApp"
            assert settings.debug is True
            assert settings.log_level == "DEBUG"

    def test_settings_api_configuration(self):
        """Test API settings"""
        from src.infrastructure.config.settings import Settings

        settings = Settings()

        assert hasattr(settings, 'api_host')
        assert hasattr(settings, 'api_port')
        assert hasattr(settings, 'api_workers')
        assert settings.api_workers >= 1

    def test_settings_database_configuration(self):
        """Test database settings"""
        from src.infrastructure.config.settings import Settings

        settings = Settings()

        assert hasattr(settings, 'db_host')
        assert hasattr(settings, 'db_port')
        assert hasattr(settings, 'db_name')
        assert hasattr(settings, 'db_user')
        assert hasattr(settings, 'db_pool_size')

    def test_settings_secret_key_generated(self):
        """Test secret key is generated if not provided"""
        from src.infrastructure.config.settings import Settings

        settings = Settings()

        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0

    def test_settings_use_test_db(self):
        """Test test database configuration"""
        from src.infrastructure.config.settings import Settings

        with patch.dict(os.environ, {"USE_TEST_DB": "true"}):
            settings = Settings()

            assert settings.use_test_db is True

    def test_get_settings_function(self):
        """Test get_settings function returns Settings"""
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()

        assert settings is not None
        assert settings.app_name == "KooAI"

    def test_get_settings_is_cached(self):
        """Test get_settings returns same instance (cached)"""
        from src.infrastructure.config.settings import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2


class TestSettingsValidation:
    """Test Settings validation"""

    def test_settings_validates_port_number(self):
        """Test port number validation"""
        from src.infrastructure.config.settings import Settings

        with patch.dict(os.environ, {"API_PORT": "8080"}):
            settings = Settings()

            assert settings.api_port == 8080
            assert isinstance(settings.api_port, int)

    def test_settings_validates_boolean(self):
        """Test boolean field validation"""
        from src.infrastructure.config.settings import Settings

        with patch.dict(os.environ, {"DEBUG": "1"}):
            settings = Settings()

            # Pydantic converts truthy strings to bool
            assert isinstance(settings.debug, bool)

    def test_settings_environment_modes(self):
        """Test different environment modes"""
        from src.infrastructure.config.settings import Settings

        for env in ["development", "staging", "production"]:
            with patch.dict(os.environ, {"KOOAI_ENV": env}):
                settings = Settings()
                assert settings.kooai_env == env


class TestDatabaseURL:
    """Test database URL generation"""

    def test_database_url_from_components(self):
        """Test database URL is built from components"""
        from src.infrastructure.config.settings import Settings

        settings = Settings(
            db_host="localhost",
            db_port=5432,
            db_name="testdb",
            db_user="testuser",
            db_password="testpass"
        )

        db_url = settings.get_database_url

        assert "postgresql" in db_url or "sqlite" in db_url

    def test_database_url_override(self):
        """Test database_url can be overridden"""
        from src.infrastructure.config.settings import Settings

        custom_url = "postgresql://user:pass@host:5432/db"
        settings = Settings(database_url=custom_url)

        assert settings.get_database_url == custom_url

    def test_test_database_url(self):
        """Test test database uses SQLite"""
        from src.infrastructure.config.settings import Settings

        settings = Settings(use_test_db=True)

        db_url = settings.get_database_url

        assert "sqlite" in db_url.lower()
