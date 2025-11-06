"""
커브 데이터 타입

1D 커브 데이터를 처리하는 클래스입니다.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
import numpy as np
from scipy import interpolate

from src.core.data_types.base import BaseDataType, get_compression_strategy


@dataclass
class CurveData(BaseDataType):
    """
    커브 데이터 클래스

    1D 파라메트릭 커브 또는 함수 데이터를 나타냅니다.
    시계열 데이터, 온도 분포, 응답 곡선 등에 사용됩니다.

    Attributes:
        x: X 좌표 배열
        y: Y 좌표 배열
        z: Z 좌표 배열 (3D 커브인 경우)
        attributes: 추가 속성
    """

    x: np.ndarray
    y: np.ndarray
    z: Optional[np.ndarray] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        super().__init__(data_type="curve")

        # NumPy 배열로 변환
        if not isinstance(self.x, np.ndarray):
            self.x = np.array(self.x)
        if not isinstance(self.y, np.ndarray):
            self.y = np.array(self.y)
        if self.z is not None and not isinstance(self.z, np.ndarray):
            self.z = np.array(self.z)

        self.validate()

    def validate(self) -> bool:
        """유효성 검증"""
        if self.x.ndim != 1 or self.y.ndim != 1:
            raise ValueError("x and y must be 1D arrays")

        if len(self.x) != len(self.y):
            raise ValueError(f"x and y must have same length: {len(self.x)} vs {len(self.y)}")

        if self.z is not None:
            if self.z.ndim != 1:
                raise ValueError("z must be 1D array")
            if len(self.z) != len(self.x):
                raise ValueError(f"z must have same length as x: {len(self.z)} vs {len(self.x)}")

        if len(self.x) < 2:
            raise ValueError(f"Curve must have at least 2 points, got {len(self.x)}")

        return True

    def is_2d(self) -> bool:
        """2D 커브인지 확인"""
        return self.z is None

    def is_3d(self) -> bool:
        """3D 커브인지 확인"""
        return self.z is not None

    def serialize(self) -> Dict[str, Any]:
        """직렬화"""
        return {
            "data_type": self.data_type,
            "x": self.x.tolist(),
            "y": self.y.tolist(),
            "z": self.z.tolist() if self.z is not None else None,
            "attributes": self.attributes,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "CurveData":
        """역직렬화"""
        z = data.get("z")
        if z is not None:
            z = np.array(z)

        return cls(
            x=np.array(data["x"]),
            y=np.array(data["y"]),
            z=z,
            attributes=data.get("attributes", {}),
        )

    def compress(self, method: str = "default") -> bytes:
        """압축"""
        import pickle

        data = {"x": self.x, "y": self.y, "z": self.z, "attributes": self.attributes}

        serialized = pickle.dumps(data)

        if method == "gzip":
            import gzip
            return gzip.compress(serialized)

        return serialized

    @classmethod
    def decompress(cls, data: bytes, method: str = "default") -> "CurveData":
        """압축 해제"""
        import pickle

        if method == "gzip":
            import gzip
            data = gzip.decompress(data)

        unpacked = pickle.loads(data)
        return cls(**unpacked)

    def get_metadata(self) -> Dict[str, Any]:
        """메타데이터 추출"""
        metadata = super().get_metadata()
        metadata.update({
            "num_points": len(self.x),
            "is_3d": self.is_3d(),
            "x_range": [float(np.min(self.x)), float(np.max(self.x))],
            "y_range": [float(np.min(self.y)), float(np.max(self.y))],
        })
        if self.is_3d():
            metadata["z_range"] = [float(np.min(self.z)), float(np.max(self.z))]
        return metadata

    def get_size_bytes(self) -> int:
        """크기 계산"""
        size = self.x.nbytes + self.y.nbytes
        if self.z is not None:
            size += self.z.nbytes
        return size

    def interpolate(self, x_new: np.ndarray, kind: str = "linear") -> "CurveData":
        """
        커브 보간

        Args:
            x_new: 새로운 X 좌표
            kind: 보간 방법 (linear, cubic, quadratic 등)

        Returns:
            CurveData: 보간된 커브
        """
        f_y = interpolate.interp1d(self.x, self.y, kind=kind, fill_value="extrapolate")
        y_new = f_y(x_new)

        z_new = None
        if self.z is not None:
            f_z = interpolate.interp1d(self.x, self.z, kind=kind, fill_value="extrapolate")
            z_new = f_z(x_new)

        return CurveData(x=x_new, y=y_new, z=z_new, attributes=self.attributes.copy())

    def resample(self, num_points: int) -> "CurveData":
        """균일한 간격으로 재샘플링"""
        x_new = np.linspace(np.min(self.x), np.max(self.x), num_points)
        return self.interpolate(x_new)

    def smooth(self, window_length: int = 5, polyorder: int = 2) -> "CurveData":
        """Savitzky-Golay 필터로 스무딩"""
        from scipy.signal import savgol_filter

        y_smooth = savgol_filter(self.y, window_length, polyorder)

        z_smooth = None
        if self.z is not None:
            z_smooth = savgol_filter(self.z, window_length, polyorder)

        return CurveData(x=self.x.copy(), y=y_smooth, z=z_smooth, attributes=self.attributes.copy())

    def get_length(self) -> float:
        """커브 길이 계산"""
        if self.is_2d():
            dx = np.diff(self.x)
            dy = np.diff(self.y)
            return float(np.sum(np.sqrt(dx**2 + dy**2)))
        else:
            dx = np.diff(self.x)
            dy = np.diff(self.y)
            dz = np.diff(self.z)
            return float(np.sum(np.sqrt(dx**2 + dy**2 + dz**2)))
