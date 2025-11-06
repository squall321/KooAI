"""프롬프트 템플릿 및 예시 테스트"""

import pytest
import tempfile
from pathlib import Path

from src.core.llm.prompts.template import PromptTemplate, PromptTemplateManager
from src.core.llm.prompts.examples import Example, FewShotExampleManager


class TestPromptTemplate:
    """PromptTemplate 테스트"""

    def test_create_template(self):
        """템플릿 생성 테스트"""
        template = PromptTemplate(
            template="Hello {{ name }}!",
            name="greeting",
        )

        assert template.name == "greeting"
        assert template.template_str == "Hello {{ name }}!"

    def test_format_template(self):
        """템플릿 포맷 테스트"""
        template = PromptTemplate("Hello {{ name }}!")

        result = template.format(name="World")

        assert result == "Hello World!"

    def test_complex_template(self):
        """복잡한 템플릿 테스트"""
        template = PromptTemplate(
            """
            Name: {{ name }}
            Age: {{ age }}
            {% if occupation %}
            Occupation: {{ occupation }}
            {% endif %}
            """
        )

        result = template.format(name="Alice", age=30, occupation="Engineer")

        assert "Name: Alice" in result
        assert "Age: 30" in result
        assert "Occupation: Engineer" in result

    def test_template_from_file(self):
        """파일에서 템플릿 로드 테스트"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".j2", delete=False
        ) as f:
            f.write("Test template: {{ value }}")
            temp_path = Path(f.name)

        try:
            template = PromptTemplate.from_file(temp_path)

            result = template.format(value="123")
            assert result == "Test template: 123"

        finally:
            temp_path.unlink()


class TestPromptTemplateManager:
    """PromptTemplateManager 테스트"""

    def test_register_template(self):
        """템플릿 등록 테스트"""
        manager = PromptTemplateManager()

        manager.register(
            name="test",
            template="Hello {{ name }}",
            description="Test template",
        )

        template = manager.get("test")
        assert template.name == "test"

    def test_get_nonexistent_template_raises_error(self):
        """존재하지 않는 템플릿 조회 시 에러 테스트"""
        manager = PromptTemplateManager()

        with pytest.raises(KeyError):
            manager.get("nonexistent")

    def test_format_template(self):
        """템플릿 포맷 테스트"""
        manager = PromptTemplateManager()
        manager.register("greet", "Hi {{ name }}")

        result = manager.format("greet", name="Bob")

        assert result == "Hi Bob"

    def test_list_templates(self):
        """템플릿 목록 조회 테스트"""
        manager = PromptTemplateManager()
        manager.register("t1", "Template 1")
        manager.register("t2", "Template 2")

        templates = manager.list_templates()

        assert "t1" in templates
        assert "t2" in templates

    def test_remove_template(self):
        """템플릿 제거 테스트"""
        manager = PromptTemplateManager()
        manager.register("temp", "Temporary")

        manager.remove("temp")

        with pytest.raises(KeyError):
            manager.get("temp")


class TestExample:
    """Example 테스트"""

    def test_create_example(self):
        """예시 생성 테스트"""
        example = Example(
            input="What is 2+2?",
            output="4",
            metadata={"difficulty": "easy"},
        )

        assert example.input == "What is 2+2?"
        assert example.output == "4"
        assert example.metadata["difficulty"] == "easy"

    def test_format_example(self):
        """예시 포맷 테스트"""
        example = Example(
            input="Question",
            output="Answer",
        )

        formatted = example.format()

        assert "Input: Question" in formatted
        assert "Output: Answer" in formatted

    def test_format_with_custom_labels(self):
        """커스텀 라벨로 포맷 테스트"""
        example = Example(
            input="Q",
            output="A",
        )

        formatted = example.format(input_label="Question", output_label="Answer")

        assert "Question: Q" in formatted
        assert "Answer: A" in formatted

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        example = Example(input="in", output="out", metadata={"key": "value"})

        data = example.to_dict()

        assert data["input"] == "in"
        assert data["output"] == "out"
        assert data["metadata"]["key"] == "value"

    def test_from_dict(self):
        """딕셔너리에서 생성 테스트"""
        data = {
            "input": "test input",
            "output": "test output",
            "metadata": {"tag": "test"},
        }

        example = Example.from_dict(data)

        assert example.input == "test input"
        assert example.output == "test output"
        assert example.metadata["tag"] == "test"


class TestFewShotExampleManager:
    """FewShotExampleManager 테스트"""

    def test_add_example(self):
        """예시 추가 테스트"""
        manager = FewShotExampleManager()

        example = manager.add_example(
            category="math",
            input_text="2+2",
            output_text="4",
        )

        assert example.input == "2+2"
        assert example.output == "4"

    def test_get_examples(self):
        """예시 조회 테스트"""
        manager = FewShotExampleManager()
        manager.add_example("cat1", "in1", "out1")
        manager.add_example("cat1", "in2", "out2")

        examples = manager.get_examples("cat1")

        assert len(examples) == 2
        assert examples[0].input == "in1"
        assert examples[1].input == "in2"

    def test_get_limited_examples(self):
        """제한된 개수 조회 테스트"""
        manager = FewShotExampleManager()
        for i in range(5):
            manager.add_example("test", f"in{i}", f"out{i}")

        examples = manager.get_examples("test", n=2)

        assert len(examples) == 2

    def test_format_examples(self):
        """예시 포맷 테스트"""
        manager = FewShotExampleManager()
        manager.add_example("format", "q1", "a1")
        manager.add_example("format", "q2", "a2")

        formatted = manager.format_examples("format")

        assert "Input: q1" in formatted
        assert "Output: a1" in formatted
        assert "Input: q2" in formatted

    def test_list_categories(self):
        """카테고리 목록 테스트"""
        manager = FewShotExampleManager()
        manager.add_example("cat1", "i1", "o1")
        manager.add_example("cat2", "i2", "o2")

        categories = manager.list_categories()

        assert "cat1" in categories
        assert "cat2" in categories

    def test_count_examples(self):
        """예시 개수 테스트"""
        manager = FewShotExampleManager()
        manager.add_example("c1", "i1", "o1")
        manager.add_example("c1", "i2", "o2")
        manager.add_example("c2", "i3", "o3")

        assert manager.count("c1") == 2
        assert manager.count("c2") == 1
        assert manager.count() == 3

    def test_remove_examples(self):
        """예시 제거 테스트"""
        manager = FewShotExampleManager()
        manager.add_example("temp", "i", "o")

        manager.remove_examples("temp")

        assert manager.count("temp") == 0

    def test_save_and_load_from_file(self):
        """파일 저장 및 로드 테스트"""
        manager = FewShotExampleManager()
        manager.add_example("save_test", "input", "output")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            manager.save_to_file(temp_path)

            new_manager = FewShotExampleManager()
            new_manager.load_from_file(temp_path)

            examples = new_manager.get_examples("save_test")
            assert len(examples) == 1
            assert examples[0].input == "input"

        finally:
            temp_path.unlink()
