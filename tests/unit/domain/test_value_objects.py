"""
값 객체 단위 테스트
"""

import pytest
from datetime import datetime, timedelta
import math

from src.core.domain.value_objects import (
    Coordinate3D,
    Vector3D,
    BoundingBox,
    TimeRange,
    CompressionMetadata,
    AnalysisResult,
    DataQuality,
    Statistics,
)


class TestCoordinate3D:
    """Coordinate3D 값 객체 테스트"""

    def test_create_coordinate(self):
        """좌표 생성 테스트"""
        coord = Coordinate3D(1.0, 2.0, 3.0)

        assert coord.x == 1.0
        assert coord.y == 2.0
        assert coord.z == 3.0

    def test_coordinate_is_immutable(self):
        """좌표 불변성 테스트"""
        coord = Coordinate3D(1.0, 2.0, 3.0)

        with pytest.raises(AttributeError):
            coord.x = 5.0  # type: ignore

    def test_create_with_nan_raises_error(self):
        """NaN으로 생성 시 에러"""
        with pytest.raises(ValueError, match="cannot be NaN or Inf"):
            Coordinate3D(float("nan"), 2.0, 3.0)

    def test_create_with_inf_raises_error(self):
        """Inf로 생성 시 에러"""
        with pytest.raises(ValueError, match="cannot be NaN or Inf"):
            Coordinate3D(float("inf"), 2.0, 3.0)

    def test_distance_to(self):
        """거리 계산 테스트"""
        coord1 = Coordinate3D(0.0, 0.0, 0.0)
        coord2 = Coordinate3D(3.0, 4.0, 0.0)

        distance = coord1.distance_to(coord2)

        assert distance == 5.0  # 3-4-5 삼각형

    def test_to_tuple(self):
        """튜플 변환 테스트"""
        coord = Coordinate3D(1.0, 2.0, 3.0)

        assert coord.to_tuple() == (1.0, 2.0, 3.0)

    def test_from_tuple(self):
        """튜플로부터 생성 테스트"""
        coord = Coordinate3D.from_tuple((1.0, 2.0, 3.0))

        assert coord.x == 1.0
        assert coord.y == 2.0
        assert coord.z == 3.0

    def test_origin(self):
        """원점 생성 테스트"""
        origin = Coordinate3D.origin()

        assert origin.x == 0.0
        assert origin.y == 0.0
        assert origin.z == 0.0

    def test_equality(self):
        """동등성 테스트"""
        coord1 = Coordinate3D(1.0, 2.0, 3.0)
        coord2 = Coordinate3D(1.0, 2.0, 3.0)
        coord3 = Coordinate3D(1.0, 2.0, 3.1)

        assert coord1 == coord2
        assert coord1 != coord3


class TestVector3D:
    """Vector3D 값 객체 테스트"""

    def test_create_vector(self):
        """벡터 생성 테스트"""
        vec = Vector3D(1.0, 2.0, 3.0)

        assert vec.x == 1.0
        assert vec.y == 2.0
        assert vec.z == 3.0

    def test_magnitude(self):
        """크기 계산 테스트"""
        vec = Vector3D(3.0, 4.0, 0.0)

        assert vec.magnitude() == 5.0

    def test_normalize(self):
        """정규화 테스트"""
        vec = Vector3D(3.0, 4.0, 0.0)
        normalized = vec.normalize()

        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert normalized.x == 0.6
        assert normalized.y == 0.8

    def test_normalize_zero_vector_raises_error(self):
        """영벡터 정규화 시 에러"""
        vec = Vector3D.zero()

        with pytest.raises(ValueError, match="Cannot normalize zero vector"):
            vec.normalize()

    def test_dot_product(self):
        """내적 테스트"""
        vec1 = Vector3D(1.0, 0.0, 0.0)
        vec2 = Vector3D(0.0, 1.0, 0.0)

        assert vec1.dot(vec2) == 0.0  # 직교

        vec3 = Vector3D(1.0, 1.0, 0.0)
        assert vec1.dot(vec3) == 1.0

    def test_cross_product(self):
        """외적 테스트"""
        vec1 = Vector3D(1.0, 0.0, 0.0)
        vec2 = Vector3D(0.0, 1.0, 0.0)

        cross = vec1.cross(vec2)

        assert cross.x == 0.0
        assert cross.y == 0.0
        assert cross.z == 1.0

    def test_scale(self):
        """스칼라 곱 테스트"""
        vec = Vector3D(1.0, 2.0, 3.0)
        scaled = vec.scale(2.0)

        assert scaled.x == 2.0
        assert scaled.y == 4.0
        assert scaled.z == 6.0


