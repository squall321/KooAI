"""
Model Adapter 플러그인

커스텀 AI 모델 어댑터를 플러그인으로 확장.
"""

from typing import Any, Dict

from ...ai_models.adapters.base import BaseModelAdapter
from ..base import BasePlugin, PluginMetadata, PluginType


class AdapterPlugin(BasePlugin):
    """
    Model Adapter 플러그인 베이스 클래스

    커스텀 AI 모델 어댑터를 플러그인으로 구현.
    """

    def __init__(self, metadata: PluginMetadata):
        """
        Args:
            metadata: 플러그인 메타데이터 (plugin_type은 ADAPTER여야 함)
        """
        if metadata.plugin_type != PluginType.ADAPTER:
            raise ValueError(
                f"AdapterPlugin requires PluginType.ADAPTER, " f"got {metadata.plugin_type}"
            )

        super().__init__(metadata)
        self._adapter_class: type[BaseModelAdapter] | None = None

    async def _on_initialize(self, config: Dict[str, Any]) -> None:
        """초기화: 어댑터 클래스 설정"""
        # 서브클래스에서 self._adapter_class를 설정해야 함
        if self._adapter_class is None:
            raise NotImplementedError("Subclass must set self._adapter_class in _on_initialize")

    def get_adapter_class(self) -> type[BaseModelAdapter]:
        """
        Model Adapter 클래스 반환

        Returns:
            BaseModelAdapter 클래스

        Raises:
            RuntimeError: 플러그인이 초기화되지 않음
        """
        if self._adapter_class is None:
            raise RuntimeError(
                f"Plugin '{self.name}' not initialized. " f"Call initialize() first."
            )

        return self._adapter_class

    def create_adapter(self) -> BaseModelAdapter:
        """
        Adapter 인스턴스 생성

        Returns:
            BaseModelAdapter 인스턴스
        """
        adapter_class = self.get_adapter_class()
        return adapter_class()


class AdapterPluginRegistry:
    """
    Adapter 플러그인 레지스트리

    Model Adapter 플러그인을 관리하고 어댑터 인스턴스를 생성.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, AdapterPlugin] = {}  # adapter_name -> plugin

    def register(self, plugin: AdapterPlugin) -> None:
        """
        Adapter 플러그인 등록

        Args:
            plugin: 등록할 플러그인
        """
        metadata = plugin.get_metadata()
        self._plugins[metadata.name] = plugin

    def unregister(self, name: str) -> None:
        """
        Adapter 플러그인 등록 해제

        Args:
            name: 플러그인 이름
        """
        if name in self._plugins:
            del self._plugins[name]

    def get(self, name: str) -> AdapterPlugin:
        """
        Adapter 플러그인 조회

        Args:
            name: 플러그인 이름

        Returns:
            AdapterPlugin 인스턴스

        Raises:
            KeyError: 플러그인을 찾을 수 없음
        """
        if name not in self._plugins:
            raise KeyError(f"Adapter plugin '{name}' not found")

        return self._plugins[name]

    def create_adapter(self, name: str) -> BaseModelAdapter:
        """
        Adapter 인스턴스 생성

        Args:
            name: 플러그인 이름

        Returns:
            BaseModelAdapter 인스턴스

        Raises:
            KeyError: 플러그인을 찾을 수 없음
        """
        plugin = self.get(name)
        return plugin.create_adapter()

    def list_adapters(self) -> list[str]:
        """등록된 모든 Adapter 플러그인 이름"""
        return list(self._plugins.keys())

    def has(self, name: str) -> bool:
        """Adapter 플러그인 존재 여부"""
        return name in self._plugins
