"""
플러그인 로더

플러그인을 동적으로 로드하는 시스템.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .base import (
    BasePlugin,
    IPlugin,
    PluginError,
    PluginLoadError,
    PluginMetadata,
)
from .registry import PluginRegistry


class PluginLoader:
    """
    플러그인 로더

    파일 시스템 또는 모듈에서 플러그인을 동적으로 로드.
    """

    def __init__(self, registry: PluginRegistry):
        """
        Args:
            registry: 플러그인 레지스트리
        """
        self._registry = registry
        self._loaded_modules: Dict[str, Any] = {}  # 로드된 모듈 캐시

    def load_from_file(
        self,
        plugin_path: Path,
        class_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> IPlugin:
        """
        파일에서 플러그인 로드

        Args:
            plugin_path: 플러그인 파일 경로 (.py)
            class_name: 플러그인 클래스 이름
            config: 플러그인 설정

        Returns:
            로드된 플러그인 인스턴스

        Raises:
            PluginLoadError: 로드 실패
        """
        if not plugin_path.exists():
            raise PluginLoadError(f"Plugin file not found: {plugin_path}")

        if not plugin_path.suffix == ".py":
            raise PluginLoadError(
                f"Plugin file must be .py file: {plugin_path}"
            )

        try:
            # 모듈 이름 생성
            module_name = f"plugin_{plugin_path.stem}"

            # 이미 로드된 모듈인지 확인
            if module_name in self._loaded_modules:
                module = self._loaded_modules[module_name]
            else:
                # 모듈 스펙 생성
                spec = importlib.util.spec_from_file_location(
                    module_name, plugin_path
                )
                if spec is None or spec.loader is None:
                    raise PluginLoadError(
                        f"Failed to create module spec for {plugin_path}"
                    )

                # 모듈 로드
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # 캐시에 저장
                self._loaded_modules[module_name] = module

            # 클래스 가져오기
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Class '{class_name}' not found in {plugin_path}"
                )

            plugin_class = getattr(module, class_name)

            # IPlugin 인터페이스 확인
            if not issubclass(plugin_class, BasePlugin):
                raise PluginLoadError(
                    f"Class '{class_name}' must inherit from BasePlugin"
                )

            # 플러그인 인스턴스 생성
            plugin = plugin_class()

            # 초기화
            if config:
                import asyncio

                asyncio.create_task(plugin.initialize(config))

            # 레지스트리에 등록
            self._registry.register(plugin)

            return plugin

        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin from {plugin_path}: {e}") from e

    def load_from_module(
        self,
        module_path: str,
        class_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> IPlugin:
        """
        모듈에서 플러그인 로드

        Args:
            module_path: 모듈 경로 (예: "my_plugins.custom_stage")
            class_name: 플러그인 클래스 이름
            config: 플러그인 설정

        Returns:
            로드된 플러그인 인스턴스

        Raises:
            PluginLoadError: 로드 실패
        """
        try:
            # 모듈 임포트
            if module_path in self._loaded_modules:
                module = self._loaded_modules[module_path]
            else:
                module = importlib.import_module(module_path)
                self._loaded_modules[module_path] = module

            # 클래스 가져오기
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Class '{class_name}' not found in module '{module_path}'"
                )

            plugin_class = getattr(module, class_name)

            # IPlugin 인터페이스 확인
            if not issubclass(plugin_class, BasePlugin):
                raise PluginLoadError(
                    f"Class '{class_name}' must inherit from BasePlugin"
                )

            # 플러그인 인스턴스 생성
            plugin = plugin_class()

            # 초기화
            if config:
                import asyncio

                asyncio.create_task(plugin.initialize(config))

            # 레지스트리에 등록
            self._registry.register(plugin)

            return plugin

        except ImportError as e:
            raise PluginLoadError(
                f"Failed to import module '{module_path}': {e}"
            ) from e
        except Exception as e:
            raise PluginLoadError(
                f"Failed to load plugin from module '{module_path}': {e}"
            ) from e

    def load_from_directory(
        self,
        plugins_dir: Path,
        config_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[IPlugin]:
        """
        디렉토리에서 모든 플러그인 로드

        디렉토리 구조:
        plugins_dir/
        ├── plugin1/
        │   ├── __init__.py
        │   └── plugin.py  (플러그인 클래스 정의)
        └── plugin2/
            ├── __init__.py
            └── plugin.py

        Args:
            plugins_dir: 플러그인 디렉토리
            config_map: 플러그인 이름 -> 설정 맵

        Returns:
            로드된 플러그인 리스트

        Raises:
            PluginLoadError: 로드 실패
        """
        if not plugins_dir.exists():
            raise PluginLoadError(f"Plugins directory not found: {plugins_dir}")

        config_map = config_map or {}
        loaded_plugins = []

        # 각 서브디렉토리를 순회
        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # __init__.py가 없으면 건너뜀
            if not (plugin_dir / "__init__.py").exists():
                continue

            plugin_name = plugin_dir.name

            try:
                # plugin.py 파일에서 로드 시도
                plugin_file = plugin_dir / "plugin.py"
                if plugin_file.exists():
                    # 클래스 이름 추측 (CamelCase 변환)
                    class_name = "".join(
                        word.capitalize() for word in plugin_name.split("_")
                    ) + "Plugin"

                    config = config_map.get(plugin_name, {})
                    plugin = self.load_from_file(plugin_file, class_name, config)
                    loaded_plugins.append(plugin)
                else:
                    print(f"Warning: No plugin.py found in {plugin_dir}")

            except PluginLoadError as e:
                # 개별 플러그인 로드 실패는 로그만 남기고 계속
                print(f"Failed to load plugin from {plugin_dir}: {e}")

        return loaded_plugins

    def reload_plugin(self, plugin_name: str) -> IPlugin:
        """
        플러그인 리로드

        Args:
            plugin_name: 플러그인 이름

        Returns:
            리로드된 플러그인

        Raises:
            PluginLoadError: 리로드 실패
        """
        # 기존 플러그인 정보 가져오기
        try:
            old_plugin = self._registry.get(plugin_name)
            metadata = old_plugin.get_metadata()
        except Exception as e:
            raise PluginLoadError(
                f"Cannot reload plugin '{plugin_name}': {e}"
            ) from e

        # 모듈 캐시에서 제거
        module_names_to_remove = [
            name
            for name in self._loaded_modules.keys()
            if plugin_name in name
        ]
        for module_name in module_names_to_remove:
            del self._loaded_modules[module_name]
            if module_name in sys.modules:
                del sys.modules[module_name]

        # 레지스트리에서 제거
        self._registry.unregister(plugin_name)

        # TODO: 원래 소스에서 다시 로드
        # 현재는 메타데이터만 유지하고 재등록 불가
        raise PluginLoadError(
            f"Plugin reload not fully implemented. "
            f"Please manually reload plugin '{plugin_name}'"
        )

    def unload_plugin(self, plugin_name: str) -> None:
        """
        플러그인 언로드

        Args:
            plugin_name: 플러그인 이름

        Raises:
            PluginError: 언로드 실패
        """
        try:
            # 플러그인 정리
            plugin = self._registry.get(plugin_name)
            import asyncio

            asyncio.create_task(plugin.cleanup())

            # 레지스트리에서 제거
            self._registry.unregister(plugin_name)

            # 모듈 캐시에서 제거
            module_names_to_remove = [
                name
                for name in self._loaded_modules.keys()
                if plugin_name in name
            ]
            for module_name in module_names_to_remove:
                del self._loaded_modules[module_name]
                if module_name in sys.modules:
                    del sys.modules[module_name]

        except Exception as e:
            raise PluginError(f"Failed to unload plugin '{plugin_name}': {e}") from e

    def get_loaded_modules(self) -> List[str]:
        """로드된 모듈 목록"""
        return list(self._loaded_modules.keys())
