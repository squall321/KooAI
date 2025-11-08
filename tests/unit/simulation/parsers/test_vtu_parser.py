"""
VTU 파서 단위 테스트
"""

import pytest
import tempfile
from pathlib import Path
import numpy as np

from src.core.simulation.parsers.vtu_parser import VTUParser
from src.core.simulation.models import FieldType, DataLocation


@pytest.fixture
def sample_vtu_file():
    """샘플 VTU 파일 생성"""
    content = """<?xml version="1.0"?>
<VTKFile type="UnstructuredGrid" version="0.1" byte_order="LittleEndian">
  <UnstructuredGrid>
    <Piece NumberOfPoints="8" NumberOfCells="1">
      <Points>
        <DataArray type="Float32" NumberOfComponents="3" format="ascii">
          0 0 0
          1 0 0
          1 1 0
          0 1 0
          0 0 1
          1 0 1
          1 1 1
          0 1 1
        </DataArray>
      </Points>
      <Cells>
        <DataArray type="Int32" Name="connectivity" format="ascii">
          0 1 2 3 4 5 6 7
        </DataArray>
        <DataArray type="Int32" Name="offsets" format="ascii">
          8
        </DataArray>
        <DataArray type="UInt8" Name="types" format="ascii">
          12
        </DataArray>
      </Cells>
      <PointData>
        <DataArray type="Float32" Name="pressure" NumberOfComponents="1" format="ascii">
          101325 101326 101327 101328 101329 101330 101331 101332
        </DataArray>
        <DataArray type="Float32" Name="velocity" NumberOfComponents="3" format="ascii">
          1.0 0.0 0.0
          1.1 0.1 0.0
          1.2 0.2 0.0
          1.3 0.3 0.0
          1.4 0.4 0.0
          1.5 0.5 0.0
          1.6 0.6 0.0
          1.7 0.7 0.0
        </DataArray>
      </PointData>
    </Piece>
  </UnstructuredGrid>
</VTKFile>
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".vtu", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_vtu_parser_can_parse(sample_vtu_file):
    """VTU 파일 인식 테스트"""
    parser = VTUParser()
    assert parser.can_parse(sample_vtu_file) is True


def test_vtu_parser_supported_extensions():
    """지원 확장자 테스트"""
    parser = VTUParser()
    extensions = parser.get_supported_extensions()
    assert ".vtu" in extensions


def test_vtu_parser_parse(sample_vtu_file):
    """VTU 파일 파싱 테스트"""
    parser = VTUParser()
    result = parser.parse(sample_vtu_file, name="Test VTU")

    # 기본 정보 확인
    assert result.name == "Test VTU"
    assert result.simulation_type == "VTU"
    assert result.num_timesteps == 1

    # 메시 확인
    assert result.mesh.num_vertices == 8
    assert result.mesh.vertices.shape == (8, 3)

    # 첫 번째 꼭짓점 확인
    assert np.allclose(result.mesh.vertices[0], [0, 0, 0])
    assert np.allclose(result.mesh.vertices[1], [1, 0, 0])

    # 필드 확인
    timestep = result.timesteps[0]
    assert "pressure" in timestep.fields
    assert "velocity" in timestep.fields

    # Pressure 필드 확인
    pressure = timestep.fields["pressure"]
    assert pressure.field_type == FieldType.SCALAR
    assert pressure.location == DataLocation.NODE
    assert len(pressure.data) == 8
    assert pressure.data[0] == 101325

    # Velocity 필드 확인
    velocity = timestep.fields["velocity"]
    assert velocity.field_type == FieldType.VECTOR
    assert velocity.location == DataLocation.NODE
    assert velocity.data.shape == (8, 3)
    assert np.allclose(velocity.data[0], [1.0, 0.0, 0.0])


def test_vtu_parser_invalid_file():
    """잘못된 VTU 파일 테스트"""
    content = """<?xml version="1.0"?>
<InvalidRoot>
</InvalidRoot>
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".vtu", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        parser = VTUParser()
        with pytest.raises(ValueError):
            parser.parse(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_vtu_parser_non_vtu_file():
    """VTU가 아닌 파일 테스트"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Not a VTU file")
        temp_path = Path(f.name)

    try:
        parser = VTUParser()
        assert parser.can_parse(temp_path) is False
    finally:
        if temp_path.exists():
            temp_path.unlink()
