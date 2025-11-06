"""3D 기하학 시스템 통합 테스트"""

import numpy as np
import pytest

from src.core.geometry import (
    GeometricAnalyzer,
    MeshOperations,
    MeshQualityAnalyzer,
    MeshTransform,
)


class TestGeometricAnalyzer:
    """기하학적 분석 테스트"""

    def test_triangle_area(self):
        """삼각형 면적 계산 테스트"""
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        v3 = np.array([0.0, 1.0, 0.0])

        area = GeometricAnalyzer.calculate_triangle_area(v1, v2, v3)

        # 직각 이등변 삼각형: 면적 = 0.5
        assert abs(area - 0.5) < 1e-6

    def test_triangle_normal(self):
        """삼각형 법선 벡터 테스트"""
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        v3 = np.array([0.0, 1.0, 0.0])

        normal = GeometricAnalyzer.calculate_triangle_normal(v1, v2, v3)

        # Z축 방향 법선
        expected = np.array([0.0, 0.0, 1.0])
        assert np.allclose(normal, expected)

    def test_cube_volume(self):
        """정육면체 부피 테스트"""
        # 단위 정육면체 (0~1)
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )

        # 정육면체를 삼각형으로 구성 (12개 삼각형)
        faces = np.array(
            [
                # 하단
                [0, 1, 2],
                [0, 2, 3],
                # 상단
                [4, 6, 5],
                [4, 7, 6],
                # 앞면
                [0, 5, 1],
                [0, 4, 5],
                # 뒷면
                [2, 7, 3],
                [2, 6, 7],
                # 왼쪽
                [0, 3, 7],
                [0, 7, 4],
                # 오른쪽
                [1, 6, 2],
                [1, 5, 6],
            ]
        )

        volume = GeometricAnalyzer.calculate_mesh_volume(vertices, faces)

        # 단위 정육면체: 부피 = 1
        assert abs(volume - 1.0) < 0.1

    def test_surface_area(self):
        """표면적 계산 테스트"""
        # 단위 정육면체
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )

        faces = np.array(
            [
                [0, 1, 2],
                [0, 2, 3],
                [4, 6, 5],
                [4, 7, 6],
                [0, 5, 1],
                [0, 4, 5],
                [2, 7, 3],
                [2, 6, 7],
                [0, 3, 7],
                [0, 7, 4],
                [1, 6, 2],
                [1, 5, 6],
            ]
        )

        area = GeometricAnalyzer.calculate_mesh_surface_area(vertices, faces)

        # 단위 정육면체: 표면적 = 6
        assert abs(area - 6.0) < 0.1

    def test_centroid(self):
        """무게 중심 계산 테스트"""
        # 단위 정육면체의 중심은 (0.5, 0.5, 0.5)
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )

        faces = np.array([[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6]])

        centroid = GeometricAnalyzer.calculate_centroid(vertices, faces)

        expected = np.array([0.5, 0.5, 0.5])
        assert np.allclose(centroid, expected, atol=0.2)

    def test_bounding_box(self):
        """바운딩 박스 테스트"""
        vertices = np.array([[0, 0, 0], [1, 2, 3], [-1, -2, -3]], dtype=float)

        min_point, max_point = GeometricAnalyzer.calculate_bounding_box(vertices)

        assert np.allclose(min_point, [-1, -2, -3])
        assert np.allclose(max_point, [1, 2, 3])

    def test_edge_length(self):
        """엣지 길이 테스트"""
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([3.0, 4.0, 0.0])

        length = GeometricAnalyzer.calculate_edge_length(v1, v2)

        # 3-4-5 삼각형
        assert abs(length - 5.0) < 1e-6


class TestMeshQualityAnalyzer:
    """메시 품질 분석 테스트"""

    def test_equilateral_triangle_quality(self):
        """정삼각형 품질 테스트"""
        # 정삼각형
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        v3 = np.array([0.5, np.sqrt(3) / 2, 0.0])

        quality = MeshQualityAnalyzer.calculate_triangle_quality(v1, v2, v3)

        # 정삼각형: 품질 = 1
        assert quality > 0.99

    def test_degenerate_triangle_quality(self):
        """퇴화 삼각형 품질 테스트"""
        # 일직선상의 점들
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        v3 = np.array([2.0, 0.0, 0.0])

        quality = MeshQualityAnalyzer.calculate_triangle_quality(v1, v2, v3)

        # 퇴화 삼각형: 품질 = 0
        assert quality < 0.1


