"""
Processing Stage 플러그인

커스텀 파이프라인 단계를 플러그인으로 확장.
"""

from typing import Any, Dict

from ...pipeline import ProcessingStage
from ..base import BasePlugin, PluginMetadata, PluginType


class StagePlugin(BasePlugin):
    """
    Processing Stage 플러그인 베이스 클래스

    커스텀 파이프라인 단계를 플러그인으로 구현.
    """

    def __init__(self, metadata: PluginMetadata):
        """
        Args:
            metadata: 플러그인 메타데이터 (plugin_type은 STAGE여야 함)
        """
        if metadata.plugin_type != PluginType.STAGE:
            raise ValueError(
                f"StagePlugin requires PluginType.STAGE, " f"got {metadata.plugin_type}"
            )

        super().__init__(metadata)
        self._stage_class: type[ProcessingStage] | None = None

    async def _on_initialize(self, config: Dict[str, Any]) -> None:
        """초기화: 단계 클래스 생성"""
        # 서브클래스에서 self._stage_class를 설정해야 함
        if self._stage_class is None:
            raise NotImplementedError("Subclass must set self._stage_class in _on_initialize")

    def get_stage_class(self) -> type[ProcessingStage]:
        """
        Processing Stage 클래스 반환

        Returns:
            ProcessingStage 클래스

        Raises:
            RuntimeError: 플러그인이 초기화되지 않음
        """
        if self._stage_class is None:
            raise RuntimeError(
                f"Plugin '{self.name}' not initialized. " f"Call initialize() first."
            )

        return self._stage_class

    def create_stage(self, **kwargs) -> ProcessingStage:
        """
        Stage 인스턴스 생성

        Args:
            **kwargs: Stage 생성자에 전달할 인자

        Returns:
            ProcessingStage 인스턴스
        """
        stage_class = self.get_stage_class()
        return stage_class(**kwargs)


class StagePluginRegistry:
    """
    Stage 플러그인 레지스트리

    Stage 플러그인을 관리하고 Stage 인스턴스를 생성.
    """

    def __init__(self):
        self._plugins: Dict[str, StagePlugin] = {}  # stage_name -> plugin

    def register(self, plugin: StagePlugin) -> None:
        """
        Stage 플러그인 등록

        Args:
            plugin: 등록할 플러그인
        """
        metadata = plugin.get_metadata()
        self._plugins[metadata.name] = plugin

    def unregister(self, name: str) -> None:
        """
        Stage 플러그인 등록 해제

        Args:
            name: 플러그인 이름
        """
        if name in self._plugins:
            del self._plugins[name]

    def get(self, name: str) -> StagePlugin:
        """
        Stage 플러그인 조회

        Args:
            name: 플러그인 이름

        Returns:
            StagePlugin 인스턴스

        Raises:
            KeyError: 플러그인을 찾을 수 없음
        """
        if name not in self._plugins:
            raise KeyError(f"Stage plugin '{name}' not found")

        return self._plugins[name]

    def create_stage(self, name: str, **kwargs) -> ProcessingStage:
        """
        Stage 인스턴스 생성

        Args:
            name: 플러그인 이름
            **kwargs: Stage 생성자 인자

        Returns:
            ProcessingStage 인스턴스

        Raises:
            KeyError: 플러그인을 찾을 수 없음
        """
        plugin = self.get(name)
        return plugin.create_stage(**kwargs)

    def list_stages(self) -> list[str]:
        """등록된 모든 Stage 플러그인 이름"""
        return list(self._plugins.keys())

    def has(self, name: str) -> bool:
        """Stage 플러그인 존재 여부"""
        return name in self._plugins
