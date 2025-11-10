"""
VAE 전처리 테스트
"""

import pytest
import numpy as np
import torch

from src.core.ai_models.vae.preprocessing import (
    ContourNormalizer,
    ContourSampler,
    ContourAugmentor,
    ContourDataset,
)


class TestContourNormalizer:
    """ContourNormalizer 테스트"""

    def test_fit_transform(self) -> None:
        """Fit 및 transform 테스트"""
        contours = np.random.randn(10, 100, 2)

        normalizer = ContourNormalizer(center=True, scale=True, scale_method="max")
        normalized = normalizer.fit_transform(contours)

        # 중심이 0에 가까워야 함
        assert np.abs(normalized.mean()) < 0.1

        # 최대값이 1 근처여야 함
        assert np.abs(normalized).max() <= 1.0 + 1e-6

    def test_inverse_transform(self) -> None:
        """역변환 테스트"""
        contours = np.random.randn(5, 50, 2) * 100 + 50

        normalizer = ContourNormalizer()
        normalized = normalizer.fit_transform(contours)
        restored = normalizer.inverse_transform(normalized)

        # 원본과 거의 같아야 함
        np.testing.assert_array_almost_equal(contours, restored, decimal=5)

    def test_center_only(self) -> None:
        """중심 정렬만 테스트"""
        contours = np.random.randn(3, 20, 2) + 10  # 중심 이동

        normalizer = ContourNormalizer(center=True, scale=False)
        normalized = normalizer.fit_transform(contours)

        # 중심이 0 근처
        assert np.abs(normalized.mean()) < 0.1

    def test_scale_methods(self) -> None:
        """스케일 방법 테스트"""
        contours = np.random.randn(5, 30, 2) * 100

        for method in ["max", "std", "bbox"]:
            normalizer = ContourNormalizer(scale_method=method)
            normalized = normalizer.fit_transform(contours)

            # 스케일이 조정되었는지 확인
            assert normalized.std() < contours.std()


class TestContourSampler:
    """ContourSampler 테스트"""

    def test_uniform_sample(self) -> None:
        """균등 샘플링 테스트"""
        # 원형 컨투어
        theta = np.linspace(0, 2 * np.pi, 200, endpoint=False)
        contour = np.stack([np.cos(theta), np.sin(theta)], axis=1)

        sampler = ContourSampler()
        sampled = sampler.uniform_sample(contour, num_points=50, closed=True)

        # 샘플링된 포인트 수 확인
        assert sampled.shape == (50, 2)

        # 여전히 원 위에 있는지 확인
        distances = np.linalg.norm(sampled, axis=1)
        assert np.allclose(distances, 1.0, atol=0.1)

    def test_uniform_sample_same_size(self) -> None:
        """같은 크기 샘플링"""
        contour = np.random.randn(100, 2)

        sampler = ContourSampler()
        sampled = sampler.uniform_sample(contour, num_points=100)

        # 크기가 같으면 복사본 반환
        assert sampled.shape == (100, 2)

    def test_random_sample(self) -> None:
        """랜덤 샘플링 테스트"""
        contour = np.random.randn(200, 2)

        sampler = ContourSampler()
        sampled = sampler.random_sample(contour, num_points=50, replace=False)

        assert sampled.shape == (50, 2)

        # 원본의 부분집합인지 확인
        # (각 포인트가 원본에 있는지)
        for point in sampled:
            found = any(np.allclose(point, orig_point) for orig_point in contour)
            assert found


