"""플러그인 시스템 통합 테스트"""

import pytest
from pathlib import Path
import tempfile
from typing import Any, Dict

from src.core.plugins import (
    BasePlugin,
    PluginMetadata,
    PluginVersion,
    PluginType,
    PluginStatus,
    PluginRegistry,
    PluginDependency,
    PluginDependencyError,
    PluginVersionConflictError,
    PluginConfigManager,
    ConfigBuilder,
)


# 테스트용 플러그인
class TestPlugin(BasePlugin):
    """테스트용 플러그인"""

    def __init__(self, name: str = "test_plugin", version: str = "1.0.0") -> None:
        metadata = PluginMetadata(
            name=name,
            version=PluginVersion.from_string(version),
            plugin_type=PluginType.CUSTOM,
            description="Test plugin",
            author="Test Author",
        )
        super().__init__(metadata)

    async def _on_initialize(self, config: Dict[str, Any]) -> None:
        self.init_called = True

    async def _on_activate(self) -> None:
        self.activate_called = True

    async def _on_deactivate(self) -> None:
        self.deactivate_called = True

    async def _on_cleanup(self) -> None:
        self.cleanup_called = True


class TestPluginWithDependency(BasePlugin):
    """의존성이 있는 테스트 플러그인"""

    def __init__(self, name: str, depends_on: str, min_version: str = "1.0.0") -> None:
        metadata = PluginMetadata(
            name=name,
            version=PluginVersion.from_string("1.0.0"),
            plugin_type=PluginType.CUSTOM,
            dependencies=[
                PluginDependency(
                    name=depends_on,
                    min_version=PluginVersion.from_string(min_version),
                )
            ],
        )
        super().__init__(metadata)


class TestPluginVersion:
    """PluginVersion 테스트"""

    def test_version_creation(self) -> None:
        """버전 생성 테스트"""
        version = PluginVersion(major=1, minor=2, patch=3)
        assert str(version) == "1.2.3"

    def test_version_from_string(self) -> None:
        """문자열에서 버전 파싱"""
        version = PluginVersion.from_string("2.0.5")
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 5

    def test_version_comparison(self) -> None:
        """버전 비교"""
        v1 = PluginVersion(1, 0, 0)
        v2 = PluginVersion(1, 0, 1)
        v3 = PluginVersion(2, 0, 0)

        assert v1 < v2
        assert v2 < v3
        assert v1 < v3
        assert v2 > v1
        assert v3 >= v2

    def test_version_equality(self) -> None:
        """버전 동등성"""
        v1 = PluginVersion(1, 2, 3)
        v2 = PluginVersion(1, 2, 3)
        v3 = PluginVersion(1, 2, 4)

        assert v1 == v2
        assert v1 != v3


class TestPluginDependency:
    """PluginDependency 테스트"""

    def test_dependency_compatibility(self) -> None:
        """의존성 호환성 확인"""
        dep = PluginDependency(
            name="dep_plugin",
            min_version=PluginVersion(1, 0, 0),
            max_version=PluginVersion(2, 0, 0),
        )

        assert dep.is_compatible(PluginVersion(1, 0, 0))
        assert dep.is_compatible(PluginVersion(1, 5, 0))
        assert dep.is_compatible(PluginVersion(2, 0, 0))
        assert not dep.is_compatible(PluginVersion(0, 9, 0))
        assert not dep.is_compatible(PluginVersion(2, 0, 1))

    def test_dependency_min_only(self) -> None:
        """최소 버전만 있는 의존성"""
        dep = PluginDependency(name="dep_plugin", min_version=PluginVersion(1, 0, 0))

        assert dep.is_compatible(PluginVersion(1, 0, 0))
        assert dep.is_compatible(PluginVersion(2, 0, 0))
        assert not dep.is_compatible(PluginVersion(0, 9, 9))


