"""
VAE 모델 테스트
"""

import pytest
import torch
import numpy as np

from src.core.ai_models.vae.model import (
    ContourEncoder,
    ContourDecoder,
    ContourVAE,
    VAELoss,
)


class TestContourEncoder:
    """ContourEncoder 테스트"""

    def test_encoder_forward(self):
        """순전파 테스트"""
        encoder = ContourEncoder(
            input_dim=2,
            hidden_dims=[64, 128],
            latent_dim=16,
        )

        # 입력: (batch, num_points, 2)
        x = torch.randn(4, 100, 2)

        # 순전파
        mu, logvar, z = encoder(x)

        # 출력 shape 확인
        assert mu.shape == (4, 16)
        assert logvar.shape == (4, 16)
        assert z.shape == (4, 16)

    def test_reparameterize(self):
        """Reparameterization trick 테스트"""
        encoder = ContourEncoder(latent_dim=8)

        mu = torch.zeros(2, 8)
        logvar = torch.zeros(2, 8)

        z = encoder.reparameterize(mu, logvar)

        assert z.shape == (2, 8)
        # 평균 0, 표준편차 1에 가까워야 함
        assert z.mean().abs() < 0.5
        assert (z.std() - 1.0).abs() < 0.5


class TestContourDecoder:
    """ContourDecoder 테스트"""

    def test_decoder_forward(self):
        """순전파 테스트"""
        decoder = ContourDecoder(
            latent_dim=16,
            hidden_dims=[128, 64],
            output_dim=2,
            num_points=100,
        )

        # 입력: (batch, latent_dim)
        z = torch.randn(4, 16)

        # 순전파
        recon = decoder(z)

        # 출력 shape 확인
        assert recon.shape == (4, 100, 2)


class TestContourVAE:
    """ContourVAE 테스트"""

    def test_vae_forward(self):
        """VAE 순전파 테스트"""
        model = ContourVAE(
            input_dim=2,
            latent_dim=16,
            encoder_hidden_dims=[64, 128],
            decoder_hidden_dims=[128, 64],
            num_points=100,
        )

        x = torch.randn(4, 100, 2)

        # 순전파
        recon, mu, logvar, z = model(x)

        # Shape 확인
        assert recon.shape == x.shape
        assert mu.shape == (4, 16)
        assert logvar.shape == (4, 16)
        assert z.shape == (4, 16)

    def test_encode(self):
        """인코딩만 테스트"""
        model = ContourVAE(latent_dim=8, num_points=50)

        x = torch.randn(2, 50, 2)
        z = model.encode(x)

        assert z.shape == (2, 8)

    def test_decode(self):
        """디코딩만 테스트"""
        model = ContourVAE(latent_dim=8, num_points=50)

        z = torch.randn(2, 8)
        recon = model.decode(z)

        assert recon.shape == (2, 50, 2)

    def test_sample(self):
        """샘플 생성 테스트"""
        model = ContourVAE(latent_dim=8, num_points=50)
        device = torch.device("cpu")

        samples = model.sample(num_samples=5, device=device)

        assert samples.shape == (5, 50, 2)

    def test_get_config(self):
        """설정 반환 테스트"""
        model = ContourVAE(input_dim=3, latent_dim=16, num_points=200)

        config = model.get_config()

        assert config["input_dim"] == 3
        assert config["latent_dim"] == 16
        assert config["num_points"] == 200


class TestVAELoss:
    """VAELoss 테스트"""

    def test_loss_computation(self):
        """손실 계산 테스트"""
        loss_fn = VAELoss(recon_loss_type="mse", beta=1.0)

        # 더미 데이터
        recon = torch.randn(4, 100, 2)
        x = torch.randn(4, 100, 2)
        mu = torch.randn(4, 16)
        logvar = torch.randn(4, 16)

        # 손실 계산
        total_loss, loss_dict = loss_fn(recon, x, mu, logvar)

        # 손실이 스칼라인지 확인
        assert isinstance(total_loss.item(), float)

        # loss_dict 확인
        assert "loss" in loss_dict
        assert "recon_loss" in loss_dict
        assert "kl_loss" in loss_dict
        assert "beta" in loss_dict

    def test_mse_reconstruction_loss(self):
        """MSE 재구성 손실 테스트"""
        loss_fn = VAELoss(recon_loss_type="mse", beta=0.0)  # KL 제외

        recon = torch.zeros(2, 10, 2)
        x = torch.zeros(2, 10, 2)
        mu = torch.zeros(2, 8)
        logvar = torch.zeros(2, 8)

        total_loss, loss_dict = loss_fn(recon, x, mu, logvar)

        # 완전히 같으면 loss = 0
        assert total_loss.item() == pytest.approx(0.0, abs=1e-6)

    def test_beta_schedule_linear(self):
        """Linear beta 스케줄링 테스트"""
        loss_fn = VAELoss(beta=1.0, beta_schedule="linear")

        recon = torch.randn(2, 10, 2)
        x = torch.randn(2, 10, 2)
        mu = torch.randn(2, 8)
        logvar = torch.randn(2, 8)

        # 초기 step
        _, loss_dict_1 = loss_fn(recon, x, mu, logvar)
        beta_1 = loss_dict_1["beta"].item()

        # 여러 step 진행
        for _ in range(1000):
            loss_fn(recon, x, mu, logvar)

        _, loss_dict_2 = loss_fn(recon, x, mu, logvar)
        beta_2 = loss_dict_2["beta"].item()

        # Beta가 증가했는지 확인
        assert beta_2 > beta_1

    def test_chamfer_distance(self):
        """Chamfer distance 손실 테스트"""
        loss_fn = VAELoss(recon_loss_type="chamfer", beta=0.0)

        # 같은 포인트들
        points = torch.randn(2, 10, 2)
        recon = points.clone()
        mu = torch.zeros(2, 8)
        logvar = torch.zeros(2, 8)

        total_loss, _ = loss_fn(recon, points, mu, logvar)

        # 완전히 같으면 Chamfer distance = 0
        assert total_loss.item() == pytest.approx(0.0, abs=1e-6)


class TestIntegration:
    """통합 테스트"""

    def test_full_forward_backward(self):
        """전체 순전파 + 역전파 테스트"""
        model = ContourVAE(
            input_dim=2,
            latent_dim=8,
            num_points=50,
        )

        loss_fn = VAELoss(recon_loss_type="mse", beta=1.0)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        # 더미 데이터
        x = torch.randn(4, 50, 2)

        # 순전파
        recon, mu, logvar, z = model(x)
        loss, loss_dict = loss_fn(recon, x, mu, logvar)

        # 역전파
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 에러 없이 진행되었는지 확인
        assert loss.item() > 0

    def test_model_save_load(self, tmp_path):
        """모델 저장/로드 테스트"""
        model = ContourVAE(latent_dim=16, num_points=100)

        # 더미 데이터로 순전파
        x = torch.randn(2, 100, 2)
        output1, _, _, _ = model(x)

        # 모델 저장
        checkpoint_path = tmp_path / "model.pth"
        torch.save(model.state_dict(), checkpoint_path)

        # 새 모델 생성 및 로드
        model2 = ContourVAE(latent_dim=16, num_points=100)
        model2.load_state_dict(torch.load(checkpoint_path))

        # 같은 입력에 대해 같은 출력
        model2.eval()
        with torch.no_grad():
            output2, _, _, _ = model2(x)

        torch.testing.assert_close(output1, output2)
