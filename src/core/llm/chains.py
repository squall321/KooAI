"""
LLM 체인

복잡한 LLM 작업을 위한 체인 구성.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .clients.base import BaseLLMClient
from .prompts.template import (
    PromptTemplate,
    SIMULATION_SUMMARY_TEMPLATE,
    SIMULATION_COMPARISON_TEMPLATE,
    INSIGHT_GENERATION_TEMPLATE,
)
from .prompts.examples import FewShotExampleManager


@dataclass
class ChainResult:
    """체인 실행 결과"""

    output: str
    intermediate_steps: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    def get_output(self) -> str:
        """최종 출력 반환"""
        return self.output


class BaseChain:
    """
    기본 체인 클래스

    LLM을 사용한 순차적 작업 처리.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        template: Optional[PromptTemplate] = None,
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            template: 프롬프트 템플릿 (optional)
        """
        self.llm_client = llm_client
        self.template = template

    async def run(self, **kwargs: Any) -> ChainResult:
        """
        체인 실행

        Args:
            **kwargs: 입력 변수

        Returns:
            ChainResult: 실행 결과
        """
        raise NotImplementedError("Subclasses must implement run()")

    def _format_prompt(self, **kwargs: Any) -> str:
        """프롬프트 포맷"""
        if self.template:
            return self.template.format(**kwargs)
        raise ValueError("No template provided")


class SummaryChain(BaseChain):
    """
    데이터 요약 체인

    시뮬레이션 결과를 요약합니다.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        template: Optional[PromptTemplate] = None,
        few_shot_examples: Optional[FewShotExampleManager] = None,
        num_examples: int = 2,
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            template: 프롬프트 템플릿
            few_shot_examples: Few-shot 예시 관리자
            num_examples: 사용할 예시 개수
        """
        if template is None:
            template = PromptTemplate(SIMULATION_SUMMARY_TEMPLATE, name="summary")

        super().__init__(llm_client, template)
        self.few_shot_examples = few_shot_examples
        self.num_examples = num_examples

    async def run(  # type: ignore[override]
        self,
        simulation_type: str,
        simulation_name: str,
        parameters: Dict[str, Any],
        results: Dict[str, Any],
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> ChainResult:
        """
        시뮬레이션 요약 생성

        Args:
            simulation_type: 시뮬레이션 타입
            simulation_name: 시뮬레이션 이름
            parameters: 파라미터
            results: 결과
            description: 설명 (optional)
            **kwargs: 추가 인자

        Returns:
            ChainResult: 요약 결과
        """
        intermediate_steps = []

        # Few-shot 예시 추가 (있으면)
        examples_text = ""
        if self.few_shot_examples:
            examples_text = self.few_shot_examples.format_examples(
                category="summary", n=self.num_examples
            )

        # 프롬프트 구성
        if not self.template:
            raise ValueError("Template not initialized")
        prompt = self.template.format(
            simulation_type=simulation_type,
            simulation_name=simulation_name,
            parameters=parameters,
            results=results,
            description=description,
        )

        if examples_text:
            prompt = f"Here are some example analyses:\n\n{examples_text}\n\n{prompt}"

        intermediate_steps.append({"step": "prompt_formatted", "prompt": prompt})

        # LLM 호출
        response = await self.llm_client.generate(prompt, **kwargs)

        token_usage_dict: Optional[Dict[str, Any]] = (
            response.token_usage.__dict__ if response.token_usage else None
        )
        step_dict: Dict[str, Any] = {
            "step": "llm_response",
            "token_usage": token_usage_dict,
        }
        intermediate_steps.append(step_dict)

        return ChainResult(
            output=response.content,
            intermediate_steps=intermediate_steps,
            metadata={
                "simulation_name": simulation_name,
                "simulation_type": simulation_type,
            },
        )


class ComparisonChain(BaseChain):
    """
    비교 분석 체인

    여러 시뮬레이션 결과를 비교합니다.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        template: Optional[PromptTemplate] = None,
        few_shot_examples: Optional[FewShotExampleManager] = None,
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            template: 프롬프트 템플릿
            few_shot_examples: Few-shot 예시 관리자
        """
        if template is None:
            template = PromptTemplate(SIMULATION_COMPARISON_TEMPLATE, name="comparison")

        super().__init__(llm_client, template)
        self.few_shot_examples = few_shot_examples

    async def run(  # type: ignore[override]
        self,
        sim1_name: str,
        sim1_type: str,
        sim1_parameters: Dict[str, Any],
        sim1_results: Dict[str, Any],
        sim2_name: str,
        sim2_type: str,
        sim2_parameters: Dict[str, Any],
        sim2_results: Dict[str, Any],
        **kwargs: Any,
    ) -> ChainResult:
        """
        시뮬레이션 비교 분석

        Args:
            sim1_name: 시뮬레이션 1 이름
            sim1_type: 시뮬레이션 1 타입
            sim1_parameters: 시뮬레이션 1 파라미터
            sim1_results: 시뮬레이션 1 결과
            sim2_name: 시뮬레이션 2 이름
            sim2_type: 시뮬레이션 2 타입
            sim2_parameters: 시뮬레이션 2 파라미터
            sim2_results: 시뮬레이션 2 결과
            **kwargs: 추가 인자

        Returns:
            ChainResult: 비교 결과
        """
        intermediate_steps = []

        # Few-shot 예시
        examples_text = ""
        if self.few_shot_examples:
            examples_text = self.few_shot_examples.format_examples(category="comparison", n=2)

        # 프롬프트 구성
        if not self.template:
            raise ValueError("Template not initialized")
        prompt = self.template.format(
            sim1_name=sim1_name,
            sim1_type=sim1_type,
            sim1_parameters=sim1_parameters,
            sim1_results=sim1_results,
            sim2_name=sim2_name,
            sim2_type=sim2_type,
            sim2_parameters=sim2_parameters,
            sim2_results=sim2_results,
        )

        if examples_text:
            prompt = f"Here are some example comparisons:\n\n{examples_text}\n\n{prompt}"

        intermediate_steps.append({"step": "prompt_formatted", "prompt": prompt})

        # LLM 호출
        response = await self.llm_client.generate(prompt, **kwargs)

        token_usage_dict: Optional[Dict[str, Any]] = (
            response.token_usage.__dict__ if response.token_usage else None
        )
        step_dict: Dict[str, Any] = {
            "step": "llm_response",
            "token_usage": token_usage_dict,
        }
        intermediate_steps.append(step_dict)

        return ChainResult(
            output=response.content,
            intermediate_steps=intermediate_steps,
            metadata={
                "sim1_name": sim1_name,
                "sim2_name": sim2_name,
            },
        )


class InsightChain(BaseChain):
    """
    인사이트 생성 체인

    데이터를 분석하고 인사이트를 도출합니다.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        template: Optional[PromptTemplate] = None,
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            template: 프롬프트 템플릿
        """
        if template is None:
            template = PromptTemplate(INSIGHT_GENERATION_TEMPLATE, name="insight")

        super().__init__(llm_client, template)

    async def run(  # type: ignore[override]
        self,
        context: str,
        data: str,
        task: str,
        **kwargs: Any,
    ) -> ChainResult:
        """
        인사이트 생성

        Args:
            context: 분석 맥락
            data: 데이터
            task: 분석 과제
            **kwargs: 추가 인자

        Returns:
            ChainResult: 인사이트 결과
        """
        intermediate_steps = []

        # 프롬프트 구성
        if not self.template:
            raise ValueError("Template not initialized")
        prompt = self.template.format(
            context=context,
            data=data,
            task=task,
        )

        intermediate_steps.append({"step": "prompt_formatted", "prompt": prompt})

        # LLM 호출
        response = await self.llm_client.generate(prompt, **kwargs)

        token_usage_dict: Optional[Dict[str, Any]] = (
            response.token_usage.__dict__ if response.token_usage else None
        )
        step_dict: Dict[str, Any] = {
            "step": "llm_response",
            "token_usage": token_usage_dict,
        }
        intermediate_steps.append(step_dict)

        return ChainResult(
            output=response.content,
            intermediate_steps=intermediate_steps,
            metadata={
                "task": task,
            },
        )


class SequentialChain:
    """
    순차 체인

    여러 체인을 순서대로 실행합니다.
    """

    def __init__(self, chains: List[BaseChain]):
        """
        Args:
            chains: 체인 리스트
        """
        self.chains = chains

    async def run(self, initial_input: Dict[str, Any]) -> ChainResult:
        """
        체인 순차 실행

        Args:
            initial_input: 초기 입력

        Returns:
            ChainResult: 최종 결과
        """
        all_steps = []
        current_input = initial_input
        final_output: Optional[str] = None

        for i, chain in enumerate(self.chains):
            result = await chain.run(**current_input)
            all_steps.extend(result.intermediate_steps)

            # 다음 체인을 위한 입력 구성
            current_input = {**current_input, "previous_output": result.output}
            final_output = result.output

        if final_output is None:
            raise ValueError("No chains executed or all chains returned None")

        return ChainResult(
            output=final_output,
            intermediate_steps=all_steps,
            metadata={"num_chains": len(self.chains)},
        )
