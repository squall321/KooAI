"""
ContourData 테스트
"""

import pytest
import numpy as np
from src.core.data_types.contour import ContourData


class TestContourData:
    """ContourData 클래스 테스트"""

    def test_create_2d_contour(self):
        """2D 컨투어 생성"""
        points = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        contour = ContourData(points=points)

        assert contour.is_2d()
        assert not contour.is_3d()
        assert len(contour.points) == 4
        assert contour.is_closed

    def test_create_3d_contour(self):
        """3D 컨투어 생성"""
        points = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])
        contour = ContourData(points=points)

        assert contour.is_3d()
        assert not contour.is_2d()

    def test_create_with_too_few_points_raises_error(self):
        """포인트가 너무 적으면 에러"""
        with pytest.raises(ValueError, match="at least 2 points"):
            ContourData(points=np.array([[0, 0]]))

    def test_area_calculation_2d(self):
        """2D 면적 계산"""
        # 단위 정사각형
        points = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        contour = ContourData(points=points)

        area = contour.get_area()
        assert abs(area - 1.0) < 0.01

    def test_perimeter_calculation(self):
        """둘레 계산"""
        # 단위 정사각형
        points = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        contour = ContourData(points=points)

        perimeter = contour.get_perimeter()
        assert abs(perimeter - 4.0) < 0.01

    def test_serialize_deserialize(self):
        """직렬화/역직렬화"""
        points = np.array([[0, 0], [1, 1], [2, 0]])
        contour = ContourData(points=points, value=100.0)

        serialized = contour.serialize()
        restored = ContourData.deserialize(serialized)

        assert np.allclose(restored.points, contour.points)
        assert restored.value == contour.value

    def test_compress_decompress(self):
        """압축/압축 해제"""
        points = np.array([[0, 0], [1, 1], [2, 0]])
        contour = ContourData(points=points)

        compressed = contour.compress(method="gzip")
        restored = ContourData.decompress(compressed, method="gzip")

        assert np.allclose(restored.points, contour.points)

    def test_simplify(self):
        """단순화"""
        # 직선상의 많은 점
        points = np.array([[i, i] for i in range(10)], dtype=float)
        contour = ContourData(points=points, is_closed=False)

        simplified = contour.simplify(epsilon=0.1)

        # 단순화 후 포인트 수가 줄어야 함
        assert len(simplified.points) < len(contour.points)

    def test_resample(self):
        """재샘플링"""
        points = np.array([[0, 0], [1, 1], [2, 0]])
        contour = ContourData(points=points, is_closed=False)

        resampled = contour.resample(num_points=10)

        assert len(resampled.points) == 10

    def test_get_metadata(self):
        """메타데이터 추출"""
        points = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        contour = ContourData(points=points)

        metadata = contour.get_metadata()

        assert metadata["num_points"] == 4
        assert metadata["dimensions"] == 2
        assert metadata["is_closed"] == True
        assert "bounding_box" in metadata
