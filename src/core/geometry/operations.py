"""
3D 메시 조작

메시 변환, 단순화, 스무딩 등의 조작 기능.
"""

from typing import Tuple

import numpy as np


class MeshOperations:
    """
    메시 조작 연산

    메시 변환, 단순화, 스무딩 등.
    """

    @staticmethod
    def translate(vertices: np.ndarray, translation: np.ndarray) -> np.ndarray:
        """
        메시 이동

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            translation: 이동 벡터 (3,)

        Returns:
            이동된 꼭짓점
        """
        return vertices + translation

    @staticmethod
    def rotate(vertices: np.ndarray, rotation_matrix: np.ndarray) -> np.ndarray:
        """
        메시 회전

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            rotation_matrix: 회전 행렬 (3 x 3)

        Returns:
            회전된 꼭짓점
        """
        return np.dot(vertices, rotation_matrix.T)

    @staticmethod
    def scale(vertices: np.ndarray, scale_factor: float) -> np.ndarray:
        """
        메시 스케일 변경

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            scale_factor: 스케일 인자

        Returns:
            스케일된 꼭짓점
        """
        return vertices * scale_factor

    @staticmethod
    def normalize_scale(vertices: np.ndarray) -> np.ndarray:
        """
        메시를 단위 박스로 정규화

        Args:
            vertices: 꼭짓점 배열 (N x 3)

        Returns:
            정규화된 꼭짓점
        """
        min_point = np.min(vertices, axis=0)
        max_point = np.max(vertices, axis=0)

        # 중심으로 이동
        centered = vertices - (min_point + max_point) / 2.0

        # 최대 차원으로 스케일
        max_extent = np.max(max_point - min_point)
        if max_extent > 1e-10:
            normalized = centered / max_extent
        else:
            normalized = centered

        return normalized

    @staticmethod
    def center_at_origin(vertices: np.ndarray) -> np.ndarray:
        """
        메시를 원점 중심으로 이동

        Args:
            vertices: 꼭짓점 배열 (N x 3)

        Returns:
            중심 이동된 꼭짓점
        """
        centroid = np.mean(vertices, axis=0)
        return vertices - centroid

    @staticmethod
    def flip_normals(faces: np.ndarray) -> np.ndarray:
        """
        법선 방향 반전 (면의 와인딩 순서 반전)

        Args:
            faces: 면 배열 (M x 3)

        Returns:
            반전된 면
        """
        # 와인딩 순서 반전
        return faces[:, [0, 2, 1]]

    @staticmethod
    def laplacian_smoothing(
        vertices: np.ndarray,
        faces: np.ndarray,
        iterations: int = 1,
        lambda_factor: float = 0.5,
    ) -> np.ndarray:
        """
        Laplacian 스무딩

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)
            iterations: 반복 횟수
            lambda_factor: 스무딩 강도 (0~1)

        Returns:
            스무딩된 꼭짓점
        """
        smoothed = vertices.copy()

        # 인접 정보 구축
        adjacency = MeshOperations._build_adjacency(len(vertices), faces)

        for _ in range(iterations):
            new_vertices = smoothed.copy()

            for i, neighbors in enumerate(adjacency):
                if len(neighbors) > 0:
                    # 이웃 평균
                    neighbor_mean = np.mean(smoothed[list(neighbors)], axis=0)

                    # Laplacian 업데이트
                    new_vertices[i] = (1 - lambda_factor) * smoothed[
                        i
                    ] + lambda_factor * neighbor_mean

            smoothed = new_vertices

        return smoothed

    @staticmethod
    def _build_adjacency(num_vertices: int, faces: np.ndarray) -> list[set]:
        """
        꼭짓점 인접 정보 구축

        Args:
            num_vertices: 꼭짓점 개수
            faces: 면 배열 (M x 3)

        Returns:
            각 꼭짓점의 이웃 인덱스 set 리스트
        """
        adjacency = [set() for _ in range(num_vertices)]

        for face in faces:
            v1, v2, v3 = face

            adjacency[v1].add(v2)
            adjacency[v1].add(v3)

            adjacency[v2].add(v1)
            adjacency[v2].add(v3)

            adjacency[v3].add(v1)
            adjacency[v3].add(v2)

        return adjacency

    @staticmethod
    def decimate(
        vertices: np.ndarray, faces: np.ndarray, target_faces: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        메시 단순화 (간단한 버전)

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)
            target_faces: 목표 면 개수

        Returns:
            (단순화된 꼭짓점, 단순화된 면)
        """
        # 간단한 uniform decimation
        # 실제 구현은 quadric error metrics 등을 사용해야 함

        if len(faces) <= target_faces:
            return vertices.copy(), faces.copy()

        # 면을 균등하게 샘플링
        step = len(faces) / target_faces
        indices = np.arange(0, len(faces), step).astype(int)
        indices = indices[:target_faces]

        decimated_faces = faces[indices]

        # 사용된 꼭짓점만 추출
        used_vertices = set(decimated_faces.flatten())
        vertex_map = {old: new for new, old in enumerate(sorted(used_vertices))}

        new_vertices = vertices[sorted(used_vertices)]
        new_faces = np.array([[vertex_map[v] for v in face] for face in decimated_faces])

        return new_vertices, new_faces

    @staticmethod
    def subdivide(vertices: np.ndarray, faces: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        메시 서브디비전 (Loop subdivision 간단 버전)

        각 삼각형을 4개로 분할.

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)

        Returns:
            (서브디비전된 꼭짓점, 서브디비전된 면)
        """
        new_vertices = list(vertices)
        new_faces = []

        # 엣지 중점 맵
        edge_midpoints = {}

        def get_midpoint_index(v1: int, v2: int) -> int:
            """엣지 중점 인덱스 가져오기 (없으면 생성)"""
            edge = tuple(sorted([v1, v2]))

            if edge not in edge_midpoints:
                midpoint = (vertices[v1] + vertices[v2]) / 2.0
                edge_midpoints[edge] = len(new_vertices)
                new_vertices.append(midpoint)

            return edge_midpoints[edge]

        # 각 면을 4개로 분할
        for face in faces:
            v1, v2, v3 = face

            # 엣지 중점
            m1 = get_midpoint_index(v1, v2)
            m2 = get_midpoint_index(v2, v3)
            m3 = get_midpoint_index(v3, v1)

            # 4개 삼각형 생성
            new_faces.append([v1, m1, m3])
            new_faces.append([v2, m2, m1])
            new_faces.append([v3, m3, m2])
            new_faces.append([m1, m2, m3])

        return np.array(new_vertices), np.array(new_faces)

    @staticmethod
    def remove_duplicates(
        vertices: np.ndarray, faces: np.ndarray, tolerance: float = 1e-6
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        중복 꼭짓점 제거

        Args:
            vertices: 꼭짓점 배열 (N x 3)
            faces: 면 배열 (M x 3)
            tolerance: 거리 허용 오차

        Returns:
            (중복 제거된 꼭짓점, 업데이트된 면)
        """
        unique_vertices = []
        vertex_map = {}

        for i, vertex in enumerate(vertices):
            # 기존 꼭짓점 중 가까운 것 찾기
            found = False

            for j, unique_vertex in enumerate(unique_vertices):
                if np.linalg.norm(vertex - unique_vertex) < tolerance:
                    vertex_map[i] = j
                    found = True
                    break

            if not found:
                vertex_map[i] = len(unique_vertices)
                unique_vertices.append(vertex)

        # 면 업데이트
        new_faces = np.array([[vertex_map[v] for v in face] for face in faces])

        return np.array(unique_vertices), new_faces


class MeshTransform:
    """
    메시 변환 유틸리티

    회전 행렬 생성 등.
    """

    @staticmethod
    def rotation_matrix_x(angle: float) -> np.ndarray:
        """
        X축 회전 행렬

        Args:
            angle: 각도 (라디안)

        Returns:
            회전 행렬 (3 x 3)
        """
        c = np.cos(angle)
        s = np.sin(angle)

        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

    @staticmethod
    def rotation_matrix_y(angle: float) -> np.ndarray:
        """
        Y축 회전 행렬

        Args:
            angle: 각도 (라디안)

        Returns:
            회전 행렬 (3 x 3)
        """
        c = np.cos(angle)
        s = np.sin(angle)

        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

    @staticmethod
    def rotation_matrix_z(angle: float) -> np.ndarray:
        """
        Z축 회전 행렬

        Args:
            angle: 각도 (라디안)

        Returns:
            회전 행렬 (3 x 3)
        """
        c = np.cos(angle)
        s = np.sin(angle)

        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    @staticmethod
    def rotation_matrix_axis_angle(axis: np.ndarray, angle: float) -> np.ndarray:
        """
        임의 축 회전 행렬 (Rodrigues' rotation formula)

        Args:
            axis: 회전축 (정규화된 3D 벡터)
            angle: 각도 (라디안)

        Returns:
            회전 행렬 (3 x 3)
        """
        axis = axis / np.linalg.norm(axis)
        c = np.cos(angle)
        s = np.sin(angle)
        t = 1 - c

        x, y, z = axis

        return np.array(
            [
                [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
                [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
                [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
            ]
        )