class TestContourAugmentor:
    """ContourAugmentor 테스트"""

    def test_rotate(self) -> None:
        """회전 변환 테스트"""
        contour = np.array([[1.0, 0.0], [0.0, 1.0]])

        augmentor = ContourAugmentor()
        rotated = augmentor.rotate(contour, angle=np.pi / 2)  # 90도 회전

        # (1, 0) → (0, 1), (0, 1) → (-1, 0)
        expected = np.array([[0.0, 1.0], [-1.0, 0.0]])

        np.testing.assert_array_almost_equal(rotated, expected, decimal=5)

    def test_scale(self) -> None:
        """스케일 변환 테스트"""
        contour = np.array([[1.0, 2.0], [3.0, 4.0]])

        augmentor = ContourAugmentor()
        scaled = augmentor.scale(contour, scale_factor=2.0)

        expected = np.array([[2.0, 4.0], [6.0, 8.0]])

        np.testing.assert_array_almost_equal(scaled, expected)

    def test_translate(self) -> None:
        """평행 이동 테스트"""
        contour = np.array([[1.0, 2.0], [3.0, 4.0]])

        augmentor = ContourAugmentor()
        translated = augmentor.translate(contour, offset=np.array([10.0, 20.0]))

        expected = np.array([[11.0, 22.0], [13.0, 24.0]])

        np.testing.assert_array_almost_equal(translated, expected)

    def test_add_noise(self) -> None:
        """노이즈 추가 테스트"""
        contour = np.ones((100, 2))

        augmentor = ContourAugmentor()
        noisy = augmentor.add_noise(contour, noise_level=0.1, noise_type="gaussian")

        # 노이즈가 추가되었는지 확인
        assert not np.allclose(noisy, contour)

        # 평균은 여전히 1 근처
        assert np.abs(noisy.mean() - 1.0) < 0.1

    def test_flip(self) -> None:
        """반전 테스트"""
        contour = np.array([[1.0, 2.0], [3.0, 4.0]])

        augmentor = ContourAugmentor()

        # X축 반전
        flipped_x = augmentor.flip(contour, axis=0)
        expected_x = np.array([[-1.0, 2.0], [-3.0, 4.0]])
        np.testing.assert_array_almost_equal(flipped_x, expected_x)

        # Y축 반전
        flipped_y = augmentor.flip(contour, axis=1)
        expected_y = np.array([[1.0, -2.0], [3.0, -4.0]])
        np.testing.assert_array_almost_equal(flipped_y, expected_y)

    def test_random_augment(self) -> None:
        """랜덤 증강 테스트"""
        contour = np.random.randn(50, 2)

        augmentor = ContourAugmentor()
        augmented = augmentor.random_augment(
            contour,
            rotation_range=(-np.pi / 4, np.pi / 4),
            scale_range=(0.9, 1.1),
            noise_level=0.01,
            flip_prob=0.5,
        )

        # 증강 후에도 shape 유지
        assert augmented.shape == contour.shape

        # 원본과 달라졌는지 확인
        assert not np.allclose(augmented, contour)


class TestContourDataset:
    """ContourDataset 테스트"""

    def test_dataset_creation(self) -> None:
        """데이터셋 생성 테스트"""
        # 더미 컨투어들
        contours = [np.random.randn(np.random.randint(50, 150), 2) for _ in range(10)]

        dataset = ContourDataset(
            np.array(contours, dtype=object),
            num_points=100,
            normalize=True,
            augment=False,
        )

        assert len(dataset) == 10

    def test_dataset_getitem(self) -> None:
        """데이터셋 아이템 가져오기 테스트"""
        contours = [np.random.randn(100, 2) for _ in range(5)]

        dataset = ContourDataset(
            np.array(contours),
            num_points=50,
            normalize=True,
            augment=False,
        )

        # 첫 번째 아이템
        item = dataset[0]

        # 텐서인지 확인
        assert isinstance(item, torch.Tensor)

        # Shape 확인
        assert item.shape == (50, 2)

        # Float 타입인지 확인
        assert item.dtype == torch.float32

    def test_dataset_with_augmentation(self) -> None:
        """증강이 있는 데이터셋 테스트"""
        contours = [np.random.randn(100, 2) for _ in range(3)]

        dataset = ContourDataset(
            np.array(contours),
            num_points=50,
            normalize=True,
            augment=True,
            augment_params={
                "rotation_range": (-np.pi / 6, np.pi / 6),
                "scale_range": (0.8, 1.2),
                "noise_level": 0.01,
            },
        )

        # 같은 인덱스를 두 번 가져와도 다른 결과 (랜덤 증강)
        item1 = dataset[0]
        item2 = dataset[0]

        # 증강으로 인해 달라야 함
        # (확률적이므로 매번 다를 수는 있지만, 대부분 다름)
        assert not torch.allclose(item1, item2, atol=1e-6)


class TestIntegration:
    """통합 테스트"""

    def test_full_preprocessing_pipeline(self) -> None:
        """전체 전처리 파이프라인 테스트"""
        # 원형 컨투어 10개 생성
        contours = []
        for i in range(10):
            theta = np.linspace(0, 2 * np.pi, 200, endpoint=False)
            radius = 1.0 + i * 0.1  # 반지름 변화
            contour = np.stack([radius * np.cos(theta), radius * np.sin(theta)], axis=1)
            contours.append(contour)

        # 데이터셋 생성
        dataset = ContourDataset(
            np.array(contours),
            num_points=100,
            normalize=True,
            augment=True,
        )

        # 데이터 로더 생성
        loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=True)

        # 배치 가져오기
        batch = next(iter(loader))

        # 배치 shape 확인
        assert batch.shape == (4, 100, 2)

        # 텐서인지 확인
        assert isinstance(batch, torch.Tensor)
