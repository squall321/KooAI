"""
Tests for FFT analysis
"""

import pytest
import numpy as np

from src.core.advanced_analysis.fft import (
    FFTAnalyzer,
    compute_fft,
    compute_power_spectrum,
)


def test_fft_analyzer_initialization():
    """Test FFT analyzer initialization"""
    analyzer = FFTAnalyzer(sampling_rate=100.0, window="hann")

    assert analyzer.sampling_rate == 100.0
    assert analyzer.window == "hann"


def test_fft_sine_wave():
    """Test FFT on simple sine wave"""
    # Create sine wave: 10 Hz signal sampled at 1000 Hz
    sampling_rate = 1000.0
    duration = 1.0
    frequency = 10.0

    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    signal = np.sin(2 * np.pi * frequency * t)

    # Perform FFT
    analyzer = FFTAnalyzer(sampling_rate=sampling_rate)
    result = analyzer.analyze(signal)

    # Check dominant frequency
    assert result.dominant_frequency == pytest.approx(frequency, abs=0.5)
    assert len(result.frequencies) > 0
    assert len(result.amplitudes) == len(result.frequencies)


def test_fft_with_window():
    """Test FFT with windowing"""
    sampling_rate = 100.0
    t = np.linspace(0, 1.0, 100, endpoint=False)
    signal = np.sin(2 * np.pi * 5.0 * t)

    analyzer = FFTAnalyzer(sampling_rate=sampling_rate, window="hann")
    result = analyzer.analyze(signal)

    assert result is not None
    assert result.sampling_rate == sampling_rate


def test_compute_power_spectrum():
    """Test power spectrum computation"""
    sampling_rate = 100.0
    t = np.linspace(0, 10.0, 1000, endpoint=False)
    signal = np.sin(2 * np.pi * 5.0 * t) + 0.5 * np.sin(2 * np.pi * 10.0 * t)

    frequencies, psd = compute_power_spectrum(signal, sampling_rate=sampling_rate, method="welch")

    assert len(frequencies) > 0
    assert len(psd) == len(frequencies)
    assert np.all(psd >= 0)


def test_spectrogram():
    """Test spectrogram computation"""
    sampling_rate = 100.0
    t = np.linspace(0, 5.0, 500, endpoint=False)
    signal = np.sin(2 * np.pi * 10.0 * t)

    analyzer = FFTAnalyzer(sampling_rate=sampling_rate)
    frequencies, times, spectrogram = analyzer.compute_spectrogram(signal)

    assert len(frequencies) > 0
    assert len(times) > 0
    assert spectrogram.shape == (len(frequencies), len(times))


def test_fft_result_attributes():
    """Test FFT result has all expected attributes"""
    signal = np.random.randn(100)
    result = compute_fft(signal, sampling_rate=10.0)

    assert hasattr(result, "frequencies")
    assert hasattr(result, "amplitudes")
    assert hasattr(result, "phases")
    assert hasattr(result, "power_spectrum")
    assert hasattr(result, "dominant_frequency")
    assert hasattr(result, "sampling_rate")
