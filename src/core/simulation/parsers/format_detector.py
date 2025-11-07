"""
파일 형식 자동 감지

파일 내용을 분석하여 적절한 파서를 자동으로 선택합니다.
확장자에 의존하지 않고 실제 파일 내용 기반으로 판단합니다.
"""

import mimetypes
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class FileFormat(Enum):
    """지원되는 파일 형식"""

    VTK = "vtk"  # Legacy VTK
    VTU = "vtu"  # VTK XML Unstructured Grid
    HDF5 = "hdf5"  # HDF5
    CSV = "csv"  # CSV
    JSON = "json"  # JSON
    UNKNOWN = "unknown"


@dataclass
class DetectionResult:
    """
    파일 형식 감지 결과

    Attributes:
        format: 감지된 파일 형식
        confidence: 신뢰도 (0.0 - 1.0)
        mime_type: MIME 타입 (선택적)
        details: 추가 상세 정보
    """

    format: FileFormat
    confidence: float
    mime_type: Optional[str] = None
    details: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"Format: {self.format.value} "
            f"(confidence: {self.confidence:.1%}, "
            f"MIME: {self.mime_type or 'unknown'})"
        )


class FormatDetector:
    """
    파일 형식 감지기

    파일 내용을 분석하여 형식을 자동으로 감지합니다.

    감지 방법:
    1. Magic bytes 검사 (파일 시작 시그니처)
    2. 파일 헤더 분석
    3. MIME 타입 확인 (보조적)
    4. 확장자 확인 (최후 수단)

    사용 예:
        detector = FormatDetector()
        result = detector.detect(Path("data.vtk"))
        print(f"Detected format: {result.format.value}")
        print(f"Confidence: {result.confidence:.1%}")
    """

    # Magic bytes 시그니처 (파일 시작 바이트)
    MAGIC_BYTES = {
        FileFormat.HDF5: [
            b"\x89HDF\r\n\x1a\n",  # HDF5 signature
        ],
        FileFormat.VTU: [
            b"<?xml",  # XML 파일
            b"\xef\xbb\xbf<?xml",  # UTF-8 BOM + XML
        ],
    }

    # 텍스트 헤더 시그니처
    TEXT_SIGNATURES = {
        FileFormat.VTK: [
            "# vtk DataFile Version",
        ],
        FileFormat.VTU: [
            "<VTKFile",
            '<?xml version="1.0"?>',
        ],
        FileFormat.CSV: [
            # CSV는 특정 헤더가 없으므로 패턴 검사
        ],
        FileFormat.JSON: [
            "{",  # JSON 객체
            "[",  # JSON 배열
        ],
    }

    # MIME 타입 매핑
    MIME_TYPES = {
        "application/x-vtk": FileFormat.VTK,
        "application/xml": FileFormat.VTU,
        "text/xml": FileFormat.VTU,
        "application/x-hdf": FileFormat.HDF5,
        "application/x-hdf5": FileFormat.HDF5,
        "text/csv": FileFormat.CSV,
        "application/json": FileFormat.JSON,
        "text/json": FileFormat.JSON,
    }

    # 확장자 매핑
    EXTENSION_MAP = {
        ".vtk": FileFormat.VTK,
        ".vtu": FileFormat.VTU,
        ".vti": FileFormat.VTU,  # VTK Image Data (XML)
        ".vtp": FileFormat.VTU,  # VTK PolyData (XML)
        ".vtr": FileFormat.VTU,  # VTK Rectilinear Grid (XML)
        ".h5": FileFormat.HDF5,
        ".hdf5": FileFormat.HDF5,
        ".hdf": FileFormat.HDF5,
        ".csv": FileFormat.CSV,
        ".json": FileFormat.JSON,
    }

    def __init__(self, max_header_bytes: int = 1024):
        """
        Args:
            max_header_bytes: 헤더 읽기 최대 바이트 수 (기본: 1024)
        """
        self.max_header_bytes = max_header_bytes

    def detect(self, file_path: Path) -> DetectionResult:
        """
        파일 형식 감지

        Args:
            file_path: 파일 경로

        Returns:
            DetectionResult

        Raises:
            FileNotFoundError: 파일이 없는 경우
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # 여러 방법으로 감지 시도
        results: List[DetectionResult] = []

        # 1. Magic bytes 검사 (가장 신뢰도 높음)
        magic_result = self._detect_by_magic_bytes(file_path)
        if magic_result:
            results.append(magic_result)

        # 2. 텍스트 헤더 분석
        header_result = self._detect_by_header(file_path)
        if header_result:
            results.append(header_result)

        # 3. MIME 타입 확인
        mime_result = self._detect_by_mime_type(file_path)
        if mime_result:
            results.append(mime_result)

        # 4. 확장자 확인 (최후 수단)
        ext_result = self._detect_by_extension(file_path)
        if ext_result:
            results.append(ext_result)

        # 가장 신뢰도 높은 결과 반환
        if results:
            results.sort(key=lambda r: r.confidence, reverse=True)
            return results[0]

        # 감지 실패
        return DetectionResult(
            format=FileFormat.UNKNOWN,
            confidence=0.0,
            details="No matching format detected",
        )

    def _detect_by_magic_bytes(self, file_path: Path) -> Optional[DetectionResult]:
        """Magic bytes로 형식 감지"""
        try:
            with open(file_path, "rb") as f:
                header = f.read(self.max_header_bytes)

            for file_format, signatures in self.MAGIC_BYTES.items():
                for signature in signatures:
                    if header.startswith(signature):
                        return DetectionResult(
                            format=file_format,
                            confidence=0.95,  # Magic bytes는 매우 신뢰도 높음
                            details=f"Magic bytes matched: {signature[:20]}...",
                        )

        except Exception:
            pass

        return None

    def _detect_by_header(self, file_path: Path) -> Optional[DetectionResult]:
        """텍스트 헤더로 형식 감지"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                header = f.read(self.max_header_bytes)

            # VTK 헤더 검사
            if any(sig in header for sig in self.TEXT_SIGNATURES[FileFormat.VTK]):
                return DetectionResult(
                    format=FileFormat.VTK,
                    confidence=0.9,
                    details="VTK header signature found",
                )

            # VTU (XML) 헤더 검사
            if "<VTKFile" in header:
                return DetectionResult(
                    format=FileFormat.VTU,
                    confidence=0.9,
                    details="VTKFile XML tag found",
                )

            # JSON 검사
            header_stripped = header.strip()
            if header_stripped.startswith("{") or header_stripped.startswith("["):
                # JSON 파싱 시도로 신뢰도 확인
                try:
                    import json

                    with open(file_path, "r", encoding="utf-8") as f:
                        json.load(f)
                    return DetectionResult(
                        format=FileFormat.JSON,
                        confidence=0.85,
                        details="Valid JSON structure",
                    )
                except json.JSONDecodeError:
                    # JSON 형식이지만 파싱 실패
                    return DetectionResult(
                        format=FileFormat.JSON,
                        confidence=0.6,
                        details="JSON-like structure (parsing failed)",
                    )

            # CSV 검사 (쉼표 또는 탭 구분)
            if self._looks_like_csv(header):
                return DetectionResult(
                    format=FileFormat.CSV,
                    confidence=0.7,
                    details="CSV structure detected",
                )

        except Exception:
            pass

        return None

    def _detect_by_mime_type(self, file_path: Path) -> Optional[DetectionResult]:
        """MIME 타입으로 형식 감지"""
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))

            if mime_type and mime_type in self.MIME_TYPES:
                return DetectionResult(
                    format=self.MIME_TYPES[mime_type],
                    confidence=0.6,  # MIME 타입은 중간 신뢰도
                    mime_type=mime_type,
                    details=f"MIME type: {mime_type}",
                )

        except Exception:
            pass

        return None

    def _detect_by_extension(self, file_path: Path) -> Optional[DetectionResult]:
        """확장자로 형식 감지 (최후 수단)"""
        extension = file_path.suffix.lower()

        if extension in self.EXTENSION_MAP:
            return DetectionResult(
                format=self.EXTENSION_MAP[extension],
                confidence=0.5,  # 확장자는 낮은 신뢰도
                details=f"Extension: {extension}",
            )

        return None

    def _looks_like_csv(self, text: str) -> bool:
        """CSV 형식인지 휴리스틱 검사"""
        lines = text.strip().split("\n")

        if len(lines) < 2:
            return False

        # 첫 두 줄의 쉼표/탭 개수 확인
        first_line_commas = lines[0].count(",")
        first_line_tabs = lines[0].count("\t")

        # 쉼표 또는 탭이 있어야 함
        if first_line_commas == 0 and first_line_tabs == 0:
            return False

        # 여러 줄이 일관된 구분자 개수를 가지는지 확인
        delimiter_counts = []
        for line in lines[:min(10, len(lines))]:  # 최대 10줄 확인
            comma_count = line.count(",")
            tab_count = line.count("\t")
            delimiter_counts.append(max(comma_count, tab_count))

        # 구분자 개수가 일관되면 CSV일 가능성 높음
        if len(set(delimiter_counts)) == 1 and delimiter_counts[0] > 0:
            return True

        # 구분자 개수가 비슷하면 (표준편차 작으면) CSV
        import statistics

        if len(delimiter_counts) > 1:
            std_dev = statistics.stdev(delimiter_counts)
            mean = statistics.mean(delimiter_counts)
            # 변동 계수 (CV) < 0.2이면 일관된 것으로 판단
            if mean > 0 and std_dev / mean < 0.2:
                return True

        return False


