"""
Correlation analysis

Provides correlation and coherence analysis between signals.
"""

from typing import Optional, Tuple
import numpy as np
from scipy import signal, stats


class CorrelationAnalyzer:
    """
    Correlation analyzer

    Performs correlation analysis between multiple signals.
    """

    def compute_cross_correlation(
        self,
        x: np.ndarray,
        y: np.ndarray,
        mode: str = "full",
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Compute cross-correlation between two signals

        Args:
            x: First signal
            y: Second signal
            mode: 'full', 'valid', or 'same'
            normalize: Whether to normalize correlation

        Returns:
            Cross-correlation values
        """
        if normalize:
            x_centered = x - np.mean(x)
            y_centered = y - np.mean(y)

            x_norm = x_centered / np.std(x)
            y_norm = y_centered / np.std(y)

            corr = np.correlate(x_norm, y_norm, mode=mode) / len(x)
        else:
            corr = np.correlate(x, y, mode=mode)

        return corr

    def compute_coherence(
        self,
        x: np.ndarray,
        y: np.ndarray,
        sampling_rate: float = 1.0,
        nperseg: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute coherence between two signals

        Args:
            x: First signal
            y: Second signal
            sampling_rate: Sampling rate
            nperseg: Segment length

        Returns:
            Tuple of (frequencies, coherence)
        """
        if nperseg is None:
            nperseg = min(256, len(x) // 8)

        frequencies, coherence = signal.coherence(
            x,
            y,
            fs=sampling_rate,
            nperseg=nperseg,
        )

        return frequencies, coherence

    def compute_cross_spectrum(
        self,
        x: np.ndarray,
        y: np.ndarray,
        sampling_rate: float = 1.0,
        nperseg: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute cross power spectral density

        Args:
            x: First signal
            y: Second signal
            sampling_rate: Sampling rate
            nperseg: Segment length

        Returns:
            Tuple of (frequencies, cross_spectrum)
        """
        if nperseg is None:
            nperseg = min(256, len(x) // 8)

        frequencies, cross_spectrum = signal.csd(
            x,
            y,
            fs=sampling_rate,
            nperseg=nperseg,
        )

        return frequencies, cross_spectrum

    def compute_pearson_correlation(
        self, x: np.ndarray, y: np.ndarray
    ) -> Tuple[float, float]:
        """
        Compute Pearson correlation coefficient

        Args:
            x: First signal
            y: Second signal

        Returns:
            Tuple of (correlation_coefficient, p_value)
        """
        corr, p_value = stats.pearsonr(x, y)
        return float(corr), float(p_value)

    def compute_spearman_correlation(
        self, x: np.ndarray, y: np.ndarray
    ) -> Tuple[float, float]:
        """
        Compute Spearman rank correlation coefficient

        Args:
            x: First signal
            y: Second signal

        Returns:
            Tuple of (correlation_coefficient, p_value)
        """
        corr, p_value = stats.spearmanr(x, y)
        return float(corr), float(p_value)

    def compute_mutual_information(
        self, x: np.ndarray, y: np.ndarray, bins: int = 50
    ) -> float:
        """
        Compute mutual information between signals

        Args:
            x: First signal
            y: Second signal
            bins: Number of bins for histogram

        Returns:
            Mutual information
        """
        # Create 2D histogram
        hist_2d, x_edges, y_edges = np.histogram2d(x, y, bins=bins)

        # Normalize to get probabilities
        pxy = hist_2d / float(np.sum(hist_2d))
        px = np.sum(pxy, axis=1)
        py = np.sum(pxy, axis=0)

        # Compute mutual information
        px_py = px[:, None] * py[None, :]

        # Avoid log(0)
        nzs = pxy > 0

        mi = np.sum(pxy[nzs] * np.log(pxy[nzs] / px_py[nzs]))

        return float(mi)

    def compute_lagged_correlation(
        self, x: np.ndarray, y: np.ndarray, max_lag: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute correlation at different lags

        Args:
            x: First signal
            y: Second signal
            max_lag: Maximum lag to compute

        Returns:
            Tuple of (lags, correlations)
        """
        lags = np.arange(-max_lag, max_lag + 1)
        correlations = np.zeros_like(lags, dtype=float)

        for i, lag in enumerate(lags):
            if lag < 0:
                # Negative lag: shift x backward (or y forward)
                overlap_x = x[: lag if lag != 0 else None]
                overlap_y = y[-lag :]
            elif lag > 0:
                # Positive lag: shift x forward (or y backward)
                overlap_x = x[lag:]
                overlap_y = y[:-lag]
            else:
                # No lag
                overlap_x = x
                overlap_y = y

            if len(overlap_x) > 0:
                correlations[i], _ = self.compute_pearson_correlation(
                    overlap_x, overlap_y
                )

        return lags, correlations

    def compute_correlation_matrix(self, data: np.ndarray) -> np.ndarray:
        """
        Compute correlation matrix for multivariate data

        Args:
            data: Data matrix (n_samples, n_variables)

        Returns:
            Correlation matrix (n_variables, n_variables)
        """
        return np.corrcoef(data.T)


def compute_cross_correlation(
    x: np.ndarray, y: np.ndarray, normalize: bool = True
) -> np.ndarray:
    """
    Convenience function for cross-correlation

    Args:
        x: First signal
        y: Second signal
        normalize: Whether to normalize

    Returns:
        Cross-correlation values
    """
    analyzer = CorrelationAnalyzer()
    return analyzer.compute_cross_correlation(x, y, normalize=normalize)


def compute_coherence(
    x: np.ndarray, y: np.ndarray, sampling_rate: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convenience function for coherence

    Args:
        x: First signal
        y: Second signal
        sampling_rate: Sampling rate

    Returns:
        Tuple of (frequencies, coherence)
    """
    analyzer = CorrelationAnalyzer()
    return analyzer.compute_coherence(x, y, sampling_rate=sampling_rate)
