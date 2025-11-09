"""
Tests for Stage Plugin
"""

import pytest
from typing import Any, Dict


class TestStagePluginClass:
    """Test StagePlugin class."""

    def test_init_with_correct_type(self):
        """Test initialization with correct plugin type."""
        from src.core.plugins.types.stage_plugin import StagePlugin
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        # Create mock stage
        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return "processed_data"

        # Create concrete test plugin
        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test stage plugin",
            author="Test Author",
            plugin_type=PluginType.STAGE,
        )

        plugin = TestStagePlugin(metadata)

        assert plugin.name == "test_stage"
        assert plugin.version == "1.0.0"

    def test_init_with_wrong_type_raises_error(self):
        """Test initialization with wrong plugin type raises error."""
        from src.core.plugins.types.stage_plugin import StagePlugin
        from src.core.plugins.base import PluginMetadata, PluginType

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                pass

        metadata = PluginMetadata(
            name="test_adapter",
            version="1.0.0",
            description="Wrong type",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )

        with pytest.raises(ValueError, match="requires PluginType.STAGE"):
            TestStagePlugin(metadata)

    @pytest.mark.asyncio
    async def test_initialize_sets_stage_class(self):
        """Test that initialize sets stage class."""
        from src.core.plugins.types.stage_plugin import StagePlugin
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return "mock_data"

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )

        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        assert plugin._stage_class == MockStage

    @pytest.mark.asyncio
    async def test_get_stage_class_without_setting_raises_error(self):
        """Test that using stage without setting stage class raises error."""
        from src.core.plugins.types.stage_plugin import StagePlugin
        from src.core.plugins.base import PluginMetadata, PluginType

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                # Don't set self._stage_class
                pass

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )

        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        # Should raise when trying to get the stage class
        with pytest.raises(RuntimeError, match="not initialized"):
            plugin.get_stage_class()

    @pytest.mark.asyncio
    async def test_get_stage_class_after_initialize(self):
        """Test getting stage class after initialization."""
        from src.core.plugins.types.stage_plugin import StagePlugin
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return "mock"

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )

        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        stage_class = plugin.get_stage_class()

        assert stage_class == MockStage

    def test_get_stage_class_before_initialize_raises_error(self):
        """Test getting stage class before initialization raises error."""
        from src.core.plugins.types.stage_plugin import StagePlugin
        from src.core.plugins.base import PluginMetadata, PluginType

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                pass

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )

        plugin = TestStagePlugin(metadata)

        with pytest.raises(RuntimeError, match="not initialized"):
            plugin.get_stage_class()

    @pytest.mark.asyncio
    async def test_create_stage(self):
        """Test creating stage instance."""
        from src.core.plugins.types.stage_plugin import StagePlugin
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            def __init__(self, custom_param: str = "default"):
                super().__init__()
                self.custom_param = custom_param

            async def process(self, data: Any, context: PipelineContext) -> Any:
                return f"processed_{self.custom_param}"

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )

        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        stage = plugin.create_stage(custom_param="test_value")

        assert isinstance(stage, MockStage)
        assert stage.custom_param == "test_value"


class TestStagePluginRegistry:
    """Test StagePluginRegistry class."""

    def test_init(self):
        """Test registry initialization."""
        from src.core.plugins.types.stage_plugin import StagePluginRegistry

        registry = StagePluginRegistry()

        assert registry.list_stages() == []

    @pytest.mark.asyncio
    async def test_register(self):
        """Test registering plugin."""
        from src.core.plugins.types.stage_plugin import StagePlugin, StagePluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return data

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        registry = StagePluginRegistry()

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )
        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)

        assert "test_stage" in registry.list_stages()

    @pytest.mark.asyncio
    async def test_get(self):
        """Test getting registered plugin."""
        from src.core.plugins.types.stage_plugin import StagePlugin, StagePluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return data

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        registry = StagePluginRegistry()

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )
        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)

        retrieved = registry.get("test_stage")

        assert retrieved == plugin

    def test_get_nonexistent_raises_error(self):
        """Test getting nonexistent plugin raises error."""
        from src.core.plugins.types.stage_plugin import StagePluginRegistry

        registry = StagePluginRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    @pytest.mark.asyncio
    async def test_unregister(self):
        """Test unregistering plugin."""
        from src.core.plugins.types.stage_plugin import StagePlugin, StagePluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return data

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        registry = StagePluginRegistry()

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )
        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)
        assert "test_stage" in registry.list_stages()

        registry.unregister("test_stage")

        assert "test_stage" not in registry.list_stages()

    def test_unregister_nonexistent_no_error(self):
        """Test unregistering nonexistent plugin doesn't raise error."""
        from src.core.plugins.types.stage_plugin import StagePluginRegistry

        registry = StagePluginRegistry()

        registry.unregister("nonexistent")  # Should not raise

    @pytest.mark.asyncio
    async def test_create_stage_from_registry(self):
        """Test creating stage from registry."""
        from src.core.plugins.types.stage_plugin import StagePlugin, StagePluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            def __init__(self, param: str = "default"):
                super().__init__()
                self.param = param

            async def process(self, data: Any, context: PipelineContext) -> Any:
                return f"{data}_{self.param}"

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        registry = StagePluginRegistry()

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )
        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)

        stage = registry.create_stage("test_stage", param="registry_param")

        assert isinstance(stage, MockStage)
        assert stage.param == "registry_param"

    @pytest.mark.asyncio
    async def test_has(self):
        """Test checking if plugin exists."""
        from src.core.plugins.types.stage_plugin import StagePlugin, StagePluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return data

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        registry = StagePluginRegistry()

        metadata = PluginMetadata(
            name="test_stage",
            version="1.0.0",
            description="Test",
            author="Test",
            plugin_type=PluginType.STAGE,
        )
        plugin = TestStagePlugin(metadata)
        await plugin.initialize({})

        assert not registry.has("test_stage")

        registry.register(plugin)

        assert registry.has("test_stage")

    @pytest.mark.asyncio
    async def test_list_stages(self):
        """Test listing all stages."""
        from src.core.plugins.types.stage_plugin import StagePlugin, StagePluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType
        from src.core.pipeline.base import ProcessingStage, PipelineContext

        class MockStage(ProcessingStage):
            async def process(self, data: Any, context: PipelineContext) -> Any:
                return data

        class TestStagePlugin(StagePlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._stage_class = MockStage

        registry = StagePluginRegistry()

        meta1 = PluginMetadata(
            name="stage1", version="1.0.0", description="Test", author="Test", plugin_type=PluginType.STAGE
        )
        meta2 = PluginMetadata(
            name="stage2", version="1.0.0", description="Test", author="Test", plugin_type=PluginType.STAGE
        )

        plugin1 = TestStagePlugin(meta1)
        plugin2 = TestStagePlugin(meta2)

        await plugin1.initialize({})
        await plugin2.initialize({})

        registry.register(plugin1)
        registry.register(plugin2)

        stages = registry.list_stages()

        assert set(stages) == {"stage1", "stage2"}
