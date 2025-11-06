"""
컨투어 데이터 타입

2D/3D 컨투어(윤곽선) 데이터를 처리하는 클래스입니다.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from src.core.data_types.base import BaseDataType, get_compression_strategy


@dataclass
class ContourData(BaseDataType):
    """
    컨투어 데이터 클래스

    2D 또는 3D 공간의 윤곽선(contour) 데이터를 나타냅니다.
    CFD, 지형 데이터, 이미지 처리 등에서 사용됩니다.

    Attributes:
        points: 컨투어 포인트 배열 (N, 2) 또는 (N, 3)
        is_closed: 닫힌 컨투어 여부
        value: 컨투어 값 (등고선 높이 등)
        attributes: 추가 속성 딕셔너리
    """

    points: np.ndarray
    is_closed: bool = True
    value: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """초기화 후 검증 및 설정"""
        super().__init__(data_type="contour")

        # NumPy 배열로 변환
        if not isinstance(self.points, np.ndarray):
            self.points = np.array(self.points)

        # 검증
        self.validate()

    def validate(self) -> bool:
        """
        컨투어 데이터 유효성 검증

        Returns:
            bool: 유효하면 True

        Raises:
            ValueError: 유효하지 않은 데이터
        """
        if self.points.ndim != 2:
            raise ValueError(f"Points must be 2D array, got shape {self.points.shape}")

        if self.points.shape[0] < 2:
            raise ValueError(f"Contour must have at least 2 points, got {self.points.shape[0]}")

        if self.points.shape[1] not in [2, 3]:
            raise ValueError(
                f"Points must be (N, 2) or (N, 3), got shape {self.points.shape}"
            )

        # NaN, Inf 체크
        if np.any(np.isnan(self.points)) or np.any(np.isinf(self.points)):
            raise ValueError("Points contain NaN or Inf values")

        return True

    def serialize(self) -> Dict[str, Any]:
        """
        딕셔너리로 직렬화

        Returns:
            Dict[str, Any]: 직렬화된 데이터
        """
        return {
            "data_type": self.data_type,
            "points": self.points.tolist(),
            "is_closed": self.is_closed,
            "value": self.value,
            "attributes": self.attributes,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "ContourData":
        """
        딕셔너리로부터 객체 생성

        Args:
            data: 직렬화된 데이터

        Returns:
            ContourData: 생성된 객체
        """
        return cls(
            points=np.array(data["points"]),
            is_closed=data.get("is_closed", True),
            value=data.get("value"),
            attributes=data.get("attributes", {}),
        )

    def compress(self, method: str = "default") -> bytes:
        """
        컨투어 데이터 압축

        Args:
            method: 압축 방법 (default, gzip, douglas-peucker)

        Returns:
            bytes: 압축된 데이터
        """
        if method == "douglas-peucker":
            return self._compress_douglas_peucker()

        # 기본 압축 전략 사용
        strategy = get_compression_strategy(method)
        return strategy.compress(self.points)

    @classmethod
    def decompress(cls, data: bytes, method: str = "default") -> "ContourData":
        """
        압축 해제

        Args:
            data: 압축된 데이터
            method: 압축 방법

        Returns:
            ContourData: 압축 해제된 객체
        """
        if method == "douglas-peucker":
            return cls._decompress_douglas_peucker(data)

        # 기본 압축 전략 사용
        strategy = get_compression_strategy(method)
        points = strategy.decompress(data)
        return cls(points=points)

    def get_metadata(self) -> Dict[str, Any]:
        """
        메타데이터 추출

        Returns:
            Dict[str, Any]: 메타데이터
        """
        metadata = super().get_metadata()
        metadata.update(
            {
                "num_points": len(self.points),
                "dimensions": self.points.shape[1],
                "is_closed": self.is_closed,
                "value": self.value,
                "area": self.get_area() if self.is_2d() else None,
                "perimeter": self.get_perimeter(),
                "bounding_box": self.get_bounding_box(),
            }
        )
        return metadata

    def get_size_bytes(self) -> int:
        """
        데이터 크기 계산

        Returns:
            int: 바이트 단위 크기
        """
        return self.points.nbytes

    # === 컨투어 분석 메서드 ===

    def is_2d(self) -> bool:
        """2D 컨투어인지 확인"""
        return self.points.shape[1] == 2

    def is_3d(self) -> bool:
        """3D 컨투어인지 확인"""
        return self.points.shape[1] == 3

    def get_area(self) -> float:
        """
        컨투어 내부 면적 계산 (2D만 해당)

        Returns:
            float: 면적

        Raises:
            ValueError: 3D 컨투어인 경우
        """
        if not self.is_2d():
            raise ValueError("Area calculation only supported for 2D contours")

        if not self.is_closed:
            return 0.0

        # Shoelace formula
        x = self.points[:, 0]
        y = self.points[:, 1]
        return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    def get_perimeter(self) -> float:
        """
        컨투어 둘레 계산

        Returns:
            float: 둘레
        """
        # 각 세그먼트 길이의 합
        segments = np.diff(self.points, axis=0)
        lengths = np.linalg.norm(segments, axis=1)

        total_length = np.sum(lengths)

        # 닫힌 컨투어인 경우 마지막 점에서 첫 점으로의 거리 추가
        if self.is_closed:
            closing_segment = self.points[-1] - self.points[0]
            total_length += np.linalg.norm(closing_segment)

        return float(total_length)

    def get_bounding_box(self) -> Dict[str, Any]:
        """
        경계 상자 계산

        Returns:
            Dict[str, Any]: 최소/최대 좌표
        """
        min_coords = np.min(self.points, axis=0)
        max_coords = np.max(self.points, axis=0)

        if self.is_2d():
            return {
                "min": {"x": float(min_coords[0]), "y": float(min_coords[1])},
                "max": {"x": float(max_coords[0]), "y": float(max_coords[1])},
            }
        else:
            return {
                "min": {
                    "x": float(min_coords[0]),
                    "y": float(min_coords[1]),
                    "z": float(min_coords[2]),
                },
                "max": {
                    "x": float(max_coords[0]),
                    "y": float(max_coords[1]),
                    "z": float(max_coords[2]),
                },
            }

    def get_centroid(self) -> np.ndarray:
        """
        중심점 계산

        Returns:
            np.ndarray: 중심점 좌표
        """
        if self.is_closed and self.is_2d():
            # 다각형의 중심 (가중 평균)
            area = self.get_area()
            if area == 0:
                return np.mean(self.points, axis=0)

            x = self.points[:, 0]
            y = self.points[:, 1]

            cx = np.sum((x[:-1] + x[1:]) * (x[:-1] * y[1:] - x[1:] * y[:-1])) / (
                6 * area
            )
            cy = np.sum((y[:-1] + y[1:]) * (x[:-1] * y[1:] - x[1:] * y[:-1])) / (
                6 * area
            )

            return np.array([cx, cy])

        # 단순 평균
        return np.mean(self.points, axis=0)

    def simplify(self, epsilon: float = 1.0) -> "ContourData":
        """
        Douglas-Peucker 알고리즘으로 컨투어 단순화

        Args:
            epsilon: 단순화 허용 오차

        Returns:
            ContourData: 단순화된 컨투어
        """
        simplified_points = self._douglas_peucker(self.points, epsilon)

        return ContourData(
            points=simplified_points,
            is_closed=self.is_closed,
            value=self.value,
            attributes=self.attributes.copy(),
        )

    def resample(self, num_points: int) -> "ContourData":
        """
        컨투어를 균일한 간격으로 재샘플링

        Args:
            num_points: 목표 포인트 수

        Returns:
            ContourData: 재샘플링된 컨투어
        """
        if num_points < 2:
            raise ValueError("num_points must be at least 2")

        # 누적 거리 계산
        segments = np.diff(self.points, axis=0)
        segment_lengths = np.linalg.norm(segments, axis=1)
        cumulative_distances = np.concatenate([[0], np.cumsum(segment_lengths)])

        # 닫힌 컨투어인 경우 총 길이에 마지막 세그먼트 포함
        total_length = cumulative_distances[-1]
        if self.is_closed:
            closing_length = np.linalg.norm(self.points[-1] - self.points[0])
            total_length += closing_length

        # 균일한 간격으로 샘플링할 위치 계산
        sample_distances = np.linspace(0, total_length, num_points, endpoint=not self.is_closed)

        # 보간
        resampled_points = []
        for dist in sample_distances:
            if dist <= cumulative_distances[-1]:
                # 기존 세그먼트 내에서 보간
                idx = np.searchsorted(cumulative_distances, dist)
                if idx == 0:
                    resampled_points.append(self.points[0])
                else:
                    t = (dist - cumulative_distances[idx - 1]) / segment_lengths[idx - 1]
                    point = self.points[idx - 1] + t * segments[idx - 1]
                    resampled_points.append(point)
            else:
                # 닫힌 컨투어의 마지막 세그먼트
                t = (dist - cumulative_distances[-1]) / closing_length
                point = self.points[-1] + t * (self.points[0] - self.points[-1])
                resampled_points.append(point)

        return ContourData(
            points=np.array(resampled_points),
            is_closed=self.is_closed,
            value=self.value,
            attributes=self.attributes.copy(),
        )

    # === 압축 헬퍼 메서드 ===

    def _compress_douglas_peucker(self, epsilon: float = 1.0) -> bytes:
        """Douglas-Peucker 압축"""
        simplified = self.simplify(epsilon)
        metadata = {
            "epsilon": epsilon,
            "is_closed": self.is_closed,
            "value": self.value,
            "attributes": self.attributes,
        }

        import pickle

        return pickle.dumps({"points": simplified.points, "metadata": metadata})

    @classmethod
    def _decompress_douglas_peucker(cls, data: bytes) -> "ContourData":
        """Douglas-Peucker 압축 해제"""
        import pickle

        unpacked = pickle.loads(data)
        metadata = unpacked["metadata"]

        return cls(
            points=unpacked["points"],
            is_closed=metadata["is_closed"],
            value=metadata.get("value"),
            attributes=metadata.get("attributes", {}),
        )

    @staticmethod
    def _douglas_peucker(points: np.ndarray, epsilon: float) -> np.ndarray:
        """
        Douglas-Peucker 알고리즘 구현

        Args:
            points: 포인트 배열
            epsilon: 허용 오차

        Returns:
            np.ndarray: 단순화된 포인트 배열
        """
        if len(points) <= 2:
            return points

        # 첫 점과 마지막 점을 잇는 선분
        start, end = points[0], points[-1]
        line_vec = end - start
        line_len = np.linalg.norm(line_vec)

        if line_len == 0:
            return points[[0]]

        line_unit_vec = line_vec / line_len

        # 각 점에서 선분까지의 거리 계산
        vec_from_start = points - start
        scalar_proj = np.dot(vec_from_start, line_unit_vec)
        vec_proj = scalar_proj[:, np.newaxis] * line_unit_vec
        vec_to_line = vec_from_start - vec_proj
        distances = np.linalg.norm(vec_to_line, axis=1)

        # 최대 거리 찾기
        max_dist_idx = np.argmax(distances)
        max_dist = distances[max_dist_idx]

        if max_dist > epsilon:
            # 재귀적으로 분할
            left_simplified = ContourData._douglas_peucker(
                points[: max_dist_idx + 1], epsilon
            )
            right_simplified = ContourData._douglas_peucker(
                points[max_dist_idx:], epsilon
            )

            # 중복 제거하고 합침
            return np.vstack([left_simplified[:-1], right_simplified])
        else:
            # 첫 점과 마지막 점만 유지
            return points[[0, -1]]
