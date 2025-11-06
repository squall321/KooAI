"""
플러그인 시스템

동적 플러그인 시스템으로 시스템 확장성 제공.

주요 컴포넌트:
- IPlugin, BasePlugin: 플러그인 인터페이스 및 베이스 클래스
- PluginRegistry: 플러그인 레지스트리
- PluginLoader: 동적 플러그인 로더
- PluginConfigManager: 플러그인 설정 관리
- StagePlugin, AdapterPlugin: 특화된 플러그인 타입

사용 예시:
```python
from src.core.plugins import PluginRegistry, PluginLoader

# 레지스트리 생성
registry = PluginRegistry()

# 로더 생성
loader = PluginLoader(registry)

# 플러그인 로드
plugin = loader.load_from_file(
    Path("plugins/my_plugin.py"),
    "MyPlugin",
    config={"key": "value"}
)

# 플러그인 활성화
await plugin.initialize(config)
await plugin.activate()

# 플러그인 사용
stage = plugin.create_stage()
```
"""

from .base import (
    BasePlugin,
    IPlugin,
    PluginConfigError,
    PluginDependency,
    PluginDependencyError,
    PluginError,
    PluginLoadError,
    PluginMetadata,
    PluginNotFoundError,
    PluginStatus,
    PluginType,
    PluginVersion,
    PluginVersionConflictError,
)
from .config import ConfigBuilder, PluginConfigManager
from .loader import PluginLoader
from .registry import PluginRegistry
from .types import (
    AdapterPlugin,
    AdapterPluginRegistry,
    StagePlugin,
    StagePluginRegistry,
)

__all__ = [
    # Base
    "IPlugin",
    "BasePlugin",
    "PluginMetadata",
    "PluginVersion",
    "PluginDependency",
    "PluginStatus",
    "PluginType",
    # Errors
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "PluginDependencyError",
    "PluginVersionConflictError",
    "PluginConfigError",
    # Core Components
    "PluginRegistry",
    "PluginLoader",
    "PluginConfigManager",
    "ConfigBuilder",
    # Plugin Types
    "StagePlugin",
    "StagePluginRegistry",
    "AdapterPlugin",
    "AdapterPluginRegistry",
]
