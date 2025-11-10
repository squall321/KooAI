"""
ML Model Interface

Base interfaces and abstractions for ML model serving.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np


class ModelType(str, Enum):
    """Types of ML models."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"
    COMPUTER_VISION = "computer_vision"
    NLP = "nlp"
    CUSTOM = "custom"


class ModelFramework(str, Enum):
    """ML frameworks."""

    SCIKIT_LEARN = "scikit-learn"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    ONNX = "onnx"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


class ModelStatus(str, Enum):
    """Model lifecycle status."""

    TRAINING = "training"
    TRAINED = "trained"
    VALIDATING = "validating"
    VALIDATED = "validated"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DEPRECATED = "deprecated"


@dataclass
class ModelMetrics:
    """Model performance metrics."""

    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    custom_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ModelMetadata:
    """
    Model metadata and information.

    Attributes:
        name: Model name
        version: Model version
        model_type: Type of model
        framework: ML framework used
        description: Model description
        features: List of input feature names
        target: Target variable name (for supervised models)
        hyperparameters: Model hyperparameters
        metrics: Performance metrics
        tags: Searchable tags
    """

    name: str
    version: str
    model_type: ModelType
    framework: ModelFramework
    description: str = ""
    features: List[str] = field(default_factory=list)
    target: Optional[str] = None
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metrics: ModelMetrics = field(default_factory=ModelMetrics)
    tags: List[str] = field(default_factory=list)
    status: ModelStatus = ModelStatus.TRAINED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PredictionInput:
    """Input for model prediction."""

    data: Union[np.ndarray, List[List[float]], Dict[str, Any]]
    feature_names: Optional[List[str]] = None
    batch_size: Optional[int] = None
    return_probabilities: bool = False
    return_confidence: bool = False


@dataclass
class PredictionOutput:
    """Output from model prediction."""

    predictions: Union[np.ndarray, List[Any]]
    probabilities: Optional[np.ndarray] = None
    confidence: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    inference_time_ms: float = 0.0


class ModelError(Exception):
    """Base exception for model-related errors."""

    def __init__(self, model_name: str, message: str):
        self.model_name = model_name
        self.message = message
        super().__init__(f"[{model_name}] {message}")


class ModelLoadError(ModelError):
    """Error loading model."""

    pass


class ModelPredictionError(ModelError):
    """Error during prediction."""

    pass


class ModelValidationError(ModelError):
    """Model validation error."""

    pass


# ============================================================================
# Base Model Interface
# ============================================================================


class BaseMLModel(ABC):
    """
    Base interface for all ML models.

    All models must inherit from this class and implement required methods.
    """

    def __init__(self, metadata: ModelMetadata):
        """
        Initialize model.

        Args:
            metadata: Model metadata
        """
        self.metadata = metadata
        self._loaded = False
        self._model = None

    @abstractmethod
    async def load(self, model_path: str) -> None:
        """
        Load model from disk.

        Args:
            model_path: Path to model file

        Raises:
            ModelLoadError: If model fails to load
        """
        pass

    @abstractmethod
    async def predict(self, input_data: PredictionInput) -> PredictionOutput:
        """
        Make predictions on input data.

        Args:
            input_data: Input data for prediction

        Returns:
            Prediction results

        Raises:
            ModelPredictionError: If prediction fails
        """
        pass

    @abstractmethod
    async def validate(
        self, validation_data: Dict[str, Any]
    ) -> ModelMetrics:
        """
        Validate model on validation dataset.

        Args:
            validation_data: Validation dataset

        Returns:
            Validation metrics

        Raises:
            ModelValidationError: If validation fails
        """
        pass

    async def preprocess(self, raw_data: Any) -> np.ndarray:
        """
        Preprocess raw data before prediction.

        Override this method to implement custom preprocessing.

        Args:
            raw_data: Raw input data

        Returns:
            Preprocessed data ready for model
        """
        # Default: convert to numpy array
        if isinstance(raw_data, np.ndarray):
            return raw_data
        elif isinstance(raw_data, list):
            return np.array(raw_data)
        elif isinstance(raw_data, dict):
            # Assume dict maps feature names to values
            if self.metadata.features:
                return np.array([raw_data[f] for f in self.metadata.features])
            else:
                return np.array(list(raw_data.values()))
        else:
            raise ValueError(f"Unsupported data type: {type(raw_data)}")

    async def postprocess(self, predictions: np.ndarray) -> Any:
        """
        Postprocess model predictions.

        Override this method to implement custom postprocessing.

        Args:
            predictions: Raw model predictions

        Returns:
            Postprocessed predictions
        """
        # Default: return as-is
        return predictions

    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "type": self.metadata.model_type.value,
            "framework": self.metadata.framework.value,
            "status": self.metadata.status.value,
            "loaded": self._loaded,
            "features": self.metadata.features,
            "target": self.metadata.target,
            "metrics": {
                "accuracy": self.metadata.metrics.accuracy,
                "precision": self.metadata.metrics.precision,
                "recall": self.metadata.metrics.recall,
                "f1_score": self.metadata.metrics.f1_score,
                "mse": self.metadata.metrics.mse,
                "rmse": self.metadata.metrics.rmse,
                "mae": self.metadata.metrics.mae,
                "r2_score": self.metadata.metrics.r2_score,
                **self.metadata.metrics.custom_metrics,
            },
        }


