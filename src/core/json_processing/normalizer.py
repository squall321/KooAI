"""
데이터 정규화 및 변환 유틸리티

단위 변환, 좌표계 변환, 데이터 정규화 기능을 제공합니다.
"""

import math
from typing import Dict, Tuple
import numpy as np

from src.core.json_processing.schema import CoordinateSystem


# ============================================================================
# 단위 변환
# ============================================================================


class UnitConverter:
    """
    단위 변환기

    다양한 물리량의 단위 변환을 지원합니다.
    """

    # 길이 단위 (미터 기준)
    LENGTH_UNITS = {
        "m": 1.0,
        "mm": 0.001,
        "cm": 0.01,
        "km": 1000.0,
        "in": 0.0254,
        "ft": 0.3048,
        "yd": 0.9144,
        "mi": 1609.34,
    }

    # 온도 단위
    TEMPERATURE_UNITS = {"K": "kelvin", "C": "celsius", "F": "fahrenheit"}

    # 압력 단위 (파스칼 기준)
    PRESSURE_UNITS = {
        "Pa": 1.0,
        "kPa": 1000.0,
        "MPa": 1e6,
        "bar": 1e5,
        "atm": 101325.0,
        "psi": 6894.76,
        "mmHg": 133.322,
    }

    # 속도 단위 (m/s 기준)
    VELOCITY_UNITS = {
        "m/s": 1.0,
        "km/h": 1.0 / 3.6,
        "mph": 0.44704,
        "ft/s": 0.3048,
        "knot": 0.514444,
    }

    # 시간 단위 (초 기준)
    TIME_UNITS = {
        "s": 1.0,
        "ms": 0.001,
        "us": 1e-6,
        "min": 60.0,
        "h": 3600.0,
        "day": 86400.0,
    }

    # 질량 단위 (킬로그램 기준)
    MASS_UNITS = {
        "kg": 1.0,
        "g": 0.001,
        "mg": 1e-6,
        "ton": 1000.0,
        "lb": 0.453592,
        "oz": 0.0283495,
    }

    # 에너지 단위 (줄 기준)
    ENERGY_UNITS = {
        "J": 1.0,
        "kJ": 1000.0,
        "MJ": 1e6,
        "cal": 4.184,
        "kcal": 4184.0,
        "Wh": 3600.0,
        "kWh": 3.6e6,
        "BTU": 1055.06,
    }

    @classmethod
    def convert_length(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        길이 단위 변환

        Args:
            value: 값
            from_unit: 원본 단위
            to_unit: 대상 단위

        Returns:
            변환된 값

        Example:
            >>> UnitConverter.convert_length(1000, 'mm', 'm')
            1.0
        """
        if from_unit not in cls.LENGTH_UNITS or to_unit not in cls.LENGTH_UNITS:
            raise ValueError(f"Unsupported length unit: {from_unit} or {to_unit}")

        # 먼저 미터로 변환 후 대상 단위로 변환
        meters = value * cls.LENGTH_UNITS[from_unit]
        return meters / cls.LENGTH_UNITS[to_unit]

    @classmethod
    def convert_temperature(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        온도 단위 변환

        Args:
            value: 값
            from_unit: 원본 단위 (K, C, F)
            to_unit: 대상 단위 (K, C, F)

        Returns:
            변환된 값

        Example:
            >>> UnitConverter.convert_temperature(273.15, 'K', 'C')
            0.0
        """
        if from_unit not in cls.TEMPERATURE_UNITS or to_unit not in cls.TEMPERATURE_UNITS:
            raise ValueError(f"Unsupported temperature unit: {from_unit} or {to_unit}")

        # 켈빈으로 변환
        if from_unit == "K":
            kelvin = value
        elif from_unit == "C":
            kelvin = value + 273.15
        else:  # F
            kelvin = (value - 32) * 5.0 / 9.0 + 273.15

        # 대상 단위로 변환
        if to_unit == "K":
            return kelvin
        elif to_unit == "C":
            return kelvin - 273.15
        else:  # F
            return (kelvin - 273.15) * 9.0 / 5.0 + 32

    @classmethod
    def convert_pressure(cls, value: float, from_unit: str, to_unit: str) -> float:
        """압력 단위 변환"""
        if from_unit not in cls.PRESSURE_UNITS or to_unit not in cls.PRESSURE_UNITS:
            raise ValueError(f"Unsupported pressure unit: {from_unit} or {to_unit}")

        pascals = value * cls.PRESSURE_UNITS[from_unit]
        return pascals / cls.PRESSURE_UNITS[to_unit]

    @classmethod
    def convert_velocity(cls, value: float, from_unit: str, to_unit: str) -> float:
        """속도 단위 변환"""
        if from_unit not in cls.VELOCITY_UNITS or to_unit not in cls.VELOCITY_UNITS:
            raise ValueError(f"Unsupported velocity unit: {from_unit} or {to_unit}")

        ms = value * cls.VELOCITY_UNITS[from_unit]
        return ms / cls.VELOCITY_UNITS[to_unit]

    @classmethod
    def convert_time(cls, value: float, from_unit: str, to_unit: str) -> float:
        """시간 단위 변환"""
        if from_unit not in cls.TIME_UNITS or to_unit not in cls.TIME_UNITS:
            raise ValueError(f"Unsupported time unit: {from_unit} or {to_unit}")

        seconds = value * cls.TIME_UNITS[from_unit]
        return seconds / cls.TIME_UNITS[to_unit]

    @classmethod
    def convert_mass(cls, value: float, from_unit: str, to_unit: str) -> float:
        """질량 단위 변환"""
        if from_unit not in cls.MASS_UNITS or to_unit not in cls.MASS_UNITS:
            raise ValueError(f"Unsupported mass unit: {from_unit} or {to_unit}")

        kg = value * cls.MASS_UNITS[from_unit]
        return kg / cls.MASS_UNITS[to_unit]

    @classmethod
    def convert_energy(cls, value: float, from_unit: str, to_unit: str) -> float:
        """에너지 단위 변환"""
        if from_unit not in cls.ENERGY_UNITS or to_unit not in cls.ENERGY_UNITS:
            raise ValueError(f"Unsupported energy unit: {from_unit} or {to_unit}")

        joules = value * cls.ENERGY_UNITS[from_unit]
        return joules / cls.ENERGY_UNITS[to_unit]

    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str, quantity_type: str) -> float:
        """
        일반 단위 변환

        Args:
            value: 값
            from_unit: 원본 단위
            to_unit: 대상 단위
            quantity_type: 물리량 타입 (length, temperature, pressure, velocity, time, mass, energy)

        Returns:
            변환된 값

        Example:
            >>> UnitConverter.convert(1000, 'mm', 'm', 'length')
            1.0
        """
        converters = {
            "length": cls.convert_length,
            "temperature": cls.convert_temperature,
            "pressure": cls.convert_pressure,
            "velocity": cls.convert_velocity,
            "time": cls.convert_time,
            "mass": cls.convert_mass,
            "energy": cls.convert_energy,
        }

        if quantity_type not in converters:
            raise ValueError(f"Unsupported quantity type: {quantity_type}")

        return converters[quantity_type](value, from_unit, to_unit)


