"""
Plugin System

Extensible plugin architecture for KooAI.

Features:
- Multiple plugin types (analyzers, visualizers, exporters, processors, hooks)
- Priority-based execution
- Dependency management
- Hot reload support
- Hook system for event-driven architecture
- REST API for plugin management

Usage:
    # 1. Load plugins on startup
    from src.infrastructure.plugins import get_plugin_manager

    manager = get_plugin_manager()
    await manager.load_plugins_from_directory("./plugins")
    await manager.startup()

    # 2. Create a custom plugin
    from src.infrastructure.plugins import (
        AnalyzerPlugin,
        PluginContext,
        PluginType,
        plugin,
    )

    @plugin(
        name="my-analyzer",
        version="1.0.0",
        description="My custom analyzer",
        author="Your Name",
        plugin_type=PluginType.ANALYZER,
    )
    class MyAnalyzer(AnalyzerPlugin):
        async def initialize(self, config):
            self.threshold = config.get("threshold", 0.5)

        async def analyze(self, simulation_data, context):
            return {"result": "analyzed"}

    # 3. Load and execute plugin
    await manager.load_plugin_class(MyAnalyzer, {"threshold": 0.3})
    result = await manager.execute_plugin("my-analyzer", simulation_data=data)

    # 4. Trigger hooks
    from src.infrastructure.plugins import HookEvent

    await manager.trigger_hooks(
        HookEvent.SIMULATION_ANALYZED,
        {"simulation_id": "sim_123", "user_email": "user@example.com"}
    )

Plugin Types:
    - ANALYZER: Custom analysis algorithms
    - VISUALIZER: Custom visualization generators
    - EXPORTER: Custom export formats
    - PROCESSOR: Custom data processors
    - HOOK: Event-driven hooks
    - MIDDLEWARE: Request/response middleware

Hook Events:
    - simulation.uploaded
    - simulation.analyzed
    - simulation.deleted
    - analysis.started
    - analysis.completed
    - analysis.failed
    - user.registered
    - user.login
    - system.startup
    - system.shutdown
"""

from .plugin_interface import (
    # Base classes
    Plugin,
    PluginMetadata,
    PluginContext,
    # Specialized plugins
    AnalyzerPlugin,
    VisualizerPlugin,
    ExporterPlugin,
    ProcessorPlugin,
    HookPlugin,
    # Enums
    PluginType,
    PluginPriority,
    HookEvent,
    # Exceptions
    PluginError,
    PluginLoadError,
    PluginExecutionError,
    PluginConfigError,
    # Decorator
    plugin,
)

from .plugin_manager import (
    PluginManager,
    PluginRegistry,
    get_plugin_manager,
)

__all__ = [
    # Base
    "Plugin",
    "PluginMetadata",
    "PluginContext",
    # Specialized
    "AnalyzerPlugin",
    "VisualizerPlugin",
    "ExporterPlugin",
    "ProcessorPlugin",
    "HookPlugin",
    # Enums
    "PluginType",
    "PluginPriority",
    "HookEvent",
    # Exceptions
    "PluginError",
    "PluginLoadError",
    "PluginExecutionError",
    "PluginConfigError",
    # Manager
    "PluginManager",
    "PluginRegistry",
    "get_plugin_manager",
    # Decorator
    "plugin",
]
