"""
Hugging Face 모델 어댑터

Hugging Face Transformers 모델을 로드하고 추론을 수행합니다.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import BaseModelAdapter, InferenceResult, ModelConfig, ModelFramework


class HuggingFaceAdapter(BaseModelAdapter):
    """Hugging Face Transformers 모델 어댑터"""

    def __init__(self):
        super().__init__()
        self.tokenizer: Optional[Any] = None
        self.device: Optional[str] = None
        self.model_type: Optional[str] = None  # text-generation, text-classification, etc.

    def load(self, config: ModelConfig) -> None:
        """
        Hugging Face 모델 로드

        Args:
            config: 모델 설정
                - config.config should contain:
                    - model_type: 'AutoModel', 'AutoModelForSequenceClassification', etc.
                    - task: 'text-generation', 'text-classification', etc. (optional)
                    - tokenizer_path: 토크나이저 경로 (optional, defaults to model_path)

        Raises:
            ImportError: transformers가 설치되지 않았을 때
            FileNotFoundError: 모델 파일이 없을 때
            RuntimeError: 모델 로드 실패 시
        """
        try:
            from transformers import AutoModel, AutoTokenizer, AutoConfig
        except ImportError:
            raise ImportError(
                "Transformers is not installed. "
                "Install with: pip install transformers"
            )

        if config.framework != ModelFramework.HUGGINGFACE:
            raise ValueError(
                f"Expected HuggingFace framework, got {config.framework}"
            )

        # 디바이스 설정
        self.device = config.device

        try:
            # 모델 타입 결정
            model_type = config.config.get("model_type", "AutoModel")
            self.model_type = config.config.get("task", "feature-extraction")

            # 모델 클래스 가져오기
            if model_type == "AutoModel":
                from transformers import AutoModel as ModelClass
            elif model_type == "AutoModelForSequenceClassification":
                from transformers import (
                    AutoModelForSequenceClassification as ModelClass,
                )
            elif model_type == "AutoModelForCausalLM":
                from transformers import AutoModelForCausalLM as ModelClass
            elif model_type == "AutoModelForMaskedLM":
                from transformers import AutoModelForMaskedLM as ModelClass
            else:
                # 기본값
                ModelClass = AutoModel

            # 모델 로드
            model_path_str = str(config.model_path)
            self.model = ModelClass.from_pretrained(
                model_path_str, **config.config.get("model_kwargs", {})
            )

            # 토크나이저 로드
            tokenizer_path = config.config.get("tokenizer_path", model_path_str)
            self.tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_path, **config.config.get("tokenizer_kwargs", {})
            )

            # 모델을 디바이스로 이동
            self.model = self.model.to(self.device)

            # 평가 모드로 전환
            self.model.eval()

            self.config = config
            self._is_loaded = True

        except Exception as e:
            raise RuntimeError(f"Failed to load Hugging Face model: {str(e)}")

    def predict(
        self,
        input_data: Union[str, List[str], Dict[str, Any]],
        **kwargs,
    ) -> InferenceResult:
        """
        추론 수행

        Args:
            input_data: 입력 데이터
                - str: 단일 텍스트
                - List[str]: 텍스트 리스트
                - Dict: 토크나이저 출력
            **kwargs: 추가 파라미터
                - max_length: 최대 시퀀스 길이
                - return_tensors: 반환 형식 ("pt", "np", etc.)
                - return_dict: dict 형태로 반환 여부

        Returns:
            InferenceResult: 추론 결과

        Raises:
            RuntimeError: 추론 실패 시
        """
        self._ensure_loaded()

        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch is required for Hugging Face models")

        # 추론 시간 측정 시작
        start_time = time.time()

        try:
            # 입력 토크나이징 (필요한 경우)
            if isinstance(input_data, (str, list)):
                inputs = self.tokenizer(
                    input_data,
                    padding=True,
                    truncation=True,
                    max_length=kwargs.get("max_length", 512),
                    return_tensors="pt",
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            elif isinstance(input_data, dict):
                # 이미 토크나이징된 입력
                inputs = {
                    k: v.to(self.device) if hasattr(v, "to") else v
                    for k, v in input_data.items()
                }
            else:
                raise ValueError(
                    f"Unsupported input type: {type(input_data)}. "
                    f"Expected str, List[str], or Dict"
                )

            # 추론 수행
            with torch.no_grad():
                outputs = self.model(**inputs, **kwargs)

            # 추론 시간 계산
            inference_time_ms = (time.time() - start_time) * 1000

            # 출력 처리
            if hasattr(outputs, "logits"):
                # 분류, 생성 등의 경우
                output_data = outputs.logits
            elif hasattr(outputs, "last_hidden_state"):
                # 특징 추출의 경우
                output_data = outputs.last_hidden_state
            else:
                # 기타
                output_data = outputs

            # numpy 변환 (선택적)
            if kwargs.get("return_numpy", False):
                if hasattr(output_data, "cpu"):
                    output_data = output_data.cpu().numpy()

            return InferenceResult(
                output=output_data,
                metadata={
                    "device": self.device,
                    "model_type": self.model_type,
                    "input_type": type(input_data).__name__,
                },
                inference_time_ms=inference_time_ms,
            )

        except Exception as e:
            raise RuntimeError(f"Hugging Face inference failed: {str(e)}")

    def batch_predict(
        self, input_data_list: List[Any], **kwargs
    ) -> List[InferenceResult]:
        """
        배치 추론

        Hugging Face는 자체적으로 배치를 잘 처리하므로,
        리스트를 한번에 처리하고 결과를 분리합니다.

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
            raise ImportError("PyTorch is required for Hugging Face models")

        # 텍스트 리스트인 경우 한번에 처리
        if all(isinstance(d, str) for d in input_data_list):
            batch_result = self.predict(input_data_list, **kwargs)

            # 결과를 개별 항목으로 분리
            batch_output = batch_result.output
            results = []

            for i in range(len(input_data_list)):
                results.append(
                    InferenceResult(
                        output=batch_output[i] if hasattr(batch_output, "__getitem__") else batch_output,
                        metadata=batch_result.metadata,
                        inference_time_ms=batch_result.inference_time_ms
                        / len(input_data_list),
                    )
                )

            return results
        else:
            # 기본 구현 사용
            return super().batch_predict(input_data_list, **kwargs)

    def generate(self, input_text: Union[str, List[str]], **generation_kwargs) -> str:
        """
        텍스트 생성 (LLM용)

        Args:
            input_text: 입력 텍스트 (프롬프트)
            **generation_kwargs: 생성 파라미터
                - max_new_tokens: 생성할 최대 토큰 수
                - temperature: 샘플링 온도
                - top_p: nucleus sampling
                - do_sample: 샘플링 여부

        Returns:
            str: 생성된 텍스트

        Raises:
            RuntimeError: 생성 실패 시
        """
        self._ensure_loaded()

        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch is required for Hugging Face models")

        try:
            # 입력 토크나이징
            inputs = self.tokenizer(input_text, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 텍스트 생성
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **generation_kwargs)

            # 디코딩
            generated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

            return generated_text

        except Exception as e:
            raise RuntimeError(f"Text generation failed: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 조회

        Returns:
            Dict: 모델 정보
        """
        self._ensure_loaded()

        info = {
            "framework": "huggingface",
            "device": self.device,
            "model_type": self.model_type,
            "is_loaded": self._is_loaded,
        }

        # 모델 설정 정보
        if hasattr(self.model, "config"):
            config = self.model.config
            info["model_name"] = getattr(config, "model_type", "unknown")
            info["num_parameters"] = getattr(config, "num_parameters", None)
            info["hidden_size"] = getattr(config, "hidden_size", None)
            info["num_layers"] = getattr(config, "num_hidden_layers", None)
            info["vocab_size"] = getattr(config, "vocab_size", None)

        # 토크나이저 정보
        if self.tokenizer is not None:
            info["vocab_size_tokenizer"] = len(self.tokenizer)
            info["model_max_length"] = getattr(
                self.tokenizer, "model_max_length", None
            )

        return info

    def unload(self) -> None:
        """모델 및 토크나이저 언로드"""
        super().unload()
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
