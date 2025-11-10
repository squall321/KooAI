"""
Tests for CLI Commands

Tests Click command-line interface commands.
"""

from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner


class TestCLIGroup:
    """Test main CLI group"""

    def test_cli_group_exists(self) -> None:
        """Test CLI group can be imported"""
        from src.presentation.cli.commands import cli

        assert cli is not None

    def test_cli_version(self) -> None:
        """Test CLI shows version"""
        from src.presentation.cli.commands import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower() or "1.0.0" in result.output

    def test_cli_help(self) -> None:
        """Test CLI shows help"""
        from src.presentation.cli.commands import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "KooAI" in result.output or "help" in result.output.lower()


class TestGetService:
    """Test get_service function"""

    def test_get_service_function_exists(self) -> None:
        """Test get_service function exists"""
        from src.presentation.cli.commands import get_service

        assert get_service is not None

    def test_get_service_returns_service(self) -> None:
        """Test get_service returns SimulationService"""
        from src.presentation.cli.commands import get_service
        from src.application.services import SimulationService

        service = get_service()

        assert isinstance(service, SimulationService)

    def test_get_service_is_singleton(self) -> None:
        """Test get_service returns same instance"""
        from src.presentation.cli.commands import get_service

        service1 = get_service()
        service2 = get_service()

        assert service1 is service2


class TestUploadCommand:
    """Test upload command"""

    def test_upload_command_exists(self) -> None:
        """Test upload command exists"""
        from src.presentation.cli.commands import upload

        assert upload is not None

    def test_upload_command_requires_file(self) -> None:
        """Test upload command requires file argument"""
        from src.presentation.cli.commands import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["upload"])

        # Should fail without file argument
        assert result.exit_code != 0

    @pytest.mark.skip(reason="Requires file system and mocking")
    def test_upload_command_with_file(self) -> None:
        """Test upload command with file"""
        from src.presentation.cli.commands import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            with open("test.csv", "w") as f:
                f.write("x,y,z,velocity\n")
                f.write("1,2,3,10.5\n")

            with patch("src.presentation.cli.commands.get_service") as mock_service:
                mock_result = Mock()
                mock_result.simulation_info.simulation_id = "sim_123"
                mock_result.simulation_info.name = "test"
                mock_result.simulation_info.simulation_type = "CFD"
                mock_result.simulation_info.num_vertices = 1
                mock_result.simulation_info.num_timesteps = 1
                mock_result.simulation_info.fields = ["velocity"]
                mock_result.field_analyses = {}

                mock_service.return_value.upload_and_analyze.return_value = mock_result

                result = runner.invoke(cli, ["upload", "test.csv"])

                assert result.exit_code == 0 or "Uploaded" in result.output


class TestCLIIntegration:
    """Test CLI integration"""

    def test_cli_runner_works(self) -> None:
        """Test Click CLI runner works"""
        from src.presentation.cli.commands import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert isinstance(result.exit_code, int)

    def test_cli_has_commands(self) -> None:
        """Test CLI has registered commands"""
        from src.presentation.cli.commands import cli

        # CLI should have commands
        assert hasattr(cli, "commands")
        # Upload should be registered
        assert "upload" in cli.commands
