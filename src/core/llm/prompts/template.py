"""
프롬프트 템플릿 시스템

Jinja2 기반 프롬프트 템플릿 관리.
"""

from pathlib import Path
from typing import Dict, List, Optional

try:
    from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
except ImportError:
    raise ImportError("Jinja2 is required for prompt templates. Install with: pip install jinja2")


class PromptTemplate:
    """
    프롬프트 템플릿

    Jinja2 템플릿을 사용한 동적 프롬프트 생성.
    """

    def __init__(
        self,
        template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Args:
            template: Jinja2 템플릿 문자열
            name: 템플릿 이름 (optional)
            description: 템플릿 설명 (optional)
        """
        self.name = name
        self.description = description
        self.template_str = template
        self._template = Template(template)

    def format(self, **kwargs) -> str:
        """
        템플릿 포맷

        Args:
            **kwargs: 템플릿 변수

        Returns:
            str: 포맷된 프롬프트
        """
        try:
            return self._template.render(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to format template: {str(e)}")

    def get_variables(self) -> List[str]:
        """
        템플릿 변수 목록 반환

        Returns:
            List[str]: 변수 이름 리스트
        """
        return list(self._template.module.__dict__.get("__all__", []))

    @classmethod
    def from_file(cls, file_path: Path, **kwargs) -> "PromptTemplate":
        """
        파일에서 템플릿 로드

        Args:
            file_path: 템플릿 파일 경로
            **kwargs: 추가 인자

        Returns:
            PromptTemplate: 템플릿 인스턴스
        """
        template_str = file_path.read_text()
        name = kwargs.get("name", file_path.stem)
        return cls(template=template_str, name=name, **kwargs)

    def __repr__(self) -> str:
        name_str = f" '{self.name}'" if self.name else ""
        return f"<PromptTemplate{name_str}>"


class PromptTemplateManager:
    """
    프롬프트 템플릿 관리자

    여러 템플릿을 등록하고 관리합니다.
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Args:
            template_dir: 템플릿 디렉토리 (optional)
        """
        self.template_dir = template_dir
        self._templates: Dict[str, PromptTemplate] = {}

        # Jinja2 환경 설정
        if template_dir and template_dir.exists():
            self._env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self._env = None

    def register(
        self,
        name: str,
        template: str,
        description: Optional[str] = None,
    ) -> PromptTemplate:
        """
        템플릿 등록

        Args:
            name: 템플릿 이름
            template: 템플릿 문자열
            description: 설명 (optional)

        Returns:
            PromptTemplate: 등록된 템플릿
        """
        prompt_template = PromptTemplate(template=template, name=name, description=description)
        self._templates[name] = prompt_template
        return prompt_template

    def register_from_file(self, name: str, file_path: Path) -> PromptTemplate:
        """
        파일에서 템플릿 등록

        Args:
            name: 템플릿 이름
            file_path: 파일 경로

        Returns:
            PromptTemplate: 등록된 템플릿
        """
        template = PromptTemplate.from_file(file_path, name=name)
        self._templates[name] = template
        return template

    def get(self, name: str) -> PromptTemplate:
        """
        템플릿 조회

        Args:
            name: 템플릿 이름

        Returns:
            PromptTemplate: 템플릿

        Raises:
            KeyError: 템플릿이 없을 때
        """
        if name not in self._templates:
            # 디렉토리에서 로드 시도
            if self._env:
                try:
                    template_str = self._env.get_template(f"{name}.j2").source
                    return self.register(name, template_str)
                except:
                    pass

            raise KeyError(f"Template '{name}' not found")

        return self._templates[name]

    def format(self, template_name: str, **kwargs) -> str:
        """
        템플릿 포맷

        Args:
            template_name: 템플릿 이름
            **kwargs: 템플릿 변수

        Returns:
            str: 포맷된 프롬프트
        """
        template = self.get(template_name)
        return template.format(**kwargs)

    def list_templates(self) -> List[str]:
        """
        등록된 템플릿 목록

        Returns:
            List[str]: 템플릿 이름 리스트
        """
        return list(self._templates.keys())

    def remove(self, name: str) -> None:
        """
        템플릿 제거

        Args:
            name: 템플릿 이름
        """
        if name in self._templates:
            del self._templates[name]


# 기본 시뮬레이션 템플릿
SIMULATION_SUMMARY_TEMPLATE = """
You are an expert simulation analyst. Analyze the following simulation results and provide a comprehensive summary.

## Simulation Information
Type: {{ simulation_type }}
Name: {{ simulation_name }}
{% if description %}
Description: {{ description }}
{% endif %}

## Parameters
{% for key, value in parameters.items() %}
- {{ key }}: {{ value }}
{% endfor %}

## Results
{% if results %}
{% for key, value in results.items() %}
- {{ key }}: {{ value }}
{% endfor %}
{% endif %}

Please provide:
1. A brief summary of the simulation setup
2. Key findings from the results
3. Notable trends or patterns
4. Potential areas of concern
5. Recommendations for further analysis

Keep your analysis concise and focused on the most important insights.
"""

SIMULATION_COMPARISON_TEMPLATE = """
You are an expert simulation analyst. Compare the following simulation results and identify key differences and similarities.

## Simulation 1
Name: {{ sim1_name }}
Type: {{ sim1_type }}
Parameters:
{% for key, value in sim1_parameters.items() %}
- {{ key }}: {{ value }}
{% endfor %}

Results:
{% for key, value in sim1_results.items() %}
- {{ key }}: {{ value }}
{% endfor %}

## Simulation 2
Name: {{ sim2_name }}
Type: {{ sim2_type }}
Parameters:
{% for key, value in sim2_parameters.items() %}
- {{ key }}: {{ value }}
{% endfor %}

Results:
{% for key, value in sim2_results.items() %}
- {{ key }}: {{ value }}
{% endfor %}

Please provide:
1. Key differences in parameters
2. Comparison of results
3. Impact of parameter changes on outcomes
4. Which configuration performed better (if applicable)
5. Recommendations

Focus on actionable insights and quantitative comparisons where possible.
"""

INSIGHT_GENERATION_TEMPLATE = """
You are an expert data scientist analyzing simulation results. Generate insights and recommendations.

## Context
{{ context }}

## Data
{{ data }}

## Task
{{ task }}

Please provide:
1. Data patterns and trends
2. Statistical insights
3. Anomalies or outliers
4. Correlations between variables
5. Actionable recommendations
6. Potential next steps

Be specific and provide quantitative evidence for your insights where possible.
"""
