"""
VAE 모델 아키텍처

컨투어 데이터 압축을 위한 Variational Autoencoder 구현
"""

from typing import Optional, Tuple, Dict, Any
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


class ContourEncoder(nn.Module):
    """
    컨투어 Encoder

    컨투어 포인트들을 잠재 공간(latent space)으로 인코딩합니다.
    """

    def __init__(
        self,
        input_dim: int = 2,  # 2D 컨투어 (x, y)
        hidden_dims: list[int] = [64, 128, 256, 512],
        latent_dim: int = 32,
        dropout: float = 0.1,
    ):
        """
        Args:
            input_dim: 입력 차원 (2D: 2, 3D: 3)
            hidden_dims: 은닉층 차원 리스트
            latent_dim: 잠재 공간 차원
            dropout: 드롭아웃 비율
        """
        super().__init__()

        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # 인코더 레이어 구성
        layers = []
        in_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(
                nn.Sequential(
                    nn.Linear(in_dim, hidden_dim),
                    nn.BatchNorm1d(hidden_dim),
                    nn.ReLU(inplace=True),
                    nn.Dropout(dropout),
                )
            )
            in_dim = hidden_dim

        self.encoder = nn.Sequential(*layers)

        # 잠재 공간 파라미터 (평균과 로그 분산)
        self.fc_mu = nn.Linear(hidden_dims[-1], latent_dim)
        self.fc_logvar = nn.Linear(hidden_dims[-1], latent_dim)

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        """
        순전파

        Args:
            x: 입력 컨투어 포인트 (batch_size, num_points, input_dim)

        Returns:
            mu: 평균 (batch_size, latent_dim)
            logvar: 로그 분산 (batch_size, latent_dim)
            z: 샘플링된 잠재 벡터 (batch_size, latent_dim)
        """
        batch_size, num_points, _ = x.shape

        # (B, N, D) -> (B*N, D)
        x_flat = x.view(-1, self.input_dim)

        # 인코딩
        h = self.encoder(x_flat)

        # (B*N, H) -> (B, N, H) -> (B, H) (평균 풀링)
        h = h.view(batch_size, num_points, -1)
        h = torch.mean(h, dim=1)

        # 잠재 공간 파라미터
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)

        # Reparameterization trick
        z = self.reparameterize(mu, logvar)

        return mu, logvar, z

    def reparameterize(self, mu: Tensor, logvar: Tensor) -> Tensor:
        """
        Reparameterization trick

        z = μ + σ * ε, where ε ~ N(0, 1)

        Args:
            mu: 평균
            logvar: 로그 분산

        Returns:
            샘플링된 잠재 벡터
        """
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std


class ContourDecoder(nn.Module):
    """
    컨투어 Decoder

    잠재 공간에서 컨투어 포인트들을 재구성합니다.
    """

    def __init__(
        self,
        latent_dim: int = 32,
        hidden_dims: list[int] = [512, 256, 128, 64],
        output_dim: int = 2,  # 2D 컨투어
        num_points: int = 100,  # 재구성할 포인트 수
        dropout: float = 0.1,
    ):
        """
        Args:
            latent_dim: 잠재 공간 차원
            hidden_dims: 은닉층 차원 리스트
            output_dim: 출력 차원 (2D: 2, 3D: 3)
            num_points: 재구성할 포인트 수
            dropout: 드롭아웃 비율
        """
        super().__init__()

        self.latent_dim = latent_dim
        self.output_dim = output_dim
        self.num_points = num_points

        # 디코더 레이어 구성
        layers = []
        in_dim = latent_dim

        for hidden_dim in hidden_dims:
            layers.append(
                nn.Sequential(
                    nn.Linear(in_dim, hidden_dim),
                    nn.BatchNorm1d(hidden_dim),
                    nn.ReLU(inplace=True),
                    nn.Dropout(dropout),
                )
            )
            in_dim = hidden_dim

        self.decoder = nn.Sequential(*layers)

        # 출력 레이어
        self.fc_out = nn.Linear(hidden_dims[-1], output_dim * num_points)

    def forward(self, z: Tensor) -> Tensor:
        """
        순전파

        Args:
            z: 잠재 벡터 (batch_size, latent_dim)

        Returns:
            재구성된 컨투어 포인트 (batch_size, num_points, output_dim)
        """
        batch_size = z.size(0)

        # 디코딩
        h = self.decoder(z)

        # 출력
        out = self.fc_out(h)

        # (B, N*D) -> (B, N, D)
        out = out.view(batch_size, self.num_points, self.output_dim)

        return out


