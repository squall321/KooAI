"""
모델 저장소

AI 모델 파일의 저장, 로드, 관리를 담당합니다.
"""

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
import json


class StorageBackend(str, Enum):
    """저장소 백엔드 타입"""

    LOCAL = "local"
    GIT_LFS = "git_lfs"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"


@dataclass
class StorageConfig:
    """저장소 설정"""

    backend: StorageBackend
    base_path: Path
    enable_checksum: bool = True
    enable_compression: bool = False
    git_lfs_enabled: bool = False
    git_lfs_patterns: list = None  # e.g., ["*.pth", "*.onnx"]

    def __post_init__(self):
        if self.git_lfs_patterns is None:
            self.git_lfs_patterns = ["*.pth", "*.pt", "*.onnx", "*.bin"]


class ModelStorage:
    """
    모델 저장소

    모델 파일을 저장하고 관리합니다.
    """

    def __init__(self, config: StorageConfig):
        """
        Args:
            config: 저장소 설정
        """
        self.config = config
        self.base_path = config.base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Git LFS 초기화 (필요한 경우)
        if config.git_lfs_enabled:
            self._init_git_lfs()

    def save(
        self,
        model_file: Path,
        model_name: str,
        version: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        모델 저장

        Args:
            model_file: 저장할 모델 파일 경로
            model_name: 모델 이름
            version: 모델 버전
            metadata: 추가 메타데이터 (optional)

        Returns:
            Path: 저장된 파일 경로

        Raises:
            FileNotFoundError: 원본 파일이 없을 때
            IOError: 저장 실패 시
        """
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        # 저장 경로 생성
        model_dir = self.base_path / model_name / version
        model_dir.mkdir(parents=True, exist_ok=True)

        # 대상 파일 경로
        dest_file = model_dir / model_file.name

        try:
            # 파일 복사
            shutil.copy2(model_file, dest_file)

            # 체크섬 생성 (선택적)
            if self.config.enable_checksum:
                checksum = self._compute_checksum(dest_file)
                checksum_file = dest_file.with_suffix(dest_file.suffix + ".sha256")
                checksum_file.write_text(checksum)

            # 메타데이터 저장 (선택적)
            if metadata:
                metadata_file = model_dir / "metadata.json"
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

            # Git LFS 추적 (필요한 경우)
            if self.config.git_lfs_enabled:
                self._track_with_git_lfs(dest_file)

            return dest_file

        except Exception as e:
            raise IOError(f"Failed to save model: {str(e)}")

    def load(self, model_name: str, version: str, filename: str) -> Path:
        """
        모델 로드

        Args:
            model_name: 모델 이름
            version: 모델 버전
            filename: 파일 이름

        Returns:
            Path: 모델 파일 경로

        Raises:
            FileNotFoundError: 파일이 없을 때
            ValueError: 체크섬 검증 실패 시
        """
        model_path = self.base_path / model_name / version / filename

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # 체크섬 검증 (선택적)
        if self.config.enable_checksum:
            if not self._verify_checksum(model_path):
                raise ValueError(f"Checksum verification failed for: {model_path}")

        return model_path

    def delete(self, model_name: str, version: str) -> None:
        """
        모델 삭제

        Args:
            model_name: 모델 이름
            version: 모델 버전

        Raises:
            FileNotFoundError: 모델이 없을 때
        """
        model_dir = self.base_path / model_name / version

        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found: {model_name}:{version}")

        # 디렉토리 삭제
        shutil.rmtree(model_dir)

        # 모델 디렉토리가 비었으면 삭제
        parent_dir = model_dir.parent
        if parent_dir.exists() and not list(parent_dir.iterdir()):
            parent_dir.rmdir()

    def exists(self, model_name: str, version: str, filename: str) -> bool:
        """
        모델 파일 존재 여부 확인

        Args:
            model_name: 모델 이름
            version: 모델 버전
            filename: 파일 이름

        Returns:
            bool: 파일 존재 여부
        """
        model_path = self.base_path / model_name / version / filename
        return model_path.exists()

    def get_metadata(self, model_name: str, version: str) -> Optional[Dict[str, Any]]:
        """
        모델 메타데이터 조회

        Args:
            model_name: 모델 이름
            version: 모델 버전

        Returns:
            Optional[Dict]: 메타데이터 (없으면 None)
        """
        metadata_file = self.base_path / model_name / version / "metadata.json"

        if not metadata_file.exists():
            return None

        with open(metadata_file, "r") as f:
            return json.load(f)

    def list_versions(self, model_name: str) -> list[str]:
        """
        모델의 모든 버전 조회

        Args:
            model_name: 모델 이름

        Returns:
            list[str]: 버전 리스트
        """
        model_dir = self.base_path / model_name

        if not model_dir.exists():
            return []

        versions = [d.name for d in model_dir.iterdir() if d.is_dir()]
        versions.sort(reverse=True)

        return versions

    def get_size(self, model_name: str, version: str) -> int:
        """
        모델 크기 조회 (바이트)

        Args:
            model_name: 모델 이름
            version: 모델 버전

        Returns:
            int: 크기 (바이트)

        Raises:
            FileNotFoundError: 모델이 없을 때
        """
        model_dir = self.base_path / model_name / version

        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found: {model_name}:{version}")

        total_size = 0
        for file_path in model_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    def _compute_checksum(self, file_path: Path) -> str:
        """
        파일 체크섬 계산 (SHA256)

        Args:
            file_path: 파일 경로

        Returns:
            str: SHA256 해시
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # 청크 단위로 읽어서 해시 계산
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _verify_checksum(self, file_path: Path) -> bool:
        """
        체크섬 검증

        Args:
            file_path: 파일 경로

        Returns:
            bool: 검증 성공 여부
        """
        checksum_file = file_path.with_suffix(file_path.suffix + ".sha256")

        if not checksum_file.exists():
            # 체크섬 파일이 없으면 검증 생략
            return True

        expected_checksum = checksum_file.read_text().strip()
        actual_checksum = self._compute_checksum(file_path)

        return expected_checksum == actual_checksum

    def _init_git_lfs(self) -> None:
        """Git LFS 초기화"""
        try:
            # Git LFS 설치 확인
            subprocess.run(
                ["git", "lfs", "version"],
                check=True,
                capture_output=True,
                cwd=self.base_path,
            )

            # Git 저장소 초기화 (필요한 경우)
            git_dir = self.base_path / ".git"
            if not git_dir.exists():
                subprocess.run(["git", "init"], check=True, capture_output=True, cwd=self.base_path)

            # Git LFS 설치
            subprocess.run(
                ["git", "lfs", "install"],
                check=True,
                capture_output=True,
                cwd=self.base_path,
            )

            # LFS 추적 패턴 설정
            for pattern in self.config.git_lfs_patterns:
                subprocess.run(
                    ["git", "lfs", "track", pattern],
                    check=True,
                    capture_output=True,
                    cwd=self.base_path,
                )

        except subprocess.CalledProcessError as e:
            print(f"Warning: Git LFS initialization failed: {e}")
        except FileNotFoundError:
            print("Warning: Git or Git LFS not found. LFS features disabled.")

    def _track_with_git_lfs(self, file_path: Path) -> None:
        """
        파일을 Git LFS로 추적

        Args:
            file_path: 파일 경로
        """
        if not self.config.git_lfs_enabled:
            return

        try:
            # 파일 추가
            subprocess.run(
                ["git", "add", str(file_path)],
                check=True,
                capture_output=True,
                cwd=self.base_path,
            )
        except subprocess.CalledProcessError as e:
            print(f"Warning: Git LFS tracking failed: {e}")


class ModelStorageFactory:
    """모델 저장소 팩토리"""

    @staticmethod
    def create_local_storage(base_path: Path, **kwargs) -> ModelStorage:
        """
        로컬 저장소 생성

        Args:
            base_path: 기본 경로
            **kwargs: 추가 설정

        Returns:
            ModelStorage: 모델 저장소
        """
        config = StorageConfig(backend=StorageBackend.LOCAL, base_path=base_path, **kwargs)
        return ModelStorage(config)

    @staticmethod
    def create_git_lfs_storage(base_path: Path, **kwargs) -> ModelStorage:
        """
        Git LFS 저장소 생성

        Args:
            base_path: 기본 경로
            **kwargs: 추가 설정

        Returns:
            ModelStorage: 모델 저장소
        """
        config = StorageConfig(
            backend=StorageBackend.GIT_LFS,
            base_path=base_path,
            git_lfs_enabled=True,
            **kwargs,
        )
        return ModelStorage(config)
