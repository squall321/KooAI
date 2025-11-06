"""
AI 모델 레지스트리

AI 모델의 등록, 조회, 버전 관리를 담당하는 중앙 레지스트리.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from ..domain.entities import AIModel
from .adapters.base import (
    BaseModelAdapter,
    ModelConfig,
    ModelFramework,
    ModelAdapterFactory,
)


class ModelMetadata:
    """
    모델 메타데이터

    레지스트리에서 관리하는 모델의 메타정보.
    """

    def __init__(
        self,
        name: str,
        version: str,
        framework: ModelFramework,
        model_path: Path,
        model_type: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.id = uuid4()
        self.name = name
        self.version = version
        self.framework = framework
        self.model_path = model_path
        self.model_type = model_type
        self.description = description
        self.tags = tags or []
        self.config = config or {}
        self.registered_at = datetime.utcnow()
        self.last_used_at: Optional[datetime] = None
        self.usage_count = 0

    def get_full_name(self) -> str:
        """전체 이름 (이름:버전)"""
        return f"{self.name}:{self.version}"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": str(self.id),
            "name": self.name,
            "version": self.version,
            "framework": self.framework.value,
            "model_path": str(self.model_path),
            "model_type": self.model_type,
            "description": self.description,
            "tags": self.tags,
            "config": self.config,
            "registered_at": self.registered_at.isoformat(),
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        """딕셔너리에서 생성"""
        metadata = cls(
            name=data["name"],
            version=data["version"],
            framework=ModelFramework(data["framework"]),
            model_path=Path(data["model_path"]),
            model_type=data["model_type"],
            description=data.get("description"),
            tags=data.get("tags", []),
            config=data.get("config", {}),
        )
        metadata.id = UUID(data["id"])
        metadata.registered_at = datetime.fromisoformat(data["registered_at"])
        if data.get("last_used_at"):
            metadata.last_used_at = datetime.fromisoformat(data["last_used_at"])
        metadata.usage_count = data.get("usage_count", 0)
        return metadata


class AIModelRegistry:
    """
    AI 모델 레지스트리

    모델을 등록하고, 조회하고, 로드하는 중앙 관리 시스템.
    """

    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Args:
            registry_dir: 레지스트리 메타데이터 저장 디렉토리
        """
        self.registry_dir = registry_dir or Path.home() / ".kooai" / "models"
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.registry_dir / "registry.json"
        self._models: Dict[str, ModelMetadata] = {}
        self._loaded_models: Dict[str, BaseModelAdapter] = {}

        # 레지스트리 로드
        self._load_registry()

    def register(
        self,
        name: str,
        version: str,
        framework: ModelFramework,
        model_path: Path,
        model_type: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> ModelMetadata:
        """
        모델 등록

        Args:
            name: 모델 이름
            version: 모델 버전
            framework: AI 프레임워크
            model_path: 모델 파일 경로
            model_type: 모델 타입 (vae, transformer, etc.)
            description: 설명 (optional)
            tags: 태그 리스트 (optional)
            config: 추가 설정 (optional)
            overwrite: 기존 모델 덮어쓰기 여부

        Returns:
            ModelMetadata: 등록된 모델 메타데이터

        Raises:
            ValueError: 이미 등록된 모델이 있을 때 (overwrite=False)
            FileNotFoundError: 모델 파일이 없을 때
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        full_name = f"{name}:{version}"

        # 중복 확인
        if full_name in self._models and not overwrite:
            raise ValueError(
                f"Model {full_name} already registered. "
                f"Use overwrite=True to replace."
            )

        # 메타데이터 생성
        metadata = ModelMetadata(
            name=name,
            version=version,
            framework=framework,
            model_path=model_path,
            model_type=model_type,
            description=description,
            tags=tags,
            config=config,
        )

        # 등록
        self._models[full_name] = metadata

        # 저장
        self._save_registry()

        return metadata

    def unregister(self, name: str, version: str) -> None:
        """
        모델 등록 해제

        Args:
            name: 모델 이름
            version: 모델 버전

        Raises:
            KeyError: 등록되지 않은 모델일 때
        """
        full_name = f"{name}:{version}"

        if full_name not in self._models:
            raise KeyError(f"Model {full_name} not found in registry")

        # 로드된 모델이 있으면 언로드
        if full_name in self._loaded_models:
            self._loaded_models[full_name].unload()
            del self._loaded_models[full_name]

        # 등록 해제
        del self._models[full_name]

        # 저장
        self._save_registry()

    def load(
        self,
        name: str,
        version: str = "latest",
        device: str = "cpu",
        **config_kwargs,
    ) -> BaseModelAdapter:
        """
        모델 로드

        Args:
            name: 모델 이름
            version: 모델 버전 ("latest"면 최신 버전)
            device: 디바이스 (cpu, cuda, etc.)
            **config_kwargs: 추가 설정

        Returns:
            BaseModelAdapter: 로드된 모델 어댑터

        Raises:
            KeyError: 등록되지 않은 모델일 때
            RuntimeError: 모델 로드 실패 시
        """
        # 버전 결정
        if version == "latest":
            version = self._get_latest_version(name)

        full_name = f"{name}:{version}"

        if full_name not in self._models:
            raise KeyError(f"Model {full_name} not found in registry")

        # 이미 로드된 경우 재사용
        if full_name in self._loaded_models:
            metadata = self._models[full_name]
            metadata.last_used_at = datetime.utcnow()
            metadata.usage_count += 1
            return self._loaded_models[full_name]

        # 메타데이터 가져오기
        metadata = self._models[full_name]

        # 설정 병합
        merged_config = {**metadata.config, **config_kwargs}

        # 모델 설정 생성
        model_config = ModelConfig(
            framework=metadata.framework,
            model_path=metadata.model_path,
            device=device,
            config=merged_config,
        )

        # 어댑터 생성 및 로드
        try:
            adapter = ModelAdapterFactory.create(metadata.framework)
            adapter.load(model_config)

            # 캐시에 저장
            self._loaded_models[full_name] = adapter

            # 사용 통계 업데이트
            metadata.last_used_at = datetime.utcnow()
            metadata.usage_count += 1
            self._save_registry()

            return adapter

        except Exception as e:
            raise RuntimeError(f"Failed to load model {full_name}: {str(e)}")

    def get_metadata(self, name: str, version: str = "latest") -> ModelMetadata:
        """
        모델 메타데이터 조회

        Args:
            name: 모델 이름
            version: 모델 버전

        Returns:
            ModelMetadata: 모델 메타데이터

        Raises:
            KeyError: 등록되지 않은 모델일 때
        """
        if version == "latest":
            version = self._get_latest_version(name)

        full_name = f"{name}:{version}"

        if full_name not in self._models:
            raise KeyError(f"Model {full_name} not found in registry")

        return self._models[full_name]

    def list_models(
        self,
        framework: Optional[ModelFramework] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ModelMetadata]:
        """
        모델 목록 조회

        Args:
            framework: 프레임워크 필터 (optional)
            tags: 태그 필터 (optional, AND 조건)

        Returns:
            List[ModelMetadata]: 모델 메타데이터 리스트
        """
        models = list(self._models.values())

        # 프레임워크 필터
        if framework:
            models = [m for m in models if m.framework == framework]

        # 태그 필터
        if tags:
            models = [m for m in models if all(tag in m.tags for tag in tags)]

        return models

    def list_versions(self, name: str) -> List[str]:
        """
        특정 모델의 모든 버전 조회

        Args:
            name: 모델 이름

        Returns:
            List[str]: 버전 리스트 (최신순)
        """
        versions = [
            metadata.version
            for metadata in self._models.values()
            if metadata.name == name
        ]

        # 버전 정렬 (최신순)
        versions.sort(reverse=True)

        return versions

    def unload_model(self, name: str, version: str = "latest") -> None:
        """
        로드된 모델 언로드 (메모리 해제)

        Args:
            name: 모델 이름
            version: 모델 버전
        """
        if version == "latest":
            version = self._get_latest_version(name)

        full_name = f"{name}:{version}"

        if full_name in self._loaded_models:
            self._loaded_models[full_name].unload()
            del self._loaded_models[full_name]

    def unload_all(self) -> None:
        """모든 로드된 모델 언로드"""
        for adapter in self._loaded_models.values():
            adapter.unload()
        self._loaded_models.clear()

    def _get_latest_version(self, name: str) -> str:
        """최신 버전 조회"""
        versions = self.list_versions(name)

        if not versions:
            raise KeyError(f"No versions found for model: {name}")

        return versions[0]

    def _load_registry(self) -> None:
        """레지스트리 파일 로드"""
        if not self.registry_file.exists():
            return

        try:
            with open(self.registry_file, "r") as f:
                data = json.load(f)

            for model_data in data.get("models", []):
                metadata = ModelMetadata.from_dict(model_data)
                self._models[metadata.get_full_name()] = metadata

        except Exception as e:
            print(f"Warning: Failed to load registry: {e}")

    def _save_registry(self) -> None:
        """레지스트리 파일 저장"""
        data = {
            "version": "1.0",
            "models": [metadata.to_dict() for metadata in self._models.values()],
        }

        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=2)
