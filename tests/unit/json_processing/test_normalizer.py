"""
데이터 정규화 및 변환 테스트
"""

import pytest
import math
import numpy as np

from src.core.json_processing.normalizer import (
    UnitConverter,
    CoordinateTransformer,
    DataNormalizer,
)
from src.core.json_processing.schema import CoordinateSystem


class TestUnitConverter:
    """UnitConverter 테스트"""

    def test_convert_length(self):
        """길이 단위 변환 테스트"""
        # 1 km = 1000 m
        result = UnitConverter.convert_length(1, "km", "m")
        assert result == pytest.approx(1000.0)

        # 1000 mm = 1 m
        result = UnitConverter.convert_length(1000, "mm", "m")
        assert result == pytest.approx(1.0)

        # 1 m = 100 cm
        result = UnitConverter.convert_length(1, "m", "cm")
        assert result == pytest.approx(100.0)

    def test_convert_temperature(self):
        """온도 단위 변환 테스트"""
        # 0°C = 273.15 K
        result = UnitConverter.convert_temperature(0, "C", "K")
        assert result == pytest.approx(273.15)

        # 273.15 K = 0°C
        result = UnitConverter.convert_temperature(273.15, "K", "C")
        assert result == pytest.approx(0.0)

        # 32°F = 0°C
        result = UnitConverter.convert_temperature(32, "F", "C")
        assert result == pytest.approx(0.0)

        # 212°F = 100°C
        result = UnitConverter.convert_temperature(212, "F", "C")
        assert result == pytest.approx(100.0)

    def test_convert_pressure(self):
        """압력 단위 변환 테스트"""
        # 1 bar = 100000 Pa
        result = UnitConverter.convert_pressure(1, "bar", "Pa")
        assert result == pytest.approx(100000.0)

        # 1 atm ≈ 101325 Pa
        result = UnitConverter.convert_pressure(1, "atm", "Pa")
        assert result == pytest.approx(101325.0)

    def test_convert_velocity(self):
        """속도 단위 변환 테스트"""
        # 1 m/s = 3.6 km/h
        result = UnitConverter.convert_velocity(1, "m/s", "km/h")
        assert result == pytest.approx(3.6)

        # 10 km/h ≈ 2.778 m/s
        result = UnitConverter.convert_velocity(10, "km/h", "m/s")
        assert result == pytest.approx(10.0 / 3.6)

    def test_convert_time(self):
        """시간 단위 변환 테스트"""
        # 1 min = 60 s
        result = UnitConverter.convert_time(1, "min", "s")
        assert result == pytest.approx(60.0)

        # 1 h = 3600 s
        result = UnitConverter.convert_time(1, "h", "s")
        assert result == pytest.approx(3600.0)

    def test_convert_mass(self):
        """질량 단위 변환 테스트"""
        # 1 kg = 1000 g
        result = UnitConverter.convert_mass(1, "kg", "g")
        assert result == pytest.approx(1000.0)

        # 1 ton = 1000 kg
        result = UnitConverter.convert_mass(1, "ton", "kg")
        assert result == pytest.approx(1000.0)

    def test_convert_energy(self):
        """에너지 단위 변환 테스트"""
        # 1 kJ = 1000 J
        result = UnitConverter.convert_energy(1, "kJ", "J")
        assert result == pytest.approx(1000.0)

        # 1 kWh = 3.6 MJ
        result = UnitConverter.convert_energy(1, "kWh", "MJ")
        assert result == pytest.approx(3.6)

    def test_general_convert(self):
        """일반 변환 함수 테스트"""
        result = UnitConverter.convert(1000, "mm", "m", "length")
        assert result == pytest.approx(1.0)

        result = UnitConverter.convert(273.15, "K", "C", "temperature")
        assert result == pytest.approx(0.0)

    def test_invalid_unit(self):
        """잘못된 단위 변환 시 에러"""
        with pytest.raises(ValueError):
            UnitConverter.convert_length(1, "invalid", "m")

    def test_invalid_quantity_type(self):
        """잘못된 물리량 타입"""
        with pytest.raises(ValueError):
            UnitConverter.convert(1, "m", "km", "invalid_type")


