#!/usr/bin/env python3
"""
샘플 시뮬레이션 데이터 생성 스크립트

예제 실행을 위한 다양한 형식의 샘플 데이터를 생성합니다.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_sample_csv(output_path: Path):
    """
    CSV 형식 샘플 데이터 생성

    시뮬레이션: 2D 열전달 문제
    """
    logger.info(f"Creating CSV sample: {output_path}")

    # 10x10 그리드, 5 타임스텝
    n_points = 100
    n_timesteps = 5

    data = []
    for t in range(n_timesteps):
        for i in range(n_points):
            x = (i % 10) * 0.1
            y = (i // 10) * 0.1

            # 시간에 따라 변하는 온도 분포
            temperature = 300 + 50 * np.sin(np.pi * x) * np.sin(np.pi * y) * (1 + 0.1 * t)
            pressure = 101325 + 1000 * np.cos(np.pi * x) * np.cos(np.pi * y)
            velocity_x = 0.1 * np.sin(2 * np.pi * x)
            velocity_y = 0.1 * np.cos(2 * np.pi * y)

            data.append({
                'timestep': t,
                'point_id': i,
                'x': x,
                'y': y,
                'z': 0.0,
                'temperature': temperature,
                'pressure': pressure,
                'velocity_x': velocity_x,
                'velocity_y': velocity_y,
                'velocity_z': 0.0,
            })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)

    file_size_kb = output_path.stat().st_size / 1024
    logger.info(f"✅ Created: {output_path.name} ({len(df)} rows, {file_size_kb:.1f} KB)")


def create_large_csv(output_path: Path):
    """대용량 CSV 샘플 (배치 처리 테스트용)"""
    logger.info(f"Creating large CSV sample: {output_path}")

    n_points = 10000
    n_timesteps = 10

    # 메모리 효율을 위해 청크로 생성
    chunk_size = 50000
    first_chunk = True

    for t in range(n_timesteps):
        chunk_data = []
        for i in range(n_points):
            x = np.random.random()
            y = np.random.random()
            z = np.random.random()

            temperature = 300 + 50 * np.random.random()
            pressure = 101325 + 1000 * np.random.randn()

            chunk_data.append({
                'timestep': t,
                'point_id': i,
                'x': x,
                'y': y,
                'z': z,
                'temperature': temperature,
                'pressure': pressure,
            })

        df_chunk = pd.DataFrame(chunk_data)

        # 첫 청크는 헤더 포함, 나머지는 append
        if first_chunk:
            df_chunk.to_csv(output_path, index=False, mode='w')
            first_chunk = False
        else:
            df_chunk.to_csv(output_path, index=False, mode='a', header=False)

    file_size_mb = output_path.stat().st_size / 1024 / 1024
    total_rows = n_points * n_timesteps
    logger.info(f"✅ Created: {output_path.name} ({total_rows} rows, {file_size_mb:.1f} MB)")


def create_vtk_ascii(output_path: Path):
    """
    VTK Legacy ASCII 형식 샘플 생성
    """
    logger.info(f"Creating VTK sample: {output_path}")

    # 5x5x5 structured grid
    nx, ny, nz = 5, 5, 5
    n_points = nx * ny * nz

    with open(output_path, 'w') as f:
        # Header
        f.write("# vtk DataFile Version 3.0\n")
        f.write("Sample 3D structured grid\n")
        f.write("ASCII\n")
        f.write("DATASET STRUCTURED_POINTS\n")
        f.write(f"DIMENSIONS {nx} {ny} {nz}\n")
        f.write("ORIGIN 0.0 0.0 0.0\n")
        f.write("SPACING 0.1 0.1 0.1\n")
        f.write(f"POINT_DATA {n_points}\n")

        # Temperature field (scalar)
        f.write("SCALARS temperature float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    x, y, z = i * 0.1, j * 0.1, k * 0.1
                    temp = 300 + 50 * np.sin(np.pi * x) * np.sin(np.pi * y) * np.sin(np.pi * z)
                    f.write(f"{temp:.6f}\n")

        # Velocity field (vector)
        f.write("VECTORS velocity float\n")
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    x, y, z = i * 0.1, j * 0.1, k * 0.1
                    vx = 0.1 * np.sin(2 * np.pi * x)
                    vy = 0.1 * np.cos(2 * np.pi * y)
                    vz = 0.05 * np.sin(np.pi * z)
                    f.write(f"{vx:.6f} {vy:.6f} {vz:.6f}\n")

    file_size_kb = output_path.stat().st_size / 1024
    logger.info(f"✅ Created: {output_path.name} ({file_size_kb:.1f} KB)")


def create_readme(output_dir: Path):
    """샘플 데이터 설명 README"""
    readme_content = """# 샘플 시뮬레이션 데이터

