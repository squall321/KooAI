"""
Simulation comparison module

Compare multiple simulation results
"""

from .comparator import SimulationComparator, ComparisonResult
from .diff_analyzer import DifferenceAnalyzer, FieldDifference

__all__ = [
    "SimulationComparator",
    "ComparisonResult",
    "DifferenceAnalyzer",
    "FieldDifference",
]
