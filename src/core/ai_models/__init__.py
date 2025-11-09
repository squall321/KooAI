"""
AI 모델 관리 모듈

AI/ML 모델의 레지스트리, 어댑터, 버전 관리를 제공합니다.
"""

from .registry import AIModelRegistry, ModelMetadata
from .adapters.base import (
    IModelAdapter,
    BaseModelAdapter,
    ModelConfig,
    InferenceResult,
    ModelFramework,
    InferenceMode,
    ModelAdapterFactory,
)


def _register_adapters() -> None:
    """어댑터를 팩토리에 등록"""
    try:
        from .adapters.pytorch import PyTorchAdapter

        ModelAdapterFactory.register(ModelFramework.PYTORCH, PyTorchAdapter)
    except ImportError:
        pass

    try:
        from .adapters.huggingface import HuggingFaceAdapter

        ModelAdapterFactory.register(ModelFramework.HUGGINGFACE, HuggingFaceAdapter)
    except ImportError:
        pass

    try:
        from .adapters.onnx import ONNXAdapter

        ModelAdapterFactory.register(ModelFramework.ONNX, ONNXAdapter)
    except ImportError:
        pass


# 모듈 import 시 어댑터 자동 등록
_register_adapters()

__all__ = [
    "AIModelRegistry",
    "ModelMetadata",
    "IModelAdapter",
    "BaseModelAdapter",
    "ModelConfig",
    "InferenceResult",
    "ModelFramework",
    "InferenceMode",
    "ModelAdapterFactory",
]