이 디렉토리는 KooAI 예제 실행을 위한 샘플 데이터를 포함합니다.

## 파일 설명

### simple_temperature.csv
- **형식**: CSV
- **크기**: ~50KB
- **설명**: 2D 열전달 시뮬레이션 결과
- **타임스텝**: 5개
- **포인트 수**: 100개 (10x10 그리드)
- **필드**: temperature, pressure, velocity (x, y, z)
- **용도**: 기본 사용 예제 (`01_basic_usage.py`)

### flow_simulation.csv
- **형식**: CSV
- **크기**: ~15MB
- **설명**: 대용량 유동 시뮬레이션
- **타임스텝**: 10개
- **포인트 수**: 10,000개
- **필드**: temperature, pressure
- **용도**: 배치 처리 예제 (`02_batch_processing.py`)

### pressure_field.vtk
- **형식**: VTK Legacy ASCII
- **크기**: ~100KB
- **설명**: 3D 구조 격자 데이터
- **차원**: 5x5x5
- **필드**: temperature (scalar), velocity (vector)
- **용도**: VTK 파싱 테스트

## 재생성 방법

샘플 데이터를 다시 생성하려면:

```bash
python scripts/generate_sample_data.py
```

## 커스텀 데이터

자신의 시뮬레이션 데이터를 사용하려면:

### 1. CSV 형식

필수 컬럼:
- `timestep`: 타임스텝 번호
- `point_id`: 포인트 ID
- `x`, `y`, `z`: 좌표
- 분석할 필드 (예: `temperature`, `pressure`)

예시:
```csv
timestep,point_id,x,y,z,temperature,pressure
0,0,0.0,0.0,0.0,300.5,101325.0
0,1,0.1,0.0,0.0,305.2,101330.0
...
```

### 2. VTK 형식

지원 형식:
- **VTK Legacy ASCII** (`.vtk`)
- **VTK XML** (`.vtu`, `.vtp`)

지원 데이터셋 타입:
- STRUCTURED_POINTS
- POLYDATA
- UNSTRUCTURED_GRID

### 3. 예제 코드 수정

```python
from pathlib import Path
from src.core.simulation.parsers.csv_parser import CSVParser

# 자신의 데이터 파일 사용
parser = CSVParser()
simulation = parser.parse(Path("your_data.csv"))
```

## 데이터 형식 가이드

### 스칼라 필드 (Scalar Fields)
온도, 압력, 밀도 등 단일 값
```
temperature: float
pressure: float
density: float
```

### 벡터 필드 (Vector Fields)
속도, 힘 등 방향이 있는 양
```
velocity_x: float
velocity_y: float
velocity_z: float
```

### 텐서 필드 (Tensor Fields)
응력 텐서 등 행렬 형태
```
stress_xx, stress_xy, stress_xz
stress_yx, stress_yy, stress_yz
stress_zx, stress_zy, stress_zz
```

## 문제 해결

### 파일을 찾을 수 없음
```bash
# 현재 위치 확인
pwd

# 샘플 데이터 존재 확인
ls -la data/samples/

# 재생성
python scripts/generate_sample_data.py
```

### 파싱 오류
```python
# 파일 형식 확인
with open("data/samples/simple_temperature.csv") as f:
    print(f.read(200))  # 처음 200자 출력

# 파서 디버그 모드
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 추가 정보

- 더 많은 예제: `examples/` 디렉토리 참조
- API 문서: http://localhost:8000/docs (서버 실행 후)
- 파서 문서: `docs/PARSERS.md`
"""

    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    logger.info(f"✅ Created: {readme_path.name}")


def main():
    """메인 함수"""
    print("=" * 70)
    print("📊 KooAI 샘플 데이터 생성")
    print("=" * 70)
    print()

    # 출력 디렉토리 생성
    data_dir = Path("data")
    samples_dir = data_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"출력 디렉토리: {samples_dir.absolute()}")
    print()

    try:
        # 1. CSV 샘플 (작은 파일)
        create_sample_csv(samples_dir / "simple_temperature.csv")

        # 2. CSV 샘플 (대용량)
        create_large_csv(samples_dir / "flow_simulation.csv")

        # 3. VTK 샘플
        create_vtk_ascii(samples_dir / "pressure_field.vtk")

        # 4. README
        create_readme(samples_dir)

        print()
        print("=" * 70)
        print("✅ 모든 샘플 데이터 생성 완료!")
        print("=" * 70)
        print()
        print(f"위치: {samples_dir.absolute()}")
        print()
        print("생성된 파일:")
        for file in sorted(samples_dir.glob("*")):
            if file.is_file():
                size = file.stat().st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / 1024 / 1024:.1f} MB"
                print(f"  - {file.name:30s} {size_str:>10s}")
        print()

    except Exception as e:
        logger.error(f"❌ 샘플 데이터 생성 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
