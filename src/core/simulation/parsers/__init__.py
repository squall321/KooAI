"""시뮬레이션 결과 파서"""

from typing import Optional, Type
from .base import BaseParser, ParserRegistry
from .csv_parser import CSVParser
from .format_detector import AutoFormatParser, DetectionResult, FileFormat, FormatDetector
from .streaming_base import AsyncStreamingParser, ProgressCallback, StreamingParser
from .streaming_csv_parser import StreamingCSVParser
from .streaming_json_parser import StreamingJSONParser
from .vtk_parser import VTKParser
from .vtu_parser import VTUParser

# Optional parsers (require additional dependencies)
HDF5Parser: Optional[Type[BaseParser]]
try:
    from .hdf5_parser import HDF5Parser

    HDF5_AVAILABLE = True
except ImportError:
    HDF5Parser = None
    HDF5_AVAILABLE = False

__all__ = [
    # Base
    "BaseParser",
    "ParserRegistry",
    # Format detection
    "FormatDetector",
    "AutoFormatParser",
    "FileFormat",
    "DetectionResult",
    # Streaming
    "StreamingParser",
    "AsyncStreamingParser",
    "ProgressCallback",
    # Standard parsers
    "CSVParser",
    "VTKParser",
    "VTUParser",
    "HDF5Parser",
    # Streaming parsers
    "StreamingCSVParser",
    "StreamingJSONParser",
    # Flags
    "HDF5_AVAILABLE",
]