# ============================================================================
# Specialized Model Interfaces
# ============================================================================


class ClassificationModel(BaseMLModel):
    """
    Base class for classification models.

    Example:
        ```python
        class TurbulenceClassifier(ClassificationModel):
            async def load(self, model_path: str):
                import joblib
                self._model = joblib.load(model_path)
                self._loaded = True

            async def predict(self, input_data: PredictionInput):
                X = await self.preprocess(input_data.data)
                predictions = self._model.predict(X)

                probabilities = None
                if input_data.return_probabilities:
                    probabilities = self._model.predict_proba(X)

                return PredictionOutput(
                    predictions=predictions,
                    probabilities=probabilities
                )
        ```
    """

    @abstractmethod
    async def predict_proba(
        self, input_data: PredictionInput
    ) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            input_data: Input data

        Returns:
            Probability matrix (samples x classes)
        """
        pass


class RegressionModel(BaseMLModel):
    """
    Base class for regression models.

    Example:
        ```python
        class TemperaturePredictor(RegressionModel):
            async def load(self, model_path: str):
                import joblib
                self._model = joblib.load(model_path)
                self._loaded = True

            async def predict(self, input_data: PredictionInput):
                X = await self.preprocess(input_data.data)
                predictions = self._model.predict(X)

                return PredictionOutput(predictions=predictions)
        ```
    """

    async def predict_with_uncertainty(
        self, input_data: PredictionInput
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Predict with uncertainty estimates.

        Override for models that support uncertainty quantification.

        Args:
            input_data: Input data

        Returns:
            Tuple of (predictions, uncertainties)
        """
        predictions = await self.predict(input_data)
        uncertainties = np.zeros_like(predictions.predictions)
        return predictions.predictions, uncertainties


class AnomalyDetectionModel(BaseMLModel):
    """
    Base class for anomaly detection models.

    Example:
        ```python
        class SimulationAnomalyDetector(AnomalyDetectionModel):
            async def detect_anomalies(self, input_data: PredictionInput):
                X = await self.preprocess(input_data.data)
                # -1 for anomalies, 1 for normal
                predictions = self._model.predict(X)
                scores = self._model.decision_function(X)

                return PredictionOutput(
                    predictions=predictions,
                    metadata={"anomaly_scores": scores.tolist()}
                )
        ```
    """

    @abstractmethod
    async def detect_anomalies(
        self, input_data: PredictionInput
    ) -> PredictionOutput:
        """
        Detect anomalies in data.

        Args:
            input_data: Input data

        Returns:
            Anomaly predictions (typically 1 for normal, -1 for anomaly)
        """
        pass

    @abstractmethod
    async def get_anomaly_score(
        self, input_data: PredictionInput
    ) -> np.ndarray:
        """
        Get anomaly scores for data points.

        Args:
            input_data: Input data

        Returns:
            Anomaly scores (higher = more anomalous)
        """
        pass


class TimeSeriesModel(BaseMLModel):
    """
    Base class for time series forecasting models.

    Example:
        ```python
        class ConvergenceForecaster(TimeSeriesModel):
            async def forecast(self, input_data: PredictionInput, steps: int):
                X = await self.preprocess(input_data.data)
                predictions = self._model.predict(steps=steps)

                return PredictionOutput(
                    predictions=predictions,
                    metadata={"forecast_steps": steps}
                )
        ```
    """

    @abstractmethod
    async def forecast(
        self, input_data: PredictionInput, steps: int
    ) -> PredictionOutput:
        """
        Forecast future values.

        Args:
            input_data: Historical data
            steps: Number of steps to forecast

        Returns:
            Forecasted values
        """
        pass


# ============================================================================
# Model Decorators
# ============================================================================


def ml_model(
    name: str,
    version: str,
    model_type: ModelType,
    framework: ModelFramework,
    description: str = "",
    features: Optional[List[str]] = None,
    target: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Callable[[Type[Any]], Type[Any]]:
    """
    Decorator to register an ML model.

    Usage:
        ```python
        @ml_model(
            name="turbulence-classifier",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            framework=ModelFramework.SCIKIT_LEARN,
            features=["velocity_x", "velocity_y", "velocity_z"],
            target="turbulence_level",
            tags=["turbulence", "classification"]
        )
        class TurbulenceClassifier(ClassificationModel):
            async def load(self, model_path: str):
                import joblib
                self._model = joblib.load(model_path)
                self._loaded = True

            async def predict(self, input_data: PredictionInput):
                # Implementation
                pass
        ```
    """

    def decorator(cls: Type[Any]) -> Type[Any]:
        # Create metadata
        metadata = ModelMetadata(
            name=name,
            version=version,
            model_type=model_type,
            framework=framework,
            description=description,
            features=features or [],
            target=target,
            tags=tags or [],
        )

        # Store metadata on class
        cls._model_metadata = metadata

        # Wrap __init__ to inject metadata
        original_init = cls.__init__

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            BaseMLModel.__init__(self, metadata)
            if original_init is not BaseMLModel.__init__:
                original_init(self, *args, **kwargs)

        cls.__init__ = new_init

        return cls

    return decorator
