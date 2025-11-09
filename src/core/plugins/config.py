"""
플러그인 설정 시스템

플러그인 설정을 관리하는 시스템.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, cast

from pydantic import BaseModel, ValidationError, create_model

from .base import PluginConfigError, PluginMetadata


class PluginConfigManager:
    """
    플러그인 설정 관리자

    플러그인별 설정을 로드, 검증, 저장.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: 설정 파일 저장 디렉토리
        """
        self._config_dir = config_dir
        self._configs: Dict[str, Dict[str, Any]] = {}  # plugin_name -> config
        self._schemas: Dict[str, Optional[Dict[str, Any]]] = {}  # plugin_name -> schema

        if config_dir:
            config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, plugin_name: str, config_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        플러그인 설정 로드

        Args:
            plugin_name: 플러그인 이름
            config_file: 설정 파일 경로 (None이면 기본 경로 사용)

        Returns:
            설정 딕셔너리

        Raises:
            PluginConfigError: 설정 로드 실패
        """
        # 설정 파일 경로 결정
        if config_file is None:
            if self._config_dir is None:
                raise PluginConfigError(f"No config directory specified for plugin '{plugin_name}'")
            config_file = self._config_dir / f"{plugin_name}.json"

        # 파일이 없으면 빈 설정 반환
        if not config_file.exists():
            return {}

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config: Dict[str, Any] = json.load(f)

            # 캐시에 저장
            self._configs[plugin_name] = config

            return config

        except json.JSONDecodeError as e:
            raise PluginConfigError(f"Invalid JSON in config file {config_file}: {e}") from e
        except Exception as e:
            raise PluginConfigError(f"Failed to load config for '{plugin_name}': {e}") from e

    def save_config(
        self,
        plugin_name: str,
        config: Dict[str, Any],
        config_file: Optional[Path] = None,
    ) -> None:
        """
        플러그인 설정 저장

        Args:
            plugin_name: 플러그인 이름
            config: 설정 딕셔너리
            config_file: 설정 파일 경로

        Raises:
            PluginConfigError: 설정 저장 실패
        """
        # 설정 파일 경로 결정
        if config_file is None:
            if self._config_dir is None:
                raise PluginConfigError(f"No config directory specified for plugin '{plugin_name}'")
            config_file = self._config_dir / f"{plugin_name}.json"

        try:
            # 스키마 검증 (스키마가 등록되어 있으면)
            if plugin_name in self._schemas:
                self._validate_config(plugin_name, config)

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # 캐시에 저장
            self._configs[plugin_name] = config

        except Exception as e:
            raise PluginConfigError(f"Failed to save config for '{plugin_name}': {e}") from e

    def get_config(
        self, plugin_name: str, default: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        캐시된 설정 조회

        Args:
            plugin_name: 플러그인 이름
            default: 설정이 없을 때 기본값

        Returns:
            설정 딕셔너리
        """
        return self._configs.get(plugin_name, default or {})

    def set_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """
        설정 설정 (캐시에만)

        Args:
            plugin_name: 플러그인 이름
            config: 설정 딕셔너리
        """
        # 스키마 검증
        if plugin_name in self._schemas:
            self._validate_config(plugin_name, config)

        self._configs[plugin_name] = config

    def register_schema(self, plugin_name: str, schema: Optional[Dict[str, Any]]) -> None:
        """
        플러그인 설정 스키마 등록

        Args:
            plugin_name: 플러그인 이름
            schema: JSON Schema 형식의 스키마
        """
        self._schemas[plugin_name] = schema

    def register_schema_from_metadata(self, metadata: PluginMetadata) -> None:
        """
        메타데이터에서 스키마 등록

        Args:
            metadata: 플러그인 메타데이터
        """
        self._schemas[metadata.name] = metadata.config_schema

    def validate_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        설정 검증

        Args:
            plugin_name: 플러그인 이름
            config: 검증할 설정

        Returns:
            검증 성공 여부

        Raises:
            PluginConfigError: 검증 실패
        """
        try:
            self._validate_config(plugin_name, config)
            return True
        except PluginConfigError:
            return False

    def _validate_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """
        설정 검증 (내부 메서드)

        Raises:
            PluginConfigError: 검증 실패
        """
        schema = self._schemas.get(plugin_name)

        if schema is None:
            # 스키마가 없으면 검증 건너뜀
            return

        try:
            # JSON Schema를 Pydantic 모델로 변환하여 검증
            model_class = self._create_pydantic_model(schema)
            model_class(**config)

        except ValidationError as e:
            raise PluginConfigError(f"Config validation failed for '{plugin_name}': {e}") from e
        except Exception as e:
            raise PluginConfigError(f"Config validation error for '{plugin_name}': {e}") from e

    def _create_pydantic_model(self, schema: Dict[str, Any]) -> type[BaseModel]:
        """
        JSON Schema에서 Pydantic 모델 생성

        Args:
            schema: JSON Schema

        Returns:
            Pydantic 모델 클래스
        """
        # JSON Schema의 properties를 Pydantic 필드로 변환
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        fields = {}
        for field_name, field_schema in properties.items():
            # 타입 매핑
            field_type = self._map_json_type_to_python(field_schema)

            # 필수 여부
            if field_name in required:
                fields[field_name] = (field_type, ...)
            else:
                default = field_schema.get("default")
                fields[field_name] = (field_type, default)

        # 동적 모델 생성
        return cast(type[Any], create_model("DynamicConfigModel", **fields))

    def _map_json_type_to_python(self, field_schema: Dict[str, Any]) -> Any:
        """JSON Schema 타입을 Python 타입으로 매핑"""
        json_type = field_schema.get("type", "string")

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        return type_mapping.get(json_type, Any)

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """모든 플러그인의 설정 반환"""
        return self._configs.copy()

    def clear_config(self, plugin_name: str) -> None:
        """플러그인 설정 삭제"""
        if plugin_name in self._configs:
            del self._configs[plugin_name]

    def clear_all_configs(self) -> None:
        """모든 설정 삭제"""
        self._configs.clear()


class ConfigBuilder:
    """
    플러그인 설정 빌더

    설정을 쉽게 구성하기 위한 빌더 패턴.
    """

    def __init__(self, plugin_name: str):
        self._plugin_name = plugin_name
        self._config: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> "ConfigBuilder":
        """
        설정 값 설정

        Args:
            key: 설정 키
            value: 설정 값

        Returns:
            ConfigBuilder (체이닝용)
        """
        self._config[key] = value
        return self

    def set_nested(self, path: str, value: Any) -> "ConfigBuilder":
        """
        중첩된 설정 값 설정 (점 표기법)

        Args:
            path: 설정 경로 (예: "database.host")
            value: 설정 값

        Returns:
            ConfigBuilder
        """
        keys = path.split(".")
        current = self._config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        return self

    def merge(self, other_config: Dict[str, Any]) -> "ConfigBuilder":
        """
        다른 설정과 병합

        Args:
            other_config: 병합할 설정

        Returns:
            ConfigBuilder
        """
        self._config.update(other_config)
        return self

    def build(self) -> Dict[str, Any]:
        """
        설정 빌드

        Returns:
            설정 딕셔너리
        """
        return self._config.copy()
