"""
Example ML Model: Turbulence Level Classifier

Demonstrates how to create and serve a custom ML model.
"""

import numpy as np
from typing import Dict, Any
from sklearn.ensemble import RandomForestClassifier
import joblib

from src.infrastructure.ml_pipelines.model_interface import (
    ClassificationModel,
    ModelType,
    ModelFramework,
    PredictionInput,
    PredictionOutput,
    ModelMetrics,
    ml_model,
)


@ml_model(
    name="turbulence-classifier",
    version="1.0.0",
    model_type=ModelType.CLASSIFICATION,
    framework=ModelFramework.SCIKIT_LEARN,
    description="Classifies turbulence levels (low, medium, high) from velocity fields",
    features=["velocity_x_mean", "velocity_y_mean", "velocity_z_mean",
              "velocity_x_std", "velocity_y_std", "velocity_z_std",
              "reynolds_number", "turbulent_kinetic_energy"],
    target="turbulence_level",
    tags=["turbulence", "classification", "cfd"],
)
class TurbulenceClassifier(ClassificationModel):
    """
    Random Forest classifier for turbulence level prediction.

    Classes:
        0: Low turbulence (TI < 5%)
        1: Medium turbulence (5% <= TI < 15%)
        2: High turbulence (TI >= 15%)
    """

    async def load(self, model_path: str) -> None:
        """Load trained model from disk."""
        try:
            self._model = joblib.load(model_path)
            self._loaded = True
            self._classes = ["low", "medium", "high"]
        except Exception as e:
            raise Exception(f"Failed to load model: {e}")

    async def predict(self, input_data: PredictionInput) -> PredictionOutput:
        """
        Predict turbulence levels.

        Args:
            input_data: Input features

        Returns:
            Predictions with optional probabilities
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded")

        # Preprocess input
        X = await self.preprocess(input_data.data)

        # Make predictions
        predictions = self._model.predict(X)

        # Convert to class names
        class_predictions = [self._classes[int(p)] for p in predictions]

        # Get probabilities if requested
        probabilities = None
        confidence = None

        if input_data.return_probabilities or input_data.return_confidence:
            probabilities = self._model.predict_proba(X)

            if input_data.return_confidence:
                # Confidence is the max probability for each prediction
                confidence = np.max(probabilities, axis=1).tolist()

        return PredictionOutput(
            predictions=class_predictions,
            probabilities=probabilities,
            confidence=confidence,
            metadata={
                "classes": self._classes,
                "feature_names": self.metadata.features,
            },
        )

    async def predict_proba(self, input_data: PredictionInput) -> np.ndarray:
        """Get prediction probabilities."""
        if not self._loaded:
            raise RuntimeError("Model not loaded")

        X = await self.preprocess(input_data.data)
        return self._model.predict_proba(X)

    async def validate(self, validation_data: Dict[str, Any]) -> ModelMetrics:
        """
        Validate model on validation dataset.

        Args:
            validation_data: Dict with 'X' and 'y' keys

        Returns:
            Validation metrics
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded")

        from sklearn.metrics import accuracy_score, precision_recall_fscore_support

        X = validation_data["X"]
        y_true = validation_data["y"]

        # Make predictions
        y_pred = self._model.predict(X)

        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="weighted"
        )

        metrics = ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
        )

        # Update metadata
        self.metadata.metrics = metrics

        return metrics

    async def preprocess(self, raw_data: Any) -> np.ndarray:
        """
        Preprocess input data.

        Handles various input formats:
        - NumPy array: [n_samples, n_features]
        - List of lists: [[f1, f2, ...], ...]
        - Dict: {"feature_name": [values, ...]}
        """
        if isinstance(raw_data, np.ndarray):
            return raw_data

        elif isinstance(raw_data, list):
            return np.array(raw_data)

        elif isinstance(raw_data, dict):
            # Extract features in correct order
            features = []
            for feature_name in self.metadata.features:
                if feature_name not in raw_data:
                    raise ValueError(f"Missing feature: {feature_name}")
                features.append(raw_data[feature_name])

            # Transpose to [n_samples, n_features]
            return np.array(features).T

        else:
            raise ValueError(f"Unsupported input type: {type(raw_data)}")


def train_example_model() -> str:
    """
    Train an example turbulence classifier.

    This function demonstrates how to train a model that can be served.

    Returns:
        Path to saved model file
    """
    # Generate synthetic training data
    np.random.seed(42)
    n_samples = 1000

    # Features: velocity stats + reynolds number + TKE
    X = np.random.randn(n_samples, 8)

    # Synthetic labels based on feature combinations
    # (In reality, these would come from labeled simulation data)
    turbulence_intensity = np.abs(X[:, 3:6]).mean(axis=1)  # Based on std features

    y = np.zeros(n_samples, dtype=int)
    y[turbulence_intensity < 0.5] = 0  # Low
    y[(turbulence_intensity >= 0.5) & (turbulence_intensity < 1.0)] = 1  # Medium
    y[turbulence_intensity >= 1.0] = 2  # High

    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )

    model.fit(X, y)

    # Save model
    model_path = "models/turbulence_classifier_v1.pkl"
    import os
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, model_path)

    print(f"Model trained and saved to: {model_path}")
    print(f"Training accuracy: {model.score(X, y):.2%}")

    return model_path


if __name__ == "__main__":
    # Train and save example model
    model_path = train_example_model()

    # Example prediction
    X_test = np.random.randn(5, 8)

    model = joblib.load(model_path)
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)

    print("\nExample predictions:")
    for i, (pred, probs) in enumerate(zip(predictions, probabilities)):
        classes = ["low", "medium", "high"]
        print(f"Sample {i}: {classes[pred]} (confidence={probs[pred]:.2%})")
