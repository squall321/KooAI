"""
Tests for Core Domain Value Objects

Tests Coordinate3D, Vector3D, and other immutable value objects.
"""

import math
import pytest


class TestCoordinate3D:
    """Test Coordinate3D value object"""

    def test_coordinate_creation(self) -> None:
        """Test creating Coordinate3D"""
        from src.core.domain.value_objects import Coordinate3D

        coord = Coordinate3D(x=1.0, y=2.0, z=3.0)

        assert coord.x == 1.0
        assert coord.y == 2.0
        assert coord.z == 3.0

    def test_coordinate_is_frozen(self) -> None:
        """Test Coordinate3D is immutable"""
        from src.core.domain.value_objects import Coordinate3D

        coord = Coordinate3D(x=1.0, y=2.0, z=3.0)

        with pytest.raises(Exception):  # FrozenInstanceError in dataclasses
            coord.x = 5.0  # type: ignore[misc]

    def test_coordinate_equality(self) -> None:
        """Test Coordinate3D equality"""
        from src.core.domain.value_objects import Coordinate3D

        coord1 = Coordinate3D(x=1.0, y=2.0, z=3.0)
        coord2 = Coordinate3D(x=1.0, y=2.0, z=3.0)
        coord3 = Coordinate3D(x=1.0, y=2.0, z=4.0)

        assert coord1 == coord2
        assert coord1 != coord3

    def test_coordinate_nan_raises_error(self) -> None:
        """Test NaN coordinates raise ValueError"""
        from src.core.domain.value_objects import Coordinate3D

        with pytest.raises(ValueError, match="cannot be NaN"):
            Coordinate3D(x=float('nan'), y=2.0, z=3.0)

    def test_coordinate_inf_raises_error(self) -> None:
        """Test Inf coordinates raise ValueError"""
        from src.core.domain.value_objects import Coordinate3D

        with pytest.raises(ValueError, match="cannot be NaN or Inf"):
            Coordinate3D(x=float('inf'), y=2.0, z=3.0)

    def test_coordinate_distance_to(self) -> None:
        """Test distance calculation"""
        from src.core.domain.value_objects import Coordinate3D

        coord1 = Coordinate3D(x=0.0, y=0.0, z=0.0)
        coord2 = Coordinate3D(x=3.0, y=4.0, z=0.0)

        distance = coord1.distance_to(coord2)

        assert distance == 5.0  # 3-4-5 triangle

    def test_coordinate_to_tuple(self) -> None:
        """Test converting to tuple"""
        from src.core.domain.value_objects import Coordinate3D

        coord = Coordinate3D(x=1.0, y=2.0, z=3.0)

        assert coord.to_tuple() == (1.0, 2.0, 3.0)

    def test_coordinate_from_tuple(self) -> None:
        """Test creating from tuple"""
        from src.core.domain.value_objects import Coordinate3D

        coord = Coordinate3D.from_tuple((1.0, 2.0, 3.0))

        assert coord.x == 1.0
        assert coord.y == 2.0
        assert coord.z == 3.0

    def test_coordinate_origin(self) -> None:
        """Test origin factory method"""
        from src.core.domain.value_objects import Coordinate3D

        origin = Coordinate3D.origin()

        assert origin.x == 0.0
        assert origin.y == 0.0
        assert origin.z == 0.0


class TestVector3D:
    """Test Vector3D value object"""

    def test_vector_creation(self) -> None:
        """Test creating Vector3D"""
        from src.core.domain.value_objects import Vector3D

        vec = Vector3D(x=1.0, y=2.0, z=3.0)

        assert vec.x == 1.0
        assert vec.y == 2.0
        assert vec.z == 3.0

    def test_vector_is_frozen(self) -> None:
        """Test Vector3D is immutable"""
        from src.core.domain.value_objects import Vector3D

        vec = Vector3D(x=1.0, y=2.0, z=3.0)

        with pytest.raises(Exception):  # FrozenInstanceError
            vec.x = 5.0  # type: ignore[misc]

    def test_vector_nan_raises_error(self) -> None:
        """Test NaN components raise ValueError"""
        from src.core.domain.value_objects import Vector3D

        with pytest.raises(ValueError, match="cannot be NaN"):
            Vector3D(x=float('nan'), y=2.0, z=3.0)

    def test_vector_inf_raises_error(self) -> None:
        """Test Inf components raise ValueError"""
        from src.core.domain.value_objects import Vector3D

        with pytest.raises(ValueError, match="cannot be NaN or Inf"):
            Vector3D(x=float('inf'), y=2.0, z=3.0)

    def test_vector_magnitude(self) -> None:
        """Test vector magnitude calculation"""
        from src.core.domain.value_objects import Vector3D

        vec = Vector3D(x=3.0, y=4.0, z=0.0)

        assert vec.magnitude() == 5.0  # 3-4-5 triangle

    def test_vector_normalize(self) -> None:
        """Test vector normalization"""
        from src.core.domain.value_objects import Vector3D

        vec = Vector3D(x=3.0, y=4.0, z=0.0)
        normalized = vec.normalize()

        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert normalized.x == 0.6
        assert normalized.y == 0.8

    def test_vector_normalize_zero_raises_error(self) -> None:
        """Test normalizing zero vector raises error"""
        from src.core.domain.value_objects import Vector3D

        zero_vec = Vector3D(x=0.0, y=0.0, z=0.0)

        with pytest.raises(ValueError, match="Cannot normalize zero vector"):
            zero_vec.normalize()

    def test_vector_dot_product(self) -> None:
        """Test dot product"""
        from src.core.domain.value_objects import Vector3D

        vec1 = Vector3D(x=1.0, y=2.0, z=3.0)
        vec2 = Vector3D(x=4.0, y=5.0, z=6.0)

        dot = vec1.dot(vec2)

        assert dot == 1*4 + 2*5 + 3*6  # 32

    def test_vector_cross_product(self) -> None:
        """Test cross product"""
        from src.core.domain.value_objects import Vector3D

        vec1 = Vector3D(x=1.0, y=0.0, z=0.0)
        vec2 = Vector3D(x=0.0, y=1.0, z=0.0)

        cross = vec1.cross(vec2)

        assert cross.x == 0.0
        assert cross.y == 0.0
        assert cross.z == 1.0

    def test_vector_scale(self) -> None:
        """Test scaling vector"""
        from src.core.domain.value_objects import Vector3D

        vec = Vector3D(x=1.0, y=2.0, z=3.0)
        scaled = vec.scale(2.0)

        assert scaled.x == 2.0
        assert scaled.y == 4.0
        assert scaled.z == 6.0


    def test_vector_perpendicular(self) -> None:
        """Test dot product of perpendicular vectors is zero"""
        from src.core.domain.value_objects import Vector3D

        vec1 = Vector3D(x=1.0, y=0.0, z=0.0)
        vec2 = Vector3D(x=0.0, y=1.0, z=0.0)

        dot = vec1.dot(vec2)

        assert dot == 0.0

    def test_vector_parallel(self) -> None:
        """Test cross product of parallel vectors is zero"""
        from src.core.domain.value_objects import Vector3D

        vec1 = Vector3D(x=1.0, y=2.0, z=3.0)
        vec2 = Vector3D(x=2.0, y=4.0, z=6.0)

        cross = vec1.cross(vec2)

        assert cross.magnitude() < 1e-10
