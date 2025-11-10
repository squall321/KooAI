"""
플러그인 레지스트리

플러그인을 등록하고 관리하는 중앙 시스템.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from .base import (
    IPlugin,
    PluginDependency,
    PluginDependencyError,
    PluginMetadata,
    PluginNotFoundError,
    PluginStatus,
    PluginType,
    PluginVersionConflictError,
)


class PluginRegistry:
    """
    플러그인 레지스트리

    플러그인을 등록, 조회, 관리하는 중앙 레지스트리.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 플러그인 메타데이터 저장 경로
        """
        self._plugins: Dict[str, IPlugin] = {}  # name -> plugin
        self._plugin_types: Dict[PluginType, Set[str]] = {}  # type -> plugin names
        self._storage_path = storage_path

        # 초기화
        for plugin_type in PluginType:
            self._plugin_types[plugin_type] = set()

    def register(self, plugin: IPlugin) -> None:
        """
        플러그인 등록

        Args:
            plugin: 등록할 플러그인

        Raises:
            PluginVersionConflictError: 같은 이름의 다른 버전이 이미 등록됨
            PluginDependencyError: 의존성을 만족하지 못함
        """
        metadata = plugin.get_metadata()
        name = metadata.name

        # 이미 등록된 플러그인 확인
        if name in self._plugins:
            existing = self._plugins[name]
            existing_version = existing.get_metadata().version

            if existing_version != metadata.version:
                raise PluginVersionConflictError(
                    f"Plugin '{name}' version {existing_version} already registered. "
                    f"Cannot register version {metadata.version}"
                )

            # 같은 버전이면 무시
            return

        # 의존성 확인
        self._check_dependencies(metadata)

        # 등록
        self._plugins[name] = plugin
        self._plugin_types[metadata.plugin_type].add(name)

        # 메타데이터 저장
        if self._storage_path:
            self._save_metadata(metadata)

    def unregister(self, name: str) -> None:
        """
        플러그인 등록 해제

        Args:
            name: 플러그인 이름

        Raises:
            PluginNotFoundError: 플러그인을 찾을 수 없음
            PluginDependencyError: 다른 플러그인이 이 플러그인에 의존
        """
        if name not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")

        # 의존하는 플러그인 확인
        dependent_plugins = self._find_dependent_plugins(name)
        if dependent_plugins:
            raise PluginDependencyError(
                f"Cannot unregister '{name}': " f"Plugins {dependent_plugins} depend on it"
            )

        # 등록 해제
        plugin = self._plugins[name]
        metadata = plugin.get_metadata()

        self._plugin_types[metadata.plugin_type].discard(name)
        del self._plugins[name]

    def get(self, name: str) -> IPlugin:
        """
        플러그인 조회

        Args:
            name: 플러그인 이름

        Returns:
            플러그인 인스턴스

        Raises:
            PluginNotFoundError: 플러그인을 찾을 수 없음
        """
        if name not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")

        return self._plugins[name]

    def has(self, name: str) -> bool:
        """플러그인 존재 여부 확인"""
        return name in self._plugins

    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None,
        tags: Optional[Set[str]] = None,
    ) -> List[PluginMetadata]:
        """
        플러그인 목록 조회

        Args:
            plugin_type: 플러그인 타입 필터
            status: 상태 필터
            tags: 태그 필터 (모든 태그를 포함해야 함)

        Returns:
            플러그인 메타데이터 리스트
        """
        plugins = list(self._plugins.values())

        # 타입 필터
        if plugin_type:
            plugins = [p for p in plugins if p.get_metadata().plugin_type == plugin_type]

        # 상태 필터
        if status:
            plugins = [p for p in plugins if p.get_status() == status]

        # 태그 필터
        if tags:
            plugins = [p for p in plugins if tags.issubset(p.get_metadata().tags)]

        return [p.get_metadata() for p in plugins]

    def list_by_type(self, plugin_type: PluginType) -> List[str]:
        """
        특정 타입의 플러그인 이름 목록

        Args:
            plugin_type: 플러그인 타입

        Returns:
            플러그인 이름 리스트
        """
        return list(self._plugin_types.get(plugin_type, set()))

    def get_dependencies(self, name: str) -> List[PluginDependency]:
        """
        플러그인의 의존성 목록

        Args:
            name: 플러그인 이름

        Returns:
            의존성 리스트

        Raises:
            PluginNotFoundError: 플러그인을 찾을 수 없음
        """
        plugin = self.get(name)
        return plugin.get_metadata().dependencies

    def get_dependents(self, name: str) -> List[str]:
        """
        이 플러그인에 의존하는 플러그인 목록

        Args:
            name: 플러그인 이름

        Returns:
            의존하는 플러그인 이름 리스트
        """
        return self._find_dependent_plugins(name)

    def validate_dependencies(self, name: str) -> bool:
        """
        플러그인의 의존성이 모두 만족되는지 확인

        Args:
            name: 플러그인 이름

        Returns:
            의존성이 모두 만족되면 True
        """
        try:
            plugin = self.get(name)
            self._check_dependencies(plugin.get_metadata())
            return True
        except (PluginNotFoundError, PluginDependencyError):
            return False

    async def activate_all(self, plugin_type: Optional[PluginType] = None) -> None:
        """
        모든 플러그인 활성화 (또는 특정 타입만)

        Args:
            plugin_type: 활성화할 플러그인 타입 (None이면 전체)
        """
        plugins = list(self._plugins.values())

        if plugin_type:
            plugins = [p for p in plugins if p.get_metadata().plugin_type == plugin_type]

        # 의존성 순서대로 활성화
        activation_order = self._resolve_activation_order([p.get_metadata().name for p in plugins])

        for name in activation_order:
            plugin = self._plugins[name]
            if plugin.get_status() == PluginStatus.LOADED:
                await plugin.activate()

    async def deactivate_all(self, plugin_type: Optional[PluginType] = None) -> None:
        """
        모든 플러그인 비활성화 (또는 특정 타입만)

        Args:
            plugin_type: 비활성화할 플러그인 타입
        """
        plugins = list(self._plugins.values())

        if plugin_type:
            plugins = [p for p in plugins if p.get_metadata().plugin_type == plugin_type]

        # 의존성 역순으로 비활성화
        activation_order = self._resolve_activation_order([p.get_metadata().name for p in plugins])

        for name in reversed(activation_order):
            plugin = self._plugins[name]
            if plugin.get_status() == PluginStatus.ACTIVE:
                await plugin.deactivate()

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 플러그인 헬스 체크

        Returns:
            플러그인 이름 -> 헬스 체크 결과
        """
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = plugin.health_check()
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": f"Health check failed: {str(e)}",
                }

        return results

    def _check_dependencies(self, metadata: PluginMetadata) -> None:
        """
        의존성 확인

        Raises:
            PluginDependencyError: 의존성을 만족하지 못함
        """
        for dependency in metadata.dependencies:
            # 선택적 의존성은 건너뜀
            if dependency.optional:
                continue

            # 의존하는 플러그인이 등록되어 있는지 확인
            if dependency.name not in self._plugins:
                raise PluginDependencyError(
                    f"Plugin '{metadata.name}' requires '{dependency.name}', "
                    f"but it is not registered"
                )

            # 버전 확인
            dep_plugin = self._plugins[dependency.name]
            dep_version = dep_plugin.get_metadata().version

            if not dependency.is_compatible(dep_version):
                raise PluginDependencyError(
                    f"Plugin '{metadata.name}' requires '{dependency.name}' "
                    f"version {dependency.min_version} - {dependency.max_version}, "
                    f"but version {dep_version} is installed"
                )

    def _find_dependent_plugins(self, name: str) -> List[str]:
        """이 플러그인에 의존하는 플러그인 찾기"""
        dependents = []

        for plugin_name, plugin in self._plugins.items():
            metadata = plugin.get_metadata()

            for dep in metadata.dependencies:
                if dep.name == name and not dep.optional:
                    dependents.append(plugin_name)
                    break

        return dependents

    def _resolve_activation_order(self, plugin_names: List[str]) -> List[str]:
        """
        의존성을 고려한 활성화 순서 결정 (Topological Sort)

        Args:
            plugin_names: 활성화할 플러그인 이름 목록

        Returns:
            활성화 순서 (의존성이 먼저 활성화됨)

        Raises:
            PluginDependencyError: 순환 의존성
        """
        # 의존성 그래프 구축
        graph: Dict[str, Set[str]] = {name: set() for name in plugin_names}
        in_degree: Dict[str, int] = {name: 0 for name in plugin_names}

        for name in plugin_names:
            plugin = self._plugins[name]
            dependencies = plugin.get_metadata().dependencies

            for dep in dependencies:
                if dep.optional:
                    continue

                # 활성화할 플러그인 중에만 의존성 추가
                if dep.name in plugin_names:
                    graph[dep.name].add(name)
                    in_degree[name] += 1

        # Topological Sort (Kahn's Algorithm)
        queue = [name for name in plugin_names if in_degree[name] == 0]
        result = []

        while queue:
            # in-degree가 0인 노드 선택
            current = queue.pop(0)
            result.append(current)

            # 인접 노드의 in-degree 감소
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 순환 의존성 확인
        if len(result) != len(plugin_names):
            raise PluginDependencyError(
                f"Circular dependency detected among plugins: {plugin_names}"
            )

        return result

    def _save_metadata(self, metadata: PluginMetadata) -> None:
        """메타데이터를 파일에 저장"""
        if not self._storage_path:
            return

        self._storage_path.mkdir(parents=True, exist_ok=True)
        metadata_file = self._storage_path / f"{metadata.name}.json"

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

    def load_metadata_from_storage(self) -> List[PluginMetadata]:
        """
        저장소에서 모든 플러그인 메타데이터 로드

        Returns:
            메타데이터 리스트
        """
        if not self._storage_path or not self._storage_path.exists():
            return []

        metadata_list = []

        for metadata_file in self._storage_path.glob("*.json"):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    metadata = PluginMetadata.from_dict(data)
                    metadata_list.append(metadata)
            except Exception as e:
                # 메타데이터 로드 실패는 로그만 남기고 계속
                print(f"Failed to load metadata from {metadata_file}: {e}")

        return metadata_list
