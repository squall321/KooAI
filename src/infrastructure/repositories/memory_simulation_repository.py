"""
In-Memory 시뮬레이션 결과 리포지토리

테스트 및 개발용 메모리 기반 리포지토리 구현.
"""

import uuid
from typing import Dict, List, Optional

from src.core.repositories.interfaces import SimulationResultRepository
from src.core.simulation.models import SimulationResult


class InMemorySimulationResultRepository(SimulationResultRepository):
    """
    메모리 기반 시뮬레이션 결과 리포지토리

    테스트 및 개발용. 데이터는 메모리에만 저장됩니다.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, SimulationResult] = {}
        self._name_index: Dict[str, str] = {}  # name -> id 매핑

    def add(self, result: SimulationResult) -> SimulationResult:
        """시뮬레이션 결과 저장"""
        # ID 생성 (없으면)
        if not hasattr(result, "id") or not result.id:
            result.id = str(uuid.uuid4())

        # 저장
        self._storage[result.id] = result
        self._name_index[result.name] = result.id

        return result

    def get_by_id(self, result_id: str) -> Optional[SimulationResult]:
        """ID로 조회"""
        return self._storage.get(result_id)

    def get_by_name(self, name: str) -> Optional[SimulationResult]:
        """이름으로 조회"""
        result_id = self._name_index.get(name)
        if result_id:
            return self._storage.get(result_id)
        return None

    def list_all(self, skip: int = 0, limit: int = 100) -> List[SimulationResult]:
        """모든 시뮬레이션 조회"""
        all_results = list(self._storage.values())
        return all_results[skip : skip + limit]

    def update(self, result: SimulationResult) -> SimulationResult:
        """시뮬레이션 업데이트"""
        if not hasattr(result, "id") or not result.id:
            raise ValueError("Cannot update result without ID")

        if result.id not in self._storage:
            raise KeyError(f"Result with ID {result.id} not found")

        # 이름이 변경되었으면 인덱스 업데이트
        old_result = self._storage[result.id]
        if old_result.name != result.name:
            # 이전 이름 제거
            if old_result.name in self._name_index:
                del self._name_index[old_result.name]
            # 새 이름 추가
            self._name_index[result.name] = result.id

        self._storage[result.id] = result
        return result

    def delete(self, result_id: str) -> bool:
        """시뮬레이션 삭제"""
        if result_id not in self._storage:
            return False

        result = self._storage[result_id]

        # 이름 인덱스에서 제거
        if result.name in self._name_index:
            del self._name_index[result.name]

        # 저장소에서 제거
        del self._storage[result_id]

        return True

    def exists(self, result_id: str) -> bool:
        """존재 여부 확인"""
        return result_id in self._storage

    def count(self) -> int:
        """전체 개수"""
        return len(self._storage)

    def clear(self) -> None:
        """모든 데이터 삭제 (테스트용)"""
        self._storage.clear()
        self._name_index.clear()