class TestBoundingBox:
    """BoundingBox 값 객체 테스트"""

    def test_create_bounding_box(self):
        """경계 상자 생성 테스트"""
        min_point = Coordinate3D(0.0, 0.0, 0.0)
        max_point = Coordinate3D(10.0, 10.0, 10.0)

        bbox = BoundingBox(min_point, max_point)

        assert bbox.min_point == min_point
        assert bbox.max_point == max_point

    def test_create_with_invalid_bounds_raises_error(self):
        """잘못된 경계로 생성 시 에러"""
        min_point = Coordinate3D(10.0, 0.0, 0.0)
        max_point = Coordinate3D(0.0, 10.0, 10.0)

        with pytest.raises(ValueError, match="min_point.x must be"):
            BoundingBox(min_point, max_point)

    def test_dimensions(self):
        """크기 계산 테스트"""
        min_point = Coordinate3D(0.0, 0.0, 0.0)
        max_point = Coordinate3D(10.0, 20.0, 30.0)
        bbox = BoundingBox(min_point, max_point)

        assert bbox.width() == 10.0
        assert bbox.height() == 20.0
        assert bbox.depth() == 30.0

    def test_volume(self):
        """부피 계산 테스트"""
        min_point = Coordinate3D(0.0, 0.0, 0.0)
        max_point = Coordinate3D(2.0, 3.0, 4.0)
        bbox = BoundingBox(min_point, max_point)

        assert bbox.volume() == 24.0

    def test_center(self):
        """중심점 계산 테스트"""
        min_point = Coordinate3D(0.0, 0.0, 0.0)
        max_point = Coordinate3D(10.0, 10.0, 10.0)
        bbox = BoundingBox(min_point, max_point)

        center = bbox.center()

        assert center.x == 5.0
        assert center.y == 5.0
        assert center.z == 5.0

    def test_contains(self):
        """점 포함 여부 테스트"""
        min_point = Coordinate3D(0.0, 0.0, 0.0)
        max_point = Coordinate3D(10.0, 10.0, 10.0)
        bbox = BoundingBox(min_point, max_point)

        assert bbox.contains(Coordinate3D(5.0, 5.0, 5.0))
        assert bbox.contains(Coordinate3D(0.0, 0.0, 0.0))  # 경계
        assert not bbox.contains(Coordinate3D(15.0, 5.0, 5.0))

    def test_intersects(self):
        """교차 여부 테스트"""
        bbox1 = BoundingBox(Coordinate3D(0.0, 0.0, 0.0), Coordinate3D(10.0, 10.0, 10.0))
        bbox2 = BoundingBox(Coordinate3D(5.0, 5.0, 5.0), Coordinate3D(15.0, 15.0, 15.0))
        bbox3 = BoundingBox(
            Coordinate3D(20.0, 20.0, 20.0), Coordinate3D(30.0, 30.0, 30.0)
        )

        assert bbox1.intersects(bbox2)
        assert not bbox1.intersects(bbox3)


class TestTimeRange:
    """TimeRange 값 객체 테스트"""

    def test_create_time_range(self):
        """시간 범위 생성 테스트"""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 1, 0, 0)

        time_range = TimeRange(start, end)

        assert time_range.start == start
        assert time_range.end == end

    def test_create_with_end_before_start_raises_error(self):
        """종료 시간이 시작 시간보다 빠른 경우 에러"""
        start = datetime(2024, 1, 1, 1, 0, 0)
        end = datetime(2024, 1, 1, 0, 0, 0)

        with pytest.raises(ValueError, match="Start time must be before"):
            TimeRange(start, end)

    def test_duration_seconds(self):
        """기간 계산 (초) 테스트"""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 0, 1, 30)  # 90초
        time_range = TimeRange(start, end)

        assert time_range.duration_seconds() == 90.0

    def test_duration_minutes(self):
        """기간 계산 (분) 테스트"""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 1, 0, 0)  # 60분
        time_range = TimeRange(start, end)

        assert time_range.duration_minutes() == 60.0

    def test_contains(self):
        """시간 포함 여부 테스트"""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 1, 0, 0)
        time_range = TimeRange(start, end)

        assert time_range.contains(datetime(2024, 1, 1, 0, 30, 0))
        assert time_range.contains(start)
        assert not time_range.contains(datetime(2024, 1, 1, 2, 0, 0))

    def test_overlaps(self):
        """시간 범위 겹침 여부 테스트"""
        range1 = TimeRange(
            datetime(2024, 1, 1, 0, 0, 0), datetime(2024, 1, 1, 1, 0, 0)
        )
        range2 = TimeRange(
            datetime(2024, 1, 1, 0, 30, 0), datetime(2024, 1, 1, 1, 30, 0)
        )
        range3 = TimeRange(
            datetime(2024, 1, 1, 2, 0, 0), datetime(2024, 1, 1, 3, 0, 0)
        )

        assert range1.overlaps(range2)
        assert not range1.overlaps(range3)


