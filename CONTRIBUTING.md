# Contributing to KooAI

우리 프로젝트에 기여해 주셔서 감사합니다! 이 가이드는 프로젝트에 기여하는 방법을 설명합니다.

## 개발 환경 설정

1. 저장소를 Fork하고 Clone합니다
```bash
git clone https://github.com/your-username/kooai.git
cd kooai
```

2. 가상 환경을 생성하고 활성화합니다
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

3. 개발 의존성을 설치합니다
```bash
pip install -e ".[dev]"
```

4. Pre-commit 훅을 설치합니다
```bash
pre-commit install
```

5. Docker 서비스를 시작합니다
```bash
docker-compose up -d postgres redis
```

## 코드 스타일

이 프로젝트는 다음 코드 스타일 가이드를 따릅니다:

- **포맷팅**: Black (line-length=100)
- **Import 정렬**: isort (black 프로필)
- **린팅**: Ruff
- **타입 힌트**: mypy strict 모드

코드를 커밋하기 전에 다음을 실행하세요:

```bash
# 포맷팅
black src tests

# Import 정렬
isort src tests

# 린팅
ruff check src tests --fix

# 타입 체킹
mypy src
```

Pre-commit 훅이 설치되어 있다면 자동으로 실행됩니다.

## 테스트

모든 새로운 기능과 버그 수정에는 테스트가 포함되어야 합니다.

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트 실행
pytest tests/unit/domain/test_entities.py::TestSimulationResult

# 통합 테스트만 실행
pytest tests/integration/
```

테스트 커버리지는 최소 80% 이상이어야 합니다.

## 브랜치 전략

- `main`: 프로덕션 준비 코드
- `develop`: 개발 브랜치
- `feature/*`: 새로운 기능
- `bugfix/*`: 버그 수정
- `hotfix/*`: 긴급 수정

### 브랜치 생성 예시

```bash
# 새로운 기능
git checkout -b feature/add-vae-compression

# 버그 수정
git checkout -b bugfix/fix-authentication-error
```

## 커밋 메시지

커밋 메시지는 다음 형식을 따릅니다:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 프로세스 또는 도구 변경

### 예시

```
feat(vae): add contour compression using VAE

Implement VAE-based compression for contour data with the following features:
- Encoder/decoder architecture
- Training pipeline
- Compression/decompression methods

Closes #123
```

## Pull Request 프로세스

1. Feature 브랜치를 생성합니다
2. 변경 사항을 구현합니다
3. 테스트를 추가/수정합니다
4. 모든 테스트가 통과하는지 확인합니다
5. PR을 생성합니다

### PR 체크리스트

- [ ] 코드가 프로젝트 스타일 가이드를 따름
- [ ] 새로운 기능에 대한 테스트 추가
- [ ] 모든 테스트 통과
- [ ] 문서 업데이트 (필요한 경우)
- [ ] CHANGELOG.md 업데이트 (major 변경의 경우)

### PR 템플릿

```markdown
## 변경 사항

간단한 변경 사항 설명

## 관련 이슈

Closes #이슈번호

## 변경 타입

- [ ] 버그 수정
- [ ] 새로운 기능
- [ ] Breaking change
- [ ] 문서 업데이트

## 테스트

테스트 방법 설명

## 체크리스트

- [ ] 코드 스타일 준수
- [ ] 테스트 추가/수정
- [ ] 문서 업데이트
```

## 코드 리뷰

모든 PR은 최소 1명의 리뷰어 승인이 필요합니다.

리뷰어는 다음을 확인합니다:
- 코드 품질
- 테스트 커버리지
- 문서화
- 성능 영향
- 보안 고려사항

## 문서화

### Docstring

모든 public 함수/클래스에는 docstring이 필요합니다:

```python
def process_simulation(simulation_id: str, parameters: dict) -> SimulationResult:
    """
    시뮬레이션을 처리합니다.

    Args:
        simulation_id: 시뮬레이션 ID
        parameters: 처리 파라미터

    Returns:
        처리된 시뮬레이션 결과

    Raises:
        ValueError: 유효하지 않은 시뮬레이션 ID
        ProcessingError: 처리 중 오류 발생

    Examples:
        >>> result = process_simulation("sim-123", {"method": "fast"})
        >>> print(result.status)
        'completed'
    """
    pass
```

### Type Hints

모든 함수 시그니처에 타입 힌트를 추가합니다:

```python
from typing import List, Optional, Dict, Any

async def get_simulations(
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100
) -> List[SimulationResult]:
    pass
```

## 플러그인 개발

새로운 플러그인을 개발하는 경우:

1. `src/plugins/builtin/` 또는 별도 저장소에 플러그인 생성
2. `IPlugin` 인터페이스 구현
3. 플러그인 문서 작성
4. 테스트 추가

자세한 내용은 [Plugin Development Guide](docs/guides/plugin_development.md)를 참조하세요.

## 이슈 리포팅

버그를 발견하거나 기능을 제안하고 싶다면 이슈를 생성하세요.

### 버그 리포트

```markdown
**버그 설명**
명확하고 간결한 버그 설명

**재현 방법**
1. ...
2. ...

**예상 동작**
예상했던 동작 설명

**실제 동작**
실제 발생한 동작

**환경**
- OS: [e.g. Ubuntu 22.04]
- Python 버전: [e.g. 3.11.5]
- KooAI 버전: [e.g. 0.1.0]

**추가 정보**
스크린샷, 로그 등
```

### 기능 제안

```markdown
**기능 설명**
제안하는 기능에 대한 명확한 설명

**동기**
이 기능이 필요한 이유와 해결하려는 문제

**제안하는 해결책**
기능이 어떻게 동작해야 하는지

**대안**
고려한 다른 해결책

**추가 정보**
기타 관련 정보
```

## 라이선스

기여한 코드는 프로젝트의 MIT 라이선스 하에 배포됩니다.

## 질문?

질문이 있으면:
- 이슈를 생성하거나
- 이메일 (your.email@example.com)로 문의하세요

다시 한 번 기여해 주셔서 감사합니다! 🎉