class TestBasePlugin:
    """BasePlugin 테스트"""

    @pytest.mark.asyncio
    async def test_plugin_lifecycle(self) -> None:
        """플러그인 라이프사이클 테스트"""
        plugin = TestPlugin()

        # 초기 상태
        assert plugin.get_status() == PluginStatus.REGISTERED

        # 초기화
        await plugin.initialize({"key": "value"})
        assert plugin.get_status() == PluginStatus.LOADED
        assert plugin.init_called

        # 활성화
        await plugin.activate()
        assert plugin.get_status() == PluginStatus.ACTIVE
        assert plugin.activate_called

        # 비활성화
        await plugin.deactivate()
        assert plugin.get_status() == PluginStatus.INACTIVE
        assert plugin.deactivate_called

        # 정리
        await plugin.cleanup()
        assert plugin.get_status() == PluginStatus.UNLOADED
        assert plugin.cleanup_called

    @pytest.mark.asyncio
    async def test_plugin_health_check(self) -> None:
        """플러그인 헬스 체크"""
        plugin = TestPlugin()
        await plugin.initialize({})

        health = plugin.health_check()

        assert health["healthy"] is True
        assert health["status"] == PluginStatus.LOADED.value
        assert health["name"] == "test_plugin"
        assert "version" in health

    def test_plugin_metadata(self) -> None:
        """플러그인 메타데이터"""
        plugin = TestPlugin()
        metadata = plugin.get_metadata()

        assert metadata.name == "test_plugin"
        assert str(metadata.version) == "1.0.0"
        assert metadata.plugin_type == PluginType.CUSTOM


class TestPluginRegistry:
    """PluginRegistry 테스트"""

    def test_register_plugin(self) -> None:
        """플러그인 등록"""
        registry = PluginRegistry()
        plugin = TestPlugin()

        registry.register(plugin)

        assert registry.has("test_plugin")
        assert registry.get("test_plugin") == plugin

    def test_register_duplicate_plugin(self) -> None:
        """중복 플러그인 등록 (같은 버전)"""
        registry = PluginRegistry()
        plugin1 = TestPlugin()
        plugin2 = TestPlugin()

        registry.register(plugin1)
        registry.register(plugin2)  # 같은 버전이면 무시

        assert registry.get("test_plugin") == plugin1

    def test_register_conflict_version(self) -> None:
        """버전 충돌 플러그인 등록"""
        registry = PluginRegistry()
        plugin1 = TestPlugin(version="1.0.0")
        plugin2 = TestPlugin(version="2.0.0")

        registry.register(plugin1)

        with pytest.raises(PluginVersionConflictError):
            registry.register(plugin2)

    def test_unregister_plugin(self) -> None:
        """플러그인 등록 해제"""
        registry = PluginRegistry()
        plugin = TestPlugin()

        registry.register(plugin)
        registry.unregister("test_plugin")

        assert not registry.has("test_plugin")

    def test_unregister_with_dependents(self) -> None:
        """의존하는 플러그인이 있을 때 등록 해제 실패"""
        registry = PluginRegistry()
        base_plugin = TestPlugin(name="base")
        dependent = TestPluginWithDependency(name="dependent", depends_on="base")

        registry.register(base_plugin)
        registry.register(dependent)

        with pytest.raises(PluginDependencyError):
            registry.unregister("base")

    def test_list_plugins(self) -> None:
        """플러그인 목록 조회"""
        registry = PluginRegistry()
        plugin1 = TestPlugin(name="plugin1")
        plugin2 = TestPlugin(name="plugin2")

        registry.register(plugin1)
        registry.register(plugin2)

        plugins = registry.list_plugins()

        assert len(plugins) == 2
        assert {p.name for p in plugins} == {"plugin1", "plugin2"}

    def test_list_by_type(self) -> None:
        """타입별 플러그인 조회"""
        registry = PluginRegistry()
        plugin = TestPlugin()

        registry.register(plugin)

        custom_plugins = registry.list_by_type(PluginType.CUSTOM)
        stage_plugins = registry.list_by_type(PluginType.STAGE)

        assert "test_plugin" in custom_plugins
        assert len(stage_plugins) == 0

    def test_dependency_validation(self) -> None:
        """의존성 검증"""
        registry = PluginRegistry()
        base_plugin = TestPlugin(name="base", version="1.0.0")
        dependent = TestPluginWithDependency(
            name="dependent", depends_on="base", min_version="1.0.0"
        )

        # 기본 플러그인 없이 등록 시도
        with pytest.raises(PluginDependencyError):
            registry.register(dependent)

        # 기본 플러그인 등록 후 성공
        registry.register(base_plugin)
        registry.register(dependent)

        assert registry.has("dependent")

    @pytest.mark.asyncio
    async def test_activate_all(self) -> None:
        """모든 플러그인 활성화"""
        registry = PluginRegistry()
        plugin1 = TestPlugin(name="plugin1")
        plugin2 = TestPlugin(name="plugin2")

        registry.register(plugin1)
        registry.register(plugin2)

        await plugin1.initialize({})
        await plugin2.initialize({})

        await registry.activate_all()

        assert plugin1.get_status() == PluginStatus.ACTIVE
        assert plugin2.get_status() == PluginStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activation_order_with_dependencies(self) -> None:
        """의존성 순서로 활성화"""
        registry = PluginRegistry()
        base = TestPlugin(name="base")
        dep = TestPluginWithDependency(name="dep", depends_on="base")

        registry.register(base)
        registry.register(dep)

        await base.initialize({})
        await dep.initialize({})

        await registry.activate_all()

        # 의존성 순서대로 활성화됨
        assert base.get_status() == PluginStatus.ACTIVE
        assert dep.get_status() == PluginStatus.ACTIVE


