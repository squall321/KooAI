# KooAI 사용 예제

이 디렉토리에는 KooAI 플랫폼의 다양한 기능을 사용하는 예제 코드가 포함되어 있습니다.

## 📁 예제 목록

### 1. 기본 사용법 (`01_basic_usage.py`)
시뮬레이션 파일을 로드하고 기본 분석을 수행하는 예제

**주요 기능**:
- CSV 파일 파싱
- 필드 통계 계산 (평균, 최소, 최대, 표준편차)
- 극값 찾기
- 이상치 탐지

**실행**:
```bash
python examples/01_basic_usage.py
```

### 2. 배치 처리 (`02_batch_processing.py`)
여러 시뮬레이션 파일을 병렬로 처리하는 예제

**주요 기능**:
- 병렬 파일 처리 (멀티스레딩)
- 진행률 추적
- 에러 핸들링
- 배치 처리 결과 요약

**실행**:
```bash
python examples/02_batch_processing.py
```

### 3. 시뮬레이션 비교 (`03_simulation_comparison.py`)
두 개 이상의 시뮬레이션을 비교하고 차이를 분석하는 예제

**주요 기능**:
- RMSE 계산
- 상관계수 분석
- 차이 분류 (negligible, small, moderate, large, critical)
- 이상치 영역 식별
- 다중 시뮬레이션 비교

**실행**:
```bash
python examples/03_simulation_comparison.py
```

### 4. 리포트 생성 (`04_report_generation.py`)
분석 결과를 Markdown, HTML, Text 형식의 리포트로 생성하는 예제

**주요 기능**:
- 시뮬레이션 요약
- 통계 테이블
- 배치 처리 결과
- 커스텀 섹션
- 다중 형식 출력 (Markdown, HTML, Text)

**실행**:
```bash
python examples/04_report_generation.py
```

### 5. 데이터 내보내기 (`05_export_data.py`)
시뮬레이션 데이터를 다양한 형식으로 내보내는 예제

**주요 기능**:
- JSON 내보내기 (메타데이터 포함)
- CSV 내보내기 (필드 플래팅)
- NumPy (.npz) 내보내기
- Text 요약 리포트
- 분석 결과 JSON

**실행**:
```bash
python examples/05_export_data.py
```

## 🚀 시작하기

### 사전 요구사항

```bash
# KooAI 설치
pip install -e .

# 필수 의존성
pip install numpy
```

### 샘플 데이터

예제를 실행하기 전에 `data/` 디렉토리에 샘플 시뮬레이션 파일이 필요합니다:

```bash
mkdir -p data
# sample_simulation.csv 파일을 data/ 디렉토리에 추가
```

### CSV 파일 형식 예제

```csv
x,y,z,temperature,pressure
0.0,0.0,0.0,273.15,101325
0.1,0.0,0.0,275.20,101330
0.2,0.0,0.0,278.50,101340
...
```

## 📊 고급 예제

### 파이프라인 사용

```python
from src.application.batch.pipeline import Pipeline, ParseStage, AnalyzeStage, ExportStage
from src.core.simulation.parsers.csv_parser import CSVParser

# 파이프라인 구성
pipeline = Pipeline(name="simulation_pipeline")

pipeline.add_stage(ParseStage(CSVParser().parse)) \
        .add_stage(AnalyzeStage(analyzer_func, "temperature")) \
        .add_stage(ExportStage(exporter_func, "output.json"))

# 실행
result = pipeline.process("input.csv")
```

### 캐싱 활용

```python
from src.infrastructure.cache.decorators import cache_result

@cache_result(ttl=3600)  # 1시간 캐싱
def expensive_analysis(simulation_id, field_name):
    # 시간이 오래 걸리는 분석
    return results
```

## 📝 추가 리소스

- [메인 README](../README.md) - 전체 프로젝트 개요
- [개발 현황](../DEVELOPMENT_STATUS.md) - 현재 개발 상태
- [API 문서](http://localhost:8000/docs) - REST API 문서 (서버 실행 후)

## 💡 팁

1. **대용량 파일**: 배치 처리(`02_batch_processing.py`) 사용
2. **시뮬레이션 검증**: 비교 분석(`03_simulation_comparison.py`) 활용
3. **결과 공유**: 리포트 생성(`04_report_generation.py`)으로 HTML 리포트 생성
4. **데이터 백업**: 내보내기(`05_export_data.py`)로 다양한 형식 저장

## 🐛 문제 해결

### ModuleNotFoundError
```bash
# 프로젝트 루트에서 실행
cd /path/to/KooAI
python examples/01_basic_usage.py
```

### 파일을 찾을 수 없음
```bash
# data 디렉토리 생성 및 샘플 파일 추가
mkdir -p data
# 샘플 CSV 파일을 data/ 디렉토리에 복사
```

## 🤝 기여

새로운 예제를 추가하고 싶으시면 Pull Request를 보내주세요!
