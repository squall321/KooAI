"""
ML Pipelines Infrastructure

Complete machine learning model serving and inference system.

Features:
- Multiple model types (classification, regression, anomaly detection, time series)
- Framework support (scikit-learn, TensorFlow, PyTorch, XGBoost, ONNX, HuggingFace)
- Model versioning and registry
- Batch and real-time inference
- Performance monitoring and statistics
- Model validation
- Hot reloading

Usage:
    # 1. Define a custom ML model
    from src.infrastructure.ml_pipelines import (
        ClassificationModel,
        ModelType,
        ModelFramework,
        PredictionInput,
        PredictionOutput,
        ml_model,
    )

    @ml_model(
        name="my-classifier",
        version="1.0.0",
        model_type=ModelType.CLASSIFICATION,
        framework=ModelFramework.SCIKIT_LEARN,
        features=["feature1", "feature2", "feature3"],
        target="label",
    )
    class MyClassifier(ClassificationModel):
        async def load(self, model_path: str):
            import joblib
            self._model = joblib.load(model_path)
            self._loaded = True

        async def predict(self, input_data: PredictionInput):
            X = await self.preprocess(input_data.data)
            predictions = self._model.predict(X)
            return PredictionOutput(predictions=predictions)

        async def validate(self, validation_data):
            # Implement validation
            pass

        async def predict_proba(self, input_data):
            X = await self.preprocess(input_data.data)
            return self._model.predict_proba(X)

    # 2. Load and serve models
    from src.infrastructure.ml_pipelines import get_model_server

    server = get_model_server()

    # Load model
    await server.load_model(MyClassifier, "my_model.pkl")

    # Make predictions
    result = await server.predict(
        "my-classifier",
        PredictionInput(data=[[1.0, 2.0, 3.0]])
    )

    # Batch predictions
    results = await server.batch_predict(
        "my-classifier",
        [
            PredictionInput(data=[[1.0, 2.0, 3.0]]),
            PredictionInput(data=[[4.0, 5.0, 6.0]]),
        ],
        parallel=True
    )

    # Get statistics
    stats = server.get_stats("my-classifier")
    print(f"Average inference time: {stats['avg_time_ms']}ms")

Model Types:
    - CLASSIFICATION: Multi-class or binary classification
    - REGRESSION: Continuous value prediction
    - CLUSTERING: Unsupervised clustering
    - ANOMALY_DETECTION: Outlier and anomaly detection
    - TIME_SERIES: Time series forecasting
    - COMPUTER_VISION: Image processing
    - NLP: Natural language processing
    - CUSTOM: Custom model types

Supported Frameworks:
    - Scikit-learn
    - TensorFlow
    - PyTorch
    - XGBoost
    - LightGBM
    - ONNX
    - HuggingFace Transformers

API Endpoints:
    - GET /api/v1/ml/models - List all models
    - GET /api/v1/ml/models/{name} - Get model info
    - POST /api/v1/ml/models/{name}/predict - Make prediction
    - POST /api/v1/ml/models/{name}/batch-predict - Batch predictions
    - POST /api/v1/ml/models/{name}/validate - Validate model
    - POST /api/v1/ml/models/{name}/set-active - Set active version
    - DELETE /api/v1/ml/models/{name} - Unload model
    - GET /api/v1/ml/models/{name}/stats - Get statistics
"""

from .model_interface import (
    # Base classes
    BaseMLModel,
    ModelMetadata,
    ModelMetrics,
    PredictionInput,
    PredictionOutput,
    # Specialized models
    ClassificationModel,
    RegressionModel,
    AnomalyDetectionModel,
    TimeSeriesModel,
    # Enums
    ModelType,
    ModelFramework,
    ModelStatus,
    # Exceptions
    ModelError,
    ModelLoadError,
    ModelPredictionError,
    ModelValidationError,
    # Decorator
    ml_model,
)

from .model_registry import (
    ModelRegistry,
    ModelServer,
    get_model_server,
)

__all__ = [
    # Base
    "BaseMLModel",
    "ModelMetadata",
    "ModelMetrics",
    "PredictionInput",
    "PredictionOutput",
    # Specialized
    "ClassificationModel",
    "RegressionModel",
    "AnomalyDetectionModel",
    "TimeSeriesModel",
    # Enums
    "ModelType",
    "ModelFramework",
    "ModelStatus",
    # Exceptions
    "ModelError",
    "ModelLoadError",
    "ModelPredictionError",
    "ModelValidationError",
    # Registry & Server
    "ModelRegistry",
    "ModelServer",
    "get_model_server",
    # Decorator
    "ml_model",
]
