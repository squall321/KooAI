"""
ML Model Registry

Manages model lifecycle, versioning, and deployment.
"""

import os
import json
import asyncio
import time
from typing import Any, Dict, List, Optional, Type
from pathlib import Path
from collections import defaultdict
import logging

from .model_interface import (
    BaseMLModel,
    ModelMetadata,
    ModelType,
    ModelStatus,
    PredictionInput,
    PredictionOutput,
    ModelError,
    ModelLoadError,
    ModelPredictionError,
)

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for managing ML models.

    Handles model registration, versioning, and retrieval.
    """

    def __init__(self) -> None:
        """Initialize model registry."""
        self._models: Dict[str, Dict[str, BaseMLModel]] = defaultdict(dict)
        self._active_versions: Dict[str, str] = {}  # model_name -> active_version

    def register(
        self, model: BaseMLModel, set_active: bool = True
    ) -> None:
        """
        Register a model.

        Args:
            model: Model instance to register
            set_active: Set as active version for this model name

        Raises:
            ValueError: If model with same name and version already exists
        """
        name = model.metadata.name
        version = model.metadata.version

        if version in self._models.get(name, {}):
            raise ValueError(
                f"Model '{name}' version '{version}' is already registered"
            )

        self._models[name][version] = model

        if set_active:
            self._active_versions[name] = version

        logger.info(
            f"Registered model: {name} v{version} "
            f"(type={model.metadata.model_type.value}, active={set_active})"
        )

    def unregister(self, name: str, version: Optional[str] = None) -> None:
        """
        Unregister a model.

        Args:
            name: Model name
            version: Model version (if None, unregister all versions)
        """
        if version:
            if name in self._models and version in self._models[name]:
                del self._models[name][version]
                logger.info(f"Unregistered model: {name} v{version}")

                # Update active version if this was active
                if self._active_versions.get(name) == version:
                    remaining_versions = list(self._models[name].keys())
                    if remaining_versions:
                        # Set newest version as active
                        self._active_versions[name] = remaining_versions[-1]
                    else:
                        del self._active_versions[name]
        else:
            # Unregister all versions
            if name in self._models:
                del self._models[name]
                if name in self._active_versions:
                    del self._active_versions[name]
                logger.info(f"Unregistered all versions of model: {name}")

    def get(
        self, name: str, version: Optional[str] = None
    ) -> Optional[BaseMLModel]:
        """
        Get a model.

        Args:
            name: Model name
            version: Model version (if None, returns active version)

        Returns:
            Model instance or None if not found
        """
        if name not in self._models:
            return None

        if version is None:
            version = self._active_versions.get(name)
            if version is None:
                return None

        return self._models[name].get(version)

    def get_versions(self, name: str) -> List[str]:
        """Get all versions of a model."""
        return list(self._models.get(name, {}).keys())

    def get_active_version(self, name: str) -> Optional[str]:
        """Get active version for a model."""
        return self._active_versions.get(name)

    def set_active_version(self, name: str, version: str) -> None:
        """Set active version for a model."""
        if name not in self._models or version not in self._models[name]:
            raise ValueError(f"Model '{name}' version '{version}' not found")

        self._active_versions[name] = version
        logger.info(f"Set active version for '{name}': v{version}")

    def list_models(
        self, model_type: Optional[ModelType] = None
    ) -> List[Dict[str, Any]]:
        """
        List all registered models.

        Args:
            model_type: Filter by model type

        Returns:
            List of model information dictionaries
        """
        models = []

        for name, versions in self._models.items():
            for version, model in versions.items():
                if model_type and model.metadata.model_type != model_type:
                    continue

                is_active = self._active_versions.get(name) == version

                models.append({
                    "name": name,
                    "version": version,
                    "type": model.metadata.model_type.value,
                    "framework": model.metadata.framework.value,
                    "status": model.metadata.status.value,
                    "is_active": is_active,
                    "loaded": model._loaded,
                })

        return models


class ModelServer:
    """
    ML model serving infrastructure.

    Handles model loading, caching, and inference.

    Example:
        ```python
        # Initialize server
        server = ModelServer(model_dir="./models")

        # Load model
        await server.load_model(TurbulenceClassifier, "turbulence-v1.pkl")

        # Make predictions
        result = await server.predict(
            "turbulence-classifier",
            PredictionInput(data=[[1.0, 2.0, 3.0]])
        )
        ```
    """

    def __init__(self, model_dir: str = "./models", cache_models: bool = True):
        """
        Initialize model server.

        Args:
            model_dir: Directory containing model files
            cache_models: Keep loaded models in memory
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.cache_models = cache_models
        self.registry = ModelRegistry()
        self._inference_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "total_requests": 0,
                "total_predictions": 0,
                "total_time_ms": 0.0,
                "avg_time_ms": 0.0,
                "errors": 0,
            }
        )

    # ========================================================================
    # Model Loading
    # ========================================================================

    async def load_model(
        self,
        model_class: Type[BaseMLModel],
        model_path: str,
        set_active: bool = True,
    ) -> BaseMLModel:
        """
        Load a model from disk.

        Args:
            model_class: Model class to instantiate
            model_path: Path to model file (relative to model_dir)
            set_active: Set as active version

        Returns:
            Loaded model instance

        Raises:
            ModelLoadError: If model fails to load
        """
        # Check if model class has metadata
        if not hasattr(model_class, "_model_metadata"):
            raise ModelLoadError(
                model_class.__name__,
                "Model class must use @ml_model decorator",
            )

        try:
            # Instantiate model
            metadata = model_class._model_metadata  # type: ignore[attr-defined]
            model = model_class(metadata)

            # Load model from disk
            full_path = self.model_dir / model_path
            await model.load(str(full_path))

            model.metadata.status = ModelStatus.DEPLOYED

            # Register model
            self.registry.register(model, set_active=set_active)

            return model

        except Exception as e:
            raise ModelLoadError(
                model_class.__name__, f"Failed to load model: {str(e)}"
            ) from e

    async def unload_model(
        self, name: str, version: Optional[str] = None
    ) -> None:
        """
        Unload a model from memory.

        Args:
            name: Model name
            version: Model version (if None, unloads all versions)
        """
        self.registry.unregister(name, version)

        if version:
            logger.info(f"Unloaded model: {name} v{version}")
        else:
            logger.info(f"Unloaded all versions of model: {name}")

    # ========================================================================
    # Inference
    # ========================================================================

    async def predict(
        self,
        model_name: str,
        input_data: PredictionInput,
        version: Optional[str] = None,
    ) -> PredictionOutput:
        """
        Make predictions using a model.

        Args:
            model_name: Name of model to use
            input_data: Input data for prediction
            version: Model version (if None, uses active version)

        Returns:
            Prediction results

        Raises:
            ModelPredictionError: If prediction fails
        """
        # Get model
        model = self.registry.get(model_name, version)
        if not model:
            raise ModelPredictionError(
                model_name,
                f"Model not found (version={version or 'active'})",
            )

        if not model._loaded:
            raise ModelPredictionError(
                model_name, "Model is not loaded"
            )

        # Track inference time
        start_time = time.time()

        try:
            # Make prediction
            result = await model.predict(input_data)

            # Calculate inference time
            inference_time_ms = (time.time() - start_time) * 1000
            result.inference_time_ms = inference_time_ms

            # Update stats
            self._update_stats(
                model_name, inference_time_ms, len(result.predictions)
            )

            return result

        except Exception as e:
            # Update error stats
            stats = self._inference_stats[model_name]
            stats["errors"] += 1

            raise ModelPredictionError(
                model_name, f"Prediction failed: {str(e)}"
            ) from e

    async def batch_predict(
        self,
        model_name: str,
        input_batches: List[PredictionInput],
        version: Optional[str] = None,
        parallel: bool = True,
    ) -> List[PredictionOutput]:
        """
        Make batch predictions.

        Args:
            model_name: Name of model to use
            input_batches: List of input batches
            version: Model version
            parallel: Run batches in parallel

        Returns:
            List of prediction results
        """
        if parallel:
            tasks = [
                self.predict(model_name, inp, version)
                for inp in input_batches
            ]
            results = await asyncio.gather(*tasks)
            return list(results)
        else:
            results = []
            for inp in input_batches:
                result = await self.predict(model_name, inp, version)
                results.append(result)
            return results

    # ========================================================================
    # Model Validation
    # ========================================================================

    async def validate_model(
        self,
        model_name: str,
        validation_data: Dict[str, Any],
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a model on validation dataset.

        Args:
            model_name: Model name
            validation_data: Validation dataset
            version: Model version

        Returns:
            Validation metrics
        """
        model = self.registry.get(model_name, version)
        if not model:
            raise ModelError(
                model_name, "Model not found"
            )

        model.metadata.status = ModelStatus.VALIDATING

        try:
            metrics = await model.validate(validation_data)
            model.metadata.metrics = metrics
            model.metadata.status = ModelStatus.VALIDATED

            return {
                "model_name": model_name,
                "version": model.metadata.version,
                "metrics": metrics.__dict__,
            }

        except Exception as e:
            model.metadata.status = ModelStatus.FAILED
            raise ModelError(
                model_name, f"Validation failed: {str(e)}"
            ) from e

    # ========================================================================
    # Statistics
    # ========================================================================

    def _update_stats(
        self, model_name: str, inference_time_ms: float, num_predictions: int
    ) -> None:
        """Update inference statistics."""
        stats = self._inference_stats[model_name]
        stats["total_requests"] += 1
        stats["total_predictions"] += num_predictions
        stats["total_time_ms"] += inference_time_ms
        stats["avg_time_ms"] = (
            stats["total_time_ms"] / stats["total_requests"]
        )

    def get_stats(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get inference statistics.

        Args:
            model_name: Specific model (if None, returns all)

        Returns:
            Statistics dictionary
        """
        if model_name:
            return self._inference_stats.get(model_name, {})
        else:
            return dict(self._inference_stats)

    def reset_stats(self, model_name: Optional[str] = None) -> None:
        """
        Reset inference statistics.

        Args:
            model_name: Specific model (if None, resets all)
        """
        if model_name:
            if model_name in self._inference_stats:
                del self._inference_stats[model_name]
        else:
            self._inference_stats.clear()

    # ========================================================================
    # Model Management
    # ========================================================================

    def list_models(
        self, model_type: Optional[ModelType] = None
    ) -> List[Dict[str, Any]]:
        """List all registered models."""
        return self.registry.list_models(model_type)

    def get_model_info(
        self, model_name: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed model information."""
        model = self.registry.get(model_name, version)
        if not model:
            return None

        return model.get_info()

    async def set_active_version(self, model_name: str, version: str) -> None:
        """Set active version for a model."""
        self.registry.set_active_version(model_name, version)

    # ========================================================================
    # Model Persistence
    # ========================================================================

    def save_metadata(self, model_name: str, version: Optional[str] = None) -> None:
        """
        Save model metadata to disk.

        Args:
            model_name: Model name
            version: Model version
        """
        model = self.registry.get(model_name, version)
        if not model:
            raise ModelError(model_name, "Model not found")

        metadata_path = (
            self.model_dir / f"{model_name}_v{model.metadata.version}_metadata.json"
        )

        metadata_dict = {
            "name": model.metadata.name,
            "version": model.metadata.version,
            "model_type": model.metadata.model_type.value,
            "framework": model.metadata.framework.value,
            "description": model.metadata.description,
            "features": model.metadata.features,
            "target": model.metadata.target,
            "hyperparameters": model.metadata.hyperparameters,
            "metrics": model.metadata.metrics.__dict__,
            "tags": model.metadata.tags,
            "status": model.metadata.status.value,
            "created_at": model.metadata.created_at.isoformat(),
            "updated_at": model.metadata.updated_at.isoformat(),
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata_dict, f, indent=2)

        logger.info(f"Saved metadata for {model_name} v{model.metadata.version}")

    def load_metadata(self, metadata_path: str) -> ModelMetadata:
        """
        Load model metadata from disk.

        Args:
            metadata_path: Path to metadata JSON file

        Returns:
            Model metadata
        """
        with open(metadata_path, "r") as f:
            data = json.load(f)

        # Reconstruct metadata
        from .model_interface import ModelType, ModelFramework, ModelStatus, ModelMetrics
        from datetime import datetime

        metrics = ModelMetrics(**data.get("metrics", {}))

        metadata = ModelMetadata(
            name=data["name"],
            version=data["version"],
            model_type=ModelType(data["model_type"]),
            framework=ModelFramework(data["framework"]),
            description=data.get("description", ""),
            features=data.get("features", []),
            target=data.get("target"),
            hyperparameters=data.get("hyperparameters", {}),
            metrics=metrics,
            tags=data.get("tags", []),
            status=ModelStatus(data.get("status", "trained")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
        )

        return metadata


# Global model server instance
_model_server: Optional[ModelServer] = None


def get_model_server() -> ModelServer:
    """
    Get global model server instance.

    Returns:
        Model server singleton
    """
    global _model_server
    if _model_server is None:
        _model_server = ModelServer()
    return _model_server
