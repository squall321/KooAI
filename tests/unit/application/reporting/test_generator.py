"""
Tests for ReportGenerator
"""

import pytest
from pathlib import Path

from src.application.reporting.generator import (
    ReportGenerator,
    ReportSection,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test outputs"""
    return tmp_path


@pytest.fixture
def generator():
    """Create report generator instance"""
    return ReportGenerator(title="Test Report")


def test_report_section_creation():
    """Test ReportSection creation"""
    section = ReportSection(
        title="Test Section",
        content="This is test content",
        level=2,
    )

    assert section.title == "Test Section"
    assert section.content == "This is test content"
    assert section.level == 2


def test_report_section_to_markdown():
    """Test ReportSection markdown conversion"""
    section = ReportSection(
        title="Test Section",
        content="Test content",
        level=3,
    )

    markdown = section.to_markdown()

    assert "### Test Section" in markdown
    assert "Test content" in markdown


def test_generator_initialization():
    """Test ReportGenerator initialization"""
    generator = ReportGenerator(title="Custom Title")

    assert generator.title == "Custom Title"
    assert len(generator.sections) == 0
    assert "generated_at" in generator.metadata


def test_add_section(generator):
    """Test adding sections"""
    generator.add_section("Section 1", "Content 1")
    generator.add_section("Section 2", "Content 2", level=3)

    assert len(generator.sections) == 2
    assert generator.sections[0].title == "Section 1"
    assert generator.sections[1].level == 3


def test_add_section_chaining(generator):
    """Test method chaining"""
    result = generator.add_section("Section 1", "Content 1").add_section("Section 2", "Content 2")

    assert result is generator
    assert len(generator.sections) == 2


def test_add_summary(generator):
    """Test adding simulation summary"""
    generator.add_summary(
        simulation_name="Test Sim",
        simulation_id="sim123",
        num_vertices=1000,
        num_fields=3,
        field_names=["temperature", "pressure", "velocity"],
    )

    assert len(generator.sections) == 1
    section = generator.sections[0]

    assert "Simulation Summary" in section.title
    assert "Test Sim" in section.content
    assert "sim123" in section.content
    assert "1,000" in section.content
    assert "temperature" in section.content


def test_add_statistics_table(generator):
    """Test adding statistics table"""
    stats = {
        "mean": 42.5,
        "min": 10.0,
        "max": 100.0,
        "std": 15.2,
    }

    generator.add_statistics_table("temperature", stats)

    section = generator.sections[0]

    assert "Statistics: temperature" in section.title
    assert "| Metric | Value |" in section.content
    assert "Mean" in section.content
    assert "42.500000" in section.content


def test_add_comparison_summary(generator):
    """Test adding comparison summary"""
    comparison_results = {
        "simulation_ids": ["sim1", "sim2"],
        "field_name": "temperature",
        "rmse": 5.234567,
        "correlation": 0.9876,
        "mean_difference": 2.5,
    }

    generator.add_comparison_summary(comparison_results)

    section = generator.sections[0]

    assert "Comparison Summary" in section.title
    assert "2 simulations" in section.content
    assert "temperature" in section.content
    assert "5.234567" in section.content
    assert "0.9876" in section.content


def test_add_batch_results(generator):
    """Test adding batch processing results"""
    batch_results = {
        "total_jobs": 10,
        "completed": 8,
        "failed": 2,
        "success_rate": 80.0,
        "total_duration": 45.5,
        "avg_duration": 4.55,
        "failed_jobs": [
            {"file_path": "/path/file1.csv", "error": "Parse error"},
            {"file_path": "/path/file2.csv", "error": "Missing field"},
        ],
    }

    generator.add_batch_results(batch_results)

    section = generator.sections[0]

    assert "Batch Processing Results" in section.title
    assert "Total Jobs:** 10" in section.content
    assert "Success Rate:** 80.0%" in section.content
    assert "Failed Jobs:" in section.content
    assert "Parse error" in section.content


def test_generate_markdown(generator):
    """Test markdown generation"""
    generator.add_section("Introduction", "This is a test report").add_section(
        "Results", "Test results here"
    )

    markdown = generator.generate_markdown()

    assert "# Test Report" in markdown
    assert "Generated:" in markdown
    assert "## Introduction" in markdown
    assert "## Results" in markdown
    assert "This is a test report" in markdown


def test_generate_text(generator):
    """Test plain text generation"""
    generator.add_section("Introduction", "This is a test report")

    text = generator.generate_text()

    assert "Test Report" in text
    assert "=" in text  # Title separator
    assert "-" in text  # Section separator
    assert "Introduction" in text
    assert "This is a test report" in text


def test_generate_html(generator):
    """Test HTML generation"""
    generator.add_section("Introduction", "This is a test report", level=2)

    html = generator.generate_html()

    assert "<!DOCTYPE html>" in html
    assert "<html>" in html
    assert "<title>Test Report</title>" in html
    assert "<h1>Test Report</h1>" in html
    assert "<h2>Introduction</h2>" in html
    assert "This is a test report" in html
    assert "</html>" in html


def test_save_markdown(generator, temp_dir):
    """Test saving report as markdown"""
    output_path = temp_dir / "report.md"

    generator.add_section("Test", "Content")
    generator.save(output_path, format="markdown")

    assert output_path.exists()

    with open(output_path) as f:
        content = f.read()

    assert "# Test Report" in content
    assert "## Test" in content


def test_save_html(generator, temp_dir):
    """Test saving report as HTML"""
    output_path = temp_dir / "report.html"

    generator.add_section("Test", "Content")
    generator.save(output_path, format="html")

    assert output_path.exists()

    with open(output_path) as f:
        content = f.read()

    assert "<!DOCTYPE html>" in content
    assert "<h1>Test Report</h1>" in content


def test_save_text(generator, temp_dir):
    """Test saving report as plain text"""
    output_path = temp_dir / "report.txt"

    generator.add_section("Test", "Content")
    generator.save(output_path, format="text")

    assert output_path.exists()

    with open(output_path) as f:
        content = f.read()

    assert "Test Report" in content
    assert "Test" in content


def test_save_with_md_extension(generator, temp_dir):
    """Test saving with md format"""
    output_path = temp_dir / "report.md"

    generator.add_section("Test", "Content")
    generator.save(output_path, format="md")

    assert output_path.exists()


def test_save_with_txt_extension(generator, temp_dir):
    """Test saving with txt format"""
    output_path = temp_dir / "report.txt"

    generator.add_section("Test", "Content")
    generator.save(output_path, format="txt")

    assert output_path.exists()


def test_save_unsupported_format(generator, temp_dir):
    """Test unsupported format raises error"""
    output_path = temp_dir / "report.xyz"

    with pytest.raises(ValueError, match="Unsupported format"):
        generator.save(output_path, format="xyz")


def test_add_custom_section(generator):
    """Test adding custom section"""
    data = {"key1": "value1", "key2": 42}

    generator.add_custom_section("Custom Data", data)

    section = generator.sections[0]

    assert "Custom Data" in section.title
    assert "key1" in section.content
    assert "value1" in section.content


def test_add_custom_section_with_format_func(generator):
    """Test custom section with formatting function"""
    data = {"temperature": 25.5, "pressure": 101.3}

    def format_func(d):
        return f"Temperature: {d['temperature']}°C\nPressure: {d['pressure']} kPa"

    generator.add_custom_section("Conditions", data, format_func=format_func)

    section = generator.sections[0]

    assert "Temperature: 25.5°C" in section.content
    assert "Pressure: 101.3 kPa" in section.content


def test_empty_report(generator):
    """Test generating empty report"""
    markdown = generator.generate_markdown()

    assert "# Test Report" in markdown
    assert "Generated:" in markdown


def test_multiple_sections_different_levels(generator):
    """Test multiple sections with different heading levels"""
    generator.add_section("Level 1", "Content 1", level=1).add_section(
        "Level 2", "Content 2", level=2
    ).add_section("Level 3", "Content 3", level=3)

    markdown = generator.generate_markdown()

    assert "# Level 1" in markdown
    assert "## Level 2" in markdown
    assert "### Level 3" in markdown


def test_section_content_with_newlines(generator):
    """Test section with multi-line content"""
    content = "Line 1\nLine 2\nLine 3"

    generator.add_section("Multi-line", content)

    markdown = generator.generate_markdown()

    assert "Line 1" in markdown
    assert "Line 2" in markdown
    assert "Line 3" in markdown


def test_comprehensive_report(generator, temp_dir):
    """Test creating a comprehensive report"""
    # Add various sections
    generator.add_summary(
        simulation_name="CFD Analysis",
        simulation_id="cfd_001",
        num_vertices=50000,
        num_fields=5,
        field_names=["velocity_x", "velocity_y", "pressure", "temperature", "density"],
    )

    generator.add_statistics_table(
        "velocity_x",
        {
            "mean": 12.5,
            "min": 0.1,
            "max": 25.0,
            "std": 5.2,
        },
    )

    generator.add_batch_results(
        {
            "total_jobs": 20,
            "completed": 18,
            "failed": 2,
            "success_rate": 90.0,
            "total_duration": 120.5,
            "avg_duration": 6.03,
            "failed_jobs": [],
        }
    )

    # Save in all formats
    generator.save(temp_dir / "report.md", format="markdown")
    generator.save(temp_dir / "report.html", format="html")
    generator.save(temp_dir / "report.txt", format="text")

    # Verify all files exist
    assert (temp_dir / "report.md").exists()
    assert (temp_dir / "report.html").exists()
    assert (temp_dir / "report.txt").exists()
