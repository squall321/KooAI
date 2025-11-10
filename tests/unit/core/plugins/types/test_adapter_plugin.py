"""
Tests for Adapter Plugin
"""

import pytest
from typing import Any, Dict, List


class TestAdapterPluginClass:
    """Test AdapterPlugin class."""

    def test_init_with_correct_type(self) -> None:
        """Test initialization with correct plugin type."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        # Create mock adapter
        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        # Create concrete test plugin
        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test adapter plugin",
            author="Test Author",
            plugin_type=PluginType.ADAPTER,
        )

        plugin = TestAdapterPlugin(metadata)

        assert plugin.name == "test_adapter"
        assert str(plugin.version) == "1.0.0"

    def test_init_with_wrong_type_raises_error(self) -> None:
        """Test initialization with wrong plugin type raises error."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                pass

        metadata = PluginMetadata(
            name="test_stage",
            version=PluginVersion.from_string("1.0.0"),
            description="Wrong type",
            author="Test",
            plugin_type=PluginType.STAGE,
        )

        with pytest.raises(ValueError, match="requires PluginType.ADAPTER"):
            TestAdapterPlugin(metadata)

    @pytest.mark.asyncio
    async def test_initialize_sets_adapter_class(self) -> None:
        """Test that initialize sets adapter class."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )

        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        assert plugin._adapter_class is MockAdapter

    @pytest.mark.asyncio
    async def test_get_adapter_class_after_initialize(self) -> None:
        """Test getting adapter class after initialization."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )

        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        adapter_class = plugin.get_adapter_class()

        assert adapter_class is MockAdapter

    def test_get_adapter_class_before_initialize_raises_error(self) -> None:
        """Test getting adapter class before initialization raises error."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                pass

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )

        plugin = TestAdapterPlugin(metadata)

        with pytest.raises(RuntimeError, match="not initialized"):
            plugin.get_adapter_class()

    @pytest.mark.asyncio
    async def test_create_adapter(self) -> None:
        """Test creating adapter instance."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def __init__(self) -> None:
                super().__init__()
                self.name = "mock"

            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )

        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        adapter = plugin.create_adapter()

        assert isinstance(adapter, MockAdapter)
        assert adapter.name == "mock"


class TestAdapterPluginRegistry:
    """Test AdapterPluginRegistry class."""

    def test_init(self) -> None:
        """Test registry initialization."""
        from src.core.plugins.types.adapter_plugin import AdapterPluginRegistry

        registry = AdapterPluginRegistry()

        assert registry.list_adapters() == []

    @pytest.mark.asyncio
    async def test_register(self) -> None:
        """Test registering plugin."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin, AdapterPluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        registry = AdapterPluginRegistry()

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )
        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)

        assert "test_adapter" in registry.list_adapters()

    @pytest.mark.asyncio
    async def test_get(self) -> None:
        """Test getting registered plugin."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin, AdapterPluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        registry = AdapterPluginRegistry()

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )
        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)

        retrieved = registry.get("test_adapter")

        assert retrieved == plugin

    def test_get_nonexistent_raises_error(self) -> None:
        """Test getting nonexistent plugin raises error."""
        from src.core.plugins.types.adapter_plugin import AdapterPluginRegistry

        registry = AdapterPluginRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    @pytest.mark.asyncio
    async def test_unregister(self) -> None:
        """Test unregistering plugin."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin, AdapterPluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        registry = AdapterPluginRegistry()

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )
        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)
        assert "test_adapter" in registry.list_adapters()

        registry.unregister("test_adapter")

        assert "test_adapter" not in registry.list_adapters()

    def test_unregister_nonexistent_no_error(self) -> None:
        """Test unregistering nonexistent plugin doesn't raise error."""
        from src.core.plugins.types.adapter_plugin import AdapterPluginRegistry

        registry = AdapterPluginRegistry()

        registry.unregister("nonexistent")  # Should not raise

    @pytest.mark.asyncio
    async def test_create_adapter_from_registry(self) -> None:
        """Test creating adapter from registry."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin, AdapterPluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def __init__(self) -> None:
                super().__init__()
                self.name = "registry_adapter"

            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        registry = AdapterPluginRegistry()

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )
        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        registry.register(plugin)

        adapter = registry.create_adapter("test_adapter")

        assert isinstance(adapter, MockAdapter)
        assert adapter.name == "registry_adapter"

    @pytest.mark.asyncio
    async def test_has(self) -> None:
        """Test checking if plugin exists."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin, AdapterPluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        registry = AdapterPluginRegistry()

        metadata = PluginMetadata(
            name="test_adapter",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )
        plugin = TestAdapterPlugin(metadata)
        await plugin.initialize({})

        assert not registry.has("test_adapter")

        registry.register(plugin)

        assert registry.has("test_adapter")

    @pytest.mark.asyncio
    async def test_list_adapters(self) -> None:
        """Test listing all adapters."""
        from src.core.plugins.types.adapter_plugin import AdapterPlugin, AdapterPluginRegistry
        from src.core.plugins.base import PluginMetadata, PluginType, PluginVersion
        from src.core.ai_models.adapters.base import BaseModelAdapter, ModelConfig, InferenceResult

        class MockAdapter(BaseModelAdapter):
            def load(self, config: ModelConfig) -> None:
                self._is_loaded = True

            def predict(self, input_data: Any, **kwargs: Any) -> InferenceResult:
                return InferenceResult(output="mock_prediction")

            def get_model_info(self) -> Dict[str, Any]:
                return {"type": "mock"}

        class TestAdapterPlugin(AdapterPlugin):
            async def _on_initialize(self, config: Dict[str, Any]) -> None:
                self._adapter_class = MockAdapter

        registry = AdapterPluginRegistry()

        meta1 = PluginMetadata(
            name="adapter1",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )
        meta2 = PluginMetadata(
            name="adapter2",
            version=PluginVersion.from_string("1.0.0"),
            description="Test",
            author="Test",
            plugin_type=PluginType.ADAPTER,
        )

        plugin1 = TestAdapterPlugin(meta1)
        plugin2 = TestAdapterPlugin(meta2)

        await plugin1.initialize({})
        await plugin2.initialize({})

        registry.register(plugin1)
        registry.register(plugin2)

        adapters = registry.list_adapters()

        assert set(adapters) == {"adapter1", "adapter2"}