class ContourVAE(nn.Module):
    """
    컨투어 Variational Autoencoder

    컨투어 데이터를 압축하고 재구성하는 VAE 모델입니다.
    """

    def __init__(
        self,
        input_dim: int = 2,
        latent_dim: int = 32,
        encoder_hidden_dims: list[int] = [64, 128, 256, 512],
        decoder_hidden_dims: list[int] = [512, 256, 128, 64],
        num_points: int = 100,
        dropout: float = 0.1,
    ):
        """
        Args:
            input_dim: 입력 차원 (2D: 2, 3D: 3)
            latent_dim: 잠재 공간 차원
            encoder_hidden_dims: 인코더 은닉층 차원
            decoder_hidden_dims: 디코더 은닉층 차원
            num_points: 컨투어 포인트 수
            dropout: 드롭아웃 비율
        """
        super().__init__()

        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.num_points = num_points

        # Encoder
        self.encoder = ContourEncoder(
            input_dim=input_dim,
            hidden_dims=encoder_hidden_dims,
            latent_dim=latent_dim,
            dropout=dropout,
        )

        # Decoder
        self.decoder = ContourDecoder(
            latent_dim=latent_dim,
            hidden_dims=decoder_hidden_dims,
            output_dim=input_dim,
            num_points=num_points,
            dropout=dropout,
        )

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """
        순전파

        Args:
            x: 입력 컨투어 (batch_size, num_points, input_dim)

        Returns:
            recon: 재구성된 컨투어 (batch_size, num_points, input_dim)
            mu: 평균 (batch_size, latent_dim)
            logvar: 로그 분산 (batch_size, latent_dim)
            z: 잠재 벡터 (batch_size, latent_dim)
        """
        # 인코딩
        mu, logvar, z = self.encoder(x)

        # 디코딩
        recon = self.decoder(z)

        return recon, mu, logvar, z

    def encode(self, x: Tensor) -> Tensor:
        """
        인코딩만 수행 (추론용)

        Args:
            x: 입력 컨투어 (batch_size, num_points, input_dim)

        Returns:
            잠재 벡터 (batch_size, latent_dim)
        """
        mu, logvar, z = self.encoder(x)
        return z

    def decode(self, z: Tensor) -> Tensor:
        """
        디코딩만 수행 (생성용)

        Args:
            z: 잠재 벡터 (batch_size, latent_dim)

        Returns:
            재구성된 컨투어 (batch_size, num_points, input_dim)
        """
        return self.decoder(z)

    def sample(self, num_samples: int, device: torch.device) -> Tensor:
        """
        잠재 공간에서 샘플링하여 컨투어 생성

        Args:
            num_samples: 생성할 샘플 수
            device: 디바이스

        Returns:
            생성된 컨투어 (num_samples, num_points, input_dim)
        """
        # 표준 정규분포에서 샘플링
        z = torch.randn(num_samples, self.latent_dim, device=device)

        # 디코딩
        return self.decode(z)

    def get_config(self) -> Dict[str, Any]:
        """모델 설정 반환"""
        return {
            "input_dim": self.input_dim,
            "latent_dim": self.latent_dim,
            "num_points": self.num_points,
        }


