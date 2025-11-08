"""
사전 학습 모델 관리자

사전 학습된 모델을 다운로드, 캐시, 로드하는 시스템.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests


class ModelSource(str, Enum):
    """모델 소스"""

    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    URL = "url"
    CUSTOM = "custom"


@dataclass
class PretrainedModelInfo:
    """사전 학습 모델 정보"""

    name: str  # 모델 이름
    source: ModelSource  # 소스
    model_id: str  # 소스별 모델 ID (예: "bert-base-uncased")
    framework: str = "pytorch"  # 프레임워크
    task: str = ""  # 태스크 (예: "text-classification")
    description: str = ""  # 설명
    license: str = ""  # 라이선스
    url: Optional[str] = None  # 다운로드 URL
    local_path: Optional[Path] = None  # 로컬 경로
    metadata: Dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터
    cached_at: Optional[datetime] = None  # 캐시 시간
    size_bytes: int = 0  # 파일 크기

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "source": self.source.value,
            "model_id": self.model_id,
            "framework": self.framework,
            "task": self.task,
            "description": self.description,
            "license": self.license,
            "url": self.url,
            "local_path": str(self.local_path) if self.local_path else None,
            "metadata": self.metadata,
            "cached_at": self.cached_at.isoformat() if self.cached_at else None,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PretrainedModelInfo":
        """딕셔너리에서 생성"""
        return cls(
            name=data["name"],
            source=ModelSource(data["source"]),
            model_id=data["model_id"],
            framework=data.get("framework", "pytorch"),
            task=data.get("task", ""),
            description=data.get("description", ""),
            license=data.get("license", ""),
            url=data.get("url"),
            local_path=Path(data["local_path"]) if data.get("local_path") else None,
            metadata=data.get("metadata", {}),
            cached_at=datetime.fromisoformat(data["cached_at"]) if data.get("cached_at") else None,
            size_bytes=data.get("size_bytes", 0),
        )


class PretrainedModelManager:
    """
    사전 학습 모델 관리자

    사전 학습된 모델을 다운로드, 캐시, 로드.
    """

    def __init__(self, cache_dir: Path):
        """
        Args:
            cache_dir: 모델 캐시 디렉토리
        """
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self._models: Dict[str, PretrainedModelInfo] = {}  # name -> info
        self._metadata_file = cache_dir / "models.json"

        # 메타데이터 로드
        self._load_metadata()

    def register_model(
        self,
        name: str,
        source: ModelSource,
        model_id: str,
        framework: str = "pytorch",
        task: str = "",
        description: str = "",
        license: str = "",
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PretrainedModelInfo:
        """
        모델 등록

        Args:
            name: 모델 이름
            source: 모델 소스
            model_id: 소스별 모델 ID
            framework: 프레임워크
            task: 태스크
            description: 설명
            license: 라이선스
            url: 다운로드 URL
            metadata: 추가 메타데이터

        Returns:
            PretrainedModelInfo
        """
        info = PretrainedModelInfo(
            name=name,
            source=source,
            model_id=model_id,
            framework=framework,
            task=task,
            description=description,
            license=license,
            url=url,
            metadata=metadata or {},
        )

        self._models[name] = info
        self._save_metadata()

        return info

    def get_model(self, name: str) -> Optional[PretrainedModelInfo]:
        """
        모델 정보 조회

        Args:
            name: 모델 이름

        Returns:
            PretrainedModelInfo 또는 None
        """
        return self._models.get(name)

    def list_models(
        self,
        source: Optional[ModelSource] = None,
        framework: Optional[str] = None,
        task: Optional[str] = None,
    ) -> List[PretrainedModelInfo]:
        """
        모델 목록 조회

        Args:
            source: 소스 필터
            framework: 프레임워크 필터
            task: 태스크 필터

        Returns:
            모델 정보 리스트
        """
        models = list(self._models.values())

        if source:
            models = [m for m in models if m.source == source]
        if framework:
            models = [m for m in models if m.framework == framework]
        if task:
            models = [m for m in models if m.task == task]

        return models

    def download_model(self, name: str, force: bool = False) -> Path:
        """
        모델 다운로드 (캐시에서 사용 가능하면 캐시 반환)

        Args:
            name: 모델 이름
            force: 강제 다운로드

        Returns:
            로컬 모델 경로

        Raises:
            ValueError: 모델을 찾을 수 없음
            RuntimeError: 다운로드 실패
        """
        info = self.get_model(name)
        if not info:
            raise ValueError(f"Model '{name}' not found")

        # 이미 캐시에 있으면 반환
        if not force and info.local_path and info.local_path.exists():
            return info.local_path

        # 소스별 다운로드
        if info.source == ModelSource.HUGGINGFACE:
            local_path = self._download_from_huggingface(info)
        elif info.source == ModelSource.URL:
            if not info.url:
                raise ValueError(f"Model '{name}' has no URL")
            local_path = self._download_from_url(info.url, name)
        elif info.source == ModelSource.LOCAL:
            if not info.local_path or not info.local_path.exists():
                raise ValueError(f"Local path for model '{name}' does not exist")
            local_path = info.local_path
        else:
            raise ValueError(f"Unsupported source: {info.source}")

        # 메타데이터 업데이트
        info.local_path = local_path
        info.cached_at = datetime.utcnow()
        if local_path.is_file():
            info.size_bytes = local_path.stat().st_size
        self._save_metadata()

        return local_path

    def load_model(self, name: str, **kwargs) -> Any:
        """
        모델 로드 (자동 다운로드)

        Args:
            name: 모델 이름
            **kwargs: 모델 로드 인자

        Returns:
            로드된 모델

        Raises:
            ValueError: 모델을 찾을 수 없음
        """
        info = self.get_model(name)
        if not info:
            raise ValueError(f"Model '{name}' not found")

        # 다운로드 (캐시 사용)
        model_path = self.download_model(name)

        # 프레임워크별 로드
        if info.framework == "pytorch":
            return self._load_pytorch_model(model_path, **kwargs)
        elif info.framework == "tensorflow":
            return self._load_tensorflow_model(model_path, **kwargs)
        else:
            raise ValueError(f"Unsupported framework: {info.framework}")

    def delete_cached_model(self, name: str) -> None:
        """
        캐시된 모델 삭제

        Args:
            name: 모델 이름
        """
        info = self.get_model(name)
        if info and info.local_path and info.local_path.exists():
            if info.local_path.is_file():
                info.local_path.unlink()
            elif info.local_path.is_dir():
                import shutil

                shutil.rmtree(info.local_path)

            info.local_path = None
            info.cached_at = None
            info.size_bytes = 0
            self._save_metadata()

    def get_cache_size(self) -> int:
        """캐시 전체 크기 (바이트)"""
        return sum(info.size_bytes for info in self._models.values())

    def _download_from_huggingface(self, info: PretrainedModelInfo) -> Path:
        """HuggingFace에서 다운로드"""
        try:
            from transformers import AutoModel, AutoTokenizer

            model_dir = self._cache_dir / "huggingface" / info.model_id.replace("/", "_")
            model_dir.mkdir(parents=True, exist_ok=True)

            # 모델과 토크나이저 다운로드
            AutoModel.from_pretrained(info.model_id, cache_dir=str(model_dir))
            AutoTokenizer.from_pretrained(info.model_id, cache_dir=str(model_dir))

            return model_dir

        except ImportError:
            raise RuntimeError(
                "transformers library not installed. " "Install with: pip install transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to download from HuggingFace: {e}")

    def _download_from_url(self, url: str, name: str) -> Path:
        """URL에서 다운로드"""
        # 파일명 추출
        parsed = urlparse(url)
        filename = Path(parsed.path).name or f"{name}.bin"

        local_path = self._cache_dir / "downloads" / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return local_path

        except Exception as e:
            raise RuntimeError(f"Failed to download from URL: {e}")

    def _load_pytorch_model(self, model_path: Path, **kwargs) -> Any:
        """PyTorch 모델 로드"""
        try:
            import torch

            if model_path.is_file():
                return torch.load(model_path, **kwargs)
            else:
                # 디렉토리인 경우 (HuggingFace 등)
                from transformers import AutoModel

                return AutoModel.from_pretrained(str(model_path), **kwargs)

        except ImportError:
            raise RuntimeError("PyTorch not installed")
        except Exception as e:
            raise RuntimeError(f"Failed to load PyTorch model: {e}")

    def _load_tensorflow_model(self, model_path: Path, **kwargs) -> Any:
        """TensorFlow 모델 로드"""
        try:
            import tensorflow as tf

            return tf.keras.models.load_model(str(model_path), **kwargs)

        except ImportError:
            raise RuntimeError("TensorFlow not installed")
        except Exception as e:
            raise RuntimeError(f"Failed to load TensorFlow model: {e}")

    def _save_metadata(self) -> None:
        """메타데이터 저장"""
        data = {"models": {name: info.to_dict() for name, info in self._models.items()}}

        with open(self._metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_metadata(self) -> None:
        """메타데이터 로드"""
        if not self._metadata_file.exists():
            return

        try:
            with open(self._metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            models_data = data.get("models", {})
            self._models = {
                name: PretrainedModelInfo.from_dict(info_data)
                for name, info_data in models_data.items()
            }

        except Exception as e:
            print(f"Failed to load metadata: {e}")