class TestPluginConfigManager:
    """PluginConfigManager 테스트"""

    def test_set_get_config(self) -> None:
        """설정 설정 및 조회"""
        manager = PluginConfigManager()

        config = {"host": "localhost", "port": 8080}
        manager.set_config("test_plugin", config)

        retrieved = manager.get_config("test_plugin")

        assert retrieved == config

    def test_save_load_config(self) -> None:
        """설정 저장 및 로드"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(config_dir=Path(tmpdir))

            config = {"key": "value", "number": 42}
            manager.save_config("test_plugin", config)

            # 새 매니저로 로드
            manager2 = PluginConfigManager(config_dir=Path(tmpdir))
            loaded = manager2.load_config("test_plugin")

            assert loaded == config

    def test_config_with_schema_validation(self) -> None:
        """스키마 검증이 있는 설정"""
        manager = PluginConfigManager()

        # 스키마 등록
        schema = {
            "type": "object",
            "properties": {"host": {"type": "string"}, "port": {"type": "integer"}},
            "required": ["host", "port"],
        }
        manager.register_schema("test_plugin", schema)

        # 유효한 설정
        valid_config = {"host": "localhost", "port": 8080}
        manager.set_config("test_plugin", valid_config)

        # 무효한 설정 (필수 필드 누락)
        invalid_config = {"host": "localhost"}  # port 누락
        with pytest.raises(Exception):  # PluginConfigError
            manager.set_config("test_plugin", invalid_config)


class TestConfigBuilder:
    """ConfigBuilder 테스트"""

    def test_config_builder(self) -> None:
        """설정 빌더"""
        config = (
            ConfigBuilder("test_plugin")
            .set("host", "localhost")
            .set("port", 8080)
            .set("debug", True)
            .build()
        )

        assert config == {"host": "localhost", "port": 8080, "debug": True}

    def test_config_builder_nested(self) -> None:
        """중첩 설정"""
        config = (
            ConfigBuilder("test_plugin")
            .set_nested("database.host", "localhost")
            .set_nested("database.port", 5432)
            .build()
        )

        assert config == {"database": {"host": "localhost", "port": 5432}}

    def test_config_builder_merge(self) -> None:
        """설정 병합"""
        base_config = {"host": "localhost", "port": 8080}

        config = ConfigBuilder("test_plugin").merge(base_config).set("debug", True).build()

        assert config == {"host": "localhost", "port": 8080, "debug": True}
