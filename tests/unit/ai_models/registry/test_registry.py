"""
AI Model Registry 테스트
"""

import pytest
import tempfile
import json
from pathlib import Path
from uuid import UUID

from src.core.ai_models.registry import AIModelRegistry, ModelMetadata
from src.core.ai_models.adapters.base import ModelFramework


@pytest.fixture
def temp_registry_dir():
    """임시 레지스트리 디렉토리"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_model_file():
    """임시 모델 파일"""
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        f.write(b"fake model data")
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def registry(temp_registry_dir):
    """레지스트리 인스턴스"""
    return AIModelRegistry(temp_registry_dir)


class TestModelMetadata:
    """ModelMetadata 테스트"""

    def test_create_metadata(self, temp_model_file):
        """메타데이터 생성 테스트"""
        metadata = ModelMetadata(
            name="test_model",
            version="1.0.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
            description="Test model",
            tags=["test", "demo"],
        )

        assert metadata.name == "test_model"
        assert metadata.version == "1.0.0"
        assert metadata.framework == ModelFramework.PYTORCH
        assert metadata.model_type == "vae"
        assert "test" in metadata.tags

    def test_get_full_name(self, temp_model_file):
        """전체 이름 테스트"""
        metadata = ModelMetadata(
            name="model",
            version="2.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )

        assert metadata.get_full_name() == "model:2.0"

    def test_to_dict(self, temp_model_file):
        """딕셔너리 변환 테스트"""
        metadata = ModelMetadata(
            name="model",
            version="1.0",
            framework=ModelFramework.ONNX,
            model_path=temp_model_file,
            model_type="classifier",
            tags=["production"],
        )

        data = metadata.to_dict()

        assert data["name"] == "model"
        assert data["version"] == "1.0"
        assert data["framework"] == "onnx"
        assert data["model_type"] == "classifier"
        assert "production" in data["tags"]
        assert "id" in data
        assert "registered_at" in data

    def test_from_dict(self, temp_model_file):
        """딕셔너리에서 생성 테스트"""
        original = ModelMetadata(
            name="model",
            version="1.0",
            framework=ModelFramework.HUGGINGFACE,
            model_path=temp_model_file,
            model_type="llm",
        )

        data = original.to_dict()
        restored = ModelMetadata.from_dict(data)

        assert restored.name == original.name
        assert restored.version == original.version
        assert restored.framework == original.framework
        assert restored.model_type == original.model_type
        assert str(restored.id) == str(original.id)


class TestAIModelRegistry:
    """AIModelRegistry 테스트"""

    def test_register_model(self, registry, temp_model_file):
        """모델 등록 테스트"""
        metadata = registry.register(
            name="test_model",
            version="1.0.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
            description="Test model",
        )

        assert metadata.name == "test_model"
        assert metadata.version == "1.0.0"

    def test_register_duplicate_raises_error(self, registry, temp_model_file):
        """중복 등록 시 에러 테스트"""
        registry.register(
            name="model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )

        with pytest.raises(ValueError, match="already registered"):
            registry.register(
                name="model",
                version="1.0",
                framework=ModelFramework.PYTORCH,
                model_path=temp_model_file,
                model_type="vae",
            )

    def test_register_with_overwrite(self, registry, temp_model_file):
        """덮어쓰기 등록 테스트"""
        registry.register(
            name="model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )

        # 덮어쓰기
        metadata = registry.register(
            name="model",
            version="1.0",
            framework=ModelFramework.ONNX,
            model_path=temp_model_file,
            model_type="classifier",
            overwrite=True,
        )

        assert metadata.framework == ModelFramework.ONNX
        assert metadata.model_type == "classifier"

    def test_register_nonexistent_file_raises_error(self, registry):
        """존재하지 않는 파일 등록 시 에러 테스트"""
        fake_path = Path("/nonexistent/model.pth")

        with pytest.raises(FileNotFoundError):
            registry.register(
                name="model",
                version="1.0",
                framework=ModelFramework.PYTORCH,
                model_path=fake_path,
                model_type="vae",
            )

    def test_unregister_model(self, registry, temp_model_file):
        """모델 등록 해제 테스트"""
        registry.register(
            name="model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )

        registry.unregister("model", "1.0")

        with pytest.raises(KeyError):
            registry.get_metadata("model", "1.0")

    def test_unregister_nonexistent_raises_error(self, registry):
        """존재하지 않는 모델 삭제 시 에러 테스트"""
        with pytest.raises(KeyError):
            registry.unregister("nonexistent", "1.0")

    def test_get_metadata(self, registry, temp_model_file):
        """메타데이터 조회 테스트"""
        registry.register(
            name="model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
            description="Test",
        )

        metadata = registry.get_metadata("model", "1.0")

        assert metadata.name == "model"
        assert metadata.version == "1.0"
        assert metadata.description == "Test"

    def test_get_metadata_latest_version(self, registry, temp_model_file):
        """최신 버전 조회 테스트"""
        registry.register(
            name="model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )
        registry.register(
            name="model",
            version="2.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )

        metadata = registry.get_metadata("model", "latest")

        assert metadata.version == "2.0"

    def test_list_models(self, registry, temp_model_file):
        """모델 목록 조회 테스트"""
        registry.register(
            name="model1",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )
        registry.register(
            name="model2",
            version="1.0",
            framework=ModelFramework.ONNX,
            model_path=temp_model_file,
            model_type="classifier",
        )

        models = registry.list_models()

        assert len(models) == 2
        model_names = {m.name for m in models}
        assert "model1" in model_names
        assert "model2" in model_names

    def test_list_models_with_framework_filter(self, registry, temp_model_file):
        """프레임워크 필터링 테스트"""
        registry.register(
            name="pytorch_model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )
        registry.register(
            name="onnx_model",
            version="1.0",
            framework=ModelFramework.ONNX,
            model_path=temp_model_file,
            model_type="classifier",
        )

        pytorch_models = registry.list_models(framework=ModelFramework.PYTORCH)

        assert len(pytorch_models) == 1
        assert pytorch_models[0].name == "pytorch_model"

    def test_list_models_with_tags_filter(self, registry, temp_model_file):
        """태그 필터링 테스트"""
        registry.register(
            name="model1",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
            tags=["production", "v1"],
        )
        registry.register(
            name="model2",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
            tags=["development"],
        )

        production_models = registry.list_models(tags=["production"])

        assert len(production_models) == 1
        assert production_models[0].name == "model1"

    def test_list_versions(self, registry, temp_model_file):
        """버전 목록 조회 테스트"""
        registry.register(
            name="model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )
        registry.register(
            name="model",
            version="1.1",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )
        registry.register(
            name="model",
            version="2.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
        )

        versions = registry.list_versions("model")

        assert len(versions) == 3
        assert versions[0] == "2.0"  # 최신순
        assert versions[1] == "1.1"
        assert versions[2] == "1.0"

    def test_registry_persistence(self, temp_registry_dir, temp_model_file):
        """레지스트리 영속성 테스트"""
        # 첫 번째 레지스트리: 모델 등록
        registry1 = AIModelRegistry(temp_registry_dir)
        registry1.register(
            name="model",
            version="1.0",
            framework=ModelFramework.PYTORCH,
            model_path=temp_model_file,
            model_type="vae",
            description="Persistent model",
        )

        # 두 번째 레지스트리: 동일 디렉토리에서 로드
        registry2 = AIModelRegistry(temp_registry_dir)

        metadata = registry2.get_metadata("model", "1.0")
        assert metadata.name == "model"
        assert metadata.description == "Persistent model"
