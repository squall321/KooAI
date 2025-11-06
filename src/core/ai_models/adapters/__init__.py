"""
모델 어댑터

다양한 AI 프레임워크의 모델을 통합 인터페이스로 관리합니다.
"""

from .base import IModelAdapter, ModelConfig, InferenceResult

__all__ = ["IModelAdapter", "ModelConfig", "InferenceResult"]
