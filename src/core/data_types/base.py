"""
데이터 타입 기본 인터페이스

모든 데이터 타입이 구현해야 하는 프로토콜과 기본 클래스를 정의합니다.
"""

from typing import Protocol, Self, Dict, Any
from abc import abstractmethod
import numpy as np


class IDataType(Protocol):
    """
    모든 데이터 타입의 기본 인터페이스

    다양한 데이터 형식(메시, 커브, 컨투어 등)을 통합적으로 처리하기 위한
    공통 인터페이스를 정의합니다.
    """

    @abstractmethod
    def validate(self) -> bool:
        """
        데이터 유효성 검증

        Returns:
            bool: 유효하면 True, 그렇지 않으면 False

        Raises:
            ValueError: 데이터가 유효하지 않은 경우
        """
        ...

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """
        객체를 딕셔너리로 직렬화

        Returns:
            Dict[str, Any]: 직렬화된 데이터
        """
        ...

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> Self:
        """
        딕셔너리로부터 객체 생성 (역직렬화)

        Args:
            data: 직렬화된 데이터

        Returns:
            Self: 생성된 객체
        """
        ...

    @abstractmethod
    def compress(self, method: str = "default") -> bytes:
        """
        데이터 압축

        Args:
            method: 압축 방법 (default, gzip, lz4, vae 등)

        Returns:
            bytes: 압축된 데이터
        """
        ...

    @classmethod
    @abstractmethod
    def decompress(cls, data: bytes, method: str = "default") -> Self:
        """
        압축 해제

        Args:
            data: 압축된 데이터
            method: 압축 방법

        Returns:
            Self: 압축 해제된 객체
        """
        ...

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        메타데이터 추출

        Returns:
            Dict[str, Any]: 메타데이터 (크기, 타입, 경계 등)
        """
        ...

    @abstractmethod
    def get_size_bytes(self) -> int:
        """
        데이터 크기 (바이트)

        Returns:
            int: 바이트 단위 크기
        """
        ...


class ITransformation(Protocol):
    """
    데이터 변환 인터페이스

    데이터에 적용할 수 있는 변환(회전, 이동, 스케일링 등)을 정의합니다.
    """

    @abstractmethod
    def apply(self, data: IDataType) -> IDataType:
        """
        변환 적용

        Args:
            data: 변환할 데이터

        Returns:
            IDataType: 변환된 데이터
        """
        ...

    @abstractmethod
    def inverse(self) -> "ITransformation":
        """
        역변환 생성

        Returns:
            ITransformation: 역변환
        """
        ...


class ISerializer(Protocol):
    """
    직렬화 인터페이스

    다양한 형식으로 데이터를 저장하고 불러옵니다.
    """

    @abstractmethod
    def save(self, data: IDataType, path: str) -> None:
        """
        파일로 저장

        Args:
            data: 저장할 데이터
            path: 파일 경로
        """
        ...

    @abstractmethod
    def load(self, path: str) -> IDataType:
        """
        파일에서 로드

        Args:
            path: 파일 경로

        Returns:
            IDataType: 로드된 데이터
        """
        ...


class BaseDataType:
    """
    데이터 타입 기본 클래스

    공통 기능을 제공하는 추상 기본 클래스입니다.
    """

    def __init__(self, data_type: str):
        """
        Args:
            data_type: 데이터 타입 식별자
        """
        self.data_type = data_type
        self._metadata: Dict[str, Any] = {}

    def validate(self) -> bool:
        """기본 검증 - 서브클래스에서 오버라이드"""
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        메타데이터 반환

        Returns:
            Dict[str, Any]: 메타데이터
        """
        return {
            "data_type": self.data_type,
            "size_bytes": self.get_size_bytes(),
            **self._metadata,
        }

    def set_metadata(self, key: str, value: Any) -> None:
        """
        메타데이터 설정

        Args:
            key: 메타데이터 키
            value: 메타데이터 값
        """
        self._metadata[key] = value

    def get_size_bytes(self) -> int:
        """
        기본 크기 계산 - 서브클래스에서 오버라이드

        Returns:
            int: 바이트 단위 크기
        """
        return 0

    def __repr__(self) -> str:
        """문자열 표현"""
        return f"{self.__class__.__name__}(type={self.data_type})"


class CompressionStrategy:
    """
    압축 전략 기본 클래스

    Strategy 패턴을 사용하여 다양한 압축 알고리즘을 교체 가능하게 합니다.
    """

    def compress(self, data: np.ndarray) -> bytes:
        """
        데이터 압축

        Args:
            data: 압축할 NumPy 배열

        Returns:
            bytes: 압축된 데이터
        """
        raise NotImplementedError

    def decompress(self, compressed: bytes) -> np.ndarray:
        """
        데이터 압축 해제

        Args:
            compressed: 압축된 데이터

        Returns:
            np.ndarray: 압축 해제된 배열
        """
        raise NotImplementedError


class DefaultCompressionStrategy(CompressionStrategy):
    """
    기본 압축 전략 (pickle 사용)
    """

    def compress(self, data: np.ndarray) -> bytes:
        """NumPy 배열을 바이트로 직렬화"""
        import pickle

        return pickle.dumps(data)

    def decompress(self, compressed: bytes) -> np.ndarray:
        """바이트를 NumPy 배열로 역직렬화"""
        import pickle

        return pickle.loads(compressed)


class GzipCompressionStrategy(CompressionStrategy):
    """
    Gzip 압축 전략
    """

    def compress(self, data: np.ndarray) -> bytes:
        """Gzip으로 압축"""
        import gzip
        import pickle

        serialized = pickle.dumps(data)
        return gzip.compress(serialized)

    def decompress(self, compressed: bytes) -> np.ndarray:
        """Gzip 압축 해제"""
        import gzip
        import pickle

        decompressed = gzip.decompress(compressed)
        return pickle.loads(decompressed)


def get_compression_strategy(method: str) -> CompressionStrategy:
    """
    압축 전략 팩토리

    Args:
        method: 압축 방법 (default, gzip)

    Returns:
        CompressionStrategy: 압축 전략 객체

    Raises:
        ValueError: 지원하지 않는 압축 방법
    """
    strategies = {
        "default": DefaultCompressionStrategy(),
        "gzip": GzipCompressionStrategy(),
    }

    if method not in strategies:
        raise ValueError(
            f"Unsupported compression method: {method}. " f"Available: {list(strategies.keys())}"
        )

    return strategies[method]
