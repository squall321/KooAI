"""
데이터 타입 팩토리

Factory 패턴을 사용하여 다양한 데이터 타입을 생성합니다.
"""

from typing import Dict, Any, Type, Optional
from src.core.data_types.base import IDataType
from src.core.data_types.contour import ContourData
from src.core.data_types.mesh import MeshData
from src.core.data_types.curve import CurveData


class DataTypeFactory:
    """
    데이터 타입 팩토리

    등록된 데이터 타입을 생성하고 관리합니다.
    """

    _registry: Dict[str, Type[IDataType]] = {}

    @classmethod
    def register(cls, data_type: str, data_class: Type[IDataType]) -> None:
        """
        데이터 타입 등록

        Args:
            data_type: 데이터 타입 식별자
            data_class: 데이터 클래스

        Raises:
            ValueError: 이미 등록된 타입인 경우
        """
        if data_type in cls._registry:
            raise ValueError(f"Data type '{data_type}' is already registered")

        cls._registry[data_type] = data_class

    @classmethod
    def unregister(cls, data_type: str) -> None:
        """
        데이터 타입 등록 해제

        Args:
            data_type: 데이터 타입 식별자
        """
        if data_type in cls._registry:
            del cls._registry[data_type]

    @classmethod
    def create(cls, data_type: str, data: Dict[str, Any]) -> IDataType:
        """
        데이터 타입 객체 생성

        Args:
            data_type: 데이터 타입 식별자
            data: 직렬화된 데이터

        Returns:
            IDataType: 생성된 데이터 객체

        Raises:
            ValueError: 등록되지 않은 타입인 경우
        """
        if data_type not in cls._registry:
            raise ValueError(
                f"Unknown data type: '{data_type}'. "
                f"Available types: {list(cls._registry.keys())}"
            )

        data_class = cls._registry[data_type]
        return data_class.deserialize(data)

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """
        등록된 데이터 타입 목록

        Returns:
            list: 데이터 타입 식별자 목록
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, data_type: str) -> bool:
        """
        데이터 타입 등록 여부 확인

        Args:
            data_type: 데이터 타입 식별자

        Returns:
            bool: 등록되어 있으면 True
        """
        return data_type in cls._registry


# 기본 데이터 타입 등록
DataTypeFactory.register("contour", ContourData)
DataTypeFactory.register("mesh", MeshData)
DataTypeFactory.register("curve", CurveData)
