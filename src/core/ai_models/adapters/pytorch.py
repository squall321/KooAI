"""
PyTorch 모델 어댑터

PyTorch 모델을 로드하고 추론을 수행합니다.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseModelAdapter, InferenceResult, ModelConfig, ModelFramework


class PyTorchAdapter(BaseModelAdapter):
    """PyTorch 모델 어댑터"""

    def __init__(self):
        super().__init__()
        self.device: Optional[str] = None

    def load(self, config: ModelConfig) -> None:
        """
        PyTorch 모델 로드

        Args:
            config: 모델 설정

        Raises:
            ImportError: PyTorch가 설치되지 않았을 때
            FileNotFoundError: 모델 파일이 없을 때
            RuntimeError: 모델 로드 실패 시
        """
        try:
            import torch
        except ImportError:
            raise ImportError(
                "PyTorch is not installed. Install with: pip install torch"
            )

        if config.framework != ModelFramework.PYTORCH:
            raise ValueError(f"Expected PyTorch framework, got {config.framework}")

        # 디바이스 설정
        self.device = config.device
        if self.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")

        # 모델 로드
        try:
            if config.model_path.suffix == ".pt" or config.model_path.suffix == ".pth":
                # PyTorch 체크포인트 로드
                checkpoint = torch.load(config.model_path, map_location=self.device)

                # 체크포인트 구조 확인
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    # 훈련 중 저장된 체크포인트
                    state_dict = checkpoint["model_state_dict"]
                else:
                    # state_dict만 저장된 경우
                    state_dict = checkpoint

                # 모델 아키텍처가 config에 있으면 사용
                if "model_class" in config.config:
                    model_class = config.config["model_class"]
                    model_kwargs = config.config.get("model_kwargs", {})
                    self.model = model_class(**model_kwargs)
                    self.model.load_state_dict(state_dict)
                else:
                    # state_dict를 그대로 모델로 사용 (일부 경우)
                    self.model = state_dict

            else:
                raise ValueError(
                    f"Unsupported file format: {config.model_path.suffix}"
                )

            # 모델을 디바이스로 이동
            if hasattr(self.model, "to"):
                self.model = self.model.to(self.device)

            # 평가 모드로 전환
            if hasattr(self.model, "eval"):
                self.model.eval()

            self.config = config
            self._is_loaded = True

        except Exception as e:
            raise RuntimeError(f"Failed to load PyTorch model: {str(e)}")

    def predict(self, input_data: Any, **kwargs) -> InferenceResult:
        """
        추론 수행

        Args:
            input_data: 입력 데이터 (Tensor, numpy array, list 등)
            **kwargs: 추가 파라미터

        Returns:
            InferenceResult: 추론 결과

        Raises:
            RuntimeError: 추론 실패 시
        """
        self._ensure_loaded()

        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch is not installed")

        # 추론 시간 측정 시작
        start_time = time.time()

        try:
            # 입력 데이터를 텐서로 변환
            if not isinstance(input_data, torch.Tensor):
                if isinstance(input_data, list):
                    input_tensor = torch.tensor(input_data)
                else:
                    input_tensor = torch.from_numpy(input_data)
            else:
                input_tensor = input_data

            # 디바이스로 이동
            input_tensor = input_tensor.to(self.device)

            # 추론 수행 (gradient 계산 비활성화)
            with torch.no_grad():
                output = self.model(input_tensor, **kwargs)

            # 추론 시간 계산
            inference_time_ms = (time.time() - start_time) * 1000

            # 출력을 numpy로 변환 (선택적)
            if kwargs.get("return_numpy", True):
                if isinstance(output, torch.Tensor):
                    output = output.cpu().numpy()
                elif isinstance(output, tuple):
                    output = tuple(
                        o.cpu().numpy() if isinstance(o, torch.Tensor) else o
                        for o in output
                    )

            return InferenceResult(
                output=output,
                metadata={
                    "device": self.device,
                    "input_shape": list(input_tensor.shape),
                },
                inference_time_ms=inference_time_ms,
            )

        except Exception as e:
            raise RuntimeError(f"PyTorch inference failed: {str(e)}")

    def batch_predict(
        self, input_data_list: List[Any], **kwargs
    ) -> List[InferenceResult]:
        """
        배치 추론 (최적화된 구현)

        Args:
            input_data_list: 입력 데이터 리스트
            **kwargs: 추가 파라미터

        Returns:
            List[InferenceResult]: 추론 결과 리스트
        """
        self._ensure_loaded()

        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch is not installed")

        # 배치 크기 확인
        batch_size = self.config.batch_size if self.config else len(input_data_list)

        results = []
        for i in range(0, len(input_data_list), batch_size):
            batch = input_data_list[i : i + batch_size]

            # 배치를 텐서로 변환
            if not isinstance(batch[0], torch.Tensor):
                batch_tensor = torch.stack([torch.tensor(d) for d in batch])
            else:
                batch_tensor = torch.stack(batch)

            # 배치 추론
            batch_result = self.predict(batch_tensor, **kwargs)

            # 결과를 개별 항목으로 분리
            batch_output = batch_result.output
            for j in range(len(batch)):
                results.append(
                    InferenceResult(
                        output=batch_output[j],
                        metadata=batch_result.metadata,
                        inference_time_ms=batch_result.inference_time_ms / len(batch),
                    )
                )

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 조회

        Returns:
            Dict: 모델 정보
        """
        self._ensure_loaded()

        info = {
            "framework": "pytorch",
            "device": self.device,
            "is_loaded": self._is_loaded,
        }

        # 모델 구조 정보 (가능한 경우)
        if hasattr(self.model, "__class__"):
            info["model_class"] = self.model.__class__.__name__

        # 파라미터 수 계산 (가능한 경우)
        if hasattr(self.model, "parameters"):
            try:
                total_params = sum(p.numel() for p in self.model.parameters())
                trainable_params = sum(
                    p.numel() for p in self.model.parameters() if p.requires_grad
                )
                info["total_parameters"] = total_params
                info["trainable_parameters"] = trainable_params
            except:
                pass

        return info
