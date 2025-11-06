# KooAI - AI-Powered Simulation Post-Processing Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 프로젝트 개요

KooAI는 시뮬레이션 후처리 분석을 위한 AI 기반 통합 솔루션 백엔드 플랫폼입니다.

### 핵심 기능

- **📊 다양한 데이터 타입 지원**: 정형/비정형 데이터, 3D 메시, 커브, 컨투어 데이터
- **🤖 AI/ML 통합**: VAE 기반 데이터 압축, LLM 기반 시뮬레이션 분석
- **🔍 시맨틱 검색**: 벡터 DB를 활용한 유사 시뮬레이션 검색
- **🔧 확장 가능한 아키텍처**: 플러그인 시스템으로 기능 확장
- **⚡ 고성능 처리**: 비동기 파이프라인, 분산 작업 큐

## 🏗️ 아키텍처

KooAI는 Clean Architecture 원칙을 따르며 다음과 같은 계층으로 구성됩니다:

```
┌─────────────────────────────────────┐
│     Presentation Layer (API)        │
├─────────────────────────────────────┤
│     Application Layer (Use Cases)   │
├─────────────────────────────────────┤
│     Domain Layer (Business Logic)   │
├─────────────────────────────────────┤
│     Infrastructure Layer (DB, etc)  │
└─────────────────────────────────────┘
```

자세한 내용은 [프로젝트 계획서](PROJECT_PLAN.md)와 [기술 설계 문서](TECHNICAL_DESIGN.md)를 참조하세요.

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.11 이상
- Docker & Docker Compose
- Git

### 설치

1. 저장소 클론
```bash
git clone https://github.com/yourusername/kooai.git
cd kooai
```

2. 가상 환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -e ".[dev]"
```

4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정
```

5. Docker 서비스 시작
```bash
docker-compose up -d
```

6. 데이터베이스 마이그레이션
```bash
alembic upgrade head
```

7. 서버 실행
```bash
uvicorn src.presentation.api.main:app --reload
```

API는 http://localhost:8000 에서 접근 가능합니다.
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 문서

- [프로젝트 계획서](PROJECT_PLAN.md) - 전체 프로젝트 로드맵 및 Phase별 계획
- [기술 설계 문서](TECHNICAL_DESIGN.md) - 아키텍처 및 기술 스택 상세
- [Phase 체크리스트](PHASE_CHECKLISTS.md) - 각 Phase별 세부 작업 체크리스트

## 🔧 개발

### 코드 품질

프로젝트는 다음 도구를 사용하여 코드 품질을 유지합니다:

```bash
# 포맷팅
black src tests

# 린팅
ruff check src tests

# 타입 체킹
mypy src

# 테스트
pytest

# Pre-commit 훅 설치
pre-commit install
```

### 테스트 실행

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트
pytest tests/unit/domain/test_entities.py
```

## 🏛️ 프로젝트 구조

```
kooai/
├── src/
│   ├── core/              # 핵심 비즈니스 로직
│   │   ├── domain/        # 도메인 모델
│   │   ├── data_types/    # 데이터 타입 추상화
│   │   ├── ai_models/     # AI/ML 모델
│   │   └── ...
│   ├── application/       # Use cases
│   ├── infrastructure/    # 외부 의존성
│   ├── presentation/      # API 및 CLI
│   └── plugins/           # 플러그인 시스템
├── tests/                 # 테스트
├── docs/                  # 문서
├── docker/                # Docker 설정
└── config/                # 설정 파일
```

## 🤝 기여

기여는 언제나 환영합니다! 기여 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참조하세요.

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

## 🔗 관련 링크

- [프로젝트 문서](docs/)
- [API 문서](http://localhost:8000/docs)
- [이슈 트래커](https://github.com/yourusername/kooai/issues)

## 📧 연락처

문의사항이 있으시면 이슈를 생성하거나 이메일(your.email@example.com)로 연락주세요.

---

**개발 상태**: 🚧 활발히 개발 중

현재 Phase: **Phase 1 - 프로젝트 기반 구조 설정**

진행 상황은 [Phase 체크리스트](PHASE_CHECKLISTS.md)에서 확인할 수 있습니다.
