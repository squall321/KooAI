"""
3D 기하학적 분석

메시 및 3D 데이터의 기하학적 속성 계산.
"""

from typing import List, Tuple

import numpy as np


class GeometricAnalyzer:
    """
    3D 기하학적 분석기

    메시 및 3D 데이터의 기하학적 속성을 계산.
    """

    @staticmethod
    def calculate_triangle_area(
        v1: np.ndarray, v2: np.ndarray, v3: np.ndarray
    ) -> float:
        """
        삼각형 면적 계산

        Args:
            v1, v2, v3: 삼각형의 꼭짓점 좌표 (3D)

        Returns:
            면적
        """
        # 벡터의 외적으로 면적 계산
        edge1 = v2 - v1
        edge2 = v3 - v1
        cross = np.cross(edge1, edge2)
        area = 0.5 * np.linalg.norm(cross)
        return float(area)

    @staticmethod
    def calculate_triangle_normal(
        v1: np.ndarray, v2: np.ndarray, v3: np.ndarray, normalize: bool = True
    ) -> np.ndarray:
        """
        삼각형 법선 벡터 계산

        Args:
            v1, v2, v3: 삼각형의 꼭짓점 좌표 (3D)
            normalize: 정규화 여부

        Returns:
            법선 벡터 (3D)
        """
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)

        if normalize and np.linalg.norm(normal) > 1e-10:
            normal = normal / np.linalg.norm(normal)

        return normal

    @staticmethod
    def calculate_mesh_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
        """
        메시의 부피 계산 (닫힌 메시)

        Signed volume 방법 사용.

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3, 각 면은 꼭짓점 인덱스)

        Returns:
            부피
        """
        volume = 0.0

        for face in faces:
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]

            # Signed volume of tetrahedron formed by origin and triangle
            volume += np.dot(v1, np.cross(v2, v3))

        return abs(volume) / 6.0

    @staticmethod
    def calculate_mesh_surface_area(
        vertices: np.ndarray, faces: np.ndarray
    ) -> float:
        """
        메시의 표면적 계산

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)

        Returns:
            표면적
        """
        total_area = 0.0

        for face in faces:
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]

            area = GeometricAnalyzer.calculate_triangle_area(v1, v2, v3)
            total_area += area

        return total_area

    @staticmethod
    def calculate_centroid(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
        """
        메시의 무게 중심 계산

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)

        Returns:
            무게 중심 좌표 (3D)
        """
        total_area = 0.0
        weighted_centroid = np.zeros(3)

        for face in faces:
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]

            # 삼각형 면적
            area = GeometricAnalyzer.calculate_triangle_area(v1, v2, v3)

            # 삼각형 중심
            triangle_center = (v1 + v2 + v3) / 3.0

            # 면적 가중 합
            weighted_centroid += area * triangle_center
            total_area += area

        if total_area > 1e-10:
            centroid = weighted_centroid / total_area
        else:
            centroid = np.zeros(3)

        return centroid

    @staticmethod
    def calculate_bounding_box(
        vertices: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        바운딩 박스 계산

        Args:
            vertices: 꼭짓점 배열 (N x 3)

        Returns:
            (min_point, max_point) 튜플
        """
        min_point = np.min(vertices, axis=0)
        max_point = np.max(vertices, axis=0)

        return min_point, max_point

    @staticmethod
    def calculate_bounding_box_volume(vertices: np.ndarray) -> float:
        """
        바운딩 박스의 부피

        Args:
            vertices: 꼭짓점 배열 (N x 3)

        Returns:
            바운딩 박스 부피
        """
        min_point, max_point = GeometricAnalyzer.calculate_bounding_box(vertices)
        dimensions = max_point - min_point
        volume = np.prod(dimensions)

        return float(volume)

    @staticmethod
    def calculate_inertia_tensor(
        vertices: np.ndarray, faces: np.ndarray, density: float = 1.0
    ) -> np.ndarray:
        """
        관성 텐서 계산

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)
            density: 밀도

        Returns:
            관성 텐서 (3 x 3)
        """
        inertia = np.zeros((3, 3))
        total_volume = 0.0

        for face in faces:
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]

            # Tetrahedron volume
            tet_volume = abs(np.dot(v1, np.cross(v2, v3))) / 6.0

            # Tetrahedron centroid
            tet_center = (v1 + v2 + v3) / 4.0

            # 관성 기여도 (simplified)
            for i in range(3):
                for j in range(3):
                    if i == j:
                        # 대각 성분
                        inertia[i, j] += tet_volume * (
                            tet_center[(i + 1) % 3] ** 2
                            + tet_center[(i + 2) % 3] ** 2
                        )
                    else:
                        # 비대각 성분
                        inertia[i, j] -= tet_volume * tet_center[i] * tet_center[j]

            total_volume += tet_volume

        inertia *= density

        return inertia

    @staticmethod
    def calculate_edge_length(v1: np.ndarray, v2: np.ndarray) -> float:
        """
        두 점 사이의 거리

        Args:
            v1, v2: 3D 좌표

        Returns:
            거리
        """
        return float(np.linalg.norm(v2 - v1))

    @staticmethod
    def calculate_average_edge_length(
        vertices: np.ndarray, faces: np.ndarray
    ) -> float:
        """
        평균 엣지 길이 계산

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)

        Returns:
            평균 엣지 길이
        """
        total_length = 0.0
        edge_count = 0

        for face in faces:
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]

            # 3개 엣지
            total_length += GeometricAnalyzer.calculate_edge_length(v1, v2)
            total_length += GeometricAnalyzer.calculate_edge_length(v2, v3)
            total_length += GeometricAnalyzer.calculate_edge_length(v3, v1)

            edge_count += 3

        if edge_count > 0:
            return total_length / edge_count
        else:
            return 0.0

    @staticmethod
    def calculate_aspect_ratio(vertices: np.ndarray) -> float:
        """
        바운딩 박스의 종횡비

        Args:
            vertices: 꼭짓점 배열 (N x 3)

        Returns:
            종횡비 (최대 차원 / 최소 차원)
        """
        min_point, max_point = GeometricAnalyzer.calculate_bounding_box(vertices)
        dimensions = max_point - min_point

        # 0으로 나누기 방지
        dimensions = np.maximum(dimensions, 1e-10)

        aspect_ratio = np.max(dimensions) / np.min(dimensions)

        return float(aspect_ratio)


class MeshQualityAnalyzer:
    """
    메시 품질 분석기

    메시의 품질 메트릭을 계산.
    """

    @staticmethod
    def calculate_triangle_quality(
        v1: np.ndarray, v2: np.ndarray, v3: np.ndarray
    ) -> float:
        """
        삼각형 품질 메트릭 (0~1, 1이 최고)

        정삼각형에 가까울수록 높은 값.

        Args:
            v1, v2, v3: 삼각형 꼭짓점

        Returns:
            품질 메트릭 (0~1)
        """
        # 엣지 길이
        a = np.linalg.norm(v2 - v1)
        b = np.linalg.norm(v3 - v2)
        c = np.linalg.norm(v1 - v3)

        # 반둘레
        s = (a + b + c) / 2.0

        # 면적 (Heron's formula)
        area_squared = s * (s - a) * (s - b) * (s - c)
        if area_squared < 0:
            return 0.0

        area = np.sqrt(area_squared)

        # 품질 메트릭: 4 * sqrt(3) * area / (a^2 + b^2 + c^2)
        # 정삼각형일 때 1
        quality = (4.0 * np.sqrt(3) * area) / (a**2 + b**2 + c**2 + 1e-10)

        return float(np.clip(quality, 0.0, 1.0))

    @staticmethod
    def calculate_mesh_quality(vertices: np.ndarray, faces: np.ndarray) -> dict:
        """
        메시 전체 품질 평가

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)

        Returns:
            품질 메트릭 딕셔너리
        """
        qualities = []

        for face in faces:
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]

            quality = MeshQualityAnalyzer.calculate_triangle_quality(v1, v2, v3)
            qualities.append(quality)

        qualities = np.array(qualities)

        return {
            "mean_quality": float(np.mean(qualities)),
            "min_quality": float(np.min(qualities)),
            "max_quality": float(np.max(qualities)),
            "std_quality": float(np.std(qualities)),
            "median_quality": float(np.median(qualities)),
            "num_poor_triangles": int(np.sum(qualities < 0.3)),  # 품질 30% 이하
        }
