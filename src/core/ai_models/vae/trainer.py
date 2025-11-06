"""
VAE Trainer

VAE 모델 학습을 위한 Trainer 클래스
"""

from typing import Optional, Dict, Any, Callable
from pathlib import Path
import json
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from src.core.ai_models.vae.model import ContourVAE, VAELoss


class VAETrainer:
    """
    VAE 학습 관리 클래스

    학습 루프, 체크포인트 관리, 로깅을 담당합니다.
    """

    def __init__(
        self,
        model: ContourVAE,
        loss_fn: VAELoss,
        optimizer: optim.Optimizer,
        device: torch.device,
        checkpoint_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
    ):
        """
        Args:
            model: VAE 모델
            loss_fn: 손실 함수
            optimizer: 옵티마이저
            device: 디바이스
            checkpoint_dir: 체크포인트 저장 디렉토리
            log_dir: 텐서보드 로그 디렉토리
        """
        self.model = model.to(device)
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.device = device

        # 체크포인트 디렉토리
        self.checkpoint_dir = checkpoint_dir or Path("checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 텐서보드
        self.log_dir = log_dir or Path("runs") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.writer = SummaryWriter(log_dir=str(self.log_dir))

        # 학습 상태
        self.current_epoch = 0
        self.global_step = 0
        self.best_val_loss = float("inf")

        # 학습 히스토리
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "train_recon_loss": [],
            "val_recon_loss": [],
            "train_kl_loss": [],
            "val_kl_loss": [],
        }

    def train_epoch(
        self, train_loader: DataLoader, epoch: int
    ) -> Dict[str, float]:
        """
        한 에폭 학습

        Args:
            train_loader: 학습 데이터 로더
            epoch: 현재 에폭

        Returns:
            에폭 손실 통계
        """
        self.model.train()

        epoch_stats = {
            "loss": 0.0,
            "recon_loss": 0.0,
            "kl_loss": 0.0,
        }

        pbar = tqdm(train_loader, desc=f"Epoch {epoch}")

        for batch_idx, batch in enumerate(pbar):
            # 데이터를 디바이스로 이동
            x = batch.to(self.device)

            # 순전파
            recon, mu, logvar, z = self.model(x)

            # 손실 계산
            loss, loss_dict = self.loss_fn(recon, x, mu, logvar)

            # 역전파
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # 통계 업데이트
            batch_size = x.size(0)
            epoch_stats["loss"] += loss.item() * batch_size
            epoch_stats["recon_loss"] += loss_dict["recon_loss"].item() * batch_size
            epoch_stats["kl_loss"] += loss_dict["kl_loss"].item() * batch_size

            # 프로그레스 바 업데이트
            pbar.set_postfix(
                {
                    "loss": loss.item(),
                    "recon": loss_dict["recon_loss"].item(),
                    "kl": loss_dict["kl_loss"].item(),
                }
            )

            # 텐서보드 로깅
            if self.global_step % 10 == 0:
                self.writer.add_scalar("train/loss", loss.item(), self.global_step)
                self.writer.add_scalar(
                    "train/recon_loss",
                    loss_dict["recon_loss"].item(),
                    self.global_step,
                )
                self.writer.add_scalar(
                    "train/kl_loss", loss_dict["kl_loss"].item(), self.global_step
                )
                self.writer.add_scalar(
                    "train/beta", loss_dict["beta"].item(), self.global_step
                )

            self.global_step += 1

        # 에폭 평균
        n_samples = len(train_loader.dataset)
        for key in epoch_stats:
            epoch_stats[key] /= n_samples

        return epoch_stats

    @torch.no_grad()
    def validate(self, val_loader: DataLoader) -> Dict[str, float]:
        """
        검증

        Args:
            val_loader: 검증 데이터 로더

        Returns:
            검증 손실 통계
        """
        self.model.eval()

        val_stats = {
            "loss": 0.0,
            "recon_loss": 0.0,
            "kl_loss": 0.0,
        }

        for batch in val_loader:
            x = batch.to(self.device)

            # 순전파
            recon, mu, logvar, z = self.model(x)

            # 손실 계산
            loss, loss_dict = self.loss_fn(recon, x, mu, logvar)

            # 통계 업데이트
            batch_size = x.size(0)
            val_stats["loss"] += loss.item() * batch_size
            val_stats["recon_loss"] += loss_dict["recon_loss"].item() * batch_size
            val_stats["kl_loss"] += loss_dict["kl_loss"].item() * batch_size

        # 평균
        n_samples = len(val_loader.dataset)
        for key in val_stats:
            val_stats[key] /= n_samples

        return val_stats

    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        num_epochs: int = 100,
        save_every: int = 10,
        early_stopping_patience: Optional[int] = None,
    ) -> Dict[str, list]:
        """
        전체 학습 루프

        Args:
            train_loader: 학습 데이터 로더
            val_loader: 검증 데이터 로더
            num_epochs: 총 에폭 수
            save_every: 체크포인트 저장 주기
            early_stopping_patience: Early stopping patience (None이면 비활성화)

        Returns:
            학습 히스토리
        """
        print(f"Starting training for {num_epochs} epochs...")
        print(f"Device: {self.device}")
        print(f"Checkpoint dir: {self.checkpoint_dir}")
        print(f"Log dir: {self.log_dir}")

        patience_counter = 0

        for epoch in range(self.current_epoch, num_epochs):
            self.current_epoch = epoch

            # 학습
            train_stats = self.train_epoch(train_loader, epoch)

            # 히스토리 업데이트
            self.history["train_loss"].append(train_stats["loss"])
            self.history["train_recon_loss"].append(train_stats["recon_loss"])
            self.history["train_kl_loss"].append(train_stats["kl_loss"])

            # 검증
            if val_loader is not None:
                val_stats = self.validate(val_loader)

                self.history["val_loss"].append(val_stats["loss"])
                self.history["val_recon_loss"].append(val_stats["recon_loss"])
                self.history["val_kl_loss"].append(val_stats["kl_loss"])

                # 텐서보드 로깅
                self.writer.add_scalar("val/loss", val_stats["loss"], epoch)
                self.writer.add_scalar("val/recon_loss", val_stats["recon_loss"], epoch)
                self.writer.add_scalar("val/kl_loss", val_stats["kl_loss"], epoch)

                print(
                    f"Epoch {epoch}: "
                    f"Train Loss={train_stats['loss']:.4f}, "
                    f"Val Loss={val_stats['loss']:.4f}"
                )

                # Best 모델 저장
                if val_stats["loss"] < self.best_val_loss:
                    self.best_val_loss = val_stats["loss"]
                    self.save_checkpoint("best.pth")
                    patience_counter = 0
                    print(f"  → Best model saved (val_loss={self.best_val_loss:.4f})")
                else:
                    patience_counter += 1

                # Early stopping
                if (
                    early_stopping_patience is not None
                    and patience_counter >= early_stopping_patience
                ):
                    print(f"Early stopping at epoch {epoch}")
                    break
            else:
                print(f"Epoch {epoch}: Train Loss={train_stats['loss']:.4f}")

            # 주기적 저장
            if (epoch + 1) % save_every == 0:
                self.save_checkpoint(f"epoch_{epoch+1}.pth")

        # 마지막 모델 저장
        self.save_checkpoint("last.pth")

        # 텐서보드 종료
        self.writer.close()

        print("Training completed!")
        return self.history

    def save_checkpoint(self, filename: str) -> None:
        """
        체크포인트 저장

        Args:
            filename: 파일명
        """
        checkpoint_path = self.checkpoint_dir / filename

        checkpoint = {
            "epoch": self.current_epoch,
            "global_step": self.global_step,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "best_val_loss": self.best_val_loss,
            "history": self.history,
            "model_config": self.model.get_config(),
        }

        torch.save(checkpoint, checkpoint_path)

        # 히스토리를 JSON으로도 저장
        if filename == "best.pth":
            history_path = self.checkpoint_dir / "history.json"
            with open(history_path, "w") as f:
                json.dump(self.history, f, indent=2)

    def load_checkpoint(self, checkpoint_path: Path) -> None:
        """
        체크포인트 로드

        Args:
            checkpoint_path: 체크포인트 경로
        """
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.current_epoch = checkpoint["epoch"]
        self.global_step = checkpoint["global_step"]
        self.best_val_loss = checkpoint["best_val_loss"]
        self.history = checkpoint.get("history", self.history)

        print(f"Checkpoint loaded from {checkpoint_path}")
        print(f"  Epoch: {self.current_epoch}")
        print(f"  Best val loss: {self.best_val_loss:.4f}")

    @torch.no_grad()
    def generate_samples(self, num_samples: int = 10) -> torch.Tensor:
        """
        샘플 생성 (검증용)

        Args:
            num_samples: 생성할 샘플 수

        Returns:
            생성된 컨투어 샘플들
        """
        self.model.eval()
        return self.model.sample(num_samples, self.device)

    def log_samples(self, epoch: int, num_samples: int = 8) -> None:
        """
        생성된 샘플을 텐서보드에 로깅

        Args:
            epoch: 현재 에폭
            num_samples: 로깅할 샘플 수
        """
        samples = self.generate_samples(num_samples)

        # Matplotlib를 사용하여 시각화
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        axes = axes.flatten()

        for i, ax in enumerate(axes):
            if i < num_samples:
                contour = samples[i].cpu().numpy()
                ax.plot(contour[:, 0], contour[:, 1], "b-")
                ax.scatter(contour[:, 0], contour[:, 1], c="r", s=10)
                ax.set_aspect("equal")
                ax.set_title(f"Sample {i+1}")
                ax.grid(True)
            else:
                ax.axis("off")

        plt.tight_layout()
        self.writer.add_figure("samples/generated", fig, epoch)
        plt.close(fig)