class TestCompressionMetadata:
    """CompressionMetadata 값 객체 테스트"""

    def test_create_compression_metadata(self):
        """압축 메타데이터 생성 테스트"""
        metadata = CompressionMetadata(
            original_size=1000, compressed_size=100, compression_method="gzip"
        )

        assert metadata.original_size == 1000
        assert metadata.compressed_size == 100
        assert metadata.compression_method == "gzip"
        assert metadata.compression_ratio == 10.0

    def test_space_saved(self):
        """절약 공간 계산 테스트"""
        metadata = CompressionMetadata(
            original_size=1000, compressed_size=100, compression_method="gzip"
        )

        assert metadata.space_saved_bytes() == 900
        assert metadata.space_saved_percentage() == 90.0


class TestAnalysisResult:
    """AnalysisResult 값 객체 테스트"""

    def test_create_analysis_result(self):
        """분석 결과 생성 테스트"""
        result = AnalysisResult(
            analysis_type="statistical",
            metrics={"mean": 10.5, "std": 2.3},
            summary="Normal distribution detected",
            confidence_score=0.95,
        )

        assert result.analysis_type == "statistical"
        assert result.get_metric("mean") == 10.5
        assert result.confidence_score == 0.95

    def test_has_high_confidence(self):
        """높은 신뢰도 확인 테스트"""
        result = AnalysisResult(
            analysis_type="test",
            metrics={},
            summary="test",
            confidence_score=0.85,
        )

        assert result.has_high_confidence(threshold=0.8)
        assert not result.has_high_confidence(threshold=0.9)


class TestDataQuality:
    """DataQuality 값 객체 테스트"""

    def test_create_data_quality(self):
        """데이터 품질 생성 테스트"""
        quality = DataQuality(
            completeness=0.95, accuracy=0.90, consistency=0.85, validity=0.92
        )

        assert quality.completeness == 0.95
        assert quality.accuracy == 0.90

    def test_overall_score(self):
        """전체 품질 점수 테스트"""
        quality = DataQuality(
            completeness=0.8, accuracy=0.8, consistency=0.8, validity=0.8
        )

        assert quality.overall_score() == 0.8

    def test_is_acceptable(self):
        """허용 가능한 품질 확인 테스트"""
        quality = DataQuality(
            completeness=0.75, accuracy=0.75, consistency=0.75, validity=0.75
        )

        assert quality.is_acceptable(threshold=0.7)
        assert not quality.is_acceptable(threshold=0.8)

    def test_get_weakest_dimension(self):
        """가장 약한 차원 확인 테스트"""
        quality = DataQuality(
            completeness=0.95, accuracy=0.90, consistency=0.70, validity=0.92
        )

        assert quality.get_weakest_dimension() == "consistency"


class TestStatistics:
    """Statistics 값 객체 테스트"""

    def test_create_statistics(self):
        """통계 정보 생성 테스트"""
        stats = Statistics(mean=10.0, std=2.0, min=5.0, max=15.0, count=100)

        assert stats.mean == 10.0
        assert stats.std == 2.0
        assert stats.count == 100

    def test_range(self):
        """범위 계산 테스트"""
        stats = Statistics(mean=10.0, std=2.0, min=5.0, max=15.0)

        assert stats.range() == 10.0

    def test_coefficient_of_variation(self):
        """변동계수 계산 테스트"""
        stats = Statistics(mean=10.0, std=2.0, min=5.0, max=15.0)

        assert stats.coefficient_of_variation() == 20.0

    def test_is_outlier(self):
        """이상치 확인 테스트"""
        stats = Statistics(mean=10.0, std=2.0, min=5.0, max=15.0)

        assert not stats.is_outlier(12.0, n_std=3.0)  # 정상 범위
        assert stats.is_outlier(20.0, n_std=3.0)  # 이상치
