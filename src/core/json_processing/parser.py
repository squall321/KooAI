"""
JSON 파싱 엔진

대용량 JSON 파일을 스트리밍 방식으로 파싱하고 계층적 데이터를 추출합니다.
"""

import json
from typing import (
    Optional,
    Dict,
    Any,
    Iterator,
    Callable,
    List,
    Union,
    TextIO,
    BinaryIO,
)
from pathlib import Path
from io import IOBase

try:
    import ijson
    IJSON_AVAILABLE = True
except ImportError:
    IJSON_AVAILABLE = False
    import warnings
    warnings.warn("ijson not installed. Large file streaming will be limited.")

from pydantic import ValidationError

from src.core.json_processing.schema import (
    SimulationResult,
    schema_registry,
    BaseModel,
)


class JSONParser:
    """
    JSON 파서

    표준 JSON 파싱 및 검증 기능을 제공합니다.
    """

    def __init__(self, validate: bool = True):
        """
        Args:
            validate: Pydantic 스키마 검증 여부
        """
        self.validate = validate

    def parse_file(
        self, file_path: Union[str, Path], schema_name: Optional[str] = None
    ) -> Union[Dict[str, Any], BaseModel]:
        """
        JSON 파일 파싱

        Args:
            file_path: JSON 파일 경로
            schema_name: 검증할 스키마 이름 (None이면 검증 안함)

        Returns:
            파싱된 딕셔너리 또는 검증된 Pydantic 모델

        Raises:
            FileNotFoundError: 파일이 없는 경우
            json.JSONDecodeError: JSON 파싱 오류
            ValidationError: 스키마 검증 오류
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if self.validate and schema_name:
            return schema_registry.validate(schema_name, data)

        return data

    def parse_string(
        self, json_str: str, schema_name: Optional[str] = None
    ) -> Union[Dict[str, Any], BaseModel]:
        """
        JSON 문자열 파싱

        Args:
            json_str: JSON 문자열
            schema_name: 검증할 스키마 이름

        Returns:
            파싱된 딕셔너리 또는 검증된 Pydantic 모델

        Raises:
            json.JSONDecodeError: JSON 파싱 오류
            ValidationError: 스키마 검증 오류
        """
        data = json.loads(json_str)

        if self.validate and schema_name:
            return schema_registry.validate(schema_name, data)

        return data

    def validate_data(self, data: Dict[str, Any], schema_name: str) -> BaseModel:
        """
        데이터 검증

        Args:
            data: 검증할 데이터
            schema_name: 스키마 이름

        Returns:
            검증된 Pydantic 모델

        Raises:
            ValidationError: 스키마 검증 오류
        """
        return schema_registry.validate(schema_name, data)


class StreamingJSONParser:
    """
    스트리밍 JSON 파서

    대용량 JSON 파일을 메모리 효율적으로 파싱합니다.
    ijson 라이브러리를 사용합니다.
    """

    def __init__(self):
        if not IJSON_AVAILABLE:
            raise ImportError(
                "ijson is required for streaming JSON parsing. "
                "Install it with: pip install ijson"
            )

    def stream_array_items(
        self, file_path: Union[str, Path], array_path: str = "item"
    ) -> Iterator[Any]:
        """
        JSON 배열의 아이템을 스트리밍

        Args:
            file_path: JSON 파일 경로
            array_path: 배열 경로 (예: 'time_steps.item', 'fields.item')

        Yields:
            배열의 각 아이템

        Example:
            >>> parser = StreamingJSONParser()
            >>> for item in parser.stream_array_items('data.json', 'time_steps.item'):
            ...     process(item)
        """
        file_path = Path(file_path)

        with open(file_path, "rb") as f:
            for item in ijson.items(f, array_path):
                yield item

    def stream_object_values(
        self, file_path: Union[str, Path], object_path: str
    ) -> Iterator[tuple[str, Any]]:
        """
        JSON 객체의 키-값 쌍을 스트리밍

        Args:
            file_path: JSON 파일 경로
            object_path: 객체 경로

        Yields:
            (키, 값) 튜플

        Example:
            >>> parser = StreamingJSONParser()
            >>> for key, value in parser.stream_object_values('data.json', 'fields'):
            ...     print(f"{key}: {value}")
        """
        file_path = Path(file_path)

        with open(file_path, "rb") as f:
            parser = ijson.kvitems(f, object_path)
            for key, value in parser:
                yield key, value

    def extract_field(
        self, file_path: Union[str, Path], field_path: str
    ) -> Optional[Any]:
        """
        특정 필드 값 추출

        Args:
            file_path: JSON 파일 경로
            field_path: 필드 경로 (예: 'metadata.name', 'mesh.info.num_vertices')

        Returns:
            필드 값 (없으면 None)

        Example:
            >>> parser = StreamingJSONParser()
            >>> name = parser.extract_field('data.json', 'metadata.name')
        """
        file_path = Path(file_path)

        with open(file_path, "rb") as f:
            try:
                # ijson prefix 방식으로 특정 경로의 값 추출
                for value in ijson.items(f, field_path):
                    return value
            except ijson.JSONError:
                return None

        return None

    def stream_large_array(
        self,
        file_path: Union[str, Path],
        array_path: str,
        batch_size: int = 1000,
    ) -> Iterator[List[Any]]:
        """
        대용량 배열을 배치 단위로 스트리밍

        Args:
            file_path: JSON 파일 경로
            array_path: 배열 경로
            batch_size: 배치 크기

        Yields:
            배치 리스트

        Example:
            >>> parser = StreamingJSONParser()
            >>> for batch in parser.stream_large_array('data.json', 'vertices', 10000):
            ...     process_batch(batch)
        """
        file_path = Path(file_path)
        batch = []

        with open(file_path, "rb") as f:
            for item in ijson.items(f, array_path):
                batch.append(item)

                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            # 남은 배치 yield
            if batch:
                yield batch


class HierarchicalExtractor:
    """
    계층적 데이터 추출기

    중첩된 JSON 구조에서 특정 경로의 데이터를 추출합니다.
    """

    @staticmethod
    def extract_by_path(data: Dict[str, Any], path: str, separator: str = ".") -> Any:
        """
        경로로 데이터 추출

        Args:
            data: JSON 데이터
            path: 점(.) 구분 경로 (예: 'metadata.name', 'mesh.info.num_vertices')
            separator: 경로 구분자

        Returns:
            추출된 값 (없으면 None)

        Example:
            >>> data = {'metadata': {'name': 'CFD Sim', 'version': '1.0'}}
            >>> HierarchicalExtractor.extract_by_path(data, 'metadata.name')
            'CFD Sim'
        """
        keys = path.split(separator)
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                idx = int(key)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None

        return current

    @staticmethod
    def extract_multiple(
        data: Dict[str, Any], paths: List[str]
    ) -> Dict[str, Any]:
        """
        여러 경로의 데이터를 한 번에 추출

        Args:
            data: JSON 데이터
            paths: 경로 리스트

        Returns:
            {경로: 값} 딕셔너리

        Example:
            >>> data = {'metadata': {'name': 'Sim', 'version': '1.0'}}
            >>> HierarchicalExtractor.extract_multiple(data, ['metadata.name', 'metadata.version'])
            {'metadata.name': 'Sim', 'metadata.version': '1.0'}
        """
        result = {}
        for path in paths:
            result[path] = HierarchicalExtractor.extract_by_path(data, path)
        return result

    @staticmethod
    def set_by_path(
        data: Dict[str, Any], path: str, value: Any, separator: str = "."
    ) -> None:
        """
        경로로 값 설정 (in-place)

        Args:
            data: JSON 데이터
            path: 점(.) 구분 경로
            value: 설정할 값
            separator: 경로 구분자

        Example:
            >>> data = {'metadata': {'name': 'Old'}}
            >>> HierarchicalExtractor.set_by_path(data, 'metadata.name', 'New')
            >>> data
            {'metadata': {'name': 'New'}}
        """
        keys = path.split(separator)
        current = data

        # 마지막 키 전까지 순회하며 경로 생성
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 마지막 키에 값 설정
        current[keys[-1]] = value

    @staticmethod
    def flatten(
        data: Dict[str, Any], parent_key: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """
        중첩된 딕셔너리를 평탄화

        Args:
            data: 중첩된 딕셔너리
            parent_key: 부모 키 (재귀용)
            separator: 구분자

        Returns:
            평탄화된 딕셔너리

        Example:
            >>> data = {'a': {'b': {'c': 1}}, 'd': 2}
            >>> HierarchicalExtractor.flatten(data)
            {'a.b.c': 1, 'd': 2}
        """
        items = []

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    HierarchicalExtractor.flatten(value, new_key, separator).items()
                )
            else:
                items.append((new_key, value))

        return dict(items)

    @staticmethod
    def unflatten(flat_data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """
        평탄화된 딕셔너리를 중첩 구조로 복원

        Args:
            flat_data: 평탄화된 딕셔너리
            separator: 구분자

        Returns:
            중첩된 딕셔너리

        Example:
            >>> flat = {'a.b.c': 1, 'd': 2}
            >>> HierarchicalExtractor.unflatten(flat)
            {'a': {'b': {'c': 1}}, 'd': 2}
        """
        result: Dict[str, Any] = {}

        for key, value in flat_data.items():
            HierarchicalExtractor.set_by_path(result, key, value, separator)

        return result


class ChunkedJSONWriter:
    """
    청크 단위 JSON 작성기

    대용량 데이터를 메모리 효율적으로 JSON 파일로 작성합니다.
    """

    def __init__(self, file_path: Union[str, Path], indent: Optional[int] = 2):
        """
        Args:
            file_path: 출력 파일 경로
            indent: 들여쓰기 (None이면 압축)
        """
        self.file_path = Path(file_path)
        self.indent = indent
        self._file: Optional[TextIO] = None
        self._first_item = True

    def __enter__(self):
        self._file = open(self.file_path, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            self._file.close()

    def start_object(self) -> None:
        """객체 시작"""
        if self._file:
            self._file.write("{")
            if self.indent:
                self._file.write("\n")

    def end_object(self) -> None:
        """객체 종료"""
        if self._file:
            if self.indent:
                self._file.write("\n")
            self._file.write("}")

    def start_array(self, key: Optional[str] = None) -> None:
        """배열 시작"""
        if self._file:
            if key:
                self.write_key(key)
            self._file.write("[")
            if self.indent:
                self._file.write("\n")
            self._first_item = True

    def end_array(self) -> None:
        """배열 종료"""
        if self._file:
            if self.indent:
                self._file.write("\n")
            self._file.write("]")

    def write_key(self, key: str) -> None:
        """키 작성"""
        if self._file:
            if not self._first_item:
                self._file.write(",")
                if self.indent:
                    self._file.write("\n")

            if self.indent:
                self._file.write(" " * self.indent)
            self._file.write(f'"{key}": ')
            self._first_item = False

    def write_item(self, item: Any) -> None:
        """배열 아이템 작성"""
        if self._file:
            if not self._first_item:
                self._file.write(",")
                if self.indent:
                    self._file.write("\n")

            if self.indent:
                self._file.write(" " * self.indent)

            json.dump(item, self._file, ensure_ascii=False)
            self._first_item = False

    def write_field(self, key: str, value: Any) -> None:
        """필드 작성"""
        self.write_key(key)
        if self._file:
            json.dump(value, self._file, ensure_ascii=False, indent=self.indent)
