"""
VAE 데이터 전처리

컨투어 데이터 정규화, 샘플링, 증강을 위한 전처리 파이프라인
"""

from typing import Optional, Tuple, List
import numpy as np
import torch
from torch import Tensor


class ContourNormalizer:
    """
    컨투어 정규화기

    컨투어를 중심 정렬, 스케일 정규화합니다.
    """

    def __init__(
        self,
        center: bool = True,
        scale: bool = True,
        scale_method: str = "max",  # "max", "std", "bbox"
    ):
        """
        Args:
            center: 중심 정렬 여부
            scale: 스케일 정규화 여부
            scale_method: 스케일링 방법
                - "max": 최대값 기준
                - "std": 표준편차 기준
                - "bbox": 바운딩 박스 기준
        """
        self.center = center
        self.scale = scale
        self.scale_method = scale_method

        self.mean_: Optional[np.ndarray] = None
        self.scale_: Optional[float] = None

    def fit(self, contours: np.ndarray) -> "ContourNormalizer":
        """
        정규화 파라미터 학습

        Args:
            contours: 컨투어 배열 (N, num_points, 2)

        Returns:
            self
        """
        if self.center:
            # 전체 포인트의 평균 계산
            all_points = contours.reshape(-1, contours.shape[-1])
            self.mean_ = np.mean(all_points, axis=0)
        else:
            self.mean_ = np.zeros(contours.shape[-1])

        if self.scale:
            # 중심 정렬된 포인트들
            centered = contours - self.mean_

            if self.scale_method == "max":
                # 최대값 기준
                self.scale_ = np.max(np.abs(centered))
            elif self.scale_method == "std":
                # 표준편차 기준
                self.scale_ = np.std(centered) + 1e-8
            elif self.scale_method == "bbox":
                # 바운딩 박스 대각선 길이
                mins = np.min(centered.reshape(-1, centered.shape[-1]), axis=0)
                maxs = np.max(centered.reshape(-1, centered.shape[-1]), axis=0)
                self.scale_ = np.linalg.norm(maxs - mins)
            else:
                raise ValueError(f"Unknown scale method: {self.scale_method}")
        else:
            self.scale_ = 1.0

        return self

    def transform(self, contours: np.ndarray) -> np.ndarray:
        """
        컨투어 정규화

        Args:
            contours: 컨투어 배열 (N, num_points, 2) 또는 (num_points, 2)

        Returns:
            정규화된 컨투어
        """
        if self.mean_ is None or self.scale_ is None:
            raise ValueError("Normalizer not fitted. Call fit() first.")

        # 중심 정렬
        normalized = contours - self.mean_

        # 스케일 정규화
        if self.scale:
            normalized = normalized / (self.scale_ + 1e-8)

        return normalized

    def fit_transform(self, contours: np.ndarray) -> np.ndarray:
        """학습과 변환을 한 번에 수행"""
        return self.fit(contours).transform(contours)

    def inverse_transform(self, normalized: np.ndarray) -> np.ndarray:
        """
        역변환

        Args:
            normalized: 정규화된 컨투어

        Returns:
            원본 스케일의 컨투어
        """
        if self.mean_ is None or self.scale_ is None:
            raise ValueError("Normalizer not fitted.")

        # 스케일 복원
        contours = normalized * self.scale_

        # 중심 복원
        contours = contours + self.mean_

        return contours


