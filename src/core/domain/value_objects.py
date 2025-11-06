"""
값 객체 (Value Objects)

식별자가 없고 불변인 도메인 객체들.
값 객체는 속성의 조합으로 동등성을 판단합니다.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, List
from datetime import datetime
import math


@dataclass(frozen=True)
class Coordinate3D:
    """
    3D 좌표 값 객체

    불변 3차원 좌표를 나타냅니다.
    """

    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if not all(isinstance(v, (int, float)) for v in [self.x, self.y, self.z]):
            raise ValueError("Coordinates must be numeric")

        if any(math.isnan(v) or math.isinf(v) for v in [self.x, self.y, self.z]):
            raise ValueError("Coordinates cannot be NaN or Inf")

    def distance_to(self, other: "Coordinate3D") -> float:
        """다른 좌표까지의 유클리드 거리"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def to_tuple(self) -> Tuple[float, float, float]:
        """튜플로 변환"""
        return (self.x, self.y, self.z)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float, float]) -> "Coordinate3D":
        """튜플로부터 생성"""
        return cls(x=coords[0], y=coords[1], z=coords[2])

    @classmethod
    def origin(cls) -> "Coordinate3D":
        """원점 (0, 0, 0)"""
        return cls(0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Vector3D:
    """
    3D 벡터 값 객체

    방향과 크기를 가진 3차원 벡터입니다.
    """

    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if not all(isinstance(v, (int, float)) for v in [self.x, self.y, self.z]):
            raise ValueError("Vector components must be numeric")

        if any(math.isnan(v) or math.isinf(v) for v in [self.x, self.y, self.z]):
            raise ValueError("Vector components cannot be NaN or Inf")

    def magnitude(self) -> float:
        """벡터의 크기"""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self) -> "Vector3D":
        """정규화된 벡터 (단위 벡터) 반환"""
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        return Vector3D(self.x / mag, self.y / mag, self.z / mag)

    def dot(self, other: "Vector3D") -> float:
        """내적 (Dot product)"""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vector3D") -> "Vector3D":
        """외적 (Cross product)"""
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def scale(self, factor: float) -> "Vector3D":
        """스칼라 곱"""
        return Vector3D(self.x * factor, self.y * factor, self.z * factor)

    @classmethod
    def zero(cls) -> "Vector3D":
        """영벡터"""
        return cls(0.0, 0.0, 0.0)


@dataclass(frozen=True)
class BoundingBox:
    """
    3D 경계 상자 값 객체

    최소/최대 좌표로 정의되는 경계 상자입니다.
    """

    min_point: Coordinate3D
    max_point: Coordinate3D

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if self.min_point.x > self.max_point.x:
            raise ValueError("min_point.x must be <= max_point.x")
        if self.min_point.y > self.max_point.y:
            raise ValueError("min_point.y must be <= max_point.y")
        if self.min_point.z > self.max_point.z:
            raise ValueError("min_point.z must be <= max_point.z")

    def width(self) -> float:
        """X 방향 너비"""
        return self.max_point.x - self.min_point.x

    def height(self) -> float:
        """Y 방향 높이"""
        return self.max_point.y - self.min_point.y

    def depth(self) -> float:
        """Z 방향 깊이"""
        return self.max_point.z - self.min_point.z

    def volume(self) -> float:
        """경계 상자 부피"""
        return self.width() * self.height() * self.depth()

    def center(self) -> Coordinate3D:
        """경계 상자 중심점"""
        return Coordinate3D(
            (self.min_point.x + self.max_point.x) / 2,
            (self.min_point.y + self.max_point.y) / 2,
            (self.min_point.z + self.max_point.z) / 2,
        )

    def contains(self, point: Coordinate3D) -> bool:
        """점이 경계 상자 내부에 있는지 확인"""
        return (
            self.min_point.x <= point.x <= self.max_point.x
            and self.min_point.y <= point.y <= self.max_point.y
            and self.min_point.z <= point.z <= self.max_point.z
        )

    def intersects(self, other: "BoundingBox") -> bool:
        """다른 경계 상자와 교차하는지 확인"""
        return (
            self.min_point.x <= other.max_point.x
            and self.max_point.x >= other.min_point.x
            and self.min_point.y <= other.max_point.y
            and self.max_point.y >= other.min_point.y
            and self.min_point.z <= other.max_point.z
            and self.max_point.z >= other.min_point.z
        )


