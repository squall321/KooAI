"""
DataTypeFactory 테스트
"""

import pytest
import numpy as np
from src.core.factories.data_type_factory import DataTypeFactory
from src.core.data_types.contour import ContourData
from src.core.data_types.mesh import MeshData
from src.core.data_types.curve import CurveData


class TestDataTypeFactory:
    """DataTypeFactory 클래스 테스트"""

    def test_create_contour(self):
        """컨투어 생성"""
        data = {
            "points": [[0, 0], [1, 1], [2, 0]],
            "is_closed": False,
        }

        contour = DataTypeFactory.create("contour", data)

        assert isinstance(contour, ContourData)
        assert len(contour.points) == 3

    def test_create_mesh(self):
        """메시 생성"""
        data = {
            "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            "faces": [[0, 1, 2]],
        }

        mesh = DataTypeFactory.create("mesh", data)

        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) == 3

    def test_create_curve(self):
        """커브 생성"""
        data = {
            "x": [0, 1, 2],
            "y": [0, 1, 0],
        }

        curve = DataTypeFactory.create("curve", data)

        assert isinstance(curve, CurveData)
        assert len(curve.x) == 3

    def test_create_unknown_type_raises_error(self):
        """알 수 없는 타입 생성 시 에러"""
        with pytest.raises(ValueError, match="Unknown data type"):
            DataTypeFactory.create("unknown", {})

    def test_get_registered_types(self):
        """등록된 타입 목록"""
        types = DataTypeFactory.get_registered_types()

        assert "contour" in types
        assert "mesh" in types
        assert "curve" in types

    def test_is_registered(self):
        """등록 여부 확인"""
        assert DataTypeFactory.is_registered("contour")
        assert not DataTypeFactory.is_registered("unknown")
