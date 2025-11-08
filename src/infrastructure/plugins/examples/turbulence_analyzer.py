"""
Example Plugin: Turbulence Intensity Analyzer

Demonstrates how to create a custom analyzer plugin.
"""

from typing import Dict, Any
import numpy as np

from src.infrastructure.plugins.plugin_interface import (
    AnalyzerPlugin,
    PluginContext,
    PluginType,
    PluginPriority,
    plugin,
)


@plugin(
    name="turbulence-analyzer",
    version="1.0.0",
    description="Analyzes turbulence intensity from velocity fields",
    author="KooAI Team",
    plugin_type=PluginType.ANALYZER,
    priority=PluginPriority.HIGH,
    tags=["turbulence", "cfd", "velocity"],
)
class TurbulenceAnalyzer(AnalyzerPlugin):
    """
    Calculates turbulence intensity from velocity field data.

    Configuration:
        method: Calculation method ("rms" or "tke")
        threshold: Minimum turbulence intensity to flag
        reference_velocity: Reference velocity for normalization
    """

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with configuration."""
        self.method = config.get("method", "rms")
        self.threshold = config.get("threshold", 0.05)
        self.reference_velocity = config.get("reference_velocity", None)

        if self.method not in ["rms", "tke"]:
            raise ValueError("method must be 'rms' or 'tke'")

    async def analyze(
        self, simulation_data: Dict[str, Any], context: PluginContext
    ) -> Dict[str, Any]:
        """
        Analyze turbulence intensity.

        Args:
            simulation_data: Simulation data with velocity fields
            context: Plugin context

        Returns:
            Analysis results with turbulence metrics
        """
        # Extract velocity components
        u = np.array(simulation_data.get("velocity_x", []))
        v = np.array(simulation_data.get("velocity_y", []))
        w = np.array(simulation_data.get("velocity_z", []))

        if len(u) == 0:
            return {"error": "No velocity data found"}

        # Calculate mean velocities
        u_mean = np.mean(u)
        v_mean = np.mean(v)
        w_mean = np.mean(w)

        # Calculate velocity fluctuations
        u_prime = u - u_mean
        v_prime = v - v_mean
        w_prime = w - w_mean

        if self.method == "rms":
            # RMS of velocity fluctuations
            u_rms = np.sqrt(np.mean(u_prime ** 2))
            v_rms = np.sqrt(np.mean(v_prime ** 2))
            w_rms = np.sqrt(np.mean(w_prime ** 2))

            # Turbulence intensity
            turbulence_rms = np.sqrt((u_rms**2 + v_rms**2 + w_rms**2) / 3)

            # Reference velocity
            if self.reference_velocity is None:
                reference_velocity = np.sqrt(u_mean**2 + v_mean**2 + w_mean**2)
            else:
                reference_velocity = self.reference_velocity

            turbulence_intensity = turbulence_rms / reference_velocity if reference_velocity > 0 else 0

        else:  # tke method
            # Turbulent kinetic energy
            tke = 0.5 * np.mean(u_prime**2 + v_prime**2 + w_prime**2)
            reference_velocity = self.reference_velocity or np.sqrt(u_mean**2 + v_mean**2 + w_mean**2)
            turbulence_intensity = np.sqrt(2 * tke / 3) / reference_velocity if reference_velocity > 0 else 0

        # Check if above threshold
        is_turbulent = turbulence_intensity > self.threshold

        return {
            "turbulence_intensity": float(turbulence_intensity),
            "method": self.method,
            "threshold": self.threshold,
            "is_turbulent": is_turbulent,
            "mean_velocity": {
                "u": float(u_mean),
                "v": float(v_mean),
                "w": float(w_mean),
            },
            "statistics": {
                "min_intensity": float(np.min([u_rms, v_rms, w_rms])),
                "max_intensity": float(np.max([u_rms, v_rms, w_rms])),
                "data_points": len(u),
            },
        }
