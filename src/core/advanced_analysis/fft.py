"""
Fast Fourier Transform (FFT) analysis

Provides frequency domain analysis for time-series simulation data.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq, rfft, rfftfreq


@dataclass
class FFTResult:
    """FFT analysis result"""

    frequencies: np.ndarray  # Frequency values
    amplitudes: np.ndarray  # Amplitude spectrum
    phases: np.ndarray  # Phase spectrum
    power_spectrum: np.ndarray  # Power spectral density
    dominant_frequency: float  # Most significant frequency
    sampling_rate: float  # Sampling rate used


class FFTAnalyzer:
    """
    FFT (Fast Fourier Transform) analyzer

    Performs frequency domain analysis on time-series data.
    """

    def __init__(self, sampling_rate: float = 1.0, window: Optional[str] = None):
        """
        Initialize FFT analyzer

        Args:
            sampling_rate: Sampling rate (Hz)
            window: Window function ('hann', 'hamming', 'blackman', None)
        """
        self.sampling_rate = sampling_rate
        self.window = window

    def analyze(
        self, data: np.ndarray, real_valued: bool = True
    ) -> FFTResult:
        """
        Perform FFT analysis

        Args:
            data: Time-series data (1D array)
            real_valued: If True, use real FFT (faster for real signals)

        Returns:
            FFTResult with frequency domain information
        """
        # Apply window if specified
        windowed_data = self._apply_window(data)

        # Compute FFT
        if real_valued:
            fft_values = rfft(windowed_data)
            frequencies = rfftfreq(len(data), 1.0 / self.sampling_rate)
        else:
            fft_values = fft(windowed_data)
            frequencies = fftfreq(len(data), 1.0 / self.sampling_rate)
            # Take only positive frequencies
            positive_freq_idx = frequencies >= 0
            fft_values = fft_values[positive_freq_idx]
            frequencies = frequencies[positive_freq_idx]

        # Compute amplitude and phase
        amplitudes = np.abs(fft_values)
        phases = np.angle(fft_values)

        # Compute power spectrum
        power_spectrum = amplitudes**2 / len(data)

        # Find dominant frequency
        dominant_idx = np.argmax(power_spectrum[1:]) + 1  # Skip DC component
        dominant_frequency = frequencies[dominant_idx]

        return FFTResult(
            frequencies=frequencies,
            amplitudes=amplitudes,
            phases=phases,
            power_spectrum=power_spectrum,
            dominant_frequency=dominant_frequency,
            sampling_rate=self.sampling_rate,
        )

    def compute_spectrogram(
        self,
        data: np.ndarray,
        nperseg: Optional[int] = None,
        noverlap: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute spectrogram (time-frequency representation)

        Args:
            data: Time-series data
            nperseg: Length of each segment
            noverlap: Number of points to overlap

        Returns:
            Tuple of (frequencies, times, spectrogram)
        """
        if nperseg is None:
            nperseg = min(256, len(data) // 8)

        if noverlap is None:
            noverlap = nperseg // 2

        frequencies, times, spectrogram = signal.spectrogram(
            data,
            fs=self.sampling_rate,
            window=self.window or "hann",
            nperseg=nperseg,
            noverlap=noverlap,
        )

        return frequencies, times, spectrogram

    def _apply_window(self, data: np.ndarray) -> np.ndarray:
        """Apply window function to data"""
        if self.window is None:
            return data

        n = len(data)

        if self.window == "hann":
            window = np.hanning(n)
        elif self.window == "hamming":
            window = np.hamming(n)
        elif self.window == "blackman":
            window = np.blackman(n)
        else:
            raise ValueError(f"Unknown window type: {self.window}")

        return data * window


def compute_fft(
    data: np.ndarray,
    sampling_rate: float = 1.0,
    window: Optional[str] = "hann",
) -> FFTResult:
    """
    Convenience function for FFT analysis

    Args:
        data: Time-series data
        sampling_rate: Sampling rate (Hz)
        window: Window function

    Returns:
        FFTResult
    """
    analyzer = FFTAnalyzer(sampling_rate=sampling_rate, window=window)
    return analyzer.analyze(data)


def compute_power_spectrum(
    data: np.ndarray,
    sampling_rate: float = 1.0,
    method: str = "welch",
    nperseg: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute power spectral density

    Args:
        data: Time-series data
        sampling_rate: Sampling rate
        method: 'welch' or 'periodogram'
        nperseg: Segment length for Welch method

    Returns:
        Tuple of (frequencies, power_spectrum)
    """
    if method == "welch":
        if nperseg is None:
            nperseg = min(256, len(data) // 8)

        frequencies, psd = signal.welch(
            data,
            fs=sampling_rate,
            nperseg=nperseg,
            scaling="density",
        )
    elif method == "periodogram":
        frequencies, psd = signal.periodogram(
            data,
            fs=sampling_rate,
            scaling="density",
        )
    else:
        raise ValueError(f"Unknown method: {method}")

    return frequencies, psd


def compute_coherence(
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
