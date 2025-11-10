"""
Tests for time series and correlation analysis
"""

import pytest
import numpy as np

from src.core.advanced_analysis.timeseries import (
    TimeSeriesAnalyzer,
    compute_autocorrelation,
    compute_statistics,
)
from src.core.advanced_analysis.correlation import (
    CorrelationAnalyzer,
    compute_cross_correlation,
    compute_coherence,
)


def test_timeseries_statistics() -> None:
    """Test time series statistics computation"""
    data = np.array([1, 2, 3, 4, 5, 4, 3, 2, 1])

    stats = compute_statistics(data)

    assert stats.mean == pytest.approx(np.mean(data))
    assert stats.std == pytest.approx(np.std(data))
    assert stats.variance == pytest.approx(np.var(data))
    assert stats.min == 1
    assert stats.max == 5
    assert stats.range == 4


def test_autocorrelation() -> None:
    """Test autocorrelation computation"""
    # Create periodic signal
    t = np.linspace(0, 10, 100)
    signal = np.sin(2 * np.pi * t)

    autocorr = compute_autocorrelation(signal, max_lag=50)

    assert len(autocorr) == 51  # max_lag + 1
    assert autocorr[0] == pytest.approx(1.0)  # Normalized autocorrelation at lag 0


def test_moving_average() -> None:
    """Test moving average"""
    data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    analyzer = TimeSeriesAnalyzer()
    smoothed = analyzer.compute_moving_average(data, window_size=3, mode="valid")

    assert len(smoothed) == len(data) - 2  # 'valid' mode


def test_outlier_detection() -> None:
    """Test outlier detection"""
    # Normal data with outliers
    data = np.concatenate([np.random.randn(100), [10, -10, 15]])

    analyzer = TimeSeriesAnalyzer()
    outliers = analyzer.detect_outliers(data, method="zscore", threshold=3.0)

    # Should detect the added outliers
    assert np.sum(outliers) >= 3


def test_cross_correlation() -> None:
    """Test cross-correlation"""
    # Create two similar signals
    t = np.linspace(0, 1, 100)
    signal1 = np.sin(2 * np.pi * 5 * t)
    signal2 = np.sin(2 * np.pi * 5 * t + 0.1)  # Slightly phase-shifted

    corr = compute_cross_correlation(signal1, signal2, normalize=True)

    assert len(corr) > 0
    assert np.max(np.abs(corr)) <= 1.0  # Normalized


def test_pearson_correlation() -> None:
    """Test Pearson correlation"""
    # Perfect linear relationship
    x = np.array([1, 2, 3, 4, 5])
    y = 2 * x + 1

    analyzer = CorrelationAnalyzer()
    corr, p_value = analyzer.compute_pearson_correlation(x, y)

    assert corr == pytest.approx(1.0, abs=1e-6)
    assert p_value < 0.05


def test_correlation_matrix() -> None:
    """Test correlation matrix"""
    # Multivariate data
    data = np.random.randn(100, 5)

    analyzer = CorrelationAnalyzer()
    corr_matrix = analyzer.compute_correlation_matrix(data)

    assert corr_matrix.shape == (5, 5)
    assert np.allclose(np.diag(corr_matrix), 1.0)  # Diagonal should be 1


def test_lagged_correlation() -> None:
    """Test lagged correlation"""
    # Create two signals with known lag
    t = np.linspace(0, 10, 100)
    signal1 = np.sin(2 * np.pi * t)
    signal2 = np.sin(2 * np.pi * (t - 0.25))  # Lagged

    analyzer = CorrelationAnalyzer()
    lags, correlations = analyzer.compute_lagged_correlation(signal1, signal2, max_lag=20)

    assert len(lags) == len(correlations)
    assert len(lags) == 41  # -20 to +20


def test_periodicity_detection() -> None:
    """Test periodicity detection"""
    # Create periodic signal
    t = np.linspace(0, 10, 1000)
    signal = np.sin(2 * np.pi * 5 * t)  # 5 Hz signal

    analyzer = TimeSeriesAnalyzer()
    is_periodic, period, confidence = analyzer.detect_periodicity(signal, sampling_rate=100.0)

    assert is_periodic is True
    if period is not None:
        assert period == pytest.approx(0.2, abs=0.05)  # 1/5 Hz = 0.2 seconds
