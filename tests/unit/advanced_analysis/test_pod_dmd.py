"""
Tests for POD and DMD analysis
"""

import pytest
import numpy as np

from src.core.advanced_analysis.pod import PODAnalyzer, compute_pod
from src.core.advanced_analysis.dmd import DMDAnalyzer, compute_dmd


def test_pod_analyzer_initialization() -> None:
    """Test POD analyzer initialization"""
    analyzer = PODAnalyzer(n_modes=5, energy_threshold=0.95, method="svd")

    assert analyzer.n_modes == 5
    assert analyzer.energy_threshold == 0.95
    assert analyzer.method == "svd"


def test_pod_simple_data() -> None:
    """Test POD on simple synthetic data"""
    # Create simple test data: traveling wave
    n_points = 100
    n_timesteps = 50

    x = np.linspace(0, 2 * np.pi, n_points)
    t = np.linspace(0, 1, n_timesteps)

    data = np.zeros((n_points, n_timesteps))
    for i, time in enumerate(t):
        data[:, i] = np.sin(x - 2 * np.pi * time)

    # Perform POD
    analyzer = PODAnalyzer(n_modes=3)
    result = analyzer.analyze(data)

    assert result.n_modes <= 3
    assert result.modes.shape[0] == n_points
    assert result.temporal_coefficients.shape[0] == n_timesteps
    assert len(result.eigenvalues) == result.n_modes
    assert np.all(result.cumulative_energy >= 0)
    assert np.all(result.cumulative_energy <= 1.0)


def test_pod_reconstruction() -> None:
    """Test POD reconstruction"""
    n_points = 50
    n_timesteps = 30

    # Random data
    data = np.random.randn(n_points, n_timesteps)

    analyzer = PODAnalyzer(n_modes=10)
    result = analyzer.analyze(data)

    # Reconstruct
    reconstructed = analyzer.reconstruct(result)

    # Should have same shape
    assert reconstructed.shape == data.shape


def test_pod_energy_threshold() -> None:
    """Test automatic mode selection by energy threshold"""
    n_points = 100
    n_timesteps = 50

    # Create low-rank data
    rank = 3
    data = np.random.randn(n_points, rank) @ np.random.randn(rank, n_timesteps)

    analyzer = PODAnalyzer(n_modes=None, energy_threshold=0.99)
    result = analyzer.analyze(data)

    # Should capture most energy with few modes
    assert result.n_modes <= 10


def test_dmd_analyzer_initialization() -> None:
    """Test DMD analyzer initialization"""
    analyzer = DMDAnalyzer(n_modes=5, dt=0.1, rank=10)

    assert analyzer.n_modes == 5
    assert analyzer.dt == 0.1
    assert analyzer.rank == 10


def test_dmd_simple_data() -> None:
    """Test DMD on simple synthetic data"""
    # Create simple oscillating data
    n_points = 50
    n_timesteps = 100
    dt = 0.01

    x = np.linspace(0, 2 * np.pi, n_points)
    t = np.arange(n_timesteps) * dt

    data = np.zeros((n_points, n_timesteps))
    for i, time in enumerate(t):
        data[:, i] = np.sin(x) * np.cos(2 * np.pi * 5.0 * time)

    # Perform DMD
    analyzer = DMDAnalyzer(n_modes=3, dt=dt)
    result = analyzer.analyze(data, method="exact")

    assert result.n_modes <= 3
    assert result.modes.shape[0] == n_points
    assert len(result.eigenvalues) == result.n_modes
    assert len(result.frequencies) == result.n_modes
    assert len(result.growth_rates) == result.n_modes


def test_dmd_reconstruction() -> None:
    """Test DMD reconstruction"""
    n_points = 30
    n_timesteps = 50
    dt = 0.1

    # Random data
    data = np.random.randn(n_points, n_timesteps)

    analyzer = DMDAnalyzer(n_modes=5, dt=dt)
    result = analyzer.analyze(data)

    # Reconstruct
    reconstructed = analyzer.reconstruct(result)

    # Should have compatible shape
    assert reconstructed.shape[0] == n_points


def test_compute_pod_convenience() -> None:
    """Test POD convenience function"""
    data = np.random.randn(50, 30)

    result = compute_pod(data, n_modes=5)

    assert result.n_modes <= 5
    assert result.modes.shape[0] == 50


def test_compute_dmd_convenience() -> None:
    """Test DMD convenience function"""
    data = np.random.randn(50, 30)

    result = compute_dmd(data, dt=0.1, n_modes=5)

    assert result.n_modes <= 5
    assert result.modes.shape[0] == 50
