"""
Plugin Manager

Handles plugin discovery, loading, registration, and execution.
"""

import os
import importlib
import importlib.util
import inspect
from typing import Any, Dict, List, Optional, Type, Callable
from pathlib import Path
import asyncio
from collections import defaultdict
import logging

from .plugin_interface import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginType,
    PluginPriority,
    PluginError,
    PluginLoadError,
    PluginExecutionError,
    PluginConfigError,
    HookEvent,
    HookPlugin,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Plugin registry for storing and managing loaded plugins.
    """

    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[HookEvent, List[HookPlugin]] = defaultdict(list)
        self._plugins_by_type: Dict[PluginType, List[Plugin]] = defaultdict(list)

    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If plugin with same name already exists
        """
        name = plugin.metadata.name

        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered")

        # Store plugin
        self._plugins[name] = plugin
        self._plugins_by_type[plugin.metadata.plugin_type].append(plugin)

        # Register hooks
        if isinstance(plugin, HookPlugin):
            for event in plugin.get_events():
                self._hooks[event].append(plugin)

        logger.info(
            f"Registered plugin: {name} v{plugin.metadata.version} "
            f"(type={plugin.metadata.plugin_type.value})"
        )

    def unregister(self, name: str) -> Optional[Plugin]:
        """
        Unregister a plugin.

        Args:
            name: Plugin name

        Returns:
            Unregistered plugin or None if not found
        """
        plugin = self._plugins.pop(name, None)

        if plugin:
            # Remove from type index
            self._plugins_by_type[plugin.metadata.plugin_type].remove(plugin)

            # Remove hooks
            if isinstance(plugin, HookPlugin):
                for event in plugin.get_events():
                    if plugin in self._hooks[event]:
                        self._hooks[event].remove(plugin)

            logger.info(f"Unregistered plugin: {name}")

        return plugin

    def get(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def get_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all plugins of a specific type."""
        return self._plugins_by_type.get(plugin_type, [])

    def get_hooks(self, event: HookEvent) -> List[HookPlugin]:
        """Get all hooks for an event."""
        return self._hooks.get(event, [])

    def all(self) -> List[Plugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def enabled(self) -> List[Plugin]:
        """Get all enabled plugins."""
        return [p for p in self._plugins.values() if p.metadata.enabled]


class PluginManager:
    """
    Central plugin manager for loading, configuring, and executing plugins.

    Example:
        ```python
        # Initialize manager
        manager = PluginManager()

        # Load plugins from directory
        await manager.load_plugins_from_directory("./plugins")

        # Execute analyzer plugin
        result = await manager.execute_plugin(
            "custom-analyzer",
            context=PluginContext(request_id="123"),
            simulation_data=data
        )

        # Trigger hooks
        await manager.trigger_hooks(
            HookEvent.SIMULATION_ANALYZED,
            {"simulation_id": "sim_123"}
        )
        ```
    """

    def __init__(self):
        """Initialize plugin manager."""
        self.registry = PluginRegistry()
        self._configs: Dict[str, Dict[str, Any]] = {}

    # ========================================================================
    # Plugin Loading
    # ========================================================================

    async def load_plugin_class(
        self, plugin_class: Type[Plugin], config: Optional[Dict[str, Any]] = None
    ) -> Plugin:
        """
        Load plugin from class.

        Args:
            plugin_class: Plugin class to instantiate
            config: Plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin fails to load
        """
        try:
            # Check if class has metadata
            if not hasattr(plugin_class, "_plugin_metadata"):
                raise PluginLoadError(
                    plugin_class.__name__,
                    "Plugin class must use @plugin decorator or set _plugin_metadata",
                )

            # Instantiate plugin
            plugin = plugin_class()

            # Validate and store config
            config = config or {}
            await plugin.validate_config(config)
            self._configs[plugin.metadata.name] = config

            # Initialize plugin
            await plugin.initialize(config)
            plugin._initialized = True

            # Register plugin
            self.registry.register(plugin)

            return plugin

        except Exception as e:
            raise PluginLoadError(
                plugin_class.__name__, f"Failed to load plugin: {str(e)}"
            ) from e

    async def load_plugin_from_module(
        self, module_path: str, config: Optional[Dict[str, Any]] = None
    ) -> Plugin:
        """
        Load plugin from Python module.

        Args:
            module_path: Python module path (e.g., "myapp.plugins.analyzer")
            config: Plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin fails to load
        """
        try:
            # Import module
            module = importlib.import_module(module_path)

            # Find plugin class in module
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, Plugin)
                    and obj is not Plugin
                    and hasattr(obj, "_plugin_metadata")
                ):
                    plugin_class = obj
                    break

            if not plugin_class:
                raise PluginLoadError(
                    module_path, "No plugin class found in module"
                )

            return await self.load_plugin_class(plugin_class, config)

        except ImportError as e:
            raise PluginLoadError(
                module_path, f"Failed to import module: {str(e)}"
            ) from e

    async def load_plugin_from_file(
        self, file_path: str, config: Optional[Dict[str, Any]] = None
    ) -> Plugin:
        """
        Load plugin from Python file.

        Args:
            file_path: Path to plugin Python file
            config: Plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin fails to load
        """
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location("plugin_module", file_path)
            if not spec or not spec.loader:
                raise PluginLoadError(file_path, "Failed to load file spec")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, Plugin)
                    and obj is not Plugin
                    and hasattr(obj, "_plugin_metadata")
                ):
                    plugin_class = obj
                    break

            if not plugin_class:
                raise PluginLoadError(file_path, "No plugin class found in file")

            return await self.load_plugin_class(plugin_class, config)

        except Exception as e:
            raise PluginLoadError(
                file_path, f"Failed to load plugin from file: {str(e)}"
            ) from e

    async def load_plugins_from_directory(
        self,
        directory: str,
        config_map: Optional[Dict[str, Dict[str, Any]]] = None,
        recursive: bool = True,
    ) -> List[Plugin]:
        """
        Load all plugins from directory.

        Args:
            directory: Directory path containing plugin files
            config_map: Map of plugin names to configurations
            recursive: Search subdirectories

        Returns:
            List of loaded plugins

        Example:
            ```python
            # Load all plugins from ./plugins directory
            plugins = await manager.load_plugins_from_directory(
                "./plugins",
                config_map={
                    "custom-analyzer": {"threshold": 0.1}
                }
            )
            ```
        """
        config_map = config_map or {}
        loaded_plugins = []

        path = Path(directory)
        if not path.exists():
            logger.warning(f"Plugin directory not found: {directory}")
            return loaded_plugins

        # Find all Python files
        pattern = "**/*.py" if recursive else "*.py"
        for file_path in path.glob(pattern):
            # Skip __init__.py and private files
            if file_path.name.startswith("_"):
                continue

            try:
                plugin = await self.load_plugin_from_file(str(file_path))
                # Apply config if available
                if plugin.metadata.name in config_map:
                    await self.configure_plugin(
                        plugin.metadata.name, config_map[plugin.metadata.name]
                    )
                loaded_plugins.append(plugin)

            except PluginLoadError as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")
                continue

        logger.info(f"Loaded {len(loaded_plugins)} plugins from {directory}")
        return loaded_plugins

    # ========================================================================
    # Plugin Configuration
    # ========================================================================

    async def configure_plugin(
        self, name: str, config: Dict[str, Any]
    ) -> None:
        """
        Configure a plugin.

        Args:
            name: Plugin name
            config: Configuration dictionary

        Raises:
            PluginConfigError: If configuration is invalid
        """
        plugin = self.registry.get(name)
        if not plugin:
            raise PluginConfigError(name, "Plugin not found")

        await plugin.validate_config(config)
        self._configs[name] = config

        # Re-initialize with new config
        await plugin.initialize(config)

    def get_plugin_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get plugin configuration."""
        return self._configs.get(name)

    # ========================================================================
    # Plugin Execution
    # ========================================================================

    async def execute_plugin(
        self,
        name: str,
        context: Optional[PluginContext] = None,
        **kwargs
    ) -> Any:
        """
        Execute a plugin.

        Args:
            name: Plugin name
            context: Plugin context (created if not provided)
            **kwargs: Plugin-specific arguments

        Returns:
            Plugin execution result

        Raises:
            PluginExecutionError: If execution fails
        """
        plugin = self.registry.get(name)
        if not plugin:
            raise PluginExecutionError(name, "Plugin not found")

        if not plugin.metadata.enabled:
            raise PluginExecutionError(name, "Plugin is disabled")

        # Create default context if not provided
        if context is None:
            context = PluginContext(request_id="default")

        # Add plugin config to context
        context.config = self._configs.get(name, {})

        try:
            result = await plugin.execute(context, **kwargs)
            return result

        except Exception as e:
            raise PluginExecutionError(
                name, f"Plugin execution failed: {str(e)}"
            ) from e

    async def execute_plugins_by_type(
        self,
        plugin_type: PluginType,
        context: Optional[PluginContext] = None,
        **kwargs
    ) -> List[Any]:
        """
        Execute all enabled plugins of a specific type.

        Args:
            plugin_type: Type of plugins to execute
            context: Plugin context
            **kwargs: Plugin-specific arguments

        Returns:
            List of results from each plugin

        Example:
            ```python
            # Execute all analyzer plugins
            results = await manager.execute_plugins_by_type(
                PluginType.ANALYZER,
                simulation_data=data
            )
            ```
        """
        plugins = self.registry.get_by_type(plugin_type)
        enabled_plugins = [p for p in plugins if p.metadata.enabled]

        # Sort by priority (higher priority first)
        enabled_plugins.sort(key=lambda p: p.metadata.priority.value, reverse=True)

        # Execute plugins
        results = []
        for plugin in enabled_plugins:
            try:
                result = await self.execute_plugin(
                    plugin.metadata.name, context, **kwargs
                )
                results.append(result)
            except PluginExecutionError as e:
                logger.error(f"Plugin execution failed: {e}")
                continue

        return results

    # ========================================================================
    # Hook System
    # ========================================================================

    async def trigger_hooks(
        self,
        event: HookEvent,
        data: Dict[str, Any],
        context: Optional[PluginContext] = None,
    ) -> None:
        """
        Trigger all hooks for an event.

        Args:
            event: Event that occurred
            data: Event data
            context: Plugin context

        Example:
            ```python
            # Trigger simulation analyzed hooks
            await manager.trigger_hooks(
                HookEvent.SIMULATION_ANALYZED,
                {
                    "simulation_id": "sim_123",
                    "user_id": "usr_456",
                    "results": {...}
                }
            )
            ```
        """
        hooks = self.registry.get_hooks(event)
        enabled_hooks = [h for h in hooks if h.metadata.enabled]

        # Sort by priority
        enabled_hooks.sort(key=lambda h: h.metadata.priority.value, reverse=True)

        # Create default context if not provided
        if context is None:
            context = PluginContext(request_id="hook")

        # Execute hooks in parallel
        tasks = []
        for hook in enabled_hooks:
            context.config = self._configs.get(hook.metadata.name, {})
            tasks.append(
                self._execute_hook_safe(hook, event, data, context)
            )

        await asyncio.gather(*tasks)

    async def _execute_hook_safe(
        self,
        hook: HookPlugin,
        event: HookEvent,
        data: Dict[str, Any],
        context: PluginContext,
    ) -> None:
        """Execute hook with error handling."""
        try:
            await hook.on_event(event, data, context)
        except Exception as e:
            logger.error(
                f"Hook '{hook.metadata.name}' failed for event '{event.value}': {e}"
            )

    # ========================================================================
    # Plugin Management
    # ========================================================================

    async def enable_plugin(self, name: str) -> None:
        """Enable a plugin."""
        plugin = self.registry.get(name)
        if plugin:
            plugin.metadata.enabled = True
            logger.info(f"Enabled plugin: {name}")

    async def disable_plugin(self, name: str) -> None:
        """Disable a plugin."""
        plugin = self.registry.get(name)
        if plugin:
            plugin.metadata.enabled = False
            logger.info(f"Disabled plugin: {name}")

    async def unload_plugin(self, name: str) -> None:
        """
        Unload a plugin.

        Args:
            name: Plugin name
        """
        plugin = self.registry.unregister(name)
        if plugin:
            await plugin.shutdown()
            self._configs.pop(name, None)
            logger.info(f"Unloaded plugin: {name}")

    async def reload_plugin(self, name: str) -> Plugin:
        """
        Reload a plugin.

        Args:
            name: Plugin name

        Returns:
            Reloaded plugin instance

        Raises:
            PluginLoadError: If reload fails
        """
        # Get existing plugin and config
        old_plugin = self.registry.get(name)
        if not old_plugin:
            raise PluginLoadError(name, "Plugin not found")

        config = self._configs.get(name)

        # Unload
        await self.unload_plugin(name)

        # Reload (assumes plugin was loaded from module)
        # This is a simplified reload - in production you'd need to track
        # the original source (file, module, class)
        raise NotImplementedError("Plugin reload requires tracking original source")

    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[Dict[str, Any]]:
        """
        List all plugins.

        Args:
            plugin_type: Filter by plugin type

        Returns:
            List of plugin information dictionaries
        """
        if plugin_type:
            plugins = self.registry.get_by_type(plugin_type)
        else:
            plugins = self.registry.all()

        return [p.get_info() for p in plugins]

    # ========================================================================
    # Lifecycle Management
    # ========================================================================

    async def startup(self) -> None:
        """
        Initialize plugin system on application startup.

        Triggers SYSTEM_STARTUP hooks.
        """
        logger.info("Plugin system starting up...")

        # Trigger startup hooks
        await self.trigger_hooks(
            HookEvent.SYSTEM_STARTUP,
            {"timestamp": "now"}
        )

        logger.info(f"Plugin system started with {len(self.registry.all())} plugins")

    async def shutdown(self) -> None:
        """
        Cleanup plugin system on application shutdown.

        Triggers SYSTEM_SHUTDOWN hooks and unloads all plugins.
        """
        logger.info("Plugin system shutting down...")

        # Trigger shutdown hooks
        await self.trigger_hooks(
            HookEvent.SYSTEM_SHUTDOWN,
            {"timestamp": "now"}
        )

        # Shutdown all plugins
        for plugin in self.registry.all():
            try:
                await plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin '{plugin.metadata.name}': {e}")

        logger.info("Plugin system shut down")


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    Get global plugin manager instance.

    Returns:
        Plugin manager singleton
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