@dataclass(frozen=True)
class TimeRange:
    """
    시간 범위 값 객체

    시작 시간과 종료 시간을 나타냅니다.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if self.start > self.end:
            raise ValueError("Start time must be before or equal to end time")

    def duration_seconds(self) -> float:
        """기간 (초)"""
        delta = self.end - self.start
        return delta.total_seconds()

    def duration_minutes(self) -> float:
        """기간 (분)"""
        return self.duration_seconds() / 60

    def duration_hours(self) -> float:
        """기간 (시간)"""
        return self.duration_seconds() / 3600

    def contains(self, time: datetime) -> bool:
        """특정 시간이 범위 내에 있는지 확인"""
        return self.start <= time <= self.end

    def overlaps(self, other: "TimeRange") -> bool:
        """다른 시간 범위와 겹치는지 확인"""
        return self.start <= other.end and self.end >= other.start


@dataclass(frozen=True)
class CompressionMetadata:
    """
    압축 메타데이터 값 객체

    데이터 압축에 관련된 정보를 담습니다.
    """

    original_size: int
    compressed_size: int
    compression_method: str
    compression_ratio: Optional[float] = None

    def __post_init__(self) -> None:
        """초기화 후 검증 및 압축률 계산"""
        if self.original_size < 0:
            raise ValueError("Original size cannot be negative")
        if self.compressed_size < 0:
            raise ValueError("Compressed size cannot be negative")
        if not self.compression_method:
            raise ValueError("Compression method cannot be empty")

        # 압축률 계산
        if self.compression_ratio is None and self.original_size > 0:
            object.__setattr__(
                self,
                "compression_ratio",
                self.original_size / self.compressed_size,
            )

    def space_saved_bytes(self) -> int:
        """절약된 공간 (바이트)"""
        return self.original_size - self.compressed_size

    def space_saved_percentage(self) -> float:
        """절약된 공간 (퍼센트)"""
        if self.original_size == 0:
            return 0.0
        return (self.space_saved_bytes() / self.original_size) * 100


@dataclass(frozen=True)
class AnalysisResult:
    """
    분석 결과 값 객체

    분석 작업의 결과를 나타냅니다.
    """

    analysis_type: str
    metrics: dict
    summary: str
    confidence_score: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if not self.analysis_type:
            raise ValueError("Analysis type cannot be empty")

        if self.confidence_score is not None:
            if not 0 <= self.confidence_score <= 1:
                raise ValueError("Confidence score must be between 0 and 1")

        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())

    def get_metric(self, key: str) -> Optional[float]:
        """특정 메트릭 조회"""
        return self.metrics.get(key)

    def has_high_confidence(self, threshold: float = 0.8) -> bool:
        """높은 신뢰도를 가지는지 확인"""
        if self.confidence_score is None:
            return False
        return self.confidence_score >= threshold


@dataclass(frozen=True)
class DataQuality:
    """
    데이터 품질 값 객체

    데이터 품질 메트릭을 나타냅니다.
    """

    completeness: float  # 0-1
    accuracy: float  # 0-1
    consistency: float  # 0-1
    validity: float  # 0-1

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        for field_name, value in [
            ("completeness", self.completeness),
            ("accuracy", self.accuracy),
            ("consistency", self.consistency),
            ("validity", self.validity),
        ]:
            if not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be numeric")
            if not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be between 0 and 1")

    def overall_score(self) -> float:
        """전체 품질 점수 (평균)"""
        return (
            self.completeness + self.accuracy + self.consistency + self.validity
        ) / 4

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """허용 가능한 품질인지 확인"""
        return self.overall_score() >= threshold

    def get_weakest_dimension(self) -> str:
        """가장 약한 품질 차원 반환"""
        dimensions = {
            "completeness": self.completeness,
            "accuracy": self.accuracy,
            "consistency": self.consistency,
            "validity": self.validity,
        }
        return min(dimensions, key=dimensions.get)  # type: ignore


@dataclass(frozen=True)
class Statistics:
    """
    통계 정보 값 객체

    기본 통계 정보를 담습니다.
    """

    mean: float
    std: float
    min: float
    max: float
    median: Optional[float] = None
    count: Optional[int] = None

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if self.std < 0:
            raise ValueError("Standard deviation cannot be negative")

        if self.min > self.max:
            raise ValueError("Min cannot be greater than max")

        if self.count is not None and self.count < 0:
            raise ValueError("Count cannot be negative")

    def range(self) -> float:
        """범위 (최대값 - 최소값)"""
        return self.max - self.min

    def coefficient_of_variation(self) -> Optional[float]:
        """변동계수 (CV)"""
        if self.mean == 0:
            return None
        return (self.std / abs(self.mean)) * 100

    def is_outlier(self, value: float, n_std: float = 3.0) -> bool:
        """특정 값이 이상치인지 확인 (n-시그마 규칙)"""
        return abs(value - self.mean) > n_std * self.std