class ContourSampler:
    """
    컨투어 포인트 샘플러

    컨투어에서 고정된 수의 포인트를 샘플링합니다.
    """

    @staticmethod
    def uniform_sample(contour: np.ndarray, num_points: int, closed: bool = True) -> np.ndarray:
        """
        균등 간격으로 샘플링

        Args:
            contour: 입력 컨투어 (N, 2)
            num_points: 샘플링할 포인트 수
            closed: 닫힌 컨투어 여부

        Returns:
            샘플링된 컨투어 (num_points, 2)
        """
        n_orig = len(contour)

        if n_orig == num_points:
            return contour.copy()

        # 누적 거리 계산
        dists = np.sqrt(np.sum(np.diff(contour, axis=0) ** 2, axis=1))
        cumsum = np.concatenate([[0], np.cumsum(dists)])

        if closed:
            # 마지막 점과 첫 점 사이 거리 추가
            last_dist = np.linalg.norm(contour[-1] - contour[0])
            cumsum = np.append(cumsum, cumsum[-1] + last_dist)

        # 균등 간격 샘플링 위치
        total_length = cumsum[-1]
        sample_positions = np.linspace(0, total_length, num_points, endpoint=False)

        # 보간
        sampled = np.zeros((num_points, contour.shape[1]))

        for i, pos in enumerate(sample_positions):
            # 위치에 해당하는 구간 찾기
            idx = np.searchsorted(cumsum, pos) - 1
            idx = np.clip(idx, 0, len(cumsum) - 2)

            # 선형 보간
            t = (pos - cumsum[idx]) / (cumsum[idx + 1] - cumsum[idx] + 1e-8)

            if idx < n_orig - 1:
                sampled[i] = contour[idx] + t * (contour[idx + 1] - contour[idx])
            else:
                # 마지막 구간 (닫힌 컨투어)
                sampled[i] = contour[-1] + t * (contour[0] - contour[-1])

        return sampled

    @staticmethod
    def random_sample(contour: np.ndarray, num_points: int, replace: bool = False) -> np.ndarray:
        """
        랜덤 샘플링

        Args:
            contour: 입력 컨투어 (N, 2)
            num_points: 샘플링할 포인트 수
            replace: 중복 허용 여부

        Returns:
            샘플링된 컨투어 (num_points, 2)
        """
        n_orig = len(contour)

        if n_orig <= num_points and not replace:
            # 포인트 수가 부족하면 전체 반환
            return contour.copy()

        # 랜덤 인덱스 선택
        indices = np.random.choice(n_orig, size=num_points, replace=replace)
        return contour[indices]


class ContourAugmentor:
    """
    컨투어 데이터 증강

    회전, 스케일링, 노이즈 추가 등의 증강 기법을 적용합니다.
    """

    @staticmethod
    def rotate(contour: np.ndarray, angle: float) -> np.ndarray:
        """
        회전 변환

        Args:
            contour: 입력 컨투어 (N, 2)
            angle: 회전 각도 (라디안)

        Returns:
            회전된 컨투어
        """
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])

        return np.dot(contour, rotation_matrix.T)

    @staticmethod
    def scale(contour: np.ndarray, scale_factor: float) -> np.ndarray:
        """
        스케일 변환

        Args:
            contour: 입력 컨투어 (N, 2)
            scale_factor: 스케일 배수

        Returns:
            스케일된 컨투어
        """
        return contour * scale_factor

    @staticmethod
    def translate(contour: np.ndarray, offset: np.ndarray) -> np.ndarray:
        """
        평행 이동

        Args:
            contour: 입력 컨투어 (N, 2)
            offset: 이동 벡터 (2,)

        Returns:
            이동된 컨투어
        """
        return contour + offset

    @staticmethod
    def add_noise(
        contour: np.ndarray, noise_level: float = 0.01, noise_type: str = "gaussian"
    ) -> np.ndarray:
        """
        노이즈 추가

        Args:
            contour: 입력 컨투어 (N, 2)
            noise_level: 노이즈 강도
            noise_type: 노이즈 타입 ("gaussian", "uniform")

        Returns:
            노이즈가 추가된 컨투어
        """
        if noise_type == "gaussian":
            noise = np.random.randn(*contour.shape) * noise_level
        elif noise_type == "uniform":
            noise = np.random.uniform(-noise_level, noise_level, contour.shape)
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")

        return contour + noise

    @staticmethod
    def flip(contour: np.ndarray, axis: int = 0) -> np.ndarray:
        """
        좌우/상하 반전

        Args:
            contour: 입력 컨투어 (N, 2)
            axis: 반전 축 (0: x축, 1: y축)

        Returns:
            반전된 컨투어
        """
        flipped = contour.copy()
        flipped[:, axis] = -flipped[:, axis]
        return flipped

    def random_augment(
        self,
        contour: np.ndarray,
        rotation_range: Tuple[float, float] = (-np.pi / 6, np.pi / 6),
        scale_range: Tuple[float, float] = (0.8, 1.2),
        noise_level: float = 0.01,
        flip_prob: float = 0.5,
    ) -> np.ndarray:
        """
        랜덤 증강 (여러 기법 조합)

        Args:
            contour: 입력 컨투어 (N, 2)
            rotation_range: 회전 각도 범위 (라디안)
            scale_range: 스케일 범위
            noise_level: 노이즈 강도
            flip_prob: 반전 확률

        Returns:
            증강된 컨투어
        """
        augmented = contour.copy()

        # 랜덤 회전
        angle = np.random.uniform(*rotation_range)
        augmented = self.rotate(augmented, angle)

        # 랜덤 스케일
        scale_factor = np.random.uniform(*scale_range)
        augmented = self.scale(augmented, scale_factor)

        # 노이즈 추가
        if noise_level > 0:
            augmented = self.add_noise(augmented, noise_level)

        # 랜덤 반전
        if np.random.rand() < flip_prob:
            axis = np.random.choice([0, 1])
            augmented = self.flip(augmented, axis)

        return augmented


