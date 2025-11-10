"""
ML Model Serving API Routes

Endpoints for ML model management and inference.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Body
from pydantic import BaseModel, Field

from src.infrastructure.ml_pipelines.model_registry import get_model_server
from src.infrastructure.ml_pipelines.model_interface import (
    PredictionInput,
    ModelType,
)

router = APIRouter(prefix="/ml/models", tags=["ML Models"])


# ============================================================================
# Pydantic Models
# ============================================================================


class ModelInfo(BaseModel):
    """Model information response."""

    name: str
    version: str
    type: str
    framework: str
    status: str
    is_active: bool
    loaded: bool

    class Config:
        schema_extra = {
            "example": {
                "name": "turbulence-classifier",
                "version": "1.0.0",
                "type": "classification",
                "framework": "scikit-learn",
                "status": "deployed",
                "is_active": True,
                "loaded": True,
            }
        }


class PredictRequest(BaseModel):
    """Prediction request."""

    data: Any = Field(..., description="Input data for prediction")
    feature_names: Optional[List[str]] = Field(None, description="Feature names")
    return_probabilities: bool = Field(False, description="Return class probabilities")
    return_confidence: bool = Field(False, description="Return confidence scores")

    class Config:
        schema_extra = {
            "example": {
                "data": [
                    [1.5, 2.3, 0.8, 0.2, 0.3, 0.1, 5000.0, 125.5],
                    [2.1, 1.8, 1.2, 0.4, 0.5, 0.3, 6000.0, 180.2],
                ],
                "return_probabilities": True,
                "return_confidence": True,
            }
        }


class PredictResponse(BaseModel):
    """Prediction response."""

    model_name: str
    model_version: str
    predictions: List[Any]
    probabilities: Optional[List[List[float]]] = None
    confidence: Optional[List[float]] = None
    inference_time_ms: float
    metadata: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "model_name": "turbulence-classifier",
                "model_version": "1.0.0",
                "predictions": ["low", "medium"],
                "probabilities": [
                    [0.85, 0.10, 0.05],
                    [0.20, 0.65, 0.15],
                ],
                "confidence": [0.85, 0.65],
                "inference_time_ms": 12.5,
                "metadata": {"classes": ["low", "medium", "high"]},
            }
        }


class BatchPredictRequest(BaseModel):
    """Batch prediction request."""

    batches: List[PredictRequest] = Field(..., description="List of prediction requests")
    parallel: bool = Field(True, description="Run batches in parallel")

    class Config:
        schema_extra = {
            "example": {
                "batches": [
                    {"data": [[1.0, 2.0, 3.0]]},
                    {"data": [[4.0, 5.0, 6.0]]},
                ],
                "parallel": True,
            }
        }


class ValidationRequest(BaseModel):
    """Model validation request."""

    validation_data: Dict[str, Any] = Field(
        ..., description="Validation dataset (X, y)"
    )

    class Config:
        schema_extra = {
            "example": {
                "validation_data": {
                    "X": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                    "y": [0, 1],
                }
            }
        }


class SetActiveVersionRequest(BaseModel):
    """Request to set active model version."""

    version: str = Field(..., description="Version to set as active")


# ============================================================================
# Model Discovery Endpoints
# ============================================================================


@router.get("/", response_model=List[ModelInfo])
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
) -> List[ModelInfo]:
    """
    List all registered models.

    **Example**:
    ```bash
    # List all models
    curl http://localhost:8000/api/v1/ml/models

    # Filter by type
    curl "http://localhost:8000/api/v1/ml/models?model_type=classification"
    ```
    """
    server = get_model_server()

    if model_type:
        try:
            m_type = ModelType(model_type)
            models = server.list_models(model_type=m_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model type: {model_type}",
            )
    else:
        models = server.list_models()

    return models  # type: ignore[return-value]


@router.get("/{model_name}", response_model=Dict[str, Any])
async def get_model_info(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version"),
) -> Dict[str, Any]:
    """
    Get detailed information about a model.

    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/ml/models/turbulence-classifier
    ```
    """
    server = get_model_server()
    info = server.get_model_info(model_name, version)

    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    return info


# ============================================================================
# Prediction Endpoints
# ============================================================================


@router.post("/{model_name}/predict", response_model=PredictResponse)
async def predict(
    model_name: str,
    request: PredictRequest,
    version: Optional[str] = Query(None, description="Model version to use"),
) -> Dict[str, Any]:
    """
    Make predictions using a model.

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ml/models/turbulence-classifier/predict" \\
      -H "Content-Type: application/json" \\
      -d '{
        "data": [[1.5, 2.3, 0.8, 0.2, 0.3, 0.1, 5000.0, 125.5]],
        "return_probabilities": true,
        "return_confidence": true
      }'
    ```
    """
    server = get_model_server()

    # Create prediction input
    prediction_input = PredictionInput(
        data=request.data,
        feature_names=request.feature_names,
        return_probabilities=request.return_probabilities,
        return_confidence=request.return_confidence,
    )

    try:
        result = await server.predict(model_name, prediction_input, version)

        # Get model info for response
        model = server.registry.get(model_name, version)
        model_version = model.metadata.version if model else "unknown"

        return PredictResponse(
            model_name=model_name,
            model_version=model_version,
            predictions=result.predictions.tolist() if hasattr(result.predictions, 'tolist') else list(result.predictions),
            probabilities=result.probabilities.tolist() if result.probabilities is not None else None,
            confidence=result.confidence,
            inference_time_ms=result.inference_time_ms,
            metadata=result.metadata,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post("/{model_name}/batch-predict", response_model=List[PredictResponse])
async def batch_predict(
    model_name: str,
    request: BatchPredictRequest,
    version: Optional[str] = Query(None, description="Model version to use"),
) -> Dict[str, Any]:
    """
    Make batch predictions.

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ml/models/turbulence-classifier/batch-predict" \\
      -H "Content-Type: application/json" \\
      -d '{
        "batches": [
          {"data": [[1.0, 2.0, 3.0, 0.1, 0.2, 0.3, 1000, 50]]},
          {"data": [[4.0, 5.0, 6.0, 0.4, 0.5, 0.6, 2000, 100]]}
        ],
        "parallel": true
      }'
    ```
    """
    server = get_model_server()

    # Convert requests to PredictionInput
    inputs = [
        PredictionInput(
            data=batch.data,
            feature_names=batch.feature_names,
            return_probabilities=batch.return_probabilities,
            return_confidence=batch.return_confidence,
        )
        for batch in request.batches
    ]

    try:
        results = await server.batch_predict(
            model_name, inputs, version, parallel=request.parallel
        )

        # Get model version
        model = server.registry.get(model_name, version)
        model_version = model.metadata.version if model else "unknown"

        # Format responses
        responses = []
        for result in results:
            responses.append(
                PredictResponse(
                    model_name=model_name,
                    model_version=model_version,
                    predictions=result.predictions.tolist() if hasattr(result.predictions, 'tolist') else list(result.predictions),
                    probabilities=result.probabilities.tolist() if result.probabilities is not None else None,
                    confidence=result.confidence,
                    inference_time_ms=result.inference_time_ms,
                    metadata=result.metadata,
                )
            )

        return responses  # type: ignore[return-value]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}",
        )


# ============================================================================
# Model Validation
# ============================================================================


@router.post("/{model_name}/validate", response_model=Dict[str, Any])
async def validate_model(
    model_name: str,
    request: ValidationRequest,
    version: Optional[str] = Query(None, description="Model version"),
) -> Dict[str, Any]:
    """
    Validate a model on validation dataset.

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ml/models/turbulence-classifier/validate" \\
      -H "Content-Type: application/json" \\
      -d '{
        "validation_data": {
          "X": [[1.0, 2.0, 3.0, 0.1, 0.2, 0.3, 1000, 50]],
          "y": [0]
        }
      }'
    ```
    """
    server = get_model_server()

    try:
        result = await server.validate_model(
            model_name, request.validation_data, version
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


# ============================================================================
# Model Management
# ============================================================================


@router.post("/{model_name}/set-active", response_model=Dict[str, str])
async def set_active_version(model_name: str, request: SetActiveVersionRequest) -> Dict[str, str]:
    """
    Set active version for a model.

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/ml/models/turbulence-classifier/set-active" \\
      -H "Content-Type: application/json" \\
      -d '{"version": "2.0.0"}'
    ```
    """
    server = get_model_server()

    try:
        await server.set_active_version(model_name, request.version)
        return {
            "message": f"Set active version for '{model_name}' to v{request.version}"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/{model_name}", response_model=Dict[str, str])
async def unload_model(
    model_name: str,
    version: Optional[str] = Query(None, description="Version to unload"),
) -> Dict[str, str]:
    """
    Unload a model from memory.

    **Example**:
    ```bash
    # Unload specific version
    curl -X DELETE "http://localhost:8000/api/v1/ml/models/turbulence-classifier?version=1.0.0"

    # Unload all versions
    curl -X DELETE "http://localhost:8000/api/v1/ml/models/turbulence-classifier"
    ```
    """
    server = get_model_server()

    await server.unload_model(model_name, version)

    if version:
        return {"message": f"Unloaded model '{model_name}' v{version}"}
    else:
        return {"message": f"Unloaded all versions of model '{model_name}'"}


# ============================================================================
# Statistics
# ============================================================================


@router.get("/{model_name}/stats", response_model=Dict[str, Any])
async def get_model_stats(model_name: str) -> Dict[str, Any]:
    """
    Get inference statistics for a model.

    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/ml/models/turbulence-classifier/stats
    ```
    """
    server = get_model_server()
    stats = server.get_stats(model_name)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No statistics available for this model",
        )

    return stats


@router.delete("/{model_name}/stats", response_model=Dict[str, str])
async def reset_model_stats(model_name: str) -> Dict[str, str]:
    """
    Reset inference statistics for a model.

    **Example**:
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/ml/models/turbulence-classifier/stats"
    ```
    """
    server = get_model_server()
    server.reset_stats(model_name)

    return {"message": f"Reset statistics for model '{model_name}'"}


@router.get("/stats/all", response_model=Dict[str, Any])
async def get_all_stats() -> Dict[str, Any]:
    """
    Get inference statistics for all models.

    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/ml/models/stats/all
    ```
    """
    server = get_model_server()
    return server.get_stats()
