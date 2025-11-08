"""
Advanced analysis methods for simulation data

Provides sophisticated analysis techniques including:
- Frequency domain analysis (FFT)
- Modal decomposition (POD, DMD)
- Time series analysis
- Correlation analysis
- Turbulence statistics
"""

from .fft import FFTAnalyzer, compute_fft, compute_power_spectrum
from .pod import PODAnalyzer, compute_pod
from .dmd import DMDAnalyzer, compute_dmd
from .timeseries import TimeSeriesAnalyzer, compute_autocorrelation, compute_statistics
from .correlation import CorrelationAnalyzer, compute_cross_correlation, compute_coherence
from .turbulence import (
    TurbulenceAnalyzer,
    compute_reynolds_stresses,
    compute_turbulent_kinetic_energy,
)

__all__ = [
    # FFT
    "FFTAnalyzer",
    "compute_fft",
    "compute_power_spectrum",
    # POD
    "PODAnalyzer",
    "compute_pod",
    # DMD
    "DMDAnalyzer",
    "compute_dmd",
    # Time Series
    "TimeSeriesAnalyzer",
    "compute_autocorrelation",
    "compute_statistics",
    # Correlation
    "CorrelationAnalyzer",
    "compute_cross_correlation",
    "compute_coherence",
    # Turbulence
    "TurbulenceAnalyzer",
    "compute_reynolds_stresses",
    "compute_turbulent_kinetic_energy",
]
