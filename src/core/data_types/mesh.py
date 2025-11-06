"""
3D 메시 데이터 타입

3D 메시 데이터를 처리하는 클래스입니다.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import numpy as np

from src.core.data_types.base import BaseDataType, get_compression_strategy


@dataclass
class MeshData(BaseDataType):
    """
    3D 메시 데이터 클래스

    삼각형 또는 사각형 면으로 구성된 3D 메시를 나타냅니다.
    CFD, FEA, 3D 모델링 등에서 사용됩니다.

    Attributes:
        vertices: 정점 배열 (N, 3)
        faces: 면 배열 (M, 3) 또는 (M, 4)
        normals: 법선 벡터 배열 (선택적)
        attributes: 노드별 속성 (압력, 온도, 속도 등)
    """

    vertices: np.ndarray
    faces: np.ndarray
    normals: Optional[np.ndarray] = None
    attributes: Dict[str, np.ndarray] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """초기화 후 검증 및 설정"""
        super().__init__(data_type="mesh")

        # NumPy 배열로 변환
        if not isinstance(self.vertices, np.ndarray):
            self.vertices = np.array(self.vertices)

        if not isinstance(self.faces, np.ndarray):
            self.faces = np.array(self.faces)

        if self.normals is not None and not isinstance(self.normals, np.ndarray):
            self.normals = np.array(self.normals)

        # 검증
        self.validate()

    def validate(self) -> bool:
        """
        메시 데이터 유효성 검증

        Returns:
            bool: 유효하면 True

        Raises:
            ValueError: 유효하지 않은 데이터
        """
        # 정점 검증
        if self.vertices.ndim != 2:
            raise ValueError(f"Vertices must be 2D array, got shape {self.vertices.shape}")

        if self.vertices.shape[1] != 3:
            raise ValueError(
                f"Vertices must have 3 coordinates, got shape {self.vertices.shape}"
            )

        # 면 검증
        if self.faces.ndim != 2:
            raise ValueError(f"Faces must be 2D array, got shape {self.faces.shape}")

        if self.faces.shape[1] not in [3, 4]:
            raise ValueError(
                f"Faces must be triangles (3) or quads (4), got shape {self.faces.shape}"
            )

        # 인덱스 유효성
        max_vertex_idx = np.max(self.faces)
        num_vertices = len(self.vertices)
        if max_vertex_idx >= num_vertices:
            raise ValueError(
                f"Face indices out of range: max index {max_vertex_idx}, "
                f"but only {num_vertices} vertices"
            )

        # 법선 검증
        if self.normals is not None:
            if self.normals.shape != (len(self.faces), 3):
                raise ValueError(
                    f"Normals shape {self.normals.shape} doesn't match "
                    f"expected ({len(self.faces)}, 3)"
                )

        # NaN, Inf 체크
        if np.any(np.isnan(self.vertices)) or np.any(np.isinf(self.vertices)):
            raise ValueError("Vertices contain NaN or Inf values")

        return True

    def serialize(self) -> Dict[str, Any]:
        """
        딕셔너리로 직렬화

        Returns:
            Dict[str, Any]: 직렬화된 데이터
        """
        return {
            "data_type": self.data_type,
            "vertices": self.vertices.tolist(),
            "faces": self.faces.tolist(),
            "normals": self.normals.tolist() if self.normals is not None else None,
            "attributes": {k: v.tolist() for k, v in self.attributes.items()},
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "MeshData":
        """
        딕셔너리로부터 객체 생성

        Args:
            data: 직렬화된 데이터

        Returns:
            MeshData: 생성된 객체
        """
        normals = data.get("normals")
        if normals is not None:
            normals = np.array(normals)

        attributes = data.get("attributes", {})
        attributes = {k: np.array(v) for k, v in attributes.items()}

        return cls(
            vertices=np.array(data["vertices"]),
            faces=np.array(data["faces"]),
            normals=normals,
            attributes=attributes,
        )

    def compress(self, method: str = "default") -> bytes:
        """
        메시 데이터 압축

        Args:
            method: 압축 방법 (default, gzip)

        Returns:
            bytes: 압축된 데이터
        """
        import pickle

        data = {
            "vertices": self.vertices,
            "faces": self.faces,
            "normals": self.normals,
            "attributes": self.attributes,
        }

        serialized = pickle.dumps(data)

        if method == "gzip":
            import gzip

            return gzip.compress(serialized)

        return serialized

    @classmethod
    def decompress(cls, data: bytes, method: str = "default") -> "MeshData":
        """
        압축 해제

        Args:
            data: 압축된 데이터
            method: 압축 방법

        Returns:
            MeshData: 압축 해제된 객체
        """
        import pickle

        if method == "gzip":
            import gzip

            data = gzip.decompress(data)

        unpacked = pickle.loads(data)

        return cls(
            vertices=unpacked["vertices"],
            faces=unpacked["faces"],
            normals=unpacked.get("normals"),
            attributes=unpacked.get("attributes", {}),
        )

    def get_metadata(self) -> Dict[str, Any]:
        """
        메타데이터 추출

        Returns:
            Dict[str, Any]: 메타데이터
        """
        metadata = super().get_metadata()
        metadata.update(
            {
                "num_vertices": len(self.vertices),
                "num_faces": len(self.faces),
                "face_type": "triangle" if self.faces.shape[1] == 3 else "quad",
                "has_normals": self.normals is not None,
                "attributes": list(self.attributes.keys()),
                "bounding_box": self.get_bounding_box(),
                "volume": self.compute_volume() if self.is_closed() else None,
                "surface_area": self.compute_surface_area(),
            }
        )
        return metadata

    def get_size_bytes(self) -> int:
        """
        데이터 크기 계산

        Returns:
            int: 바이트 단위 크기
        """
        size = self.vertices.nbytes + self.faces.nbytes

        if self.normals is not None:
            size += self.normals.nbytes

        for attr_array in self.attributes.values():
            size += attr_array.nbytes

        return size

    # === 메시 분석 메서드 ===

    def get_bounding_box(self) -> Dict[str, Dict[str, float]]:
        """
        경계 상자 계산

        Returns:
            Dict: 최소/최대 좌표
        """
        min_coords = np.min(self.vertices, axis=0)
        max_coords = np.max(self.vertices, axis=0)

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

    def compute_normals(self) -> np.ndarray:
        """
        면 법선 벡터 계산

        Returns:
            np.ndarray: 법선 벡터 배열 (num_faces, 3)
        """
        if self.faces.shape[1] == 3:
            # 삼각형 메시
            v0 = self.vertices[self.faces[:, 0]]
            v1 = self.vertices[self.faces[:, 1]]
            v2 = self.vertices[self.faces[:, 2]]

            # 외적으로 법선 계산
            normals = np.cross(v1 - v0, v2 - v0)

            # 정규화
            lengths = np.linalg.norm(normals, axis=1, keepdims=True)
            lengths[lengths == 0] = 1  # 0으로 나누기 방지
            normals = normals / lengths

            return normals
        else:
            # 사각형 메시 - 두 삼각형으로 분할하여 평균
            v0 = self.vertices[self.faces[:, 0]]
            v1 = self.vertices[self.faces[:, 1]]
            v2 = self.vertices[self.faces[:, 2]]
            v3 = self.vertices[self.faces[:, 3]]

            normal1 = np.cross(v1 - v0, v2 - v0)
            normal2 = np.cross(v2 - v0, v3 - v0)

            normals = (normal1 + normal2) / 2

            # 정규화
            lengths = np.linalg.norm(normals, axis=1, keepdims=True)
            lengths[lengths == 0] = 1
            normals = normals / lengths

            return normals

    def compute_surface_area(self) -> float:
        """
        표면적 계산

        Returns:
            float: 표면적
        """
        if self.faces.shape[1] == 3:
            # 삼각형 면적의 합
            v0 = self.vertices[self.faces[:, 0]]
            v1 = self.vertices[self.faces[:, 1]]
            v2 = self.vertices[self.faces[:, 2]]

            # 외적의 크기 / 2 = 삼각형 면적
            cross_products = np.cross(v1 - v0, v2 - v0)
            areas = np.linalg.norm(cross_products, axis=1) / 2

            return float(np.sum(areas))
        else:
            # 사각형을 두 삼각형으로 분할
            v0 = self.vertices[self.faces[:, 0]]
            v1 = self.vertices[self.faces[:, 1]]
            v2 = self.vertices[self.faces[:, 2]]
            v3 = self.vertices[self.faces[:, 3]]

            # 첫 번째 삼각형 (0, 1, 2)
            area1 = np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1) / 2

            # 두 번째 삼각형 (0, 2, 3)
            area2 = np.linalg.norm(np.cross(v2 - v0, v3 - v0), axis=1) / 2

            return float(np.sum(area1 + area2))

    def compute_volume(self) -> float:
        """
        부피 계산 (닫힌 메시만 해당)

        Returns:
            float: 부피

        Note:
            메시가 닫혀있지 않으면 결과가 정확하지 않을 수 있습니다.
        """
        if self.faces.shape[1] != 3:
            raise ValueError("Volume calculation only supported for triangle meshes")

        v0 = self.vertices[self.faces[:, 0]]
        v1 = self.vertices[self.faces[:, 1]]
        v2 = self.vertices[self.faces[:, 2]]

        # 부호 있는 사면체 부피의 합
        volume = np.sum(np.cross(v0, v1) * v2) / 6.0

        return abs(volume)

    def is_closed(self) -> bool:
        """
        메시가 닫혀 있는지 확인 (간단한 휴리스틱)

        Returns:
            bool: 닫혀 있으면 True
        """
        # 각 엣지가 정확히 2개의 면에 의해 공유되는지 확인
        # 간단한 구현: 모든 면이 연결되어 있는지만 확인
        # (완전한 구현은 더 복잡함)

        if self.faces.shape[1] != 3:
            return False  # 삼각형 메시만 지원

        # 엣지 딕셔너리 생성
        edge_count: Dict[Tuple[int, int], int] = {}

        for face in self.faces:
            # 각 면의 3개 엣지
            edges = [
                tuple(sorted([face[0], face[1]])),
                tuple(sorted([face[1], face[2]])),
                tuple(sorted([face[2], face[0]])),
            ]

            for edge in edges:
                edge_count[edge] = edge_count.get(edge, 0) + 1

        # 모든 엣지가 정확히 2개의 면에 공유되면 닫혀 있음
        return all(count == 2 for count in edge_count.values())

    def simplify(self, target_reduction: float = 0.5) -> "MeshData":
        """
        메시 단순화 (정점 수 감소)

        Args:
            target_reduction: 감소 비율 (0.5 = 50% 감소)

        Returns:
            MeshData: 단순화된 메시

        Note:
            간단한 구현입니다. 실제로는 PyVista 등의 라이브러리 사용 권장
        """
        if target_reduction <= 0 or target_reduction >= 1:
            raise ValueError("target_reduction must be between 0 and 1")

        # 간단한 정점 제거 전략: 무작위로 정점 제거
        # 실제 프로덕션에서는 Quadric Error Metrics 등 사용

        num_vertices_to_keep = int(len(self.vertices) * (1 - target_reduction))
        num_vertices_to_keep = max(4, num_vertices_to_keep)  # 최소 4개 유지

        # 사용되는 정점만 유지
        unique_vertex_indices = np.unique(self.faces.flatten())

        if len(unique_vertex_indices) <= num_vertices_to_keep:
            return MeshData(
                vertices=self.vertices.copy(),
                faces=self.faces.copy(),
                normals=self.normals.copy() if self.normals is not None else None,
                attributes={k: v.copy() for k, v in self.attributes.items()},
            )

        # 유지할 정점 선택
        np.random.seed(42)  # 재현성
        kept_indices = np.sort(
            np.random.choice(unique_vertex_indices, num_vertices_to_keep, replace=False)
        )

        # 인덱스 매핑
        old_to_new = {old_idx: new_idx for new_idx, old_idx in enumerate(kept_indices)}

        # 새 정점 배열
        new_vertices = self.vertices[kept_indices]

        # 새 면 배열 (유효한 면만 유지)
        new_faces = []
        for face in self.faces:
            if all(idx in old_to_new for idx in face):
                new_face = [old_to_new[idx] for idx in face]
                new_faces.append(new_face)

        if len(new_faces) == 0:
            raise ValueError("Simplification resulted in no faces")

        new_faces = np.array(new_faces)

        return MeshData(vertices=new_vertices, faces=new_faces)

    def get_vertex_attribute(self, name: str) -> Optional[np.ndarray]:
        """
        정점 속성 조회

        Args:
            name: 속성 이름

        Returns:
            np.ndarray: 속성 배열, 없으면 None
        """
        return self.attributes.get(name)

    def set_vertex_attribute(self, name: str, values: np.ndarray) -> None:
        """
        정점 속성 설정

        Args:
            name: 속성 이름
            values: 속성 값 배열

        Raises:
            ValueError: 배열 크기가 정점 수와 맞지 않으면
        """
        if len(values) != len(self.vertices):
            raise ValueError(
                f"Attribute size {len(values)} doesn't match "
                f"number of vertices {len(self.vertices)}"
            )

        self.attributes[name] = values
