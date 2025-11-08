"""
ONNX 모델 어댑터

ONNX Runtime을 사용하여 ONNX 모델을 로드하고 추론을 수행합니다.
"""

import time
import numpy as np
from typing import Any, Dict, List, Optional, Union

from .base import BaseModelAdapter, InferenceResult, ModelConfig, ModelFramework


class ONNXAdapter(BaseModelAdapter):
    """ONNX 모델 어댑터"""

    def __init__(self):
        super().__init__()
        self.session: Optional[Any] = None
        self.input_names: List[str] = []
        self.output_names: List[str] = []
        self.providers: List[str] = []

    def load(self, config: ModelConfig) -> None:
        """
        ONNX 모델 로드

        Args:
            config: 모델 설정
                - config.config should contain:
                    - providers: Execution providers (optional)
                      e.g., ['CUDAExecutionProvider', 'CPUExecutionProvider']
                    - sess_options: SessionOptions (optional)

        Raises:
            ImportError: onnxruntime가 설치되지 않았을 때
            FileNotFoundError: 모델 파일이 없을 때
            RuntimeError: 모델 로드 실패 시
        """
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError(
                "ONNX Runtime is not installed. "
                "Install with: pip install onnxruntime or onnxruntime-gpu"
            )

        if config.framework != ModelFramework.ONNX:
            raise ValueError(f"Expected ONNX framework, got {config.framework}")

        if not config.model_path.suffix == ".onnx":
            raise ValueError(f"Expected .onnx file, got {config.model_path.suffix}")

        try:
            # Execution providers 설정
            if "providers" in config.config:
                self.providers = config.config["providers"]
            else:
                # 기본 providers
                available_providers = ort.get_available_providers()
                if (
                    config.device.startswith("cuda")
                    and "CUDAExecutionProvider" in available_providers
                ):
                    self.providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                else:
                    self.providers = ["CPUExecutionProvider"]

            # Session options (선택적)
            sess_options = config.config.get("sess_options", None)

            # 모델 로드
            self.session = ort.InferenceSession(
                str(config.model_path),
                sess_options=sess_options,
                providers=self.providers,
            )

            # 입력/출력 이름 가져오기
            self.input_names = [inp.name for inp in self.session.get_inputs()]
            self.output_names = [out.name for out in self.session.get_outputs()]

            self.config = config
            self._is_loaded = True

        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {str(e)}")

    def predict(
        self,
        input_data: Union[np.ndarray, Dict[str, np.ndarray], List[np.ndarray]],
        **kwargs,
    ) -> InferenceResult:
        """
        추론 수행

        Args:
            input_data: 입력 데이터
                - np.ndarray: 단일 입력 (첫 번째 입력에 할당)
                - Dict[str, np.ndarray]: 입력 이름 -> 데이터 매핑
                - List[np.ndarray]: 입력 리스트 (순서대로 할당)
            **kwargs: 추가 파라미터
                - output_names: 반환할 출력 이름 리스트 (optional)

        Returns:
            InferenceResult: 추론 결과

        Raises:
            RuntimeError: 추론 실패 시
        """
        self._ensure_loaded()

        # 추론 시간 측정 시작
        start_time = time.time()

        try:
            # 입력 데이터를 ONNX 형식으로 변환
            if isinstance(input_data, np.ndarray):
                # 단일 배열 -> 첫 번째 입력
                input_feed = {self.input_names[0]: input_data}
            elif isinstance(input_data, dict):
                # 딕셔너리 -> 그대로 사용
                input_feed = input_data
            elif isinstance(input_data, list):
                # 리스트 -> 순서대로 매핑
                if len(input_data) != len(self.input_names):
                    raise ValueError(
                        f"Expected {len(self.input_names)} inputs, " f"got {len(input_data)}"
                    )
                input_feed = {name: data for name, data in zip(self.input_names, input_data)}
            else:
                raise ValueError(
                    f"Unsupported input type: {type(input_data)}. "
                    f"Expected np.ndarray, Dict, or List"
                )

            # 출력 이름 결정
            output_names = kwargs.get("output_names", self.output_names)

            # 추론 수행
            outputs = self.session.run(output_names, input_feed)

            # 추론 시간 계산
            inference_time_ms = (time.time() - start_time) * 1000

            # 출력 처리 (단일 출력이면 리스트 해제)
            if len(outputs) == 1:
                output_data = outputs[0]
            else:
                output_data = outputs

            return InferenceResult(
                output=output_data,
                metadata={
                    "providers": self.providers,
                    "input_names": self.input_names,
                    "output_names": output_names,
                    "num_inputs": len(self.input_names),
                    "num_outputs": len(outputs),
                },
                inference_time_ms=inference_time_ms,
            )

        except Exception as e:
            raise RuntimeError(f"ONNX inference failed: {str(e)}")

    def batch_predict(self, input_data_list: List[Any], **kwargs) -> List[InferenceResult]:
        """
        배치 추론

        Args:
            input_data_list: 입력 데이터 리스트
            **kwargs: 추가 파라미터

        Returns:
            List[InferenceResult]: 추론 결과 리스트
        """
        self._ensure_loaded()

        # 배치 크기 확인
        batch_size = self.config.batch_size if self.config else len(input_data_list)

        results = []
        for i in range(0, len(input_data_list), batch_size):
            batch = input_data_list[i : i + batch_size]

            # 배치를 numpy 배열로 결합
            if isinstance(batch[0], np.ndarray):
                # 단일 입력의 경우
                batch_array = np.stack(batch)
                batch_result = self.predict(batch_array, **kwargs)

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
            else:
                # 다중 입력 또는 복잡한 경우: 개별 처리
                for data in batch:
                    results.append(self.predict(data, **kwargs))

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 조회

        Returns:
            Dict: 모델 정보
        """
        self._ensure_loaded()

        info = {
            "framework": "onnx",
            "providers": self.providers,
            "is_loaded": self._is_loaded,
            "num_inputs": len(self.input_names),
            "num_outputs": len(self.output_names),
        }

        # 입력 정보
        input_info = []
        for inp in self.session.get_inputs():
            input_info.append(
                {
                    "name": inp.name,
                    "shape": inp.shape,
                    "type": inp.type,
                }
            )
        info["inputs"] = input_info

        # 출력 정보
        output_info = []
        for out in self.session.get_outputs():
            output_info.append(
                {
                    "name": out.name,
                    "shape": out.shape,
                    "type": out.type,
                }
            )
        info["outputs"] = output_info

        # 메타데이터 (가능한 경우)
        try:
            metadata = self.session.get_modelmeta()
            info["description"] = metadata.description
            info["producer_name"] = metadata.producer_name
            info["version"] = metadata.version
        except:
            pass

        return info

    def unload(self) -> None:
        """세션 언로드"""
        if self.session is not None:
            del self.session
            self.session = None
        self.input_names = []
        self.output_names = []
        self._is_loaded = False