class AutoFormatParser:
    """
    자동 형식 감지 파서

    파일 형식을 자동으로 감지하고 적절한 파서를 선택합니다.

    사용 예:
        auto_parser = AutoFormatParser()
        result = auto_parser.parse(Path("unknown_file.dat"))
    """

    def __init__(self, min_confidence: float = 0.5):
        """
        Args:
            min_confidence: 최소 신뢰도 (기본: 0.5)
                           이보다 낮으면 파싱을 거부합니다.
        """
        self.detector = FormatDetector()
        self.min_confidence = min_confidence
        self._parsers = {}

    def parse(self, file_path: Path, **options):
        """
        파일 자동 감지 및 파싱

        Args:
            file_path: 파일 경로
            **options: 파서 옵션

        Returns:
            SimulationResult

        Raises:
            ValueError: 파일 형식 감지 실패 또는 신뢰도 낮음
        """
        # 형식 감지
        detection = self.detector.detect(file_path)

        print(f"🔍 Format detection: {detection}")

        if detection.confidence < self.min_confidence:
            raise ValueError(
                f"Low confidence format detection: {detection.confidence:.1%} "
                f"(minimum: {self.min_confidence:.1%})"
            )

        if detection.format == FileFormat.UNKNOWN:
            raise ValueError(
                f"Unknown file format: {file_path}. "
                "Please specify the format explicitly."
            )

        # 파서 선택
        parser = self._get_parser(detection.format)

        if not parser:
            raise ValueError(
                f"No parser available for format: {detection.format.value}"
            )

        # 파싱 실행
        return parser.parse(file_path, **options)

    def _get_parser(self, file_format: FileFormat):
        """파일 형식에 맞는 파서 반환"""
        # Lazy import로 순환 참조 방지
        if file_format not in self._parsers:
            if file_format == FileFormat.VTK:
                from .vtk_parser import VTKParser

                self._parsers[file_format] = VTKParser()

            elif file_format == FileFormat.VTU:
                from .vtu_parser import VTUParser

                self._parsers[file_format] = VTUParser()

            elif file_format == FileFormat.HDF5:
                try:
                    from .hdf5_parser import HDF5Parser

                    self._parsers[file_format] = HDF5Parser()
                except ImportError:
                    return None

            elif file_format == FileFormat.CSV:
                from .streaming_csv_parser import StreamingCSVParser

                self._parsers[file_format] = StreamingCSVParser()

            elif file_format == FileFormat.JSON:
                from .streaming_json_parser import StreamingJSONParser

                self._parsers[file_format] = StreamingJSONParser()

            else:
                return None

        return self._parsers.get(file_format)
