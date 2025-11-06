"""
Dynamic Mode Decomposition (DMD)

Extracts spatiotemporal coherent structures with associated frequencies and growth rates.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
from scipy import linalg


@dataclass
class DMDResult:
    """DMD analysis result"""

    modes: np.ndarray  # DMD modes (n_points, n_modes)
    eigenvalues: np.ndarray  # DMD eigenvalues (complex)
    amplitudes: np.ndarray  # Mode amplitudes
    frequencies: np.ndarray  # Mode frequencies (Hz)
    growth_rates: np.ndarray  # Mode growth rates
    omega: np.ndarray  # Continuous eigenvalues (ln(eigenvalues)/dt)
    n_modes: int  # Number of modes


class DMDAnalyzer:
    """
    DMD (Dynamic Mode Decomposition) analyzer

    Performs data-driven modal decomposition with temporal dynamics.
    """

    def __init__(
        self,
        n_modes: Optional[int] = None,
        dt: float = 1.0,
        rank: Optional[int] = None,
    ):
        """
        Initialize DMD analyzer

        Args:
            n_modes: Number of modes to compute (None = automatic)
            dt: Time step between snapshots
            rank: Truncation rank for SVD (None = full rank)
        """
        self.n_modes = n_modes
        self.dt = dt
        self.rank = rank

    def analyze(self, data: np.ndarray, method: str = "exact") -> DMDResult:
        """
        Perform DMD analysis

        Args:
            data: Snapshot matrix (n_points, n_timesteps)
            method: 'exact' or 'standard' DMD

        Returns:
            DMDResult with modes and dynamics
        """
        n_points, n_timesteps = data.shape

        # Split data into X (snapshots 0:m-1) and Y (snapshots 1:m)
        X = data[:, :-1]
        Y = data[:, 1:]

        if method == "exact":
            modes, eigenvalues, amplitudes = self._exact_dmd(X, Y)
        elif method == "standard":
            modes, eigenvalues, amplitudes = self._standard_dmd(X, Y)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Compute continuous-time eigenvalues
        omega = np.log(eigenvalues) / self.dt

        # Extract frequencies and growth rates
        frequencies = np.imag(omega) / (2 * np.pi)
        growth_rates = np.real(omega)

        # Truncate to requested number of modes
        if self.n_modes is not None:
            n_modes_selected = min(self.n_modes, len(eigenvalues))
            modes = modes[:, :n_modes_selected]
            eigenvalues = eigenvalues[:n_modes_selected]
            amplitudes = amplitudes[:n_modes_selected]
            frequencies = frequencies[:n_modes_selected]
            growth_rates = growth_rates[:n_modes_selected]
            omega = omega[:n_modes_selected]
        else:
            n_modes_selected = len(eigenvalues)

        return DMDResult(
            modes=modes,
            eigenvalues=eigenvalues,
            amplitudes=amplitudes,
            frequencies=frequencies,
            growth_rates=growth_rates,
            omega=omega,
            n_modes=n_modes_selected,
        )

    def _standard_dmd(
        self, X: np.ndarray, Y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Standard DMD algorithm

        Args:
            X: Snapshot matrix at t
            Y: Snapshot matrix at t+dt

        Returns:
            Tuple of (modes, eigenvalues, amplitudes)
        """
        # SVD of X
        U, S, Vt = linalg.svd(X, full_matrices=False)

        # Truncate if rank specified
        if self.rank is not None:
            U = U[:, : self.rank]
            S = S[: self.rank]
            Vt = Vt[: self.rank, :]

        # Compute reduced A matrix: A_tilde = U^T * Y * V * S^-1
        A_tilde = U.T @ Y @ Vt.T @ np.diag(1.0 / S)

        # Eigendecomposition of A_tilde
        eigenvalues, W = linalg.eig(A_tilde)

        # Compute DMD modes: Phi = Y * V * S^-1 * W
        modes = Y @ Vt.T @ np.diag(1.0 / S) @ W

        # Compute amplitudes (initial condition)
        amplitudes = linalg.lstsq(modes, X[:, 0])[0]

        return modes, eigenvalues, amplitudes

    def _exact_dmd(
        self, X: np.ndarray, Y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Exact DMD algorithm (more accurate modes)

        Args:
            X: Snapshot matrix at t
            Y: Snapshot matrix at t+dt

        Returns:
            Tuple of (modes, eigenvalues, amplitudes)
        """
        # SVD of X
        U, S, Vt = linalg.svd(X, full_matrices=False)

        # Truncate if rank specified
        if self.rank is not None:
            U = U[:, : self.rank]
            S = S[: self.rank]
            Vt = Vt[: self.rank, :]

        # Compute reduced A matrix
        A_tilde = U.T @ Y @ Vt.T @ np.diag(1.0 / S)

        # Eigendecomposition of A_tilde
        eigenvalues, W = linalg.eig(A_tilde)

        # Compute exact DMD modes: Phi = (1/lambda) * Y * V * S^-1 * W
        modes = Y @ Vt.T @ np.diag(1.0 / S) @ W

        # Normalize modes
        for i in range(modes.shape[1]):
            modes[:, i] /= eigenvalues[i]

        # Compute amplitudes
        amplitudes = linalg.lstsq(modes, X[:, 0])[0]

        return modes, eigenvalues, amplitudes

    def reconstruct(
        self, dmd_result: DMDResult, timesteps: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Reconstruct field from DMD modes

        Args:
            dmd_result: DMD result
            timesteps: Time values for reconstruction (None = use dt)

        Returns:
            Reconstructed field (n_points, n_timesteps)
        """
        if timesteps is None:
            timesteps = np.arange(len(dmd_result.amplitudes)) * self.dt

        # Reconstruct: x(t) = sum_i amplitudes_i * modes_i * exp(omega_i * t)
        n_points = dmd_result.modes.shape[0]
        n_times = len(timesteps)

        reconstruction = np.zeros((n_points, n_times), dtype=complex)

        for i in range(dmd_result.n_modes):
            time_dynamics = dmd_result.amplitudes[i] * np.exp(
                dmd_result.omega[i] * timesteps
            )
            reconstruction += dmd_result.modes[:, i : i + 1] @ time_dynamics[np.newaxis, :]

        # Return real part for real-valued data
        return np.real(reconstruction)

    def forecast(
        self, dmd_result: DMDResult, n_future_steps: int
    ) -> np.ndarray:
        """
        Forecast future states using DMD

        Args:
            dmd_result: DMD result
            n_future_steps: Number of future time steps

        Returns:
            Forecasted field (n_points, n_future_steps)
        """
        future_times = np.arange(n_future_steps) * self.dt
        return self.reconstruct(dmd_result, future_times)


def compute_dmd(
    data: np.ndarray,
    dt: float = 1.0,
    n_modes: Optional[int] = None,
    rank: Optional[int] = None,
    method: str = "exact",
) -> DMDResult:
    """
    Convenience function for DMD analysis

    Args:
        data: Snapshot matrix (n_points, n_timesteps)
        dt: Time step between snapshots
        n_modes: Number of modes to compute
        rank: Truncation rank for SVD
        method: 'exact' or 'standard'

    Returns:
        DMDResult
    """
    analyzer = DMDAnalyzer(n_modes=n_modes, dt=dt, rank=rank)
    return analyzer.analyze(data, method=method)