class TestCoordinateTransformer:
    """CoordinateTransformer 테스트"""

    def test_cartesian_to_cylindrical(self):
        """Cartesian → Cylindrical 변환 테스트"""
        r, theta, z = CoordinateTransformer.cartesian_to_cylindrical(1.0, 1.0, 2.0)

        assert r == pytest.approx(math.sqrt(2.0))
        assert theta == pytest.approx(math.pi / 4)
        assert z == pytest.approx(2.0)

    def test_cylindrical_to_cartesian(self):
        """Cylindrical → Cartesian 변환 테스트"""
        x, y, z = CoordinateTransformer.cylindrical_to_cartesian(math.sqrt(2.0), math.pi / 4, 2.0)

        assert x == pytest.approx(1.0)
        assert y == pytest.approx(1.0)
        assert z == pytest.approx(2.0)

    def test_cartesian_to_spherical(self):
        """Cartesian → Spherical 변환 테스트"""
        r, theta, phi = CoordinateTransformer.cartesian_to_spherical(1.0, 1.0, 1.0)

        assert r == pytest.approx(math.sqrt(3.0))
        assert theta == pytest.approx(math.pi / 4)

    def test_spherical_to_cartesian(self):
        """Spherical → Cartesian 변환 테스트"""
        # (r=1, theta=0, phi=0) → (0, 0, 1)
        x, y, z = CoordinateTransformer.spherical_to_cartesian(1.0, 0.0, 0.0)

        assert x == pytest.approx(0.0, abs=1e-10)
        assert y == pytest.approx(0.0, abs=1e-10)
        assert z == pytest.approx(1.0)

    def test_coordinate_roundtrip(self):
        """좌표 변환 왕복 테스트"""
        # Cartesian → Cylindrical → Cartesian
        x_orig, y_orig, z_orig = 3.0, 4.0, 5.0

        r, theta, z = CoordinateTransformer.cartesian_to_cylindrical(x_orig, y_orig, z_orig)
        x, y, z = CoordinateTransformer.cylindrical_to_cartesian(r, theta, z)

        assert x == pytest.approx(x_orig)
        assert y == pytest.approx(y_orig)
        assert z == pytest.approx(z_orig)

    def test_transform_points_identity(self):
        """동일 좌표계 변환 (항등 변환)"""
        points = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])

        result = CoordinateTransformer.transform_points(
            points, CoordinateSystem.CARTESIAN, CoordinateSystem.CARTESIAN
        )

        np.testing.assert_array_almost_equal(result, points)

    def test_transform_points_cartesian_to_cylindrical(self):
        """좌표 배열 변환: Cartesian → Cylindrical"""
        points = np.array([[1.0, 0.0, 2.0], [0.0, 1.0, 3.0]])

        result = CoordinateTransformer.transform_points(
            points, CoordinateSystem.CARTESIAN, CoordinateSystem.CYLINDRICAL
        )

        # (1, 0, 2) → (1, 0, 2)
        assert result[0, 0] == pytest.approx(1.0)
        assert result[0, 1] == pytest.approx(0.0)
        assert result[0, 2] == pytest.approx(2.0)

        # (0, 1, 3) → (1, π/2, 3)
        assert result[1, 0] == pytest.approx(1.0)
        assert result[1, 1] == pytest.approx(math.pi / 2)
        assert result[1, 2] == pytest.approx(3.0)


