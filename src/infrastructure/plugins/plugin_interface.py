"""
Plugin System - Base Interfaces

Defines the core plugin architecture and interfaces for extending KooAI functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import inspect


class PluginType(str, Enum):
    """Types of plugins supported."""

    ANALYZER = "analyzer"  # Custom analysis algorithms
    VISUALIZER = "visualizer"  # Custom visualization generators
    EXPORTER = "exporter"  # Custom export formats
    PROCESSOR = "processor"  # Custom data processors
    HOOK = "hook"  # Event hooks
    MIDDLEWARE = "middleware"  # Request/response middleware


class PluginPriority(int, Enum):
    """Plugin execution priority."""

    CRITICAL = 1000
    HIGH = 100
    NORMAL = 10
    LOW = 1


@dataclass
class PluginMetadata:
    """
    Plugin metadata and registration information.

    Attributes:
        name: Unique plugin identifier
        version: Plugin version (semantic versioning)
        description: Human-readable description
        author: Plugin author
        plugin_type: Type of plugin
        priority: Execution priority
        enabled: Whether plugin is active
        dependencies: List of required plugin names
        config_schema: JSON schema for plugin configuration
        tags: Searchable tags
    """

    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    priority: PluginPriority = PluginPriority.NORMAL
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class PluginContext:
    """
    Context passed to plugins during execution.

    Provides access to services, configuration, and request data.
    """

    # Request information
    request_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

    # Plugin configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Shared data between plugins
    data: Dict[str, Any] = field(default_factory=dict)

    # Service access
    services: Dict[str, Any] = field(default_factory=dict)


class PluginError(Exception):
    """Base exception for plugin-related errors."""

    def __init__(self, plugin_name: str, message: str):
        self.plugin_name = plugin_name
        self.message = message
        super().__init__(f"[{plugin_name}] {message}")


class PluginLoadError(PluginError):
    """Error loading plugin."""

    pass


class PluginExecutionError(PluginError):
    """Error executing plugin."""

    pass


class PluginConfigError(PluginError):
    """Invalid plugin configuration."""

    pass


# ============================================================================
# Base Plugin Interface
# ============================================================================


class Plugin(ABC):
    """
    Base plugin interface.

    All plugins must inherit from this class and implement required methods.
    """

    def __init__(self, metadata: PluginMetadata):
        """
        Initialize plugin.

        Args:
            metadata: Plugin metadata
        """
        self.metadata = metadata
        self._initialized = False
        self._config: Dict[str, Any] = {}

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.

        Called once when plugin is loaded.

        Args:
            config: Plugin configuration dictionary

        Raises:
            PluginConfigError: If configuration is invalid
        """
        pass

    @abstractmethod
    async def execute(self, context: PluginContext, **kwargs: Any) -> Any:
        """
        Execute plugin logic.

        Args:
            context: Plugin execution context
            **kwargs: Plugin-specific arguments

        Returns:
            Plugin result (type depends on plugin)

        Raises:
            PluginExecutionError: If execution fails
        """
        pass

    async def shutdown(self) -> None:
        """
        Cleanup plugin resources.

        Called when plugin is unloaded or application shuts down.
        Override to implement custom cleanup logic.
        """
        pass

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid

        Raises:
            PluginConfigError: If configuration is invalid
        """
        if self.metadata.config_schema:
            # TODO: Implement JSON schema validation
            pass
        return True

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "author": self.metadata.author,
            "type": self.metadata.plugin_type.value,
            "priority": self.metadata.priority.value,
            "enabled": self.metadata.enabled,
            "initialized": self._initialized,
        }


# ============================================================================
# Specialized Plugin Interfaces
# ============================================================================


class AnalyzerPlugin(Plugin):
    """
    Plugin for custom analysis algorithms.

    Example:
        ```python
        class TurbulenceAnalyzer(AnalyzerPlugin):
            async def initialize(self, config: Dict[str, Any]):
                self.threshold = config.get("threshold", 0.1)

            async def analyze(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
                # Custom turbulence analysis
                return {"turbulence_intensity": 0.15}
        ```
    """

    @abstractmethod
    async def analyze(
        self, simulation_data: Dict[str, Any], context: PluginContext
    ) -> Dict[str, Any]:
        """
        Perform analysis on simulation data.

        Args:
            simulation_data: Simulation data to analyze
            context: Plugin context

        Returns:
            Analysis results dictionary
        """
        pass

    async def execute(self, context: PluginContext, **kwargs: Any) -> Any:
        """Execute analyzer."""
        simulation_data = kwargs.get("simulation_data", {})
        return await self.analyze(simulation_data, context)


class VisualizerPlugin(Plugin):
    """
    Plugin for custom visualizations.

    Example:
        ```python
        class ContourPlotVisualizer(VisualizerPlugin):
            async def visualize(self, data: Dict[str, Any]) -> bytes:
                # Generate custom contour plot
                return plot_bytes
        ```
    """

    @abstractmethod
    async def visualize(
        self, data: Dict[str, Any], context: PluginContext
    ) -> bytes:
        """
        Generate visualization from data.

        Args:
            data: Data to visualize
            context: Plugin context

        Returns:
            Visualization bytes (PNG, SVG, etc.)
        """
        pass

    async def execute(self, context: PluginContext, **kwargs: Any) -> Any:
        """Execute visualizer."""
        data = kwargs.get("data", {})
        return await self.visualize(data, context)


class ExporterPlugin(Plugin):
    """
    Plugin for custom export formats.

    Example:
        ```python
        class ParaViewExporter(ExporterPlugin):
            def get_format(self) -> str:
                return "vtk"

            async def export(self, data: Dict[str, Any]) -> bytes:
                # Export to ParaView format
                return vtk_bytes
        ```
    """

    @abstractmethod
    def get_format(self) -> str:
        """Get export format identifier (e.g., 'pdf', 'vtk')."""
        pass

    @abstractmethod
    async def export(self, data: Dict[str, Any], context: PluginContext) -> bytes:
        """
        Export data to custom format.

        Args:
            data: Data to export
            context: Plugin context

        Returns:
            Exported data bytes
        """
        pass

    async def execute(self, context: PluginContext, **kwargs: Any) -> Any:
        """Execute exporter."""
        data = kwargs.get("data", {})
        return await self.export(data, context)


class ProcessorPlugin(Plugin):
    """
    Plugin for custom data processing.

    Example:
        ```python
        class DataNormalizer(ProcessorPlugin):
            async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                # Normalize data
                return normalized_data
        ```
    """

    @abstractmethod
    async def process(
        self, data: Dict[str, Any], context: PluginContext
    ) -> Dict[str, Any]:
        """
        Process data.

        Args:
            data: Input data
            context: Plugin context

        Returns:
            Processed data
        """
        pass

    async def execute(self, context: PluginContext, **kwargs: Any) -> Any:
        """Execute processor."""
        data = kwargs.get("data", {})
        return await self.process(data, context)


# ============================================================================
# Hook System
# ============================================================================


class HookEvent(str, Enum):
    """Predefined hook events."""

    # Simulation lifecycle
    SIMULATION_UPLOADED = "simulation.uploaded"
    SIMULATION_ANALYZED = "simulation.analyzed"
    SIMULATION_DELETED = "simulation.deleted"

    # Analysis lifecycle
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"

    # User actions
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class HookPlugin(Plugin):
    """
    Plugin for event hooks.

    Example:
        ```python
        class NotificationHook(HookPlugin):
            def get_events(self) -> List[HookEvent]:
                return [HookEvent.SIMULATION_ANALYZED]

            async def on_event(self, event: HookEvent, data: Dict[str, Any]):
                # Send notification when analysis completes
                await send_email(data["user_email"], "Analysis complete!")
        ```
    """

    @abstractmethod
    def get_events(self) -> List[HookEvent]:
        """
        Get list of events this hook listens to.

        Returns:
            List of hook events
        """
        pass

    @abstractmethod
    async def on_event(
        self, event: HookEvent, data: Dict[str, Any], context: PluginContext
    ) -> None:
        """
        Handle event.

        Args:
            event: Event that occurred
            data: Event data
            context: Plugin context
        """
        pass

    async def execute(self, context: PluginContext, **kwargs: Any) -> Any:
        """Execute hook."""
        event = kwargs.get("event")
        data = kwargs.get("data", {})
        await self.on_event(event, data, context)  # type: ignore[arg-type]


# ============================================================================
# Plugin Decorator
# ============================================================================


def plugin(
    name: str,
    version: str,
    description: str,
    author: str,
    plugin_type: PluginType,
    priority: PluginPriority = PluginPriority.NORMAL,
    dependencies: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> Callable[[type], type]:
    """
    Decorator to register a plugin.

    Usage:
        ```python
        @plugin(
            name="custom-analyzer",
            version="1.0.0",
            description="Custom turbulence analyzer",
            author="John Doe",
            plugin_type=PluginType.ANALYZER,
            priority=PluginPriority.HIGH,
            tags=["turbulence", "cfd"]
        )
        class CustomAnalyzer(AnalyzerPlugin):
            async def initialize(self, config):
                pass

            async def analyze(self, simulation_data, context):
                return {"result": "analyzed"}
        ```
    """

    def decorator(cls: type) -> type:
        # Create metadata
        metadata = PluginMetadata(
            name=name,
            version=version,
            description=description,
            author=author,
            plugin_type=plugin_type,
            priority=priority,
            dependencies=dependencies or [],
            tags=tags or [],
        )

        # Store metadata on class
        cls._plugin_metadata = metadata  # type: ignore[attr-defined]

        # Original __init__
        original_init = cls.__init__  # type: ignore[misc]

        # Wrap __init__ to inject metadata
        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Call Plugin.__init__ with metadata
            Plugin.__init__(self, metadata)
            # Call original __init__ if it exists and is not Plugin.__init__
            if original_init is not object.__init__:
                sig = inspect.signature(original_init)
                # Only call if it accepts arguments beyond self
                if len(sig.parameters) > 1:
                    original_init(self, *args, **kwargs)

        cls.__init__ = new_init  # type: ignore[misc]

        return cls

    return decorator
