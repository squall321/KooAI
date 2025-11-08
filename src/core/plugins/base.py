"""
플러그인 시스템 기본 추상화

플러그인 인터페이스와 베이스 클래스를 정의합니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4


class PluginStatus(str, Enum):
    """플러그인 상태"""

    REGISTERED = "registered"  # 등록됨
    LOADED = "loaded"  # 로드됨
    ACTIVE = "active"  # 활성화
    INACTIVE = "inactive"  # 비활성화
    ERROR = "error"  # 에러
    UNLOADED = "unloaded"  # 언로드됨


class PluginType(str, Enum):
    """플러그인 타입"""

    STAGE = "stage"  # ProcessingStage 플러그인
    ADAPTER = "adapter"  # ModelAdapter 플러그인
    LLM_CLIENT = "llm_client"  # LLM Client 플러그인
    DATA_SOURCE = "data_source"  # 데이터 소스 플러그인
    EXPORTER = "exporter"  # 데이터 익스포터 플러그인
    CUSTOM = "custom"  # 커스텀 플러그인


@dataclass
class PluginVersion:
    """플러그인 버전"""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "PluginVersion") -> bool:
        """버전 비교"""
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other: "PluginVersion") -> bool:
        return self < other or self == other

    def __gt__(self, other: "PluginVersion") -> bool:
        return not self <= other

    def __ge__(self, other: "PluginVersion") -> bool:
        return not self < other

    @classmethod
    def from_string(cls, version_str: str) -> "PluginVersion":
        """문자열에서 버전 파싱 (예: "1.2.3")"""
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")

        try:
            return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))
        except ValueError as e:
            raise ValueError(f"Invalid version format: {version_str}") from e


@dataclass
class PluginDependency:
    """플러그인 의존성"""

    name: str  # 의존하는 플러그인 이름
    min_version: Optional[PluginVersion] = None  # 최소 버전
    max_version: Optional[PluginVersion] = None  # 최대 버전
    optional: bool = False  # 선택적 의존성

    def is_compatible(self, version: PluginVersion) -> bool:
        """버전 호환성 확인"""
        if self.min_version and version < self.min_version:
            return False
        if self.max_version and version > self.max_version:
            return False
        return True


@dataclass
class PluginMetadata:
    """플러그인 메타데이터"""

    name: str  # 플러그인 이름
    version: PluginVersion  # 버전
    plugin_type: PluginType  # 플러그인 타입
    description: str = ""  # 설명
    author: str = ""  # 작성자
    homepage: str = ""  # 홈페이지 URL
    license: str = ""  # 라이선스
    dependencies: List[PluginDependency] = field(default_factory=list)  # 의존성
    tags: Set[str] = field(default_factory=set)  # 태그
    config_schema: Optional[Dict[str, Any]] = None  # 설정 스키마
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "version": str(self.version),
            "plugin_type": self.plugin_type.value,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "license": self.license,
            "dependencies": [
                {
                    "name": dep.name,
                    "min_version": str(dep.min_version) if dep.min_version else None,
                    "max_version": str(dep.max_version) if dep.max_version else None,
                    "optional": dep.optional,
                }
                for dep in self.dependencies
            ],
            "tags": list(self.tags),
            "config_schema": self.config_schema,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        """딕셔너리에서 생성"""
        return cls(
            name=data["name"],
            version=PluginVersion.from_string(data["version"]),
            plugin_type=PluginType(data["plugin_type"]),
            description=data.get("description", ""),
            author=data.get("author", ""),
            homepage=data.get("homepage", ""),
            license=data.get("license", ""),
            dependencies=[
                PluginDependency(
                    name=dep["name"],
                    min_version=(
                        PluginVersion.from_string(dep["min_version"])
                        if dep.get("min_version")
                        else None
                    ),
                    max_version=(
                        PluginVersion.from_string(dep["max_version"])
                        if dep.get("max_version")
                        else None
                    ),
                    optional=dep.get("optional", False),
                )
                for dep in data.get("dependencies", [])
            ],
            tags=set(data.get("tags", [])),
            config_schema=data.get("config_schema"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.utcnow()
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data
                else datetime.utcnow()
            ),
        )


class IPlugin(ABC):
    """
    플러그인 인터페이스

    모든 플러그인이 구현해야 하는 인터페이스.
    """

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """플러그인 메타데이터 반환"""
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        플러그인 초기화

        Args:
            config: 플러그인 설정
        """
        pass

    @abstractmethod
    async def activate(self) -> None:
        """플러그인 활성화"""
        pass

    @abstractmethod
    async def deactivate(self) -> None:
        """플러그인 비활성화"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """플러그인 정리 (언로드 전)"""
        pass

    @abstractmethod
    def get_status(self) -> PluginStatus:
        """플러그인 상태 반환"""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        플러그인 헬스 체크

        Returns:
            상태 정보 딕셔너리 (healthy, message, details 등)
        """
        pass


