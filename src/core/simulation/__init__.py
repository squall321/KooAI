"""
시뮬레이션 결과 처리 모듈

시뮬레이션 결과 파싱, 분석, 메트릭 계산.
"""

from .analysis import ResultAnalyzer, SpatialAnalyzer
from .models import (
    DataLocation,
    FieldData,
    FieldType,
    MeshData,
    SimulationMetrics,
    SimulationResult,
    TimeStepData,
)
from .parsers import BaseParser, CSVParser, ParserRegistry, VTKParser

__all__ = [
    # Models
    "FieldType",
    "DataLocation",
    "FieldData",
    "MeshData",
    "TimeStepData",
    "SimulationResult",
    "SimulationMetrics",
    # Parsers
    "BaseParser",
    "ParserRegistry",
    "CSVParser",
    "VTKParser",
    # Analysis
    "ResultAnalyzer",
    "SpatialAnalyzer",
]
