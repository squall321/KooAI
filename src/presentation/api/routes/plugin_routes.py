"""
Plugin Management API Routes

Endpoints for managing plugins (list, enable/disable, configure).
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from src.infrastructure.plugins.plugin_manager import get_plugin_manager
from src.infrastructure.plugins.plugin_interface import (
    PluginType,
    HookEvent,
    PluginContext,
)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


# ============================================================================
# Pydantic Models
# ============================================================================


class PluginInfo(BaseModel):
    """Plugin information response."""

    name: str
    version: str
    description: str
    author: str
    type: str
    priority: int
    enabled: bool
    initialized: bool

    class Config:
        schema_extra = {
            "example": {
                "name": "turbulence-analyzer",
                "version": "1.0.0",
                "description": "Analyzes turbulence intensity",
                "author": "KooAI Team",
                "type": "analyzer",
                "priority": 100,
                "enabled": True,
                "initialized": True,
            }
        }


class PluginConfigRequest(BaseModel):
    """Request to configure a plugin."""

    config: Dict[str, Any] = Field(..., description="Plugin configuration")

    class Config:
        schema_extra = {
            "example": {
                "config": {
                    "method": "rms",
                    "threshold": 0.05,
                    "reference_velocity": 10.0,
                }
            }
        }


class PluginExecuteRequest(BaseModel):
    """Request to execute a plugin."""

    plugin_name: str = Field(..., description="Name of plugin to execute")
    context: Optional[Dict[str, Any]] = Field(None, description="Plugin context")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Plugin parameters"
    )

    class Config:
        schema_extra = {
            "example": {
                "plugin_name": "turbulence-analyzer",
                "context": {"request_id": "req_123", "user_id": "usr_456"},
                "parameters": {
                    "simulation_data": {
                        "velocity_x": [1.0, 2.0, 3.0],
                        "velocity_y": [0.5, 1.5, 2.5],
                        "velocity_z": [0.1, 0.2, 0.3],
                    }
                },
            }
        }


class TriggerHookRequest(BaseModel):
    """Request to trigger hooks."""

    event: str = Field(..., description="Hook event name")
    data: Dict[str, Any] = Field(..., description="Event data")

    class Config:
        schema_extra = {
            "example": {
                "event": "simulation.analyzed",
                "data": {
                    "simulation_id": "sim_123",
                    "user_email": "user@example.com",
                    "results": {"turbulence_intensity": 0.12},
                },
            }
        }


# ============================================================================
# Plugin Discovery Endpoints
# ============================================================================


@router.get("/", response_model=List[PluginInfo])
async def list_plugins(
    plugin_type: Optional[str] = Query(None, description="Filter by plugin type"),
    enabled_only: bool = Query(False, description="Show only enabled plugins"),
):
    """
    List all registered plugins.

    **Example**:
    ```bash
    # List all plugins
    curl http://localhost:8000/api/v1/plugins

    # List only analyzer plugins
    curl "http://localhost:8000/api/v1/plugins?plugin_type=analyzer"

    # List enabled plugins
    curl "http://localhost:8000/api/v1/plugins?enabled_only=true"
    ```
    """
    manager = get_plugin_manager()

    # Filter by type if specified
    if plugin_type:
        try:
            p_type = PluginType(plugin_type)
            plugins = manager.list_plugins(plugin_type=p_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plugin type: {plugin_type}. "
                f"Valid types: {[t.value for t in PluginType]}",
            )
    else:
        plugins = manager.list_plugins()

    # Filter enabled
    if enabled_only:
        plugins = [p for p in plugins if p["enabled"]]

    return plugins


@router.get("/{plugin_name}", response_model=PluginInfo)
async def get_plugin(plugin_name: str):
    """
    Get detailed information about a specific plugin.

    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/plugins/turbulence-analyzer
    ```
    """
    manager = get_plugin_manager()
    plugin = manager.registry.get(plugin_name)

    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        )

    return plugin.get_info()


# ============================================================================
# Plugin Configuration
# ============================================================================


@router.get("/{plugin_name}/config", response_model=Dict[str, Any])
async def get_plugin_config(plugin_name: str):
    """
    Get current configuration for a plugin.

    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/plugins/turbulence-analyzer/config
    ```
    """
    manager = get_plugin_manager()
    config = manager.get_plugin_config(plugin_name)

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        )

    return config


@router.put("/{plugin_name}/config", response_model=Dict[str, str])
async def configure_plugin(plugin_name: str, request: PluginConfigRequest):
    """
    Configure a plugin.

    **Example**:
    ```bash
    curl -X PUT http://localhost:8000/api/v1/plugins/turbulence-analyzer/config \\
      -H "Content-Type: application/json" \\
      -d '{
        "config": {
          "method": "tke",
          "threshold": 0.1
        }
      }'
    ```
    """
    manager = get_plugin_manager()

    try:
        await manager.configure_plugin(plugin_name, request.config)
        return {"message": f"Plugin '{plugin_name}' configured successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to configure plugin: {str(e)}",
        )


# ============================================================================
# Plugin Lifecycle Management
# ============================================================================


@router.post("/{plugin_name}/enable", response_model=Dict[str, str])
async def enable_plugin(plugin_name: str):
    """
    Enable a plugin.

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/plugins/turbulence-analyzer/enable
    ```
    """
    manager = get_plugin_manager()

    plugin = manager.registry.get(plugin_name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        )

    await manager.enable_plugin(plugin_name)
    return {"message": f"Plugin '{plugin_name}' enabled"}


@router.post("/{plugin_name}/disable", response_model=Dict[str, str])
async def disable_plugin(plugin_name: str):
    """
    Disable a plugin.

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/plugins/turbulence-analyzer/disable
    ```
    """
    manager = get_plugin_manager()

    plugin = manager.registry.get(plugin_name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        )

    await manager.disable_plugin(plugin_name)
    return {"message": f"Plugin '{plugin_name}' disabled"}


@router.delete("/{plugin_name}", response_model=Dict[str, str])
async def unload_plugin(plugin_name: str):
    """
    Unload a plugin.

    **Warning**: This will remove the plugin from the system.

    **Example**:
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/plugins/turbulence-analyzer
    ```
    """
    manager = get_plugin_manager()

    plugin = manager.registry.get(plugin_name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        )

    await manager.unload_plugin(plugin_name)
    return {"message": f"Plugin '{plugin_name}' unloaded"}


# ============================================================================
# Plugin Execution
# ============================================================================


@router.post("/execute", response_model=Dict[str, Any])
async def execute_plugin(request: PluginExecuteRequest):
    """
    Execute a plugin with given parameters.

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/plugins/execute \\
      -H "Content-Type: application/json" \\
      -d '{
        "plugin_name": "turbulence-analyzer",
        "parameters": {
          "simulation_data": {
            "velocity_x": [1.0, 2.0, 3.0],
            "velocity_y": [0.5, 1.5, 2.5],
            "velocity_z": [0.1, 0.2, 0.3]
          }
        }
      }'
    ```
    """
    manager = get_plugin_manager()

    # Create context
    context = PluginContext(
        request_id=request.context.get("request_id", "api") if request.context else "api",
        user_id=request.context.get("user_id") if request.context else None,
        tenant_id=request.context.get("tenant_id") if request.context else None,
    )

    try:
        result = await manager.execute_plugin(
            request.plugin_name, context, **request.parameters
        )

        return {
            "plugin": request.plugin_name,
            "status": "success",
            "result": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plugin execution failed: {str(e)}",
        )


@router.post("/execute-by-type/{plugin_type}", response_model=Dict[str, Any])
async def execute_plugins_by_type(
    plugin_type: str, parameters: Dict[str, Any] = None
):
    """
    Execute all enabled plugins of a specific type.

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/plugins/execute-by-type/analyzer" \\
      -H "Content-Type: application/json" \\
      -d '{
        "simulation_data": {
          "velocity_x": [1.0, 2.0, 3.0]
        }
      }'
    ```
    """
    manager = get_plugin_manager()

    try:
        p_type = PluginType(plugin_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plugin type: {plugin_type}",
        )

    context = PluginContext(request_id="api-batch")

    try:
        results = await manager.execute_plugins_by_type(
            p_type, context, **(parameters or {})
        )

        return {
            "plugin_type": plugin_type,
            "executed_count": len(results),
            "results": results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch execution failed: {str(e)}",
        )


# ============================================================================
# Hook System
# ============================================================================


@router.post("/hooks/trigger", response_model=Dict[str, str])
async def trigger_hooks(request: TriggerHookRequest):
    """
    Manually trigger hooks for an event.

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/plugins/hooks/trigger \\
      -H "Content-Type: application/json" \\
      -d '{
        "event": "simulation.analyzed",
        "data": {
          "simulation_id": "sim_123",
          "user_email": "user@example.com"
        }
      }'
    ```
    """
    manager = get_plugin_manager()

    try:
        event = HookEvent(request.event)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid hook event: {request.event}. "
            f"Valid events: {[e.value for e in HookEvent]}",
        )

    context = PluginContext(request_id="api-hook")

    try:
        await manager.trigger_hooks(event, request.data, context)
        return {"message": f"Triggered hooks for event '{request.event}'"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hook trigger failed: {str(e)}",
        )


@router.get("/hooks/events", response_model=List[str])
async def list_hook_events():
    """
    List all available hook events.

    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/plugins/hooks/events
    ```
    """
    return [event.value for event in HookEvent]


# ============================================================================
# Plugin Types
# ============================================================================


@router.get("/types", response_model=List[str])
async def list_plugin_types():
    """
    List all available plugin types.

    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/plugins/types
    ```
    """
    return [ptype.value for ptype in PluginType]
