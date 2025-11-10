"""
Tests for FastAPI Dependencies

Tests dependency injection functions for database, repositories, and services.
"""

from unittest.mock import Mock, patch, MagicMock
import pytest


class TestDatabaseDependencies:
    """Test database dependencies"""

    def test_get_db_function_exists(self) -> None:
        """Test get_db function can be imported"""
        from src.presentation.api.dependencies import get_db

        assert get_db is not None

    def test_get_db_yields_session(self) -> None:
        """Test get_db yields database session"""
        from src.presentation.api.dependencies import get_db

        with patch("src.presentation.api.dependencies.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            # Get generator
            gen = get_db()

            # Get session from generator
            session = next(gen)

            assert session == mock_session

    def test_get_db_closes_session(self) -> None:
        """Test get_db closes session after use"""
        from src.presentation.api.dependencies import get_db

        with patch("src.presentation.api.dependencies.SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            gen = get_db()
            next(gen)

            # Trigger finally block
            try:
                next(gen)
            except StopIteration:
                pass

            mock_session.close.assert_called_once()


class TestRepositoryDependencies:
    """Test repository dependencies"""

    def test_get_simulation_repository_exists(self) -> None:
        """Test get_simulation_repository function exists"""
        from src.presentation.api.dependencies import get_simulation_repository

        assert get_simulation_repository is not None

    def test_get_simulation_repository_returns_repository(self) -> None:
        """Test get_simulation_repository returns repository instance"""
        from src.presentation.api.dependencies import get_simulation_repository

        # Clear cache to ensure fresh instance
        get_simulation_repository.cache_clear()

        repo = get_simulation_repository()

        assert repo is not None

    def test_get_simulation_repository_is_singleton(self) -> None:
        """Test get_simulation_repository returns same instance (singleton)"""
        from src.presentation.api.dependencies import get_simulation_repository

        # Clear cache
        get_simulation_repository.cache_clear()

        repo1 = get_simulation_repository()
        repo2 = get_simulation_repository()

        # Should return same instance
        assert repo1 is repo2

    def test_get_simulation_repository_implements_interface(self) -> None:
        """Test repository implements SimulationResultRepository interface"""
        from src.presentation.api.dependencies import get_simulation_repository

        get_simulation_repository.cache_clear()

        repo = get_simulation_repository()

        # Check repository has required methods (Protocol check)
        assert hasattr(repo, 'add')
        assert hasattr(repo, 'get_by_id')
        assert hasattr(repo, 'list_all')
        assert callable(repo.add)
        assert callable(repo.get_by_id)
        assert callable(repo.list_all)


class TestServiceDependencies:
    """Test service dependencies"""

    def test_get_simulation_service_exists(self) -> None:
        """Test get_simulation_service function exists"""
        from src.presentation.api.dependencies import get_simulation_service

        assert get_simulation_service is not None

    def test_get_simulation_service_returns_service(self) -> None:
        """Test get_simulation_service returns service instance"""
        from src.presentation.api.dependencies import (
            get_simulation_service,
            get_simulation_repository,
        )

        # Clear cache
        get_simulation_repository.cache_clear()

        service = get_simulation_service()

        assert service is not None

    def test_get_simulation_service_uses_repository(self) -> None:
        """Test service is created with repository dependency"""
        from src.presentation.api.dependencies import (
            get_simulation_service,
            get_simulation_repository,
        )

        # Clear cache
        get_simulation_repository.cache_clear()

        # Mock repository
        mock_repo = Mock()

        service = get_simulation_service(repository=mock_repo)

        assert service is not None
        # Service should have repository
        assert service.repository == mock_repo

    def test_get_simulation_service_type(self) -> None:
        """Test service is of correct type"""
        from src.presentation.api.dependencies import get_simulation_service
        from src.application.services import SimulationService

        service = get_simulation_service()

        assert isinstance(service, SimulationService)


class TestDependencyInjection:
    """Test dependency injection integration"""

    def test_dependencies_can_be_used_together(self) -> None:
        """Test dependencies can be used together"""
        from src.presentation.api.dependencies import (
            get_simulation_repository,
            get_simulation_service,
        )

        # Clear caches
        get_simulation_repository.cache_clear()

        # Get repository
        repo = get_simulation_repository()

        # Get service with repo
        service = get_simulation_service(repository=repo)

        assert repo is not None
        assert service is not None
        assert service.repository is repo