def create_trainer(
    model: ContourVAE,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-5,
    device: Optional[torch.device] = None,
    checkpoint_dir: Optional[Path] = None,
    log_dir: Optional[Path] = None,
    recon_loss_type: str = "mse",
    beta: float = 1.0,
    beta_schedule: Optional[str] = None,
) -> VAETrainer:
    """
    Trainer 생성 헬퍼 함수

    Args:
        model: VAE 모델
        learning_rate: 학습률
        weight_decay: 가중치 감쇠
        device: 디바이스
        checkpoint_dir: 체크포인트 디렉토리
        log_dir: 로그 디렉토리
        recon_loss_type: 재구성 손실 타입
        beta: KL divergence 가중치
        beta_schedule: Beta 스케줄링

    Returns:
        VAETrainer 인스턴스
    """
    # 디바이스 설정
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 손실 함수
    loss_fn = VAELoss(
        recon_loss_type=recon_loss_type,
        beta=beta,
        beta_schedule=beta_schedule,
    )

    # 옵티마이저
    optimizer = optim.Adam(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    # Trainer 생성
    trainer = VAETrainer(
        model=model,
        loss_fn=loss_fn,
        optimizer=optimizer,
        device=device,
        checkpoint_dir=checkpoint_dir,
        log_dir=log_dir,
    )

    return trainer
