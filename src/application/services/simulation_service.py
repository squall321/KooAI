"""
시뮬레이션 결과 처리 서비스

Use Cases를 조합하여 복잡한 시뮬레이션 처리 워크플로우 제공.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src.core.repositories.interfaces import SimulationResultRepository
from src.core.simulation import CSVParser, ParserRegistry, VTKParser

from ..use_cases import (
    AnalyzeFieldRequest,
    AnalyzeFieldResponse,
    AnalyzeFieldUseCase,
    CompareTimestepsRequest,
    CompareTimestepsResponse,
    CompareTimestepsUseCase,
    ComputeConvergenceRequest,
    ComputeConvergenceResponse,
    ComputeConvergenceUseCase,
    GetSimulationRequest,
    GetSimulationResponse,
    GetSimulationUseCase,
    ListSimulationsRequest,
    ListSimulationsResponse,
    ListSimulationsUseCase,
    SpatialAnalysisRequest,
    SpatialAnalysisResponse,
    SpatialAnalysisUseCase,
    UploadSimulationRequest,
    UploadSimulationResponse,
    UploadSimulationUseCase,
)


@dataclass
class FullAnalysisResult:
    """전체 분석 결과"""

    simulation_info: GetSimulationResponse
    field_analyses: Dict[str, AnalyzeFieldResponse]


class SimulationService:
    """
    시뮬레이션 결과 처리 서비스

    Use Cases를 조합하여 복잡한 워크플로우 제공.
    """

    def __init__(self, repository: SimulationResultRepository):
        self.repository = repository

        # Parser Registry 설정
        self.parser_registry = ParserRegistry()
        self.parser_registry.register(CSVParser())
        self.parser_registry.register(VTKParser())

        # Use Cases 초기화
        self.upload_use_case = UploadSimulationUseCase(
            self.parser_registry, repository
        )
        self.get_use_case = GetSimulationUseCase(repository)
        self.analyze_field_use_case = AnalyzeFieldUseCase(repository)
        self.compare_timesteps_use_case = CompareTimestepsUseCase(repository)
        self.compute_convergence_use_case = ComputeConvergenceUseCase(repository)
        self.spatial_analysis_use_case = SpatialAnalysisUseCase(repository)
        self.list_use_case = ListSimulationsUseCase(repository)

    def upload_and_analyze(
        self,
        file_path: Path,
        name: Optional[str] = None,
        analyze_all_fields: bool = True,
    ) -> FullAnalysisResult:
        """
        시뮬레이션 업로드 및 전체 분석

        파일을 업로드하고 모든 필드에 대해 자동 분석 수행.

        Args:
            file_path: 시뮬레이션 파일 경로
            name: 시뮬레이션 이름 (기본: 파일명)
            analyze_all_fields: 모든 필드 분석 여부

        Returns:
            FullAnalysisResult: 업로드 및 분석 결과
        """
        # 1. 업로드
        upload_response = self.upload_use_case.execute(
            UploadSimulationRequest(file_path=file_path, name=name)
        )

        # 2. 시뮬레이션 정보 조회
        sim_info = self.get_use_case.execute(
            GetSimulationRequest(simulation_id=upload_response.simulation_id)
        )

        # 3. 필드 분석
        field_analyses = {}

        if analyze_all_fields and upload_response.fields:
            for field_name in upload_response.fields:
                # 첫 번째 타임스텝 분석
                analysis = self.analyze_field_use_case.execute(
                    AnalyzeFieldRequest(
                        simulation_id=upload_response.simulation_id,
                        timestep=0,
                        field_name=field_name,
                        compute_extremes=True,
                        detect_outliers=True,
                        compute_histogram=True,
                    )
                )
                field_analyses[field_name] = analysis

        return FullAnalysisResult(
            simulation_info=sim_info, field_analyses=field_analyses
        )

    def compare_all_timesteps(
        self, simulation_id: str, field_name: str
    ) -> List[CompareTimestepsResponse]:
        """
        모든 연속 타임스텝 비교

        Args:
            simulation_id: 시뮬레이션 ID
            field_name: 필드 이름

        Returns:
            List[CompareTimestepsResponse]: 타임스텝 비교 결과 목록
        """
        # 시뮬레이션 정보 조회
        sim_info = self.get_use_case.execute(
            GetSimulationRequest(simulation_id=simulation_id)
        )

        if sim_info.num_timesteps < 2:
            return []

        # 연속 타임스텝 비교
        comparisons = []

        for i in range(sim_info.num_timesteps - 1):
            comparison = self.compare_timesteps_use_case.execute(
                CompareTimestepsRequest(
                    simulation_id=simulation_id,
                    timestep1=i,
                    timestep2=i + 1,
                    field_name=field_name,
                )
            )
            comparisons.append(comparison)

        return comparisons

    def analyze_convergence(
        self, simulation_id: str, field_names: Optional[List[str]] = None
    ) -> Dict[str, ComputeConvergenceResponse]:
        """
        수렴성 분석 (모든 필드 또는 지정 필드)

        Args:
            simulation_id: 시뮬레이션 ID
            field_names: 분석할 필드 목록 (None이면 모든 필드)

        Returns:
            Dict[str, ComputeConvergenceResponse]: 필드별 수렴성 분석 결과
        """
        # 시뮬레이션 정보 조회
        sim_info = self.get_use_case.execute(
            GetSimulationRequest(simulation_id=simulation_id)
        )

        # 필드 목록 결정
        if field_names is None:
            field_names = sim_info.fields

        # 각 필드에 대해 수렴성 분석
        convergence_results = {}

        for field_name in field_names:
            try:
                result = self.compute_convergence_use_case.execute(
                    ComputeConvergenceRequest(
                        simulation_id=simulation_id, field_name=field_name
                    )
                )
                convergence_results[field_name] = result
            except Exception:
                # 필드가 없거나 오류 발생시 건너뜀
                continue

        return convergence_results

    def find_critical_regions(
        self,
        simulation_id: str,
        timestep: int,
        field_name: str,
        percentile: float = 95.0,
    ) -> tuple[SpatialAnalysisResponse, SpatialAnalysisResponse]:
        """
        임계 영역 찾기 (고/저 영역)

        Args:
            simulation_id: 시뮬레이션 ID
            timestep: 타임스텝
            field_name: 필드 이름
            percentile: 백분위수 (기본: 95%)

        Returns:
            tuple: (고영역 분석 결과, 저영역 분석 결과)
        """
        # 필드 분석하여 통계 얻기
        field_analysis = self.analyze_field_use_case.execute(
            AnalyzeFieldRequest(
                simulation_id=simulation_id,
                timestep=timestep,
                field_name=field_name,
            )
        )

        # 임계값 계산
        stats = field_analysis.statistics

        # percentile 키가 없으면 기본값 사용
        high_threshold = stats.get(f"percentile_{int(percentile)}", stats["max"])
        low_threshold = stats.get(f"percentile_{int(100-percentile)}", stats["min"])

        # 고영역 분석
        high_region = self.spatial_analysis_use_case.execute(
            SpatialAnalysisRequest(
                simulation_id=simulation_id,
                timestep=timestep,
                field_name=field_name,
                min_value=high_threshold,
            )
        )

        # 저영역 분석
        low_region = self.spatial_analysis_use_case.execute(
            SpatialAnalysisRequest(
                simulation_id=simulation_id,
                timestep=timestep,
                field_name=field_name,
                max_value=low_threshold,
            )
        )

        return high_region, low_region

    def list_simulations(
        self, page: int = 1, page_size: int = 20
    ) -> ListSimulationsResponse:
        """
        시뮬레이션 목록 조회 (페이지네이션)

        Args:
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기

        Returns:
            ListSimulationsResponse: 시뮬레이션 목록
        """
        skip = (page - 1) * page_size

        return self.list_use_case.execute(
            ListSimulationsRequest(skip=skip, limit=page_size)
        )

    def get_simulation_summary(self, simulation_id: str) -> Dict:
        """
        시뮬레이션 요약 정보

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            Dict: 요약 정보
        """
        sim_info = self.get_use_case.execute(
            GetSimulationRequest(simulation_id=simulation_id)
        )

        # 첫 번째 타임스텝의 각 필드에 대한 기본 통계
        field_summaries = {}

        for field_name in sim_info.fields:
            try:
                analysis = self.analyze_field_use_case.execute(
                    AnalyzeFieldRequest(
                        simulation_id=simulation_id,
                        timestep=0,
                        field_name=field_name,
                    )
                )
                field_summaries[field_name] = {
                    "type": analysis.field_type,
                    "min": analysis.statistics["min"],
                    "max": analysis.statistics["max"],
                    "mean": analysis.statistics["mean"],
                }
            except Exception:
                continue

        return {
            "id": sim_info.simulation_id,
            "name": sim_info.name,
            "type": sim_info.simulation_type,
            "num_vertices": sim_info.num_vertices,
            "num_timesteps": sim_info.num_timesteps,
            "time_range": sim_info.time_range,
            "fields": field_summaries,
            "metadata": sim_info.metadata,
        }
