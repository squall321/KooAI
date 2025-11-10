"""
Tests for CLI Utility Functions

Tests Rich console utilities for CLI output formatting.
"""

from unittest.mock import Mock, patch
import pytest


class TestPrintFunctions:
    """Test print utility functions"""

    def test_print_success_function_exists(self) -> None:
        """Test print_success function exists"""
        from src.presentation.cli.utils import print_success

        assert print_success is not None

    def test_print_error_function_exists(self) -> None:
        """Test print_error function exists"""
        from src.presentation.cli.utils import print_error

        assert print_error is not None

    def test_print_warning_function_exists(self) -> None:
        """Test print_warning function exists"""
        from src.presentation.cli.utils import print_warning

        assert print_warning is not None

    def test_print_info_function_exists(self) -> None:
        """Test print_info function exists"""
        from src.presentation.cli.utils import print_info

        assert print_info is not None

    def test_print_success_calls_console(self) -> None:
        """Test print_success uses console"""
        from src.presentation.cli import utils

        with patch.object(utils.console, "print") as mock_print:
            utils.print_success("Test message")
            mock_print.assert_called_once()

    def test_print_error_calls_console(self) -> None:
        """Test print_error uses console"""
        from src.presentation.cli import utils

        with patch.object(utils.console, "print") as mock_print:
            utils.print_error("Error message")
            mock_print.assert_called_once()

    def test_print_warning_calls_console(self) -> None:
        """Test print_warning uses console"""
        from src.presentation.cli import utils

        with patch.object(utils.console, "print") as mock_print:
            utils.print_warning("Warning message")
            mock_print.assert_called_once()

    def test_print_info_calls_console(self) -> None:
        """Test print_info uses console"""
        from src.presentation.cli import utils

        with patch.object(utils.console, "print") as mock_print:
            utils.print_info("Info message")
            mock_print.assert_called_once()


class TestTableFunctions:
    """Test table creation and printing"""

    def test_create_table_function_exists(self) -> None:
        """Test create_table function exists"""
        from src.presentation.cli.utils import create_table

        assert create_table is not None

    def test_create_table_returns_table(self) -> None:
        """Test create_table returns Table object"""
        from src.presentation.cli.utils import create_table
        from rich.table import Table

        table = create_table("Test Table", ["Column1", "Column2"])

        assert isinstance(table, Table)

    def test_create_table_with_title(self) -> None:
        """Test create_table sets title"""
        from src.presentation.cli.utils import create_table

        table = create_table("Test Title", ["Col1"])

        assert table.title == "Test Title"

    def test_print_simulation_table_function_exists(self) -> None:
        """Test print_simulation_table function exists"""
        from src.presentation.cli.utils import print_simulation_table

        assert print_simulation_table is not None

    def test_print_simulation_table_with_data(self) -> None:
        """Test print_simulation_table with simulation data"""
        from src.presentation.cli import utils

        simulations = [
            {
                "simulation_id": "sim_123456789",
                "name": "Test Sim",
                "simulation_type": "CFD",
                "num_timesteps": 100,
                "created_at": "2025-01-01",
            }
        ]

        with patch.object(utils.console, "print") as mock_print:
            utils.print_simulation_table(simulations)
            mock_print.assert_called_once()

    def test_print_simulation_info_function_exists(self) -> None:
        """Test print_simulation_info function exists"""
        from src.presentation.cli.utils import print_simulation_info

        assert print_simulation_info is not None

    def test_print_simulation_info_with_data(self) -> None:
        """Test print_simulation_info with simulation data"""
        from src.presentation.cli import utils

        info = {
            "simulation_id": "sim_123",
            "name": "Test",
            "simulation_type": "CFD",
            "num_vertices": 1000,
            "num_timesteps": 50,
            "time_range": [0.0, 1.0],
            "fields": ["velocity", "pressure"],
        }

        with patch.object(utils.console, "print") as mock_print:
            utils.print_simulation_info(info)
            # Should print multiple times (header + fields)
            assert mock_print.call_count > 1

    def test_print_field_statistics_function_exists(self) -> None:
        """Test print_field_statistics function exists"""
        from src.presentation.cli.utils import print_field_statistics

        assert print_field_statistics is not None

    def test_print_field_statistics_with_data(self) -> None:
        """Test print_field_statistics with stats data"""
        from src.presentation.cli import utils

        stats = {"min": 0.0, "max": 10.0, "mean": 5.0, "std": 2.5}

        with patch.object(utils.console, "print") as mock_print:
            utils.print_field_statistics("velocity", stats)
            # Should print header and table
            assert mock_print.call_count >= 1

    def test_print_convergence_data_function_exists(self) -> None:
        """Test print_convergence_data function exists"""
        from src.presentation.cli.utils import print_convergence_data

        assert print_convergence_data is not None

    def test_print_convergence_data_with_data(self) -> None:
        """Test print_convergence_data with convergence data"""
        from src.presentation.cli import utils

        convergence = [
            {
                "timestep": 1,
                "time": 0.01,
                "rms_change": 0.001,
                "relative_change": 0.0001,
            },
            {
                "timestep": 2,
                "time": 0.02,
                "rms_change": 0.0005,
                "relative_change": 0.00005,
            },
        ]

        with patch.object(utils.console, "print") as mock_print:
            utils.print_convergence_data("velocity", convergence)
            assert mock_print.call_count >= 1


class TestProgressDecorator:
    """Test progress decorator"""

    def test_with_progress_function_exists(self) -> None:
        """Test with_progress decorator exists"""
        from src.presentation.cli.utils import with_progress

        assert with_progress is not None

    def test_with_progress_decorator(self) -> None:
        """Test with_progress decorator wraps function"""
        from src.presentation.cli.utils import with_progress

        @with_progress("Testing")
        def test_func() -> str:
            return "result"

        result = test_func()
        assert result == "result"

    def test_with_progress_preserves_function_output(self) -> None:
        """Test decorated function returns correct value"""
        from src.presentation.cli.utils import with_progress

        @with_progress("Processing")
        def add_numbers(a: int, b: int) -> int:
            return a + b

        result = add_numbers(2, 3)
        assert result == 5


class TestConsole:
    """Test console instance"""

    def test_console_exists(self) -> None:
        """Test console instance exists"""
        from src.presentation.cli.utils import console

        assert console is not None

    def test_console_is_rich_console(self) -> None:
        """Test console is Rich Console instance"""
        from src.presentation.cli.utils import console
        from rich.console import Console

        assert isinstance(console, Console)