# ============================================================================
# 좌표계 변환
# ============================================================================


class CoordinateTransformer:
    """
    좌표계 변환기

    Cartesian, Cylindrical, Spherical 좌표계 간 변환을 지원합니다.
    """

    @staticmethod
    def cartesian_to_cylindrical(x: float, y: float, z: float) -> Tuple[float, float, float]:
        """
        Cartesian → Cylindrical 좌표 변환

        Args:
            x, y, z: Cartesian 좌표

        Returns:
            (r, theta, z): Cylindrical 좌표
            - r: 반지름
            - theta: 각도 (라디안)
            - z: 높이

        Example:
            >>> CoordinateTransformer.cartesian_to_cylindrical(1.0, 1.0, 2.0)
            (1.414..., 0.785..., 2.0)
        """
        r = math.sqrt(x * x + y * y)
        theta = math.atan2(y, x)
        return r, theta, z

    @staticmethod
    def cylindrical_to_cartesian(r: float, theta: float, z: float) -> Tuple[float, float, float]:
        """
        Cylindrical → Cartesian 좌표 변환

        Args:
            r: 반지름
            theta: 각도 (라디안)
            z: 높이

        Returns:
            (x, y, z): Cartesian 좌표
        """
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        return x, y, z

    @staticmethod
    def cartesian_to_spherical(x: float, y: float, z: float) -> Tuple[float, float, float]:
        """
        Cartesian → Spherical 좌표 변환

        Args:
            x, y, z: Cartesian 좌표

        Returns:
            (r, theta, phi): Spherical 좌표
            - r: 반지름
            - theta: 방위각 (라디안, 0 ~ 2π)
            - phi: 천정각 (라디안, 0 ~ π)
        """
        r = math.sqrt(x * x + y * y + z * z)
        theta = math.atan2(y, x)
        phi = math.acos(z / r) if r > 0 else 0.0
        return r, theta, phi

    @staticmethod
    def spherical_to_cartesian(r: float, theta: float, phi: float) -> Tuple[float, float, float]:
        """
        Spherical → Cartesian 좌표 변환

        Args:
            r: 반지름
            theta: 방위각 (라디안)
            phi: 천정각 (라디안)

        Returns:
            (x, y, z): Cartesian 좌표
        """
        x = r * math.sin(phi) * math.cos(theta)
        y = r * math.sin(phi) * math.sin(theta)
        z = r * math.cos(phi)
        return x, y, z

    @staticmethod
    def cylindrical_to_spherical(
        r_cyl: float, theta: float, z: float
    ) -> Tuple[float, float, float]:
        """
        Cylindrical → Spherical 좌표 변환

        Args:
            r_cyl: 원통 반지름
            theta: 각도 (라디안)
            z: 높이

        Returns:
            (r, theta, phi): Spherical 좌표
        """
        x, y, z_cart = CoordinateTransformer.cylindrical_to_cartesian(r_cyl, theta, z)
        return CoordinateTransformer.cartesian_to_spherical(x, y, z_cart)

    @staticmethod
    def spherical_to_cylindrical(r: float, theta: float, phi: float) -> Tuple[float, float, float]:
        """
        Spherical → Cylindrical 좌표 변환

        Args:
            r: 반지름
            theta: 방위각 (라디안)
            phi: 천정각 (라디안)

        Returns:
            (r_cyl, theta, z): Cylindrical 좌표
        """
        x, y, z = CoordinateTransformer.spherical_to_cartesian(r, theta, phi)
        return CoordinateTransformer.cartesian_to_cylindrical(x, y, z)

    @staticmethod
    def transform_points(
        points: np.ndarray,
        from_system: CoordinateSystem,
        to_system: CoordinateSystem,
    ) -> np.ndarray:
        """
        좌표 배열 변환

        Args:
            points: 좌표 배열 (N x 3)
            from_system: 원본 좌표계
            to_system: 대상 좌표계

        Returns:
            변환된 좌표 배열 (N x 3)

        Example:
            >>> points = np.array([[1, 1, 2], [2, 0, 1]])
            >>> transformed = CoordinateTransformer.transform_points(
            ...     points, CoordinateSystem.CARTESIAN, CoordinateSystem.CYLINDRICAL
            ... )
        """
        if from_system == to_system:
            return points.copy()

        result = np.zeros_like(points)

        # 변환 함수 매핑
        transforms = {
            (
                CoordinateSystem.CARTESIAN,
                CoordinateSystem.CYLINDRICAL,
            ): CoordinateTransformer.cartesian_to_cylindrical,
            (
                CoordinateSystem.CYLINDRICAL,
                CoordinateSystem.CARTESIAN,
            ): CoordinateTransformer.cylindrical_to_cartesian,
            (
                CoordinateSystem.CARTESIAN,
                CoordinateSystem.SPHERICAL,
            ): CoordinateTransformer.cartesian_to_spherical,
            (
                CoordinateSystem.SPHERICAL,
                CoordinateSystem.CARTESIAN,
            ): CoordinateTransformer.spherical_to_cartesian,
            (
                CoordinateSystem.CYLINDRICAL,
                CoordinateSystem.SPHERICAL,
            ): CoordinateTransformer.cylindrical_to_spherical,
            (
                CoordinateSystem.SPHERICAL,
                CoordinateSystem.CYLINDRICAL,
            ): CoordinateTransformer.spherical_to_cylindrical,
        }

        transform_func = transforms.get((from_system, to_system))
        if not transform_func:
            raise ValueError(f"Transformation from {from_system} to {to_system} not supported")

        for i, point in enumerate(points):
            result[i] = transform_func(point[0], point[1], point[2])

        return result


