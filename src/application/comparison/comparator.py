"""
Simulation comparator

Compare multiple simulation results and analyze differences
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np

from src.core.domain.simulation import SimulationResult


@dataclass
class ComparisonResult:
    """Result of simulation comparison"""
    
    simulation_ids: List[str]
    field_name: str
    comparison_type: str
    
    # Statistical comparison
    mean_difference: float
    max_difference: float
    min_difference: float
    rmse: float  # Root Mean Square Error
    correlation: float
    
    # Spatial distribution
    difference_histogram: Optional[Dict[str, Any]] = None
    spatial_diff_map: Optional[np.ndarray] = None
    
    # Metadata
    compared_at: datetime = None
    
    def __post_init__(self):
        if self.compared_at is None:
            self.compared_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "simulation_ids": self.simulation_ids,
            "field_name": self.field_name,
            "comparison_type": self.comparison_type,
            "mean_difference": float(self.mean_difference),
            "max_difference": float(self.max_difference),
            "min_difference": float(self.min_difference),
            "rmse": float(self.rmse),
            "correlation": float(self.correlation),
            "difference_histogram": self.difference_histogram,
            "compared_at": self.compared_at.isoformat(),
        }


class SimulationComparator:
    """
    Compare simulation results
    
    Features:
    - Field-wise comparison
    - Statistical analysis
    - Difference mapping
    - Multi-simulation comparison
    """
    
    def compare_fields(
        self,
        sim1: SimulationResult,
        sim2: SimulationResult,
        field_name: str,
    ) -> ComparisonResult:
        """
        Compare a specific field between two simulations
        
        Args:
            sim1: First simulation
            sim2: Second simulation
            field_name: Name of field to compare
            
        Returns:
            ComparisonResult with comparison metrics
        """
        # Get field data
        field1 = sim1.data.fields.get(field_name)
        field2 = sim2.data.fields.get(field_name)
        
        if field1 is None or field2 is None:
            raise ValueError(f"Field '{field_name}' not found in one or both simulations")
        
        # Ensure same shape
        if field1.shape != field2.shape:
            raise ValueError(
                f"Field shapes don't match: {field1.shape} vs {field2.shape}"
            )
        
        # Calculate differences
        diff = field2 - field1
        abs_diff = np.abs(diff)
        
        # Statistical metrics
        mean_diff = np.mean(diff)
        max_diff = np.max(abs_diff)
        min_diff = np.min(abs_diff)
        rmse = np.sqrt(np.mean(diff**2))
        
        # Correlation
        correlation = np.corrcoef(field1.flatten(), field2.flatten())[0, 1]
        
        # Difference histogram
        hist, bin_edges = np.histogram(diff, bins=50)
        histogram = {
            "counts": hist.tolist(),
            "bin_edges": bin_edges.tolist(),
        }
        
        return ComparisonResult(
            simulation_ids=[sim1.simulation_id, sim2.simulation_id],
            field_name=field_name,
            comparison_type="field_comparison",
            mean_difference=mean_diff,
            max_difference=max_diff,
            min_difference=min_diff,
            rmse=rmse,
            correlation=correlation,
            difference_histogram=histogram,
            spatial_diff_map=diff,
        )
    
    def compare_all_fields(
        self,
        sim1: SimulationResult,
        sim2: SimulationResult,
    ) -> Dict[str, ComparisonResult]:
        """
        Compare all common fields between two simulations
        
        Args:
            sim1: First simulation
            sim2: Second simulation
            
        Returns:
            Dictionary mapping field names to comparison results
        """
        # Find common fields
        fields1 = set(sim1.data.fields.keys())
        fields2 = set(sim2.data.fields.keys())
        common_fields = fields1.intersection(fields2)
        
        if not common_fields:
            raise ValueError("No common fields found between simulations")
        
        # Compare each field
        results = {}
        for field_name in common_fields:
            try:
                results[field_name] = self.compare_fields(sim1, sim2, field_name)
            except Exception as e:
                # Skip fields that can't be compared
                print(f"Warning: Could not compare field '{field_name}': {e}")
        
        return results
    
    def compare_multiple(
        self,
        simulations: List[SimulationResult],
        field_name: str,
    ) -> Dict[str, Any]:
        """
        Compare a field across multiple simulations
        
        Args:
            simulations: List of simulations to compare
            field_name: Field name to compare
            
        Returns:
            Dictionary with comparison statistics
        """
        if len(simulations) < 2:
            raise ValueError("Need at least 2 simulations to compare")
        
        # Extract field data from all simulations
        field_data = []
        sim_ids = []
        
        for sim in simulations:
            field = sim.data.fields.get(field_name)
            if field is None:
                raise ValueError(
                    f"Field '{field_name}' not found in simulation {sim.simulation_id}"
                )
            field_data.append(field.flatten())
            sim_ids.append(sim.simulation_id)
        
        # Stack all fields
        stacked = np.stack(field_data)
        
        # Calculate statistics across simulations
        mean_values = np.mean(stacked, axis=0)
        std_values = np.std(stacked, axis=0)
        min_values = np.min(stacked, axis=0)
        max_values = np.max(stacked, axis=0)
        range_values = max_values - min_values
        
        # Overall statistics
        overall_stats = {
            "simulation_ids": sim_ids,
            "field_name": field_name,
            "num_simulations": len(simulations),
            "mean_of_means": float(np.mean(mean_values)),
            "mean_of_stds": float(np.mean(std_values)),
            "mean_range": float(np.mean(range_values)),
            "max_range": float(np.max(range_values)),
            "correlation_matrix": self._calculate_correlation_matrix(field_data),
        }
        
        return overall_stats
    
    def calculate_convergence(
        self,
        simulations: List[SimulationResult],
        field_name: str,
        reference_idx: int = -1,
    ) -> Dict[str, Any]:
        """
        Calculate convergence metrics comparing simulations to a reference
        
        Useful for mesh refinement studies or iterative simulations
        
        Args:
            simulations: List of simulations (ordered by refinement/iteration)
            field_name: Field to analyze
            reference_idx: Index of reference simulation (default: last one)
            
        Returns:
            Convergence metrics
        """
        if len(simulations) < 2:
            raise ValueError("Need at least 2 simulations for convergence analysis")
        
        reference = simulations[reference_idx]
        ref_field = reference.data.fields[field_name]
        
        convergence_metrics = []
        
        for i, sim in enumerate(simulations[:-1]):
            field = sim.data.fields[field_name]
            
            # Interpolate or resize if needed
            if field.shape != ref_field.shape:
                # For now, skip if shapes don't match
                # In production, would need interpolation
                continue
            
            # Calculate error metrics
            diff = field - ref_field
            l2_error = np.sqrt(np.mean(diff**2))
            l_inf_error = np.max(np.abs(diff))
            
            convergence_metrics.append({
                "simulation_id": sim.simulation_id,
                "l2_error": float(l2_error),
                "l_inf_error": float(l_inf_error),
                "relative_l2_error": float(l2_error / np.max(np.abs(ref_field))),
            })
        
        return {
            "reference_simulation_id": reference.simulation_id,
            "field_name": field_name,
            "metrics": convergence_metrics,
        }
    
    def identify_differences(
        self,
        sim1: SimulationResult,
        sim2: SimulationResult,
        field_name: str,
        threshold: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Identify regions where two simulations differ significantly
        
        Args:
            sim1: First simulation
            sim2: Second simulation
            field_name: Field to compare
            threshold: Relative difference threshold (default: 10%)
            
        Returns:
            Information about different regions
        """
        field1 = sim1.data.fields[field_name]
        field2 = sim2.data.fields[field_name]
        
        # Calculate relative difference
        mean_val = (np.abs(field1) + np.abs(field2)) / 2
        mean_val = np.where(mean_val == 0, 1e-10, mean_val)  # Avoid division by zero
        
        rel_diff = np.abs(field2 - field1) / mean_val
        
        # Find points exceeding threshold
        significant_diff_mask = rel_diff > threshold
        num_significant = np.sum(significant_diff_mask)
        percentage_significant = (num_significant / rel_diff.size) * 100
        
        # Statistics of significant differences
        if num_significant > 0:
            significant_diffs = rel_diff[significant_diff_mask]
            max_rel_diff = float(np.max(significant_diffs))
            mean_rel_diff = float(np.mean(significant_diffs))
        else:
            max_rel_diff = 0.0
            mean_rel_diff = 0.0
        
        return {
            "simulation_ids": [sim1.simulation_id, sim2.simulation_id],
            "field_name": field_name,
            "threshold": threshold,
            "num_significant_differences": int(num_significant),
            "percentage_significant": float(percentage_significant),
            "max_relative_difference": max_rel_diff,
            "mean_relative_difference": mean_rel_diff,
            "difference_mask": significant_diff_mask,
        }
    
    def _calculate_correlation_matrix(
        self, field_data: List[np.ndarray]
    ) -> List[List[float]]:
        """Calculate correlation matrix between all field pairs"""
        n = len(field_data)
        corr_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    corr = np.corrcoef(field_data[i], field_data[j])[0, 1]
                    corr_matrix[i, j] = corr
        
        return corr_matrix.tolist()
