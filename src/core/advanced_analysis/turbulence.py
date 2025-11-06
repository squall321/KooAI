"""
Turbulence statistics analysis

Provides turbulence-specific analysis including Reynolds stresses and TKE.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


@dataclass
class ReynoldsStresses:
    """Reynolds stress tensor components"""

    uu: np.ndarray  # <u'u'>
    vv: np.ndarray  # <v'v'>
    ww: np.ndarray  # <w'w'>
    uv: np.ndarray  # <u'v'>
    uw: np.ndarray  # <u'w'>
    vw: np.ndarray  # <v'w'>


@dataclass
class TurbulenceStats:
    """Turbulence statistics"""

    mean_velocity: np.ndarray  # Mean velocity field (3, n_points)
    reynolds_stresses: ReynoldsStresses  # Reynolds stresses
    tke: np.ndarray  # Turbulent kinetic energy
    turbulent_intensity: np.ndarray  # Turbulence intensity
    dissipation_rate: Optional[np.ndarray] = None  # Dissipation rate (if computed)


class TurbulenceAnalyzer:
    """
    Turbulence statistics analyzer

    Computes Reynolds-averaged statistics for turbulent flows.
    """

    def compute_reynolds_stresses(
        self, velocity_snapshots: np.ndarray
    ) -> ReynoldsStresses:
        """
        Compute Reynolds stress tensor

        Args:
            velocity_snapshots: Velocity snapshots (n_points, n_components, n_timesteps)
                               where n_components = 3 for 3D (u, v, w)

        Returns:
            ReynoldsStresses object
        """
        n_points, n_components, n_timesteps = velocity_snapshots.shape

        # Compute mean velocities
        mean_velocity = np.mean(velocity_snapshots, axis=2)

        # Compute fluctuations: u' = u - <u>
        fluctuations = velocity_snapshots - mean_velocity[:, :, np.newaxis]

        # Extract components
        u_prime = fluctuations[:, 0, :]
        v_prime = fluctuations[:, 1, :] if n_components > 1 else np.zeros_like(u_prime)
        w_prime = fluctuations[:, 2, :] if n_components > 2 else np.zeros_like(u_prime)

        # Compute Reynolds stresses: <u'_i u'_j>
        uu = np.mean(u_prime * u_prime, axis=1)
        vv = np.mean(v_prime * v_prime, axis=1)
        ww = np.mean(w_prime * w_prime, axis=1)
        uv = np.mean(u_prime * v_prime, axis=1)
        uw = np.mean(u_prime * w_prime, axis=1)
        vw = np.mean(v_prime * w_prime, axis=1)

        return ReynoldsStresses(uu=uu, vv=vv, ww=ww, uv=uv, uw=uw, vw=vw)

    def compute_turbulent_kinetic_energy(
        self, reynolds_stresses: ReynoldsStresses
    ) -> np.ndarray:
        """
        Compute turbulent kinetic energy: TKE = 0.5 * (uu + vv + ww)

        Args:
            reynolds_stresses: Reynolds stress tensor

        Returns:
            Turbulent kinetic energy field
        """
        tke = 0.5 * (
            reynolds_stresses.uu + reynolds_stresses.vv + reynolds_stresses.ww
        )
        return tke

    def compute_turbulent_intensity(
        self, reynolds_stresses: ReynoldsStresses, mean_velocity: np.ndarray
    ) -> np.ndarray:
        """
        Compute turbulence intensity: I = sqrt(2*TKE/3) / |U_mean|

        Args:
            reynolds_stresses: Reynolds stress tensor
            mean_velocity: Mean velocity field (n_points, 3)

        Returns:
            Turbulence intensity
        """
        tke = self.compute_turbulent_kinetic_energy(reynolds_stresses)

        # Compute mean velocity magnitude
        u_mag = np.linalg.norm(mean_velocity, axis=1)

        # Avoid division by zero
        u_mag = np.maximum(u_mag, 1e-10)

        intensity = np.sqrt(2 * tke / 3) / u_mag

        return intensity

    def compute_dissipation_rate(
        self,
        velocity_snapshots: np.ndarray,
        viscosity: float,
        method: str = "gradient",
    ) -> np.ndarray:
        """
        Compute turbulent dissipation rate

        Args:
            velocity_snapshots: Velocity snapshots
            viscosity: Kinematic viscosity
            method: Computation method ('gradient', 'spectral')

        Returns:
            Dissipation rate field
        """
        if method == "gradient":
            # Simplified: epsilon ≈ nu * <(du/dx)^2>
            # This is a rough approximation
            n_points, n_components, n_timesteps = velocity_snapshots.shape

            # Compute spatial gradients (simplified 1D approximation)
            dissipation = np.zeros(n_points)

            for comp in range(n_components):
                for t in range(n_timesteps):
                    grad = np.gradient(velocity_snapshots[:, comp, t])
                    dissipation += grad**2

            dissipation *= viscosity / n_timesteps

            return dissipation

        elif method == "spectral":
            # TODO: Implement spectral method
            raise NotImplementedError("Spectral dissipation not yet implemented")

        else:
            raise ValueError(f"Unknown method: {method}")

    def analyze(
        self, velocity_snapshots: np.ndarray, viscosity: Optional[float] = None
    ) -> TurbulenceStats:
        """
        Comprehensive turbulence analysis

        Args:
            velocity_snapshots: Velocity snapshots (n_points, n_components, n_timesteps)
            viscosity: Kinematic viscosity (optional, for dissipation)

        Returns:
            TurbulenceStats object
        """
        # Compute mean velocity
        mean_velocity = np.mean(velocity_snapshots, axis=2)

        # Compute Reynolds stresses
        reynolds_stresses = self.compute_reynolds_stresses(velocity_snapshots)

        # Compute TKE
        tke = self.compute_turbulent_kinetic_energy(reynolds_stresses)

        # Compute turbulence intensity
        turbulent_intensity = self.compute_turbulent_intensity(
            reynolds_stresses, mean_velocity
        )

        # Compute dissipation rate if viscosity provided
        dissipation_rate = None
        if viscosity is not None:
            dissipation_rate = self.compute_dissipation_rate(
                velocity_snapshots, viscosity
            )

        return TurbulenceStats(
            mean_velocity=mean_velocity,
            reynolds_stresses=reynolds_stresses,
            tke=tke,
            turbulent_intensity=turbulent_intensity,
            dissipation_rate=dissipation_rate,
        )

    def compute_anisotropy_tensor(
        self, reynolds_stresses: ReynoldsStresses
    ) -> np.ndarray:
        """
        Compute Reynolds stress anisotropy tensor

        Args:
            reynolds_stresses: Reynolds stress tensor

        Returns:
            Anisotropy tensor (n_points, 3, 3)
        """
        n_points = len(reynolds_stresses.uu)

        # Construct Reynolds stress tensor
        R = np.zeros((n_points, 3, 3))
        R[:, 0, 0] = reynolds_stresses.uu
        R[:, 1, 1] = reynolds_stresses.vv
        R[:, 2, 2] = reynolds_stresses.ww
        R[:, 0, 1] = R[:, 1, 0] = reynolds_stresses.uv
        R[:, 0, 2] = R[:, 2, 0] = reynolds_stresses.uw
        R[:, 1, 2] = R[:, 2, 1] = reynolds_stresses.vw

        # Compute TKE
        tke = 0.5 * (reynolds_stresses.uu + reynolds_stresses.vv + reynolds_stresses.ww)

        # Anisotropy tensor: b_ij = R_ij / (2*TKE) - delta_ij / 3
        b = np.zeros_like(R)

        for i in range(n_points):
            if tke[i] > 1e-10:
                b[i] = R[i] / (2 * tke[i])
                b[i, 0, 0] -= 1.0 / 3.0
                b[i, 1, 1] -= 1.0 / 3.0
                b[i, 2, 2] -= 1.0 / 3.0

        return b

    def compute_invariants(self, anisotropy_tensor: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute invariants of anisotropy tensor

        Args:
            anisotropy_tensor: Anisotropy tensor (n_points, 3, 3)

        Returns:
            Tuple of (second_invariant, third_invariant)
        """
        n_points = anisotropy_tensor.shape[0]

        second_invariant = np.zeros(n_points)
        third_invariant = np.zeros(n_points)

        for i in range(n_points):
            b = anisotropy_tensor[i]

            # Second invariant: II = b_ij * b_ji
            second_invariant[i] = np.trace(b @ b)

            # Third invariant: III = b_ij * b_jk * b_ki
            third_invariant[i] = np.trace(b @ b @ b)

        return second_invariant, third_invariant


def compute_reynolds_stresses(velocity_snapshots: np.ndarray) -> ReynoldsStresses:
    """
    Convenience function for Reynolds stresses

    Args:
        velocity_snapshots: Velocity snapshots

    Returns:
        ReynoldsStresses
    """
    analyzer = TurbulenceAnalyzer()
    return analyzer.compute_reynolds_stresses(velocity_snapshots)


def compute_turbulent_kinetic_energy(velocity_snapshots: np.ndarray) -> np.ndarray:
    """
    Convenience function for TKE

    Args:
        velocity_snapshots: Velocity snapshots

    Returns:
        Turbulent kinetic energy
    """
    analyzer = TurbulenceAnalyzer()
    reynolds_stresses = analyzer.compute_reynolds_stresses(velocity_snapshots)
    return analyzer.compute_turbulent_kinetic_energy(reynolds_stresses)