class TestDataNormalizer:
    """DataNormalizer 테스트"""

    def test_min_max_normalize(self):
        """Min-Max 정규화 테스트"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        normalized, metadata = DataNormalizer.min_max_normalize(data)

        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)
        assert metadata["min"] == 1.0
        assert metadata["max"] == 5.0

    def test_min_max_with_custom_range(self):
        """커스텀 범위로 Min-Max 정규화"""
        data = np.array([0.0, 10.0, 20.0])

        normalized, metadata = DataNormalizer.min_max_normalize(data, feature_range=(-1.0, 1.0))

        assert normalized.min() == pytest.approx(-1.0)
        assert normalized.max() == pytest.approx(1.0)

    def test_denormalize_min_max(self):
        """Min-Max 정규화 역변환 테스트"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        normalized, metadata = DataNormalizer.min_max_normalize(data)
        denormalized = DataNormalizer.denormalize_min_max(normalized, metadata)

        np.testing.assert_array_almost_equal(denormalized, data)

    def test_standardize(self):
        """Z-score 표준화 테스트"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        standardized, metadata = DataNormalizer.standardize(data)

        # 평균이 0에 가까워야 함
        assert standardized.mean() == pytest.approx(0.0, abs=1e-10)
        # 표준편차가 1에 가까워야 함
        assert standardized.std() == pytest.approx(1.0)

        assert "mean" in metadata
        assert "std" in metadata

    def test_destandardize(self):
        """표준화 역변환 테스트"""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

        standardized, metadata = DataNormalizer.standardize(data)
        destandardized = DataNormalizer.destandardize(standardized, metadata)

        np.testing.assert_array_almost_equal(destandardized, data)

    def test_log_normalize(self):
        """로그 정규화 테스트"""
        data = np.array([1.0, 10.0, 100.0, 1000.0])

        log_normalized = DataNormalizer.log_normalize(data)

        # 로그 스케일로 변환
        expected = np.log(data + 1e-8)
        np.testing.assert_array_almost_equal(log_normalized, expected)

    def test_robust_scale(self):
        """Robust 스케일링 테스트"""
        # 이상치가 포함된 데이터
        data = np.array([1, 2, 3, 4, 5, 100])  # 100이 이상치

        scaled, metadata = DataNormalizer.robust_scale(data)

        assert "median" in metadata
        assert "iqr" in metadata

        # 중앙값 기준이므로 이상치에 덜 민감
        median = np.median(data)
        assert metadata["median"] == median

    def test_normalize_constant_data(self):
        """상수 데이터 정규화"""
        data = np.array([5.0, 5.0, 5.0, 5.0])

        # Min-Max
        normalized, _ = DataNormalizer.min_max_normalize(data)
        # 모든 값이 feature_range의 최소값이 되어야 함
        assert np.all(normalized == 0.0)

        # Standardize
        standardized, _ = DataNormalizer.standardize(data)
        # 평균이 0이 되어야 함
        assert np.all(standardized == 0.0)


class TestNormalizerIntegration:
    """정규화 통합 테스트"""

    def test_unit_and_coordinate_transform(self):
        """단위 변환 + 좌표 변환 통합"""
        # mm 단위의 Cartesian 좌표
        points_mm = np.array([[1000.0, 0.0, 2000.0]])  # 1m, 0, 2m

        # 먼저 m로 단위 변환
        points_m = points_mm * UnitConverter.LENGTH_UNITS["mm"]

        # Cylindrical로 좌표 변환
        points_cyl = CoordinateTransformer.transform_points(
            points_m, CoordinateSystem.CARTESIAN, CoordinateSystem.CYLINDRICAL
        )

        # (1, 0, 2) → (1, 0, 2) in cylindrical
        assert points_cyl[0, 0] == pytest.approx(1.0)
        assert points_cyl[0, 1] == pytest.approx(0.0)
        assert points_cyl[0, 2] == pytest.approx(2.0)

    def test_normalize_physical_data(self):
        """물리량 정규화 통합"""
        # 온도 데이터 (Celsius)
        temps_celsius = np.array([0.0, 25.0, 50.0, 100.0])

        # Kelvin으로 변환
        temps_kelvin = np.array(
            [UnitConverter.convert_temperature(t, "C", "K") for t in temps_celsius]
        )

        # 정규화
        normalized, metadata = DataNormalizer.min_max_normalize(temps_kelvin)

        # 0 ~ 1 범위 확인
        assert normalized.min() >= 0.0
        assert normalized.max() <= 1.0

        # 역변환 확인
        denormalized = DataNormalizer.denormalize_min_max(normalized, metadata)
        np.testing.assert_array_almost_equal(denormalized, temps_kelvin)