class VAELoss(nn.Module):
    """
    VAE 손실 함수

    Total Loss = Reconstruction Loss + β * KL Divergence Loss
    """

    def __init__(
        self,
        recon_loss_type: str = "mse",  # "mse" or "chamfer"
        beta: float = 1.0,  # KL divergence weight
        beta_schedule: Optional[str] = None,  # "linear", "cyclical", or None
    ):
        """
        Args:
            recon_loss_type: 재구성 손실 타입 ("mse" or "chamfer")
            beta: KL divergence 가중치
            beta_schedule: Beta 스케줄링 방식
        """
        super().__init__()

        self.recon_loss_type = recon_loss_type
        self.beta = beta
        self.beta_schedule = beta_schedule

        self._step = 0

    def forward(
        self,
        recon: Tensor,
        x: Tensor,
        mu: Tensor,
        logvar: Tensor,
    ) -> Tuple[Tensor, Dict[str, Tensor]]:
        """
        손실 계산

        Args:
            recon: 재구성된 컨투어
            x: 원본 컨투어
            mu: 평균
            logvar: 로그 분산

        Returns:
            total_loss: 총 손실
            loss_dict: 손실 세부 정보
        """
        # 재구성 손실
        recon_loss = self._reconstruction_loss(recon, x)

        # KL Divergence 손실
        kl_loss = self._kl_divergence(mu, logvar)

        # Beta 스케줄링
        current_beta = self._get_current_beta()

        # 총 손실
        total_loss = recon_loss + current_beta * kl_loss

        loss_dict = {
            "loss": total_loss,
            "recon_loss": recon_loss,
            "kl_loss": kl_loss,
            "beta": torch.tensor(current_beta),
        }

        self._step += 1

        return total_loss, loss_dict

    def _reconstruction_loss(self, recon: Tensor, x: Tensor) -> Tensor:
        """재구성 손실 계산"""
        if self.recon_loss_type == "mse":
            # Mean Squared Error
            return F.mse_loss(recon, x, reduction="mean")
        elif self.recon_loss_type == "chamfer":
            # Chamfer Distance (간단한 구현)
            return self._chamfer_distance(recon, x)
        else:
            raise ValueError(f"Unknown reconstruction loss type: {self.recon_loss_type}")

    def _kl_divergence(self, mu: Tensor, logvar: Tensor) -> Tensor:
        """
        KL Divergence 계산

        KL(q(z|x) || p(z)) where p(z) = N(0, I)
        = -0.5 * Σ(1 + log(σ²) - μ² - σ²)
        """
        return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp()) / mu.size(0)

    def _chamfer_distance(self, recon: Tensor, x: Tensor) -> Tensor:
        """
        Chamfer Distance 계산

        간단한 구현: 각 포인트에서 가장 가까운 포인트까지의 거리 합

        Args:
            recon: 재구성된 포인트 (B, N, D)
            x: 원본 포인트 (B, N, D)

        Returns:
            Chamfer distance
        """
        # recon의 각 포인트에서 x로의 최소 거리
        dist1 = torch.cdist(recon, x, p=2)  # (B, N, N)
        min_dist1, _ = torch.min(dist1, dim=2)  # (B, N)
        loss1 = torch.mean(min_dist1)

        # x의 각 포인트에서 recon으로의 최소 거리
        min_dist2, _ = torch.min(dist1, dim=1)  # (B, N)
        loss2 = torch.mean(min_dist2)

        return loss1 + loss2

    def _get_current_beta(self) -> float:
        """현재 step의 beta 값 반환"""
        if self.beta_schedule is None:
            return self.beta
        elif self.beta_schedule == "linear":
            # Linear warmup (0 -> beta over 10000 steps)
            return min(self.beta, self.beta * self._step / 10000)
        elif self.beta_schedule == "cyclical":
            # Cyclical annealing
            cycle = 10000
            return self.beta * (self._step % cycle) / cycle
        else:
            return self.beta
