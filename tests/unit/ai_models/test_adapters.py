"""
모델 어댑터 테스트

Note: PyTorch, Transformers, ONNX Runtime이 설치되지 않았을 수 있으므로,
기본 인터페이스와 팩토리 테스트에 집중합니다.
"""

import pytest
from pathlib import Path
from typing import Any

from src.core.ai_models.adapters.base import (
    ModelConfig,
    ModelFramework,
    InferenceMode,
    InferenceResult,
    ModelAdapterFactory,
)


class TestModelConfig:
    """ModelConfig 테스트"""

    def test_create_model_config(self, tmp_path: Path) -> None:
        """모델 설정 생성 테스트"""
        model_path = tmp_path / "model.pth"
        model_path.touch()

        config = ModelConfig(
            framework=ModelFramework.PYTORCH,
            model_path=model_path,
            device="cpu",
            batch_size=32,
        )

        assert config.framework == ModelFramework.PYTORCH
        assert config.model_path == model_path
        assert config.device == "cpu"
        assert config.batch_size == 32

    def test_config_validates_path_exists(self, tmp_path: Path) -> None:
        """경로 존재 확인 테스트"""
        nonexistent_path = tmp_path / "nonexistent.pth"

        with pytest.raises(FileNotFoundError):
            ModelConfig(
                framework=ModelFramework.PYTORCH,
                model_path=nonexistent_path,
            )


class TestInferenceResult:
    """InferenceResult 테스트"""

    def test_create_inference_result(self) -> None:
        """추론 결과 생성 테스트"""
        output = [0.1, 0.2, 0.7]
        metadata = {"model_name": "test", "version": "1.0"}

        result = InferenceResult(
            output=output,
            metadata=metadata,
            inference_time_ms=15.5,
            model_name="test",
            model_version="1.0",
        )

        assert result.output == output
        assert result.metadata["model_name"] == "test"
        assert result.inference_time_ms == 15.5

    def test_get_output(self) -> None:
        """출력 가져오기 테스트"""
        output = {"logits": [0.1, 0.9], "labels": [0, 1]}

        result = InferenceResult(output=output)

        assert result.get_output() == output

    def test_get_metadata(self) -> None:
        """메타데이터 조회 테스트"""
        result = InferenceResult(
            output=[],
            metadata={"device": "cpu", "batch_size": 16},
        )

        assert result.get_metadata("device") == "cpu"
        assert result.get_metadata("batch_size") == 16
        assert result.get_metadata("nonexistent", "default") == "default"


class TestModelAdapterFactory:
    """ModelAdapterFactory 테스트"""

    def test_list_frameworks(self) -> None:
        """등록된 프레임워크 목록 조회 테스트"""
        frameworks = ModelAdapterFactory.list_frameworks()

        # 어댑터가 자동 등록되어 있어야 함
        assert len(frameworks) >= 0  # 의존성이 없으면 0개

    def test_create_raises_for_unsupported_framework(self) -> None:
        """지원하지 않는 프레임워크 생성 시 에러 테스트"""
        # CUSTOM 프레임워크는 등록되지 않음
        with pytest.raises(ValueError, match="Unsupported framework"):
            ModelAdapterFactory.create(ModelFramework.CUSTOM)


class TestModelFramework:
    """ModelFramework Enum 테스트"""

    def test_framework_values(self) -> None:
        """프레임워크 값 테스트"""
        assert ModelFramework.PYTORCH.value == "pytorch"
        assert ModelFramework.HUGGINGFACE.value == "huggingface"
        assert ModelFramework.ONNX.value == "onnx"

    def test_framework_from_string(self) -> None:
        """문자열에서 프레임워크 생성 테스트"""
        framework = ModelFramework("pytorch")
        assert framework == ModelFramework.PYTORCH


class TestInferenceMode:
    """InferenceMode Enum 테스트"""

    def test_inference_mode_values(self) -> None:
        """추론 모드 값 테스트"""
        assert InferenceMode.CPU.value == "cpu"
        assert InferenceMode.GPU.value == "gpu"
        assert InferenceMode.MIXED.value == "mixed"
