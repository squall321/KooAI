"""
VAE 모듈

컨투어 데이터 압축을 위한 Variational Autoencoder
"""

from src.core.ai_models.vae.model import (
    ContourEncoder,
    ContourDecoder,
    ContourVAE,
    VAELoss,
)
from src.core.ai_models.vae.preprocessing import (
    ContourNormalizer,
    ContourSampler,
    ContourAugmentor,
    ContourDataset,
    prepare_contour_data,
)
from src.core.ai_models.vae.trainer import (
    VAETrainer,
    create_trainer,
)

__all__ = [
    # Model
    "ContourEncoder",
    "ContourDecoder",
    "ContourVAE",
    "VAELoss",
    # Preprocessing
    "ContourNormalizer",
    "ContourSampler",
    "ContourAugmentor",
    "ContourDataset",
    "prepare_contour_data",
    # Training
    "VAETrainer",
    "create_trainer",
]
