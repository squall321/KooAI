"""
모델 저장소 테스트
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.infrastructure.model_storage import (
    ModelStorage,
    ModelStorageFactory,
    StorageConfig,
    StorageBackend,
)


@pytest.fixture
def temp_storage_dir():
    """임시 저장소 디렉토리"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_model_file():
    """임시 모델 파일"""
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        f.write(b"fake model data for testing")
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def storage(temp_storage_dir):
    """저장소 인스턴스"""
    config = StorageConfig(
        backend=StorageBackend.LOCAL,
        base_path=temp_storage_dir,
        enable_checksum=True,
    )
    return ModelStorage(config)


class TestModelStorage:
    """ModelStorage 테스트"""

    def test_save_model(self, storage, temp_model_file):
        """모델 저장 테스트"""
        saved_path = storage.save(
            model_file=temp_model_file,
            model_name="test_model",
            version="1.0.0",
        )

        assert saved_path.exists()
        assert saved_path.name == temp_model_file.name
        assert saved_path.parent.name == "1.0.0"

    def test_save_with_metadata(self, storage, temp_model_file):
        """메타데이터 포함 저장 테스트"""
        metadata = {
            "framework": "pytorch",
            "model_type": "vae",
            "parameters": 1000000,
        }

        storage.save(
            model_file=temp_model_file,
            model_name="model",
            version="1.0",
            metadata=metadata,
        )

        loaded_metadata = storage.get_metadata("model", "1.0")

        assert loaded_metadata is not None
        assert loaded_metadata["framework"] == "pytorch"
        assert loaded_metadata["parameters"] == 1000000

    def test_save_creates_checksum(self, temp_storage_dir, temp_model_file):
        """체크섬 생성 테스트"""
        config = StorageConfig(
            backend=StorageBackend.LOCAL,
            base_path=temp_storage_dir,
            enable_checksum=True,
        )
        storage = ModelStorage(config)

        saved_path = storage.save(
            model_file=temp_model_file,
            model_name="model",
            version="1.0",
        )

        checksum_file = saved_path.with_suffix(saved_path.suffix + ".sha256")
        assert checksum_file.exists()

        checksum = checksum_file.read_text().strip()
        assert len(checksum) == 64  # SHA256 hash length

    def test_save_nonexistent_file_raises_error(self, storage):
        """존재하지 않는 파일 저장 시 에러 테스트"""
        fake_path = Path("/nonexistent/model.pth")

        with pytest.raises(FileNotFoundError):
            storage.save(
                model_file=fake_path,
                model_name="model",
                version="1.0",
            )

    def test_load_model(self, storage, temp_model_file):
        """모델 로드 테스트"""
        storage.save(
            model_file=temp_model_file,
            model_name="model",
            version="1.0",
        )

        loaded_path = storage.load(model_name="model", version="1.0", filename=temp_model_file.name)

        assert loaded_path.exists()
        assert loaded_path.read_bytes() == temp_model_file.read_bytes()

    def test_load_nonexistent_model_raises_error(self, storage):
        """존재하지 않는 모델 로드 시 에러 테스트"""
        with pytest.raises(FileNotFoundError):
            storage.load(model_name="nonexistent", version="1.0", filename="model.pth")

    def test_delete_model(self, storage, temp_model_file):
        """모델 삭제 테스트"""
        storage.save(
            model_file=temp_model_file,
            model_name="model",
            version="1.0",
        )

        storage.delete("model", "1.0")

        assert not storage.exists("model", "1.0", temp_model_file.name)

    def test_delete_nonexistent_raises_error(self, storage):
        """존재하지 않는 모델 삭제 시 에러 테스트"""
        with pytest.raises(FileNotFoundError):
            storage.delete("nonexistent", "1.0")

    def test_exists(self, storage, temp_model_file):
        """파일 존재 확인 테스트"""
        assert not storage.exists("model", "1.0", "model.pth")

        storage.save(
            model_file=temp_model_file,
            model_name="model",
            version="1.0",
        )

        assert storage.exists("model", "1.0", temp_model_file.name)

    def test_list_versions(self, storage, temp_model_file):
        """버전 목록 조회 테스트"""
        storage.save(model_file=temp_model_file, model_name="model", version="1.0")
        storage.save(model_file=temp_model_file, model_name="model", version="2.0")
        storage.save(model_file=temp_model_file, model_name="model", version="1.5")

        versions = storage.list_versions("model")

        assert len(versions) == 3
        assert "1.0" in versions
        assert "1.5" in versions
        assert "2.0" in versions

    def test_list_versions_empty(self, storage):
        """빈 버전 목록 테스트"""
        versions = storage.list_versions("nonexistent")

        assert versions == []

    def test_get_size(self, storage, temp_model_file):
        """모델 크기 조회 테스트"""
        storage.save(
            model_file=temp_model_file,
            model_name="model",
            version="1.0",
        )

        size = storage.get_size("model", "1.0")

        assert size > 0
        assert size >= len(b"fake model data for testing")

    def test_get_size_nonexistent_raises_error(self, storage):
        """존재하지 않는 모델 크기 조회 시 에러 테스트"""
        with pytest.raises(FileNotFoundError):
            storage.get_size("nonexistent", "1.0")


class TestModelStorageFactory:
    """ModelStorageFactory 테스트"""

    def test_create_local_storage(self, temp_storage_dir):
        """로컬 저장소 생성 테스트"""
        storage = ModelStorageFactory.create_local_storage(temp_storage_dir)

        assert storage.config.backend == StorageBackend.LOCAL
        assert storage.base_path == temp_storage_dir

    def test_create_git_lfs_storage(self, temp_storage_dir):
        """Git LFS 저장소 생성 테스트"""
        storage = ModelStorageFactory.create_git_lfs_storage(temp_storage_dir)

        assert storage.config.backend == StorageBackend.GIT_LFS
        assert storage.config.git_lfs_enabled is True
