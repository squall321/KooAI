"""
체크포인트 관리

모델 학습 중 체크포인트 저장 및 복원.
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import torch


@dataclass
class CheckpointMetadata:
    """체크포인트 메타데이터"""

    checkpoint_name: str
    epoch: int
    step: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, float] = field(default_factory=dict)
    best_metric: Optional[str] = None
    best_metric_value: Optional[float] = None
    is_best: bool = False
    model_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "checkpoint_name": self.checkpoint_name,
            "epoch": self.epoch,
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "best_metric": self.best_metric,
            "best_metric_value": self.best_metric_value,
            "is_best": self.is_best,
            "model_config": self.model_config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointMetadata":
        """딕셔너리에서 생성"""
        return cls(
            checkpoint_name=data["checkpoint_name"],
            epoch=data["epoch"],
            step=data["step"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metrics=data.get("metrics", {}),
            best_metric=data.get("best_metric"),
            best_metric_value=data.get("best_metric_value"),
            is_best=data.get("is_best", False),
            model_config=data.get("model_config", {}),
        )


class CheckpointManager:
    """
    체크포인트 관리자

    모델 학습 중 체크포인트를 저장, 로드, 관리.
    """

    def __init__(
        self,
        checkpoint_dir: Path,
        max_checkpoints: Optional[int] = None,
        best_metric_name: Optional[str] = None,
        best_metric_mode: str = "min",  # "min" or "max"
    ):
        """
        Args:
            checkpoint_dir: 체크포인트 저장 디렉토리
            max_checkpoints: 최대 체크포인트 개수 (None이면 무제한)
            best_metric_name: 최고 모델 결정 메트릭
            best_metric_mode: 메트릭 모드 ("min" 또는 "max")
        """
        self._checkpoint_dir = checkpoint_dir
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self._max_checkpoints = max_checkpoints
        self._best_metric_name = best_metric_name
        self._best_metric_mode = best_metric_mode

        self._checkpoints: List[CheckpointMetadata] = []
        self._best_checkpoint: Optional[CheckpointMetadata] = None
        self._metadata_file = checkpoint_dir / "checkpoints.json"

        # 메타데이터 로드
        self._load_metadata()

    def save_checkpoint(
        self,
        model: Any,  # torch.nn.Module
        optimizer: Any,  # torch.optim.Optimizer
        scheduler: Optional[Any],
        epoch: int,
        step: int,
        metrics: Dict[str, float],
        model_config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        체크포인트 저장

        Args:
            model: 모델
            optimizer: 옵티마이저
            scheduler: 스케줄러
            epoch: 에포크
            step: 스텝
            metrics: 메트릭
            model_config: 모델 설정

        Returns:
            체크포인트 경로
        """
        try:
            import torch
        except ImportError:
            raise RuntimeError("PyTorch not installed. Install with: pip install torch")

        checkpoint_name = f"checkpoint-epoch{epoch}-step{step}"
        checkpoint_path = self._checkpoint_dir / checkpoint_name
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # 체크포인트 저장
        checkpoint_data = {
            "epoch": epoch,
            "step": step,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
            "metrics": metrics,
            "model_config": model_config or {},
        }

        torch.save(checkpoint_data, checkpoint_path / "checkpoint.pt")

        # 메타데이터 생성
        is_best = self._is_best_checkpoint(metrics)
        metadata = CheckpointMetadata(
            checkpoint_name=checkpoint_name,
            epoch=epoch,
            step=step,
            metrics=metrics,
            best_metric=self._best_metric_name,
            best_metric_value=metrics.get(self._best_metric_name)
            if self._best_metric_name
            else None,
            is_best=is_best,
            model_config=model_config or {},
        )

        # 체크포인트 목록에 추가
        self._checkpoints.append(metadata)

        # 최고 체크포인트 업데이트
        if is_best:
            self._best_checkpoint = metadata

            # 최고 모델 복사
            best_path = self._checkpoint_dir / "best"
            best_path.mkdir(parents=True, exist_ok=True)
            shutil.copy(checkpoint_path / "checkpoint.pt", best_path / "checkpoint.pt")

        # 오래된 체크포인트 삭제
        self._cleanup_old_checkpoints()

        # 메타데이터 저장
        self._save_metadata()

        return checkpoint_path

    def load_checkpoint(
        self,
        checkpoint_name: str,
        model: Any,  # torch.nn.Module
        optimizer: Optional[Any] = None,  # torch.optim.Optimizer
        scheduler: Optional[Any] = None,
        device: str = "cpu",
    ) -> CheckpointMetadata:
        """
        체크포인트 로드

        Args:
            checkpoint_name: 체크포인트 이름 ("best" 또는 "checkpoint-...")
            model: 모델
            optimizer: 옵티마이저 (None이면 건너뜀)
            scheduler: 스케줄러 (None이면 건너뜀)
            device: 디바이스

        Returns:
            CheckpointMetadata

        Raises:
            FileNotFoundError: 체크포인트를 찾을 수 없음
        """
        try:
            import torch
        except ImportError:
            raise RuntimeError("PyTorch not installed. Install with: pip install torch")

        checkpoint_path = self._checkpoint_dir / checkpoint_name / "checkpoint.pt"

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        # 체크포인트 로드
        checkpoint_data = torch.load(checkpoint_path, map_location=device)

        # 모델 상태 복원
        model.load_state_dict(checkpoint_data["model_state_dict"])

        # 옵티마이저 상태 복원
        if optimizer and "optimizer_state_dict" in checkpoint_data:
            optimizer.load_state_dict(checkpoint_data["optimizer_state_dict"])

        # 스케줄러 상태 복원
        if scheduler and checkpoint_data.get("scheduler_state_dict"):
            scheduler.load_state_dict(checkpoint_data["scheduler_state_dict"])

        # 메타데이터 조회
        metadata = self.get_checkpoint_metadata(checkpoint_name)
        if not metadata:
            # 메타데이터가 없으면 체크포인트 데이터에서 생성
            metadata = CheckpointMetadata(
                checkpoint_name=checkpoint_name,
                epoch=checkpoint_data["epoch"],
                step=checkpoint_data["step"],
                metrics=checkpoint_data.get("metrics", {}),
                model_config=checkpoint_data.get("model_config", {}),
            )

        return metadata

    def load_best_checkpoint(
        self,
        model: Any,  # torch.nn.Module
        optimizer: Optional[Any] = None,  # torch.optim.Optimizer
        scheduler: Optional[Any] = None,
        device: str = "cpu",
    ) -> Optional[CheckpointMetadata]:
        """
        최고 체크포인트 로드

        Args:
            model: 모델
            optimizer: 옵티마이저
            scheduler: 스케줄러
            device: 디바이스

        Returns:
            CheckpointMetadata 또는 None
        """
        if not self._best_checkpoint:
            return None

        return self.load_checkpoint("best", model, optimizer, scheduler, device)

    def get_checkpoint_metadata(
        self, checkpoint_name: str
    ) -> Optional[CheckpointMetadata]:
        """체크포인트 메타데이터 조회"""
        for metadata in self._checkpoints:
            if metadata.checkpoint_name == checkpoint_name:
                return metadata
        return None

    def list_checkpoints(self) -> List[CheckpointMetadata]:
        """모든 체크포인트 목록"""
        return self._checkpoints.copy()

    def get_best_checkpoint(self) -> Optional[CheckpointMetadata]:
        """최고 체크포인트 메타데이터"""
        return self._best_checkpoint

    def delete_checkpoint(self, checkpoint_name: str) -> None:
        """체크포인트 삭제"""
        checkpoint_path = self._checkpoint_dir / checkpoint_name

        if checkpoint_path.exists():
            shutil.rmtree(checkpoint_path)

        # 메타데이터에서 제거
        self._checkpoints = [
            cp for cp in self._checkpoints if cp.checkpoint_name != checkpoint_name
        ]

        self._save_metadata()

    def _is_best_checkpoint(self, metrics: Dict[str, float]) -> bool:
        """최고 체크포인트인지 확인"""
        if not self._best_metric_name or self._best_metric_name not in metrics:
            return False

        current_value = metrics[self._best_metric_name]

        if not self._best_checkpoint:
            return True

        best_value = self._best_checkpoint.best_metric_value
        if best_value is None:
            return True

        if self._best_metric_mode == "min":
            return current_value < best_value
        else:  # "max"
            return current_value > best_value

    def _cleanup_old_checkpoints(self) -> None:
        """오래된 체크포인트 삭제"""
        if not self._max_checkpoints:
            return

        # 최고 체크포인트 제외
        non_best_checkpoints = [
            cp for cp in self._checkpoints if not cp.is_best
        ]

        # 개수 초과 시 오래된 것 삭제
        if len(non_best_checkpoints) > self._max_checkpoints:
            # 타임스탬프 기준 정렬
            sorted_checkpoints = sorted(
                non_best_checkpoints, key=lambda x: x.timestamp
            )

            # 삭제할 체크포인트
            to_delete = sorted_checkpoints[: -self._max_checkpoints]

            for checkpoint in to_delete:
                self.delete_checkpoint(checkpoint.checkpoint_name)

    def _save_metadata(self) -> None:
        """메타데이터 저장"""
        data = {
            "checkpoints": [cp.to_dict() for cp in self._checkpoints],
            "best_checkpoint": self._best_checkpoint.to_dict()
            if self._best_checkpoint
            else None,
        }

        with open(self._metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_metadata(self) -> None:
        """메타데이터 로드"""
        if not self._metadata_file.exists():
            return

        try:
            with open(self._metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._checkpoints = [
                CheckpointMetadata.from_dict(cp_data)
                for cp_data in data.get("checkpoints", [])
            ]

            if data.get("best_checkpoint"):
                self._best_checkpoint = CheckpointMetadata.from_dict(
                    data["best_checkpoint"]
                )

        except Exception as e:
            print(f"Failed to load checkpoint metadata: {e}")
