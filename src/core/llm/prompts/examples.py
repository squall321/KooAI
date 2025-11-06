"""
Few-shot 예시 관리

프롬프트에 사용할 예시를 관리합니다.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
from pathlib import Path


@dataclass
class Example:
    """Few-shot 학습 예시"""

    input: str
    output: str
    metadata: Optional[Dict[str, Any]] = None

    def format(self, input_label: str = "Input", output_label: str = "Output") -> str:
        """
        예시를 문자열로 포맷

        Args:
            input_label: 입력 라벨
            output_label: 출력 라벨

        Returns:
            str: 포맷된 예시
        """
        return f"{input_label}: {self.input}\n{output_label}: {self.output}"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "input": self.input,
            "output": self.output,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Example":
        """딕셔너리에서 생성"""
        return cls(
            input=data["input"],
            output=data["output"],
            metadata=data.get("metadata"),
        )


class FewShotExampleManager:
    """
    Few-shot 예시 관리자

    예시를 저장하고 선택적으로 로드합니다.
    """

    def __init__(self):
        """초기화"""
        self._examples: Dict[str, List[Example]] = {}

    def add_example(
        self,
        category: str,
        input_text: str,
        output_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Example:
        """
        예시 추가

        Args:
            category: 카테고리 (예: "summary", "comparison")
            input_text: 입력 텍스트
            output_text: 출력 텍스트
            metadata: 메타데이터 (optional)

        Returns:
            Example: 추가된 예시
        """
        example = Example(input=input_text, output=output_text, metadata=metadata)

        if category not in self._examples:
            self._examples[category] = []

        self._examples[category].append(example)
        return example

    def get_examples(
        self,
        category: str,
        n: Optional[int] = None,
        shuffle: bool = False,
    ) -> List[Example]:
        """
        예시 조회

        Args:
            category: 카테고리
            n: 반환할 예시 개수 (None이면 전체)
            shuffle: 무작위 선택 여부

        Returns:
            List[Example]: 예시 리스트
        """
        if category not in self._examples:
            return []

        examples = self._examples[category]

        if shuffle:
            import random

            examples = examples.copy()
            random.shuffle(examples)

        if n is not None:
            examples = examples[:n]

        return examples

    def format_examples(
        self,
        category: str,
        n: Optional[int] = None,
        shuffle: bool = False,
        separator: str = "\n\n",
    ) -> str:
        """
        예시를 문자열로 포맷

        Args:
            category: 카테고리
            n: 예시 개수
            shuffle: 무작위 선택 여부
            separator: 예시 구분자

        Returns:
            str: 포맷된 예시들
        """
        examples = self.get_examples(category, n=n, shuffle=shuffle)
        formatted = [ex.format() for ex in examples]
        return separator.join(formatted)

    def remove_examples(self, category: str) -> None:
        """
        카테고리의 모든 예시 제거

        Args:
            category: 카테고리
        """
        if category in self._examples:
            del self._examples[category]

    def list_categories(self) -> List[str]:
        """
        카테고리 목록 반환

        Returns:
            List[str]: 카테고리 리스트
        """
        return list(self._examples.keys())

    def count(self, category: Optional[str] = None) -> int:
        """
        예시 개수 반환

        Args:
            category: 카테고리 (None이면 전체)

        Returns:
            int: 예시 개수
        """
        if category:
            return len(self._examples.get(category, []))
        else:
            return sum(len(examples) for examples in self._examples.values())

    def save_to_file(self, file_path: Path) -> None:
        """
        예시를 파일에 저장

        Args:
            file_path: 파일 경로
        """
        data = {
            category: [ex.to_dict() for ex in examples]
            for category, examples in self._examples.items()
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, file_path: Path) -> None:
        """
        파일에서 예시 로드

        Args:
            file_path: 파일 경로
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        for category, example_dicts in data.items():
            self._examples[category] = [
                Example.from_dict(ex_dict) for ex_dict in example_dicts
            ]


# 기본 예시들
DEFAULT_SIMULATION_EXAMPLES = {
    "summary": [
        Example(
            input="""Simulation: CFD Analysis of Airfoil
Type: Computational Fluid Dynamics
Parameters: velocity=50m/s, angle_of_attack=5deg, Reynolds=1e6
Results: lift_coefficient=0.8, drag_coefficient=0.02, pressure_distribution=...""",
            output="""This CFD simulation analyzed airfoil performance at moderate velocity (50 m/s) and low angle of attack (5°). Key findings:

1. Lift coefficient of 0.8 indicates good aerodynamic efficiency
2. Low drag coefficient (0.02) suggests minimal resistance
3. The lift-to-drag ratio of 40:1 is excellent for this configuration
4. Pressure distribution shows expected behavior with higher pressure on lower surface

Recommendations:
- Test higher angles of attack to find optimal performance
- Investigate boundary layer behavior near trailing edge
- Consider parametric study varying Reynolds number""",
        ),
    ],
    "comparison": [
        Example(
            input="""Sim1: temperature=300K, pressure=1atm, flow_rate=10L/s → efficiency=0.75
Sim2: temperature=350K, pressure=1atm, flow_rate=10L/s → efficiency=0.82""",
            output="""Comparison Analysis:

Parameter Changes:
- Temperature increased from 300K to 350K (+16.7%)
- Pressure and flow rate remained constant

Results Impact:
- Efficiency improved from 0.75 to 0.82 (+9.3%)
- Higher temperature resulted in better performance

Conclusion:
- Temperature increase positively impacted efficiency
- Recommend: Further testing at 375K and 400K to find optimal temperature
- Monitor thermal limits of materials""",
        ),
    ],
}
