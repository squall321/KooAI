"""
Proper Orthogonal Decomposition (POD)

Also known as Principal Component Analysis (PCA) or Karhunen-Loève decomposition.
Extracts dominant spatial modes from time-series data.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
from scipy import linalg


@dataclass
class PODResult:
    """POD analysis result"""

    modes: np.ndarray  # Spatial modes (n_points, n_modes)
    temporal_coefficients: np.ndarray  # Temporal coefficients (n_timesteps, n_modes)
    eigenvalues: np.ndarray  # Eigenvalues (energy of each mode)
    cumulative_energy: np.ndarray  # Cumulative energy ratio
    mean_field: np.ndarray  # Mean field (n_points,)
    n_modes: int  # Number of modes computed


class PODAnalyzer:
    """
    POD (Proper Orthogonal Decomposition) analyzer

    Performs modal decomposition to extract dominant coherent structures.
    """

    def __init__(
        self,
        n_modes: Optional[int] = None,
        energy_threshold: float = 0.99,
        method: str = "svd",
    ):
        """
        Initialize POD analyzer

        Args:
            n_modes: Number of modes to compute (None = automatic)
            energy_threshold: Energy threshold for automatic mode selection
            method: Decomposition method ('svd', 'correlation', 'snapshot')
        """
        self.n_modes = n_modes
        self.energy_threshold = energy_threshold
        self.method = method

    def analyze(self, data: np.ndarray, subtract_mean: bool = True) -> PODResult:
        """
        Perform POD analysis

        Args:
            data: Snapshot matrix (n_points, n_timesteps)
            subtract_mean: Whether to subtract mean field

        Returns:
            PODResult with modes and coefficients
        """
        n_points, n_timesteps = data.shape

        # Subtract mean field
        if subtract_mean:
            mean_field = np.mean(data, axis=1)
            data_centered = data - mean_field[:, np.newaxis]
        else:
            mean_field = np.zeros(n_points)
            data_centered = data.copy()

        # Perform decomposition based on method
        if self.method == "svd":
            modes, temporal_coefficients, eigenvalues = self._svd_method(data_centered)
        elif self.method == "correlation":
            modes, temporal_coefficients, eigenvalues = self._correlation_method(data_centered)
        elif self.method == "snapshot":
            modes, temporal_coefficients, eigenvalues = self._snapshot_method(data_centered)
        else:
            raise ValueError(f"Unknown method: {self.method}")

        # Determine number of modes
        cumulative_energy = np.cumsum(eigenvalues) / np.sum(eigenvalues)

        if self.n_modes is None:
            # Auto-select based on energy threshold
            n_modes_selected = np.searchsorted(cumulative_energy, self.energy_threshold) + 1
        else:
            n_modes_selected = min(self.n_modes, len(eigenvalues))

        # Truncate to selected modes
        modes = modes[:, :n_modes_selected]
        temporal_coefficients = temporal_coefficients[:, :n_modes_selected]
        eigenvalues = eigenvalues[:n_modes_selected]
        cumulative_energy = cumulative_energy[:n_modes_selected]

        return PODResult(
            modes=modes,
            temporal_coefficients=temporal_coefficients,
            eigenvalues=eigenvalues,
            cumulative_energy=cumulative_energy,
            mean_field=mean_field,
            n_modes=n_modes_selected,
        )

    def _svd_method(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        SVD-based POD (most accurate, slower for large data)

        Args:
            data: Centered snapshot matrix (n_points, n_timesteps)

        Returns:
            Tuple of (modes, temporal_coefficients, eigenvalues)
        """
        # Perform SVD: data = U * S * V^T
        U, S, Vt = linalg.svd(data, full_matrices=False)

        modes = U
        temporal_coefficients = (S[:, np.newaxis] * Vt).T
        eigenvalues = S**2 / data.shape[1]

        return modes, temporal_coefficients, eigenvalues

    def _correlation_method(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Correlation matrix method (better for n_points >> n_timesteps)

        Args:
            data: Centered snapshot matrix

        Returns:
            Tuple of (modes, temporal_coefficients, eigenvalues)
        """
        # Compute correlation matrix: C = data^T * data
        correlation_matrix = data.T @ data / data.shape[1]

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = linalg.eigh(correlation_matrix)

        # Sort by descending eigenvalues
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Compute spatial modes
        modes = data @ eigenvectors

        # Normalize modes
        for i in range(modes.shape[1]):
            norm = np.linalg.norm(modes[:, i])
            if norm > 1e-10:
                modes[:, i] /= norm

        temporal_coefficients = eigenvectors * np.sqrt(eigenvalues)[np.newaxis, :]

        return modes, temporal_coefficients, eigenvalues

    def _snapshot_method(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Snapshot method (better for n_timesteps >> n_points)

        Args:
            data: Centered snapshot matrix

        Returns:
            Tuple of (modes, temporal_coefficients, eigenvalues)
        """
        # Compute spatial correlation: C = data * data^T
        spatial_correlation = data @ data.T / data.shape[1]

        # Eigenvalue decomposition
        eigenvalues, modes = linalg.eigh(spatial_correlation)

        # Sort by descending eigenvalues
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        modes = modes[:, idx]

        # Compute temporal coefficients
        temporal_coefficients = modes.T @ data
        temporal_coefficients = temporal_coefficients.T

        return modes, temporal_coefficients, eigenvalues

    def reconstruct(self, pod_result: PODResult, n_modes: Optional[int] = None) -> np.ndarray:
        """
        Reconstruct field from POD modes

        Args:
            pod_result: POD result
            n_modes: Number of modes to use (None = all)

        Returns:
            Reconstructed field (n_points, n_timesteps)
        """
        if n_modes is None:
            n_modes = pod_result.n_modes
        else:
            n_modes = min(n_modes, pod_result.n_modes)

        # Reconstruct: data ≈ mean + modes * coefficients^T
        reconstruction = (
            pod_result.modes[:, :n_modes] @ pod_result.temporal_coefficients[:, :n_modes].T
        )
        reconstruction += pod_result.mean_field[:, np.newaxis]

        return reconstruction


def compute_pod(
    data: np.ndarray,
    n_modes: Optional[int] = None,
    energy_threshold: float = 0.99,
    method: str = "svd",
) -> PODResult:
    """
    Convenience function for POD analysis

    Args:
        data: Snapshot matrix (n_points, n_timesteps)
        n_modes: Number of modes to compute
        energy_threshold: Energy threshold for mode selection
        method: Decomposition method

    Returns:
        PODResult
    """
    analyzer = PODAnalyzer(n_modes=n_modes, energy_threshold=energy_threshold, method=method)
    return analyzer.analyze(data)
