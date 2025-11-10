"""
도메인 엔티티 단위 테스트
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from src.core.domain.entities import (
    SimulationResult,
    SimulationStatus,
    Dataset,
    Analysis,
    AnalysisStatus,
    AIModel,
)


class TestSimulationResult:
    """SimulationResult 엔티티 테스트"""

    def test_create_simulation(self) -> None:
        """시뮬레이션 생성 테스트"""
        sim = SimulationResult(
            name="Test Simulation",
            type="CFD",
            parameters={"mesh_size": 1000, "time_steps": 100},
        )

        assert sim.name == "Test Simulation"
        assert sim.type == "CFD"
        assert sim.status == SimulationStatus.PENDING
        assert isinstance(sim.id, UUID)
        assert sim.parameters["mesh_size"] == 1000
        assert isinstance(sim.created_at, datetime)
        assert isinstance(sim.updated_at, datetime)

    def test_create_with_empty_name_raises_error(self) -> None:
        """빈 이름으로 생성 시 에러"""
        with pytest.raises(ValueError, match="name cannot be empty"):
            SimulationResult(name="", type="CFD")

    def test_create_with_empty_type_raises_error(self) -> None:
        """빈 타입으로 생성 시 에러"""
        with pytest.raises(ValueError, match="type cannot be empty"):
            SimulationResult(name="Test", type="")

    def test_create_with_too_long_name_raises_error(self) -> None:
        """너무 긴 이름으로 생성 시 에러"""
        long_name = "x" * 256
        with pytest.raises(ValueError, match="name too long"):
            SimulationResult(name=long_name, type="CFD")

    def test_mark_as_processing(self) -> None:
        """처리 중으로 표시 테스트"""
        sim = SimulationResult(name="Test", type="CFD")
        original_updated_at = sim.updated_at

        sim.mark_as_processing()

        assert sim.status == SimulationStatus.PROCESSING
        assert sim.updated_at > original_updated_at

    def test_mark_as_processing_from_wrong_status_raises_error(self) -> None:
        """잘못된 상태에서 처리 중으로 표시 시 에러"""
        sim = SimulationResult(name="Test", type="CFD")
        sim.mark_as_processing()

        with pytest.raises(ValueError, match="Cannot mark as processing"):
            sim.mark_as_processing()

    def test_mark_as_completed(self) -> None:
        """완료로 표시 테스트"""
        sim = SimulationResult(name="Test", type="CFD")
        sim.mark_as_processing()
        original_updated_at = sim.updated_at

        sim.mark_as_completed()

        assert sim.status == SimulationStatus.COMPLETED
        assert sim.updated_at > original_updated_at
        assert sim.is_completed()
        assert sim.can_be_analyzed()

    def test_mark_as_completed_from_wrong_status_raises_error(self) -> None:
        """잘못된 상태에서 완료로 표시 시 에러"""
        sim = SimulationResult(name="Test", type="CFD")

        with pytest.raises(ValueError, match="Cannot mark as completed"):
            sim.mark_as_completed()

    def test_mark_as_failed(self) -> None:
        """실패로 표시 테스트"""
        sim = SimulationResult(name="Test", type="CFD")
        error_msg = "Out of memory"

        sim.mark_as_failed(error_msg)

        assert sim.status == SimulationStatus.FAILED
        assert sim.is_failed()
        assert sim.metadata["error"] == error_msg
        assert "failed_at" in sim.metadata

    def test_cancel(self) -> None:
        """취소 테스트"""
        sim = SimulationResult(name="Test", type="CFD")

        sim.cancel()

        assert sim.status == SimulationStatus.CANCELLED

    def test_cancel_completed_simulation_raises_error(self) -> None:
        """완료된 시뮬레이션 취소 시 에러"""
        sim = SimulationResult(name="Test", type="CFD")
        sim.mark_as_processing()
        sim.mark_as_completed()

        with pytest.raises(ValueError, match="Cannot cancel"):
            sim.cancel()

    def test_add_tag(self) -> None:
        """태그 추가 테스트"""
        sim = SimulationResult(name="Test", type="CFD")

        sim.add_tag("important")
        sim.add_tag("production")

        assert "important" in sim.tags
        assert "production" in sim.tags
        assert len(sim.tags) == 2

    def test_add_duplicate_tag(self) -> None:
        """중복 태그 추가 테스트"""
        sim = SimulationResult(name="Test", type="CFD")

        sim.add_tag("important")
        sim.add_tag("important")

        assert len(sim.tags) == 1

    def test_remove_tag(self) -> None:
        """태그 제거 테스트"""
        sim = SimulationResult(name="Test", type="CFD", tags=["tag1", "tag2"])

        sim.remove_tag("tag1")

        assert "tag1" not in sim.tags
        assert "tag2" in sim.tags

    def test_update_metadata(self) -> None:
        """메타데이터 업데이트 테스트"""
        sim = SimulationResult(name="Test", type="CFD")

        sim.update_metadata("solver", "SIMPLE")
        sim.update_metadata("convergence", 0.001)

        assert sim.metadata["solver"] == "SIMPLE"
        assert sim.metadata["convergence"] == 0.001


class TestDataset:
    """Dataset 엔티티 테스트"""

    def test_create_dataset(self) -> None:
        """데이터셋 생성 테스트"""
        from uuid import uuid4

        sim_id = uuid4()
        dataset = Dataset(
            simulation_id=sim_id,
            data_type="mesh",
            data_format="vtk",
            storage_path="/data/simulation-123/mesh.vtk",
            size_bytes=1024000,
        )

        assert dataset.simulation_id == sim_id
        assert dataset.data_type == "mesh"
        assert dataset.data_format == "vtk"
        assert dataset.size_bytes == 1024000
        assert isinstance(dataset.id, UUID)

    def test_create_with_empty_data_type_raises_error(self) -> None:
        """빈 데이터 타입으로 생성 시 에러"""
        from uuid import uuid4

        with pytest.raises(ValueError, match="Data type cannot be empty"):
            Dataset(
                simulation_id=uuid4(),
                data_type="",
                data_format="vtk",
                storage_path="/data/test",
            )

    def test_create_with_negative_size_raises_error(self) -> None:
        """음수 크기로 생성 시 에러"""
        from uuid import uuid4

        with pytest.raises(ValueError, match="Size cannot be negative"):
            Dataset(
                simulation_id=uuid4(),
                data_type="mesh",
                data_format="vtk",
                storage_path="/data/test",
                size_bytes=-100,
            )

    def test_update_checksum(self) -> None:
        """체크섬 업데이트 테스트"""
        from uuid import uuid4

        dataset = Dataset(
            simulation_id=uuid4(),
            data_type="mesh",
            data_format="vtk",
            storage_path="/data/test",
        )

        dataset.update_checksum("abc123")

        assert dataset.checksum == "abc123"

    def test_update_size(self) -> None:
        """크기 업데이트 테스트"""
        from uuid import uuid4

        dataset = Dataset(
            simulation_id=uuid4(),
            data_type="mesh",
            data_format="vtk",
            storage_path="/data/test",
        )

        dataset.update_size(2048)

        assert dataset.size_bytes == 2048


class TestAnalysis:
    """Analysis 엔티티 테스트"""

    def test_create_analysis(self) -> None:
        """분석 작업 생성 테스트"""
        from uuid import uuid4

        sim_id = uuid4()
        analysis = Analysis(
            simulation_id=sim_id,
            analysis_type="statistical",
            input_parameters={"method": "t-test", "alpha": 0.05},
        )

        assert analysis.simulation_id == sim_id
        assert analysis.analysis_type == "statistical"
        assert analysis.status == AnalysisStatus.PENDING
        assert isinstance(analysis.id, UUID)

    def test_start_analysis(self) -> None:
        """분석 시작 테스트"""
        from uuid import uuid4

        analysis = Analysis(simulation_id=uuid4(), analysis_type="statistical")

        analysis.start()

        assert analysis.status == AnalysisStatus.RUNNING
        assert isinstance(analysis.started_at, datetime)

    def test_start_running_analysis_raises_error(self) -> None:
        """이미 실행 중인 분석 시작 시 에러"""
        from uuid import uuid4

        analysis = Analysis(simulation_id=uuid4(), analysis_type="statistical")
        analysis.start()

        with pytest.raises(ValueError, match="Cannot start"):
            analysis.start()

    def test_complete_analysis(self) -> None:
        """분석 완료 테스트"""
        from uuid import uuid4

        analysis = Analysis(simulation_id=uuid4(), analysis_type="statistical")
        analysis.start()

        results = {"mean": 10.5, "std": 2.3}
        analysis.complete(results)

        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.results == results
        assert isinstance(analysis.completed_at, datetime)

    def test_complete_pending_analysis_raises_error(self) -> None:
        """대기 중인 분석 완료 시 에러"""
        from uuid import uuid4

        analysis = Analysis(simulation_id=uuid4(), analysis_type="statistical")

        with pytest.raises(ValueError, match="Cannot complete"):
            analysis.complete({})

    def test_fail_analysis(self) -> None:
        """분석 실패 테스트"""
        from uuid import uuid4

        analysis = Analysis(simulation_id=uuid4(), analysis_type="statistical")
        analysis.start()

        error_msg = "Insufficient data"
        analysis.fail(error_msg)

        assert analysis.status == AnalysisStatus.FAILED
        assert analysis.results["error"] == error_msg

    def test_get_duration_seconds(self) -> None:
        """분석 소요 시간 계산 테스트"""
        from uuid import uuid4

        analysis = Analysis(simulation_id=uuid4(), analysis_type="statistical")

        # 시작 전
        assert analysis.get_duration_seconds() is None

        # 시작
        analysis.start()
        assert analysis.get_duration_seconds() is None

        # 완료
        analysis.complete({"result": "success"})
        duration = analysis.get_duration_seconds()

        assert duration is not None
        assert duration >= 0


class TestAIModel:
    """AIModel 엔티티 테스트"""

    def test_create_ai_model(self) -> None:
        """AI 모델 생성 테스트"""
        model = AIModel(
            name="ContourVAE",
            version="1.0.0",
            model_type="vae",
            architecture={"latent_dim": 16, "hidden_dims": [128, 64, 32]},
        )

        assert model.name == "ContourVAE"
        assert model.version == "1.0.0"
        assert model.model_type == "vae"
        assert isinstance(model.id, UUID)

    def test_create_with_empty_name_raises_error(self) -> None:
        """빈 이름으로 생성 시 에러"""
        with pytest.raises(ValueError, match="name cannot be empty"):
            AIModel(name="", version="1.0.0", model_type="vae")

    def test_update_performance_metrics(self) -> None:
        """성능 메트릭 업데이트 테스트"""
        model = AIModel(name="TestModel", version="1.0", model_type="vae")

        model.update_performance_metrics({"loss": 0.05, "accuracy": 0.95})

        assert model.get_metric("loss") == 0.05
        assert model.get_metric("accuracy") == 0.95

    def test_get_full_name(self) -> None:
        """전체 모델 이름 조회 테스트"""
        model = AIModel(name="ContourVAE", version="2.1.0", model_type="vae")

        assert model.get_full_name() == "ContourVAE:2.1.0"
