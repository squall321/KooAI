"""
모델 어댑터 기본 인터페이스

다양한 AI 프레임워크의 모델을 통합하기 위한 어댑터 패턴 구현.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
from enum import Enum


class ModelFramework(str, Enum):
    """지원하는 AI 프레임워크"""

    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    HUGGINGFACE = "huggingface"
    ONNX = "onnx"
    SKLEARN = "sklearn"
    CUSTOM = "custom"


class InferenceMode(str, Enum):
    """추론 모드"""

    CPU = "cpu"
    GPU = "gpu"
    MIXED = "mixed"


@dataclass
class ModelConfig:
    """
    모델 설정

    모델 로드 및 추론에 필요한 설정을 정의합니다.
    """

    framework: ModelFramework
    model_path: Path
    device: str = "cpu"  # cpu, cuda, cuda:0, etc.
    inference_mode: InferenceMode = InferenceMode.CPU
    batch_size: int = 1
    precision: str = "fp32"  # fp32, fp16, int8
    config: Dict[str, Any] = field(default_factory=dict)
    preprocessing: Optional[Dict[str, Any]] = None
    postprocessing: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model path does not exist: {self.model_path}")


@dataclass
class InferenceResult:
    """
    추론 결과

    모델 추론의 출력과 메타데이터를 담습니다.
    """

    output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    inference_time_ms: Optional[float] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None

    def get_output(self) -> Any:
        """출력 데이터 반환"""
        return self.output

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        return self.metadata.get(key, default)


class IModelAdapter(Protocol):
    """
    모델 어댑터 인터페이스

    다양한 프레임워크의 모델을 통일된 방식으로 사용하기 위한 인터페이스.
    """

    def load(self, config: ModelConfig) -> None:
        """
        모델 로드

        Args:
            config: 모델 설정

        Raises:
            FileNotFoundError: 모델 파일이 없을 때
            ValueError: 설정이 잘못되었을 때
        """
        ...

    def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
        """
        추론 수행

        Args:
            input_data: 입력 데이터
            **kwargs: 추가 파라미터

        Returns:
            InferenceResult: 추론 결과

        Raises:
            RuntimeError: 추론 실패 시
        """
        ...

    def batch_predict(self, input_data_list: List[Any], **kwargs: Any) -> List[InferenceResult]:
        """
        배치 추론

        Args:
            input_data_list: 입력 데이터 리스트
            **kwargs: 추가 파라미터

        Returns:
            List[InferenceResult]: 추론 결과 리스트
        """
        ...

    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 조회

        Returns:
            Dict: 모델 정보 (아키텍처, 입력/출력 형태 등)
        """
        ...

    def unload(self) -> None:
        """모델 언로드 (메모리 해제)"""
        ...


class BaseModelAdapter(ABC):
    """
    모델 어댑터 기본 추상 클래스

    공통 기능을 제공하는 추상 클래스.
    """

    def __init__(self) -> None:
        self.model: Optional[Any] = None
        self.config: Optional[ModelConfig] = None
        self._is_loaded: bool = False

    @abstractmethod
    def load(self, config: ModelConfig) -> None:
        """모델 로드 (서브클래스에서 구현)"""
        pass

    @abstractmethod
    def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
        """추론 수행 (서브클래스에서 구현)"""
        pass

    def batch_predict(self, input_data_list: List[Any], **kwargs: Any) -> List[InferenceResult]:
        """
        배치 추론 기본 구현

        개별 predict를 반복 호출. 서브클래스에서 최적화 가능.
        """
        return [self.predict(data, **kwargs) for data in input_data_list]

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 조회 (서브클래스에서 구현)"""
        pass

    def unload(self) -> None:
        """모델 언로드"""
        if self.model is not None:
            del self.model
            self.model = None
            self._is_loaded = False

    def is_loaded(self) -> bool:
        """모델 로드 여부 확인"""
        return self._is_loaded

    def _ensure_loaded(self) -> None:
        """모델이 로드되었는지 확인"""
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")


class ModelAdapterFactory:
    """
    모델 어댑터 팩토리

    프레임워크에 따라 적절한 어댑터를 생성합니다.
    """

    _adapters: Dict[ModelFramework, type[BaseModelAdapter]] = {}

    @classmethod
    def register(cls, framework: ModelFramework, adapter_class: type[BaseModelAdapter]) -> None:
        """
        어댑터 등록

        Args:
            framework: 프레임워크 종류
            adapter_class: 어댑터 클래스
        """
        cls._adapters[framework] = adapter_class

    @classmethod
    def create(cls, framework: ModelFramework) -> BaseModelAdapter:
        """
        어댑터 생성

        Args:
            framework: 프레임워크 종류

        Returns:
            BaseModelAdapter: 어댑터 인스턴스

        Raises:
            ValueError: 지원하지 않는 프레임워크일 때
        """
        if framework not in cls._adapters:
            raise ValueError(
                f"Unsupported framework: {framework}. " f"Available: {list(cls._adapters.keys())}"
            )

        return cls._adapters[framework]()

    @classmethod
    def list_frameworks(cls) -> List[ModelFramework]:
        """등록된 프레임워크 목록 반환"""
        return list(cls._adapters.keys())
