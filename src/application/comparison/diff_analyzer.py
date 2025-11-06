"""
Difference analyzer

Analyze and categorize differences between simulations
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np


class DifferenceType(Enum):
    """Types of differences"""
    NEGLIGIBLE = "negligible"  # < 1%
    SMALL = "small"  # 1-5%
    MODERATE = "moderate"  # 5-20%
    LARGE = "large"  # 20-50%
    CRITICAL = "critical"  # > 50%


@dataclass
class FieldDifference:
    """Detailed difference information for a field"""
    
    field_name: str
    
    # Overall metrics
    mean_absolute_diff: float
    mean_relative_diff: float
    max_absolute_diff: float
    max_relative_diff: float
    
    # Classification
    difference_type: DifferenceType
    
    # Spatial information
    regions_with_large_diff: int
    percentage_affected: float
    
    # Zones
    critical_zones: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "field_name": self.field_name,
            "mean_absolute_diff": float(self.mean_absolute_diff),
            "mean_relative_diff": float(self.mean_relative_diff),
            "max_absolute_diff": float(self.max_absolute_diff),
            "max_relative_diff": float(self.max_relative_diff),
            "difference_type": self.difference_type.value,
            "regions_with_large_diff": int(self.regions_with_large_diff),
            "percentage_affected": float(self.percentage_affected),
        }


class DifferenceAnalyzer:
    """
    Analyze differences between simulations
    
    Provides detailed analysis of where and how simulations differ
    """
    
    def __init__(
        self,
        negligible_threshold: float = 0.01,
        small_threshold: float = 0.05,
        moderate_threshold: float = 0.20,
        large_threshold: float = 0.50,
    ):
        """
        Initialize analyzer
        
        Args:
            negligible_threshold: Threshold for negligible differences (1%)
            small_threshold: Threshold for small differences (5%)
            moderate_threshold: Threshold for moderate differences (20%)
            large_threshold: Threshold for large differences (50%)
        """
        self.negligible_threshold = negligible_threshold
        self.small_threshold = small_threshold
        self.moderate_threshold = moderate_threshold
        self.large_threshold = large_threshold
    
    def analyze_field_difference(
        self,
        field1: np.ndarray,
        field2: np.ndarray,
        field_name: str,
    ) -> FieldDifference:
        """
        Analyze difference for a single field
        
        Args:
            field1: First field data
            field2: Second field data
            field_name: Name of the field
            
        Returns:
            FieldDifference with detailed analysis
        """
        # Calculate absolute and relative differences
        abs_diff = np.abs(field2 - field1)
        
        # Relative difference (avoid division by zero)
        denominator = np.maximum(np.abs(field1), 1e-10)
        rel_diff = abs_diff / denominator
        
        # Overall metrics
        mean_abs_diff = np.mean(abs_diff)
        mean_rel_diff = np.mean(rel_diff)
        max_abs_diff = np.max(abs_diff)
        max_rel_diff = np.max(rel_diff)
        
        # Classify difference type
        diff_type = self._classify_difference(mean_rel_diff)
        
        # Find critical zones (> 20% difference)
        critical_mask = rel_diff > self.moderate_threshold
        num_critical = np.sum(critical_mask)
        percentage_critical = (num_critical / rel_diff.size) * 100
        
        return FieldDifference(
            field_name=field_name,
            mean_absolute_diff=mean_abs_diff,
            mean_relative_diff=mean_rel_diff,
            max_absolute_diff=max_abs_diff,
            max_relative_diff=max_rel_diff,
            difference_type=diff_type,
            regions_with_large_diff=num_critical,
            percentage_affected=percentage_critical,
            critical_zones=critical_mask,
        )
    
    def analyze_all_fields(
        self,
        fields1: Dict[str, np.ndarray],
        fields2: Dict[str, np.ndarray],
    ) -> Dict[str, FieldDifference]:
        """
        Analyze differences for all common fields
        
        Args:
            fields1: First simulation fields
            fields2: Second simulation fields
            
        Returns:
            Dictionary of field differences
        """
        common_fields = set(fields1.keys()).intersection(set(fields2.keys()))
        
        results = {}
        for field_name in common_fields:
            if fields1[field_name].shape == fields2[field_name].shape:
                results[field_name] = self.analyze_field_difference(
                    fields1[field_name],
                    fields2[field_name],
                    field_name,
                )
        
        return results
    
    def generate_summary(
        self,
        differences: Dict[str, FieldDifference]
    ) -> Dict:
        """
        Generate summary of all differences
        
        Args:
            differences: Dictionary of field differences
            
        Returns:
            Summary dictionary
        """
        if not differences:
            return {"status": "no_differences_analyzed"}
        
        # Count by type
        type_counts = {dt.value: 0 for dt in DifferenceType}
        for diff in differences.values():
            type_counts[diff.difference_type.value] += 1
        
        # Find fields with largest differences
        sorted_fields = sorted(
            differences.items(),
            key=lambda x: x[1].mean_relative_diff,
            reverse=True
        )
        
        top_different_fields = [
            {
                "field_name": name,
                "mean_relative_diff": diff.mean_relative_diff,
                "difference_type": diff.difference_type.value,
            }
            for name, diff in sorted_fields[:5]
        ]
        
        # Overall assessment
        critical_fields = [
            name for name, diff in differences.items()
            if diff.difference_type in [DifferenceType.LARGE, DifferenceType.CRITICAL]
        ]
        
        return {
            "total_fields_compared": len(differences),
            "difference_type_counts": type_counts,
            "top_different_fields": top_different_fields,
            "critical_fields": critical_fields,
            "overall_status": self._assess_overall_status(differences),
        }
    
    def _classify_difference(self, mean_rel_diff: float) -> DifferenceType:
        """Classify difference based on relative difference"""
        if mean_rel_diff < self.negligible_threshold:
            return DifferenceType.NEGLIGIBLE
        elif mean_rel_diff < self.small_threshold:
            return DifferenceType.SMALL
        elif mean_rel_diff < self.moderate_threshold:
            return DifferenceType.MODERATE
        elif mean_rel_diff < self.large_threshold:
            return DifferenceType.LARGE
        else:
            return DifferenceType.CRITICAL
    
    def _assess_overall_status(
        self, differences: Dict[str, FieldDifference]
    ) -> str:
        """Assess overall status of comparison"""
        critical_count = sum(
            1 for diff in differences.values()
            if diff.difference_type == DifferenceType.CRITICAL
        )
        large_count = sum(
            1 for diff in differences.values()
            if diff.difference_type == DifferenceType.LARGE
        )
        
        if critical_count > 0:
            return "critical_differences_found"
        elif large_count > len(differences) / 2:
            return "significant_differences_found"
        elif large_count > 0:
            return "some_differences_found"
        else:
            return "minor_differences_only"
    
    def identify_outlier_regions(
        self,
        field1: np.ndarray,
        field2: np.ndarray,
        threshold_std: float = 3.0,
    ) -> Tuple[np.ndarray, Dict]:
        """
        Identify regions where differences are statistical outliers
        
        Args:
            field1: First field
            field2: Second field
            threshold_std: Number of standard deviations for outlier (default: 3)
            
        Returns:
            Tuple of (outlier_mask, statistics)
        """
        diff = field2 - field1
        mean_diff = np.mean(diff)
        std_diff = np.std(diff)
        
        # Identify outliers
        outlier_mask = np.abs(diff - mean_diff) > (threshold_std * std_diff)
        num_outliers = np.sum(outlier_mask)
        
        statistics = {
            "num_outliers": int(num_outliers),
            "percentage_outliers": float((num_outliers / diff.size) * 100),
            "threshold_std": threshold_std,
            "mean_difference": float(mean_diff),
            "std_difference": float(std_diff),
        }
        
        return outlier_mask, statistics
