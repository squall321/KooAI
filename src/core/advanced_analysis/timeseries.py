"""
Time series analysis

Provides statistical analysis of temporal data.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
from scipy import signal, stats


@dataclass
class TimeSeriesStats:
    """Time series statistics"""

    mean: float
    std: float
    variance: float
    skewness: float
    kurtosis: float
    min: float
    max: float
    range: float
    trend: Optional[Tuple[float, float]]  # (slope, intercept) if trend computed


class TimeSeriesAnalyzer:
    """
    Time series analyzer

    Performs statistical and temporal analysis of time-series data.
    """

    def compute_statistics(self, data: np.ndarray) -> TimeSeriesStats:
        """
        Compute comprehensive time series statistics

        Args:
            data: Time-series data (1D array)

        Returns:
            TimeSeriesStats
        """
        return TimeSeriesStats(
            mean=float(np.mean(data)),
            std=float(np.std(data)),
            variance=float(np.var(data)),
            skewness=float(stats.skew(data)),
            kurtosis=float(stats.kurtosis(data)),
            min=float(np.min(data)),
            max=float(np.max(data)),
            range=float(np.max(data) - np.min(data)),
            trend=None,
        )

    def compute_trend(
        self, data: np.ndarray, time: Optional[np.ndarray] = None
    ) -> Tuple[float, float, np.ndarray]:
        """
        Compute linear trend

        Args:
            data: Time-series data
            time: Time values (None = use indices)

        Returns:
            Tuple of (slope, intercept, detrended_data)
        """
        if time is None:
            time = np.arange(len(data))

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(time, data)

        # Compute trend line
        trend_line = slope * time + intercept

        # Detrend data
        detrended = data - trend_line

        return slope, intercept, detrended

    def compute_autocorrelation(
        self, data: np.ndarray, max_lag: Optional[int] = None, normalize: bool = True
    ) -> np.ndarray:
        """
        Compute autocorrelation function

        Args:
            data: Time-series data
            max_lag: Maximum lag (None = len(data) - 1)
            normalize: Whether to normalize autocorrelation

        Returns:
            Autocorrelation values
        """
        if max_lag is None:
            max_lag = len(data) - 1

        # Center the data
        data_centered = data - np.mean(data)

        # Compute autocorrelation
        autocorr = np.correlate(data_centered, data_centered, mode="full")
        autocorr = autocorr[len(autocorr) // 2 :]  # Take positive lags

        if normalize:
            autocorr /= autocorr[0]  # Normalize by variance

        return autocorr[: max_lag + 1]

    def detect_periodicity(
        self, data: np.ndarray, sampling_rate: float = 1.0
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        """
        Detect periodicity in time series

        Args:
            data: Time-series data
            sampling_rate: Sampling rate

        Returns:
            Tuple of (is_periodic, period, confidence)
        """
        # Compute autocorrelation
        autocorr = self.compute_autocorrelation(data, normalize=True)

        # Find peaks in autocorrelation (excluding lag 0)
        peaks, properties = signal.find_peaks(autocorr[1:], height=0.5)

        if len(peaks) > 0:
            # First significant peak indicates period
            period_samples = peaks[0] + 1
            period = period_samples / sampling_rate

            # Confidence based on peak height
            confidence = float(properties["peak_heights"][0])

            return True, period, confidence
        else:
            return False, None, None

    def compute_moving_average(
        self, data: np.ndarray, window_size: int, mode: str = "valid"
    ) -> np.ndarray:
        """
        Compute moving average

        Args:
            data: Time-series data
            window_size: Window size
            mode: Convolution mode ('valid', 'same', 'full')

        Returns:
            Smoothed data
        """
        window = np.ones(window_size) / window_size
        return np.convolve(data, window, mode=mode)

    def compute_exponential_smoothing(
        self, data: np.ndarray, alpha: float = 0.3
    ) -> np.ndarray:
        """
        Compute exponential smoothing

        Args:
            data: Time-series data
            alpha: Smoothing factor (0 < alpha <= 1)

        Returns:
            Smoothed data
        """
        smoothed = np.zeros_like(data)
        smoothed[0] = data[0]

        for i in range(1, len(data)):
            smoothed[i] = alpha * data[i] + (1 - alpha) * smoothed[i - 1]

        return smoothed

    def detect_outliers(
        self, data: np.ndarray, method: str = "zscore", threshold: float = 3.0
    ) -> np.ndarray:
        """
        Detect outliers in time series

        Args:
            data: Time-series data
            method: Detection method ('zscore', 'iqr', 'mad')
            threshold: Threshold for outlier detection

        Returns:
            Boolean array indicating outliers
        """
        if method == "zscore":
            z_scores = np.abs(stats.zscore(data))
            return z_scores > threshold

        elif method == "iqr":
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            return (data < lower_bound) | (data > upper_bound)

        elif method == "mad":
            median = np.median(data)
            mad = np.median(np.abs(data - median))
            modified_z = 0.6745 * (data - median) / mad
            return np.abs(modified_z) > threshold

        else:
            raise ValueError(f"Unknown method: {method}")


def compute_autocorrelation(
    data: np.ndarray, max_lag: Optional[int] = None
) -> np.ndarray:
    """
    Convenience function for autocorrelation

    Args:
        data: Time-series data
        max_lag: Maximum lag

    Returns:
        Autocorrelation values
    """
    analyzer = TimeSeriesAnalyzer()
    return analyzer.compute_autocorrelation(data, max_lag=max_lag)


def compute_statistics(data: np.ndarray) -> TimeSeriesStats:
    """
    Convenience function for time series statistics

    Args:
        data: Time-series data

    Returns:
        TimeSeriesStats
    """
    analyzer = TimeSeriesAnalyzer()
    return analyzer.compute_statistics(data)
