"""
Batch processing module

Process multiple simulations automatically
"""

from .processor import BatchProcessor, BatchJob, BatchResult
from .pipeline import Pipeline, PipelineStage

__all__ = [
    "BatchProcessor",
    "BatchJob",
    "BatchResult",
    "Pipeline",
    "PipelineStage",
]
