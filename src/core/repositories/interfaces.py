"""
Repository 인터페이스

데이터 접근을 추상화하는 Repository 인터페이스들을 정의합니다.
"""

from typing import Protocol, Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from src.core.domain.entities import (
    SimulationResult as DomainSimulationResult,
    Dataset,
    Analysis,
    AIModel,
    SimulationStatus,
    AnalysisStatus,
)

# Import for new simulation system
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.simulation.models import SimulationResult


class ISimulationRepository(Protocol):
    """
    시뮬레이션 리포지토리 인터페이스

    시뮬레이션 결과 데이터의 영속성을 관리합니다.
    (도메인 엔티티용 - 레거시)
    """

    async def save(self, simulation: DomainSimulationResult) -> UUID:
        """
        시뮬레이션 저장

        Args:
            simulation: 저장할 시뮬레이션

        Returns:
            UUID: 저장된 시뮬레이션 ID
        """
        ...

    async def find_by_id(self, simulation_id: UUID) -> Optional[DomainSimulationResult]:
        """
        ID로 시뮬레이션 조회

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            Optional[DomainSimulationResult]: 시뮬레이션 또는 None
        """
        ...

    async def find_by_name(self, name: str) -> List[DomainSimulationResult]:
        """
        이름으로 시뮬레이션 조회

        Args:
            name: 시뮬레이션 이름

        Returns:
            List[DomainSimulationResult]: 시뮬레이션 목록
        """
        ...

    async def find_by_status(self, status: SimulationStatus) -> List[DomainSimulationResult]:
        """
        상태로 시뮬레이션 조회

        Args:
            status: 시뮬레이션 상태

        Returns:
            List[DomainSimulationResult]: 시뮬레이션 목록
        """
        ...

    async def find_by_type(self, sim_type: str) -> List[DomainSimulationResult]:
        """
        타입으로 시뮬레이션 조회

        Args:
            sim_type: 시뮬레이션 타입

        Returns:
            List[DomainSimulationResult]: 시뮬레이션 목록
        """
        ...

    async def find_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> List[DomainSimulationResult]:
        """
        복합 조건으로 시뮬레이션 조회

        Args:
            criteria: 검색 조건 딕셔너리
            limit: 최대 결과 수
            offset: 오프셋

        Returns:
            List[DomainSimulationResult]: 시뮬레이션 목록
        """
        ...

    async def update(self, simulation: DomainSimulationResult) -> None:
        """
        시뮬레이션 업데이트

        Args:
            simulation: 업데이트할 시뮬레이션
        """
        ...

    async def delete(self, simulation_id: UUID) -> None:
        """
        시뮬레이션 삭제

        Args:
            simulation_id: 삭제할 시뮬레이션 ID
        """
        ...

    async def exists(self, simulation_id: UUID) -> bool:
        """
        시뮬레이션 존재 여부 확인

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            bool: 존재하면 True
        """
        ...

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        시뮬레이션 개수 조회

        Args:
            criteria: 검색 조건 (선택)

        Returns:
            int: 시뮬레이션 개수
        """
        ...


class IDatasetRepository(Protocol):
    """
    데이터셋 리포지토리 인터페이스

    시뮬레이션 데이터셋의 영속성을 관리합니다.
    """

    async def save(self, dataset: Dataset) -> UUID:
        """데이터셋 저장"""
        ...

    async def find_by_id(self, dataset_id: UUID) -> Optional[Dataset]:
        """ID로 데이터셋 조회"""
        ...

    async def find_by_simulation_id(self, simulation_id: UUID) -> List[Dataset]:
        """시뮬레이션 ID로 데이터셋 조회"""
        ...

    async def find_by_data_type(self, data_type: str) -> List[Dataset]:
        """데이터 타입으로 조회"""
        ...

    async def update(self, dataset: Dataset) -> None:
        """데이터셋 업데이트"""
        ...

    async def delete(self, dataset_id: UUID) -> None:
        """데이터셋 삭제"""
        ...


class IAnalysisRepository(Protocol):
    """
    분석 리포지토리 인터페이스

    분석 작업의 영속성을 관리합니다.
    """

    async def save(self, analysis: Analysis) -> UUID:
        """분석 저장"""
        ...

    async def find_by_id(self, analysis_id: UUID) -> Optional[Analysis]:
        """ID로 분석 조회"""
        ...

    async def find_by_simulation_id(self, simulation_id: UUID) -> List[Analysis]:
        """시뮬레이션 ID로 분석 조회"""
        ...

    async def find_by_status(self, status: AnalysisStatus) -> List[Analysis]:
        """상태로 분석 조회"""
        ...

    async def find_pending(self, limit: int = 10) -> List[Analysis]:
        """대기 중인 분석 조회"""
        ...

    async def update(self, analysis: Analysis) -> None:
        """분석 업데이트"""
        ...

    async def delete(self, analysis_id: UUID) -> None:
        """분석 삭제"""
        ...


class IAIModelRepository(Protocol):
    """
    AI 모델 리포지토리 인터페이스

    AI 모델 메타데이터의 영속성을 관리합니다.
    """

    async def save(self, model: AIModel) -> UUID:
        """모델 저장"""
        ...

    async def find_by_id(self, model_id: UUID) -> Optional[AIModel]:
        """ID로 모델 조회"""
        ...

    async def find_by_name(self, name: str) -> List[AIModel]:
        """이름으로 모델 조회"""
        ...

    async def find_by_name_and_version(
        self, name: str, version: str
    ) -> Optional[AIModel]:
        """이름과 버전으로 모델 조회"""
        ...

    async def find_by_type(self, model_type: str) -> List[AIModel]:
        """타입으로 모델 조회"""
        ...

    async def find_latest_by_name(self, name: str) -> Optional[AIModel]:
        """이름으로 최신 모델 조회"""
        ...

    async def update(self, model: AIModel) -> None:
        """모델 업데이트"""
        ...

    async def delete(self, model_id: UUID) -> None:
        """모델 삭제"""
        ...


class SimulationResultRepository(Protocol):
    """
    시뮬레이션 결과 리포지토리 인터페이스
    
    시뮬레이션 파싱 결과(Phase 13)의 영속성을 관리합니다.
    """
    
    def add(self, result: "SimulationResult") -> "SimulationResult":
        """
        시뮬레이션 결과 저장
        
        Args:
            result: 저장할 시뮬레이션 결과
            
        Returns:
            SimulationResult: 저장된 결과 (ID 포함)
        """
        ...
    
    def get_by_id(self, result_id: str) -> Optional["SimulationResult"]:
        """
        ID로 시뮬레이션 결과 조회
        
        Args:
            result_id: 시뮬레이션 결과 ID
            
        Returns:
            Optional[SimulationResult]: 시뮬레이션 결과 또는 None
        """
        ...
    
    def get_by_name(self, name: str) -> Optional["SimulationResult"]:
        """
        이름으로 시뮬레이션 결과 조회
        
        Args:
            name: 시뮬레이션 이름
            
        Returns:
            Optional[SimulationResult]: 시뮬레이션 결과 또는 None
        """
        ...
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List["SimulationResult"]:
        """
        모든 시뮬레이션 결과 조회
        
        Args:
            skip: 건너뛸 개수
            limit: 최대 결과 수
            
        Returns:
            List[SimulationResult]: 시뮬레이션 결과 목록
        """
        ...
    
    def update(self, result: "SimulationResult") -> "SimulationResult":
        """
        시뮬레이션 결과 업데이트
        
        Args:
            result: 업데이트할 시뮬레이션 결과
            
        Returns:
            SimulationResult: 업데이트된 결과
        """
        ...
    
    def delete(self, result_id: str) -> bool:
        """
        시뮬레이션 결과 삭제
        
        Args:
            result_id: 삭제할 시뮬레이션 결과 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        ...
    
    def exists(self, result_id: str) -> bool:
        """
        시뮬레이션 결과 존재 여부 확인
        
        Args:
            result_id: 시뮬레이션 결과 ID
            
        Returns:
            bool: 존재하면 True
        """
        ...
    
    def count(self) -> int:
        """
        저장된 시뮬레이션 결과 개수
        
        Returns:
            int: 시뮬레이션 결과 개수
        """
        ...
