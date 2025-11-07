"""시뮬레이션 결과 파서"""

from .base import BaseParser, ParserRegistry
from .csv_parser import CSVParser
from .streaming_base import AsyncStreamingParser, ProgressCallback, StreamingParser
from .streaming_csv_parser import StreamingCSVParser
from .streaming_json_parser import StreamingJSONParser
from .vtk_parser import VTKParser
from .vtu_parser import VTUParser

# Optional parsers (require additional dependencies)
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
