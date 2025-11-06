"""플러그인 타입 모듈"""

from .adapter_plugin import AdapterPlugin, AdapterPluginRegistry
from .stage_plugin import StagePlugin, StagePluginRegistry

__all__ = [
    "StagePlugin",
    "StagePluginRegistry",
    "AdapterPlugin",
    "AdapterPluginRegistry",
]
