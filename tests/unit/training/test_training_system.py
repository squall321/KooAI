"""Transfer Learning & Fine-tuning 시스템 통합 테스트"""

import tempfile
from pathlib import Path

import pytest

from src.core.training import (
    CheckpointManager,
    DataConfig,
    FinetuneConfig,
    LossType,
    MetricsTracker,
    ModelSource,
    OptimizerConfig,
    OptimizerType,
    PretrainedModelManager,
    SchedulerConfig,
    SchedulerType,
    TrainingConfig,
)


class TestPretrainedModelManager:
    """사전 학습 모델 관리자 테스트"""

    def test_register_model(self) -> None:
        """모델 등록 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PretrainedModelManager(cache_dir=Path(tmpdir))

            info = manager.register_model(
                name="test_model",
                source=ModelSource.LOCAL,
                model_id="test_id",
                framework="pytorch",
                task="classification",
            )

            assert info.name == "test_model"
            assert info.source == ModelSource.LOCAL
            assert info.framework == "pytorch"

    def test_get_model(self) -> None:
        """모델 조회 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PretrainedModelManager(cache_dir=Path(tmpdir))

            manager.register_model(name="model1", source=ModelSource.LOCAL, model_id="id1")

            info = manager.get_model("model1")
            assert info is not None
            assert info.name == "model1"

            # 존재하지 않는 모델
            assert manager.get_model("nonexistent") is None

    def test_list_models(self) -> None:
        """모델 목록 조회 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PretrainedModelManager(cache_dir=Path(tmpdir))

            manager.register_model(
                name="model1",
                source=ModelSource.HUGGINGFACE,
                model_id="id1",
                framework="pytorch",
            )
            manager.register_model(
                name="model2",
                source=ModelSource.LOCAL,
                model_id="id2",
                framework="tensorflow",
            )

            # 전체 조회
            all_models = manager.list_models()
            assert len(all_models) == 2

            # 소스별 필터
            hf_models = manager.list_models(source=ModelSource.HUGGINGFACE)
            assert len(hf_models) == 1
            assert hf_models[0].name == "model1"

            # 프레임워크별 필터
            tf_models = manager.list_models(framework="tensorflow")
            assert len(tf_models) == 1
            assert tf_models[0].name == "model2"


class TestFinetuneConfig:
    """Fine-tuning 설정 테스트"""

    def test_default_config(self) -> None:
        """기본 설정 생성 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = FinetuneConfig(model_name="test_model", output_dir=Path(tmpdir) / "outputs")

            assert config.model_name == "test_model"
            assert config.optimizer.type == OptimizerType.ADAMW
            assert config.scheduler.type == SchedulerType.LINEAR
            assert config.training.num_epochs == 10

    def test_custom_config(self) -> None:
        """커스텀 설정 생성 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = OptimizerConfig(type=OptimizerType.SGD, learning_rate=0.01, momentum=0.9)

            scheduler = SchedulerConfig(type=SchedulerType.COSINE, warmup_steps=100)

            data = DataConfig(train_batch_size=64, eval_batch_size=128)

            training = TrainingConfig(num_epochs=20, logging_steps=50)

            config = FinetuneConfig(
                model_name="custom_model",
                output_dir=Path(tmpdir) / "outputs",
                optimizer=optimizer,
                scheduler=scheduler,
                data=data,
                training=training,
                loss_type=LossType.CROSS_ENTROPY,
            )

            assert config.optimizer.type == OptimizerType.SGD
            assert config.optimizer.learning_rate == 0.01
            assert config.scheduler.type == SchedulerType.COSINE
            assert config.data.train_batch_size == 64
            assert config.training.num_epochs == 20
            assert config.loss_type == LossType.CROSS_ENTROPY

    def test_save_load_config(self) -> None:
        """설정 저장/로드 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"

            # 설정 생성 및 저장
            config = FinetuneConfig(
                model_name="test_model",
                output_dir=Path(tmpdir) / "outputs",
                pretrained_model_name="bert-base",
            )
            config.save(config_path)

            # 로드
            loaded_config = FinetuneConfig.load(config_path)

            assert loaded_config.model_name == config.model_name
            assert loaded_config.pretrained_model_name == config.pretrained_model_name
            assert loaded_config.optimizer.learning_rate == config.optimizer.learning_rate

    def test_to_from_dict(self) -> None:
        """딕셔너리 변환 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = FinetuneConfig(model_name="test_model", output_dir=Path(tmpdir) / "outputs")

            # to_dict
            config_dict = config.to_dict()
            assert config_dict["model_name"] == "test_model"
            assert "optimizer" in config_dict
            assert "scheduler" in config_dict

            # from_dict
            restored_config = FinetuneConfig.from_dict(config_dict)
            assert restored_config.model_name == config.model_name
            assert restored_config.optimizer.type == config.optimizer.type


class TestMetricsTracker:
    """메트릭 추적기 테스트"""

    def test_log_metrics(self) -> None:
        """메트릭 기록 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = MetricsTracker(log_dir=Path(tmpdir))

            tracker.log_metrics({"loss": 0.5, "accuracy": 0.9}, step=100, epoch=1)

            latest = tracker.get_latest_metrics()
            assert latest is not None
            assert latest["loss"] == 0.5
            assert latest["accuracy"] == 0.9

    def test_metric_history(self) -> None:
        """메트릭 히스토리 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = MetricsTracker(log_dir=Path(tmpdir))

            tracker.log_metrics({"loss": 0.5}, step=100, epoch=1, phase="train")
            tracker.log_metrics({"loss": 0.4}, step=200, epoch=1, phase="train")
            tracker.log_metrics({"loss": 0.3}, step=300, epoch=2, phase="train")

            history = tracker.get_metric_history("loss", phase="train")

            assert len(history) == 3
            assert history[0] == (100, 0.5)
            assert history[1] == (200, 0.4)
            assert history[2] == (300, 0.3)

    def test_best_metric(self) -> None:
        """최적 메트릭 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = MetricsTracker(log_dir=Path(tmpdir))

            tracker.log_metrics({"loss": 0.5}, step=100, epoch=1)
            tracker.log_metrics({"loss": 0.3}, step=200, epoch=1)
            tracker.log_metrics({"loss": 0.4}, step=300, epoch=2)

            best = tracker.get_best_metric("loss")
            assert best is not None
            assert best[0] == 0.3  # 최소값
            assert best[1] == 200  # 해당 스텝

    def test_metric_summary(self) -> None:
        """메트릭 요약 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = MetricsTracker(log_dir=Path(tmpdir))

            tracker.log_metrics({"loss": 0.5}, step=100, epoch=1)
            tracker.log_metrics({"loss": 0.3}, step=200, epoch=1)
            tracker.log_metrics({"loss": 0.4}, step=300, epoch=2)

            summary = tracker.get_metric_summary("loss")

            assert "mean" in summary
            assert "std" in summary
            assert "min" in summary
            assert "max" in summary
            assert summary["min"] == 0.3
            assert summary["max"] == 0.5
            assert summary["latest"] == 0.4

    def test_phase_filtering(self) -> None:
        """학습 단계 필터링 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = MetricsTracker(log_dir=Path(tmpdir))

            tracker.log_metrics({"loss": 0.5}, step=100, epoch=1, phase="train")
            tracker.log_metrics({"loss": 0.4}, step=200, epoch=1, phase="val")
            tracker.log_metrics({"loss": 0.3}, step=300, epoch=2, phase="train")

            train_history = tracker.get_metric_history("loss", phase="train")
            val_history = tracker.get_metric_history("loss", phase="val")

            assert len(train_history) == 2
            assert len(val_history) == 1

    def test_export_csv(self) -> None:
        """CSV 내보내기 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = MetricsTracker(log_dir=Path(tmpdir))

            tracker.log_metrics({"loss": 0.5, "accuracy": 0.8}, step=100, epoch=1)
            tracker.log_metrics({"loss": 0.4, "accuracy": 0.9}, step=200, epoch=1)

            csv_path = Path(tmpdir) / "metrics.csv"
            tracker.export_to_csv(csv_path)

            assert csv_path.exists()

            # CSV 파일 내용 확인
            import csv

            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0]["loss"] == "0.5"
            assert rows[0]["accuracy"] == "0.8"
