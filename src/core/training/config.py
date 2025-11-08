"""
Fine-tuning 설정

모델 학습 설정을 정의하고 관리.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class OptimizerType(str, Enum):
    """옵티마이저 타입"""

    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"
    RMSPROP = "rmsprop"
    ADAGRAD = "adagrad"


class SchedulerType(str, Enum):
    """학습률 스케줄러 타입"""

    CONSTANT = "constant"
    LINEAR = "linear"
    COSINE = "cosine"
    EXPONENTIAL = "exponential"
    STEP = "step"
    PLATEAU = "plateau"


class LossType(str, Enum):
    """손실 함수 타입"""

    MSE = "mse"  # Mean Squared Error
    MAE = "mae"  # Mean Absolute Error
    CROSS_ENTROPY = "cross_entropy"
    BINARY_CROSS_ENTROPY = "binary_cross_entropy"
    KL_DIVERGENCE = "kl_divergence"
    CUSTOM = "custom"


@dataclass
class OptimizerConfig:
    """옵티마이저 설정"""

    type: OptimizerType = OptimizerType.ADAMW
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    betas: tuple = (0.9, 0.999)  # Adam/AdamW
    momentum: float = 0.9  # SGD
    epsilon: float = 1e-8
    kwargs: Dict[str, Any] = field(default_factory=dict)  # 추가 인자


@dataclass
class SchedulerConfig:
    """학습률 스케줄러 설정"""

    type: SchedulerType = SchedulerType.LINEAR
    warmup_steps: int = 0
    warmup_ratio: float = 0.0
    num_training_steps: Optional[int] = None
    num_cycles: float = 0.5  # Cosine
    gamma: float = 0.1  # Exponential/Step
    step_size: int = 10  # Step
    patience: int = 10  # Plateau
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataConfig:
    """데이터 설정"""

    train_batch_size: int = 32
    eval_batch_size: int = 64
    num_workers: int = 4
    shuffle: bool = True
    pin_memory: bool = True
    drop_last: bool = False
    prefetch_factor: int = 2


@dataclass
class TrainingConfig:
    """학습 설정"""

    # 기본 설정
    num_epochs: int = 10
    max_steps: Optional[int] = None
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0

    # 평가
    eval_strategy: str = "epoch"  # "no", "steps", "epoch"
    eval_steps: int = 500
    save_strategy: str = "epoch"  # "no", "steps", "epoch"
    save_steps: int = 500
    save_total_limit: Optional[int] = 3

    # 로깅
    logging_steps: int = 100
    log_level: str = "info"

    # Mixed Precision
    fp16: bool = False
    bf16: bool = False

    # Early Stopping
    early_stopping_patience: Optional[int] = None
    early_stopping_threshold: float = 0.0

    # 기타
    seed: int = 42
    dataloader_num_workers: int = 0


@dataclass
class FinetuneConfig:
    """
    Fine-tuning 전체 설정

    모델 학습에 필요한 모든 설정을 포함.
    """

    # 모델
    model_name: str
    pretrained_model_name: Optional[str] = None

    # 출력 디렉토리
    output_dir: Path = Path("./outputs")
    checkpoint_dir: Path = Path("./checkpoints")
    log_dir: Path = Path("./logs")

    # 옵티마이저 & 스케줄러
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)

    # 데이터
    data: DataConfig = field(default_factory=DataConfig)

    # 학습
    training: TrainingConfig = field(default_factory=TrainingConfig)

    # 손실 함수
    loss_type: LossType = LossType.MSE

    # Freeze 설정
    freeze_layers: List[str] = field(default_factory=list)  # Freeze할 레이어 패턴
    unfreeze_layers: List[str] = field(default_factory=list)  # Unfreeze할 레이어 패턴

    # 추가 설정
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """초기화 후 처리"""
        # Path 타입 보장
        self.output_dir = Path(self.output_dir)
        self.checkpoint_dir = Path(self.checkpoint_dir)
        self.log_dir = Path(self.log_dir)

        # 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "model_name": self.model_name,
            "pretrained_model_name": self.pretrained_model_name,
            "output_dir": str(self.output_dir),
            "checkpoint_dir": str(self.checkpoint_dir),
            "log_dir": str(self.log_dir),
            "optimizer": {
                "type": self.optimizer.type.value,
                "learning_rate": self.optimizer.learning_rate,
                "weight_decay": self.optimizer.weight_decay,
                "betas": self.optimizer.betas,
                "momentum": self.optimizer.momentum,
                "epsilon": self.optimizer.epsilon,
                "kwargs": self.optimizer.kwargs,
            },
            "scheduler": {
                "type": self.scheduler.type.value,
                "warmup_steps": self.scheduler.warmup_steps,
                "warmup_ratio": self.scheduler.warmup_ratio,
                "num_training_steps": self.scheduler.num_training_steps,
                "num_cycles": self.scheduler.num_cycles,
                "gamma": self.scheduler.gamma,
                "step_size": self.scheduler.step_size,
                "patience": self.scheduler.patience,
                "kwargs": self.scheduler.kwargs,
            },
            "data": {
                "train_batch_size": self.data.train_batch_size,
                "eval_batch_size": self.data.eval_batch_size,
                "num_workers": self.data.num_workers,
                "shuffle": self.data.shuffle,
                "pin_memory": self.data.pin_memory,
                "drop_last": self.data.drop_last,
                "prefetch_factor": self.data.prefetch_factor,
            },
            "training": {
                "num_epochs": self.training.num_epochs,
                "max_steps": self.training.max_steps,
                "gradient_accumulation_steps": self.training.gradient_accumulation_steps,
                "max_grad_norm": self.training.max_grad_norm,
                "eval_strategy": self.training.eval_strategy,
                "eval_steps": self.training.eval_steps,
                "save_strategy": self.training.save_strategy,
                "save_steps": self.training.save_steps,
                "save_total_limit": self.training.save_total_limit,
                "logging_steps": self.training.logging_steps,
                "log_level": self.training.log_level,
                "fp16": self.training.fp16,
                "bf16": self.training.bf16,
                "early_stopping_patience": self.training.early_stopping_patience,
                "early_stopping_threshold": self.training.early_stopping_threshold,
                "seed": self.training.seed,
                "dataloader_num_workers": self.training.dataloader_num_workers,
            },
            "loss_type": self.loss_type.value,
            "freeze_layers": self.freeze_layers,
            "unfreeze_layers": self.unfreeze_layers,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinetuneConfig":
        """딕셔너리에서 생성"""
        optimizer_data = data.get("optimizer", {})
        scheduler_data = data.get("scheduler", {})
        data_config_data = data.get("data", {})
        training_data = data.get("training", {})

        optimizer = OptimizerConfig(
            type=OptimizerType(optimizer_data.get("type", "adamw")),
            learning_rate=optimizer_data.get("learning_rate", 1e-4),
            weight_decay=optimizer_data.get("weight_decay", 0.01),
            betas=tuple(optimizer_data.get("betas", (0.9, 0.999))),
            momentum=optimizer_data.get("momentum", 0.9),
            epsilon=optimizer_data.get("epsilon", 1e-8),
            kwargs=optimizer_data.get("kwargs", {}),
        )

        scheduler = SchedulerConfig(
            type=SchedulerType(scheduler_data.get("type", "linear")),
            warmup_steps=scheduler_data.get("warmup_steps", 0),
            warmup_ratio=scheduler_data.get("warmup_ratio", 0.0),
            num_training_steps=scheduler_data.get("num_training_steps"),
            num_cycles=scheduler_data.get("num_cycles", 0.5),
            gamma=scheduler_data.get("gamma", 0.1),
            step_size=scheduler_data.get("step_size", 10),
            patience=scheduler_data.get("patience", 10),
            kwargs=scheduler_data.get("kwargs", {}),
        )

        data_config = DataConfig(
            train_batch_size=data_config_data.get("train_batch_size", 32),
            eval_batch_size=data_config_data.get("eval_batch_size", 64),
            num_workers=data_config_data.get("num_workers", 4),
            shuffle=data_config_data.get("shuffle", True),
            pin_memory=data_config_data.get("pin_memory", True),
            drop_last=data_config_data.get("drop_last", False),
            prefetch_factor=data_config_data.get("prefetch_factor", 2),
        )

        training = TrainingConfig(
            num_epochs=training_data.get("num_epochs", 10),
            max_steps=training_data.get("max_steps"),
            gradient_accumulation_steps=training_data.get("gradient_accumulation_steps", 1),
            max_grad_norm=training_data.get("max_grad_norm", 1.0),
            eval_strategy=training_data.get("eval_strategy", "epoch"),
            eval_steps=training_data.get("eval_steps", 500),
            save_strategy=training_data.get("save_strategy", "epoch"),
            save_steps=training_data.get("save_steps", 500),
            save_total_limit=training_data.get("save_total_limit", 3),
            logging_steps=training_data.get("logging_steps", 100),
            log_level=training_data.get("log_level", "info"),
            fp16=training_data.get("fp16", False),
            bf16=training_data.get("bf16", False),
            early_stopping_patience=training_data.get("early_stopping_patience"),
            early_stopping_threshold=training_data.get("early_stopping_threshold", 0.0),
            seed=training_data.get("seed", 42),
            dataloader_num_workers=training_data.get("dataloader_num_workers", 0),
        )

        return cls(
            model_name=data["model_name"],
            pretrained_model_name=data.get("pretrained_model_name"),
            output_dir=Path(data.get("output_dir", "./outputs")),
            checkpoint_dir=Path(data.get("checkpoint_dir", "./checkpoints")),
            log_dir=Path(data.get("log_dir", "./logs")),
            optimizer=optimizer,
            scheduler=scheduler,
            data=data_config,
            training=training,
            loss_type=LossType(data.get("loss_type", "mse")),
            freeze_layers=data.get("freeze_layers", []),
            unfreeze_layers=data.get("unfreeze_layers", []),
            metadata=data.get("metadata", {}),
        )

    def save(self, path: Path) -> None:
        """설정을 파일에 저장"""
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> "FinetuneConfig":
        """파일에서 설정 로드"""
        import json

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)