class BasePlugin(IPlugin):
    """
    플러그인 베이스 클래스

    공통 기능을 제공하는 추상 베이스 클래스.
    """

    def __init__(self, metadata: PluginMetadata):
        self._metadata = metadata
        self._status = PluginStatus.REGISTERED
        self._config: Dict[str, Any] = {}
        self._plugin_id = uuid4()
        self._error: Optional[str] = None

    @property
    def plugin_id(self) -> UUID:
        """플러그인 고유 ID"""
        return self._plugin_id

    @property
    def name(self) -> str:
        """플러그인 이름"""
        return self._metadata.name

    @property
    def version(self) -> PluginVersion:
        """플러그인 버전"""
        return self._metadata.version

    def get_metadata(self) -> PluginMetadata:
        """플러그인 메타데이터 반환"""
        return self._metadata

    async def initialize(self, config: Dict[str, Any]) -> None:
        """플러그인 초기화"""
        self._config = config
        self._status = PluginStatus.LOADED

        try:
            await self._on_initialize(config)
        except Exception as e:
            self._status = PluginStatus.ERROR
            self._error = str(e)
            raise

    async def activate(self) -> None:
        """플러그인 활성화"""
        if self._status != PluginStatus.LOADED:
            raise RuntimeError(f"Cannot activate plugin in {self._status} status")

        try:
            await self._on_activate()
            self._status = PluginStatus.ACTIVE
        except Exception as e:
            self._status = PluginStatus.ERROR
            self._error = str(e)
            raise

    async def deactivate(self) -> None:
        """플러그인 비활성화"""
        if self._status != PluginStatus.ACTIVE:
            raise RuntimeError(f"Cannot deactivate plugin in {self._status} status")

        try:
            await self._on_deactivate()
            self._status = PluginStatus.INACTIVE
        except Exception as e:
            self._status = PluginStatus.ERROR
            self._error = str(e)
            raise

    async def cleanup(self) -> None:
        """플러그인 정리"""
        try:
            await self._on_cleanup()
            self._status = PluginStatus.UNLOADED
        except Exception as e:
            self._status = PluginStatus.ERROR
            self._error = str(e)
            raise

    def get_status(self) -> PluginStatus:
        """플러그인 상태 반환"""
        return self._status

    def health_check(self) -> Dict[str, Any]:
        """플러그인 헬스 체크"""
        healthy = self._status in (PluginStatus.LOADED, PluginStatus.ACTIVE)

        result = {
            "healthy": healthy,
            "status": self._status.value,
            "plugin_id": str(self._plugin_id),
            "name": self.name,
            "version": str(self.version),
        }

        if self._error:
            result["error"] = self._error

        # 서브클래스의 추가 헬스 체크
        try:
            custom_health = self._custom_health_check()
            result["details"] = custom_health
        except Exception as e:
            result["health_check_error"] = str(e)

        return result

    # 서브클래스에서 오버라이드할 훅 메서드
    async def _on_initialize(self, config: Dict[str, Any]) -> None:
        """초기화 훅 (서브클래스에서 구현)"""
        pass

    async def _on_activate(self) -> None:
        """활성화 훅 (서브클래스에서 구현)"""
        pass

    async def _on_deactivate(self) -> None:
        """비활성화 훅 (서브클래스에서 구현)"""
        pass

    async def _on_cleanup(self) -> None:
        """정리 훅 (서브클래스에서 구현)"""
        pass

    def _custom_health_check(self) -> Dict[str, Any]:
        """커스텀 헬스 체크 (서브클래스에서 구현)"""
        return {}


class PluginError(Exception):
    """플러그인 에러 베이스 클래스"""

    pass


class PluginNotFoundError(PluginError):
    """플러그인을 찾을 수 없음"""

    pass


class PluginLoadError(PluginError):
    """플러그인 로드 실패"""

    pass


class PluginDependencyError(PluginError):
    """플러그인 의존성 에러"""

    pass


class PluginVersionConflictError(PluginError):
    """플러그인 버전 충돌"""

    pass


class PluginConfigError(PluginError):
    """플러그인 설정 에러"""

    pass