class TestMeshOperations:
    """메시 조작 테스트"""

    def test_translation(self):
        """이동 테스트"""
        vertices = np.array([[0, 0, 0], [1, 1, 1]], dtype=float)
        translation = np.array([1.0, 2.0, 3.0])

        translated = MeshOperations.translate(vertices, translation)

        expected = np.array([[1, 2, 3], [2, 3, 4]], dtype=float)
        assert np.allclose(translated, expected)

    def test_scaling(self):
        """스케일 테스트"""
        vertices = np.array([[1, 2, 3], [4, 5, 6]], dtype=float)

        scaled = MeshOperations.scale(vertices, 2.0)

        expected = np.array([[2, 4, 6], [8, 10, 12]], dtype=float)
        assert np.allclose(scaled, expected)

    def test_center_at_origin(self):
        """원점 중심 이동 테스트"""
        vertices = np.array([[1, 1, 1], [3, 3, 3]], dtype=float)

        centered = MeshOperations.center_at_origin(vertices)

        # 중심이 원점
        centroid = np.mean(centered, axis=0)
        assert np.allclose(centroid, [0, 0, 0])

    def test_flip_normals(self):
        """법선 반전 테스트"""
        faces = np.array([[0, 1, 2], [3, 4, 5]])

        flipped = MeshOperations.flip_normals(faces)

        expected = np.array([[0, 2, 1], [3, 5, 4]])
        assert np.array_equal(flipped, expected)

    def test_laplacian_smoothing(self):
        """Laplacian 스무딩 테스트"""
        # 간단한 메시
        vertices = np.array(
            [[0, 0, 0], [1, 0, 0], [0.5, 1, 0], [0.5, 0.5, 1]], dtype=float
        )

        faces = np.array([[0, 1, 2], [0, 1, 3]])

        smoothed = MeshOperations.laplacian_smoothing(
            vertices, faces, iterations=1, lambda_factor=0.5
        )

        # 스무딩 후에도 형태 유지
        assert smoothed.shape == vertices.shape

    def test_subdivide(self):
        """서브디비전 테스트"""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)

        faces = np.array([[0, 1, 2]])

        new_vertices, new_faces = MeshOperations.subdivide(vertices, faces)

        # 1개 삼각형 -> 4개 삼각형
        assert len(new_faces) == 4
        # 3개 꼭짓점 + 3개 중점 = 6개
        assert len(new_vertices) == 6

    def test_remove_duplicates(self):
        """중복 꼭짓점 제거 테스트"""
        # 중복 포함 꼭짓점
        vertices = np.array(
            [[0, 0, 0], [1, 0, 0], [0, 0, 0], [1, 1, 0]], dtype=float  # 중복
        )

        faces = np.array([[0, 1, 3], [2, 1, 3]])  # 0과 2는 같은 점

        unique_vertices, new_faces = MeshOperations.remove_duplicates(
            vertices, faces
        )

        # 3개로 축소
        assert len(unique_vertices) == 3


class TestMeshTransform:
    """메시 변환 테스트"""

    def test_rotation_matrix_x(self):
        """X축 회전 행렬 테스트"""
        matrix = MeshTransform.rotation_matrix_x(np.pi / 2)

        # Y축 벡터를 Z축으로 회전
        v = np.array([0, 1, 0])
        rotated = np.dot(matrix, v)

        expected = np.array([0, 0, 1])
        assert np.allclose(rotated, expected, atol=1e-6)

    def test_rotation_matrix_z(self):
        """Z축 회전 행렬 테스트"""
        matrix = MeshTransform.rotation_matrix_z(np.pi / 2)

        # X축 벡터를 Y축으로 회전
        v = np.array([1, 0, 0])
        rotated = np.dot(matrix, v)

        expected = np.array([0, 1, 0])
        assert np.allclose(rotated, expected, atol=1e-6)