# ============================================================================
# 데이터 정규화
# ============================================================================


class DataNormalizer:
    """
    데이터 정규화기

    다양한 정규화 기법을 제공합니다.
    """

    @staticmethod
    def min_max_normalize(
        data: np.ndarray, feature_range: Tuple[float, float] = (0.0, 1.0)
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Min-Max 정규화

        Args:
            data: 입력 데이터
            feature_range: 목표 범위 (min, max)

        Returns:
            (정규화된 데이터, 메타데이터)
            메타데이터: {'min': 원본 최소값, 'max': 원본 최대값}

        Example:
            >>> data = np.array([1, 2, 3, 4, 5])
            >>> normalized, metadata = DataNormalizer.min_max_normalize(data)
        """
        data_min = np.min(data)
        data_max = np.max(data)

        if data_max - data_min == 0:
            return np.full_like(data, feature_range[0]), {"min": data_min, "max": data_max}

        # [0, 1]로 정규화
        normalized = (data - data_min) / (data_max - data_min)

        # feature_range로 스케일링
        feature_min, feature_max = feature_range
        normalized = normalized * (feature_max - feature_min) + feature_min

        metadata = {"min": float(data_min), "max": float(data_max)}

        return normalized, metadata

    @staticmethod
    def standardize(data: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Z-score 표준화

        Args:
            data: 입력 데이터

        Returns:
            (표준화된 데이터, 메타데이터)
            메타데이터: {'mean': 평균, 'std': 표준편차}

        Example:
            >>> data = np.array([1, 2, 3, 4, 5])
            >>> standardized, metadata = DataNormalizer.standardize(data)
        """
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return data - mean, {"mean": float(mean), "std": float(std)}

        standardized = (data - mean) / std
        metadata = {"mean": float(mean), "std": float(std)}

        return standardized, metadata

    @staticmethod
    def denormalize_min_max(
        normalized_data: np.ndarray,
        metadata: Dict[str, float],
        feature_range: Tuple[float, float] = (0.0, 1.0),
    ) -> np.ndarray:
        """
        Min-Max 정규화 역변환

        Args:
            normalized_data: 정규화된 데이터
            metadata: 정규화 시 저장한 메타데이터
            feature_range: 정규화 시 사용한 범위

        Returns:
            원본 스케일로 복원된 데이터
        """
        feature_min, feature_max = feature_range

        # feature_range에서 [0, 1]로
        data = (normalized_data - feature_min) / (feature_max - feature_min)

        # 원본 스케일로 복원
        data_min = metadata["min"]
        data_max = metadata["max"]

        return data * (data_max - data_min) + data_min

    @staticmethod
    def destandardize(standardized_data: np.ndarray, metadata: Dict[str, float]) -> np.ndarray:
        """
        표준화 역변환

        Args:
            standardized_data: 표준화된 데이터
            metadata: 표준화 시 저장한 메타데이터

        Returns:
            원본 스케일로 복원된 데이터
        """
        mean = metadata["mean"]
        std = metadata["std"]

        return standardized_data * std + mean

    @staticmethod
    def log_normalize(data: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
        """
        로그 정규화

        Args:
            data: 입력 데이터
            epsilon: 0 방지용 작은 값

        Returns:
            로그 정규화된 데이터
        """
        return np.log(data + epsilon)

    @staticmethod
    def robust_scale(data: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Robust 스케일링 (이상치에 강건)

        중앙값과 IQR을 사용한 스케일링입니다.

        Args:
            data: 입력 데이터

        Returns:
            (스케일링된 데이터, 메타데이터)
            메타데이터: {'median': 중앙값, 'iqr': IQR}
        """
        median = np.median(data)
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1

        if iqr == 0:
            return data - median, {"median": float(median), "iqr": float(iqr)}

        scaled = (data - median) / iqr
        metadata = {"median": float(median), "iqr": float(iqr)}

        return scaled, metadata