class ContourDataset(torch.utils.data.Dataset):
    """
    컨투어 데이터셋

    PyTorch Dataset 구현
    """

    def __init__(
        self,
        contours: np.ndarray,
        num_points: int = 100,
        normalize: bool = True,
        augment: bool = False,
        augment_params: Optional[dict] = None,
    ):
        """
        Args:
            contours: 컨투어 배열 (N, variable_points, 2)
            num_points: 고정 포인트 수
            normalize: 정규화 여부
            augment: 증강 여부
            augment_params: 증강 파라미터
        """
        self.contours = contours
        self.num_points = num_points
        self.augment = augment
        self.augment_params = augment_params or {}

        # 샘플러 및 증강기
        self.sampler = ContourSampler()
        self.augmentor = ContourAugmentor()

        # 정규화기
        self.normalizer: Optional[ContourNormalizer]
        if normalize:
            self.normalizer = ContourNormalizer()
            # 모든 컨투어를 샘플링하여 정규화 파라미터 학습
            sampled_all = np.array([self.sampler.uniform_sample(c, num_points) for c in contours])
            self.normalizer.fit(sampled_all)
        else:
            self.normalizer = None

    def __len__(self) -> int:
        return len(self.contours)

    def __getitem__(self, idx: int) -> Tensor:
        """
        컨투어 가져오기

        Returns:
            텐서 (num_points, 2)
        """
        contour = self.contours[idx]

        # 포인트 샘플링
        sampled = self.sampler.uniform_sample(contour, self.num_points)

        # 정규화
        if self.normalizer is not None:
            sampled = self.normalizer.transform(sampled)

        # 증강
        if self.augment:
            sampled = self.augmentor.random_augment(sampled, **self.augment_params)

        # 텐서로 변환
        return torch.from_numpy(sampled).float()


def prepare_contour_data(
    contours: List[np.ndarray],
    num_points: int = 100,
    train_ratio: float = 0.8,
    batch_size: int = 32,
    normalize: bool = True,
    augment_train: bool = True,
) -> Tuple[torch.utils.data.DataLoader, torch.utils.data.DataLoader]:
    """
    컨투어 데이터 준비

    Args:
        contours: 컨투어 리스트
        num_points: 고정 포인트 수
        train_ratio: 학습 데이터 비율
        batch_size: 배치 크기
        normalize: 정규화 여부
        augment_train: 학습 데이터 증강 여부

    Returns:
        train_loader, val_loader
    """
    # 학습/검증 분할
    n_train = int(len(contours) * train_ratio)
    train_contours = contours[:n_train]
    val_contours = contours[n_train:]

    # 데이터셋 생성
    train_dataset = ContourDataset(
        np.array(train_contours),
        num_points=num_points,
        normalize=normalize,
        augment=augment_train,
    )

    val_dataset = ContourDataset(
        np.array(val_contours),
        num_points=num_points,
        normalize=normalize,
        augment=False,  # 검증 데이터는 증강 안함
    )

    # 데이터 로더 생성
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,  # 단순화를 위해 0
        pin_memory=True,
    )

    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True,
    )

    return train_loader, val_loader
