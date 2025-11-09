"""
Report generator

Generate automated analysis reports
"""

from dataclasses import dataclass
from typing import Callable, List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json


@dataclass
class ReportSection:
    """Section of a report"""

    title: str
    content: str
    level: int = 2  # Markdown heading level

    def to_markdown(self) -> str:
        """Convert to markdown"""
        heading = "#" * self.level
        return f"{heading} {self.title}\n\n{self.content}\n\n"


class ReportGenerator:
    """
    Generate automated analysis reports

    Supports:
    - Markdown format
    - HTML format
    - Plain text format
    """

    def __init__(self, title: str = "Simulation Analysis Report"):
        self.title = title
        self.sections: List[ReportSection] = []
        self.metadata: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
        }

    def add_section(
        self,
        title: str,
        content: str,
        level: int = 2,
    ) -> "ReportGenerator":
        """
        Add a section to the report

        Args:
            title: Section title
            content: Section content
            level: Heading level (1-6)

        Returns:
            Self for method chaining
        """
        section = ReportSection(title=title, content=content, level=level)
        self.sections.append(section)
        return self

    def add_summary(
        self,
        simulation_name: str,
        simulation_id: str,
        num_vertices: int,
        num_fields: int,
        field_names: List[str],
    ) -> "ReportGenerator":
        """Add simulation summary section"""
        content = f"""
**Simulation Name:** {simulation_name}
**Simulation ID:** `{simulation_id}`
**Number of Vertices:** {num_vertices:,}
**Number of Fields:** {num_fields}
**Fields:** {', '.join(field_names)}
"""
        return self.add_section("Simulation Summary", content.strip())

    def add_statistics_table(
        self,
        field_name: str,
        statistics: Dict[str, float],
    ) -> "ReportGenerator":
        """Add statistics table section"""
        rows = [
            "| Metric | Value |",
            "|--------|-------|",
        ]

        for metric, value in statistics.items():
            if isinstance(value, float):
                rows.append(f"| {metric.capitalize()} | {value:.6f} |")
            else:
                rows.append(f"| {metric.capitalize()} | {value} |")

        table = "\n".join(rows)
        return self.add_section(f"Statistics: {field_name}", table)

    def add_comparison_summary(
        self,
        comparison_results: Dict[str, Any],
    ) -> "ReportGenerator":
        """Add comparison summary"""
        content_parts = []

        if "simulation_ids" in comparison_results:
            sim_ids = comparison_results["simulation_ids"]
            content_parts.append(f"**Comparing:** {len(sim_ids)} simulations")
            content_parts.append("")

        if "field_name" in comparison_results:
            content_parts.append(f"**Field:** {comparison_results['field_name']}")

        if "rmse" in comparison_results:
            content_parts.append(f"**RMSE:** {comparison_results['rmse']:.6f}")

        if "correlation" in comparison_results:
            content_parts.append(f"**Correlation:** {comparison_results['correlation']:.4f}")

        if "mean_difference" in comparison_results:
            content_parts.append(
                f"**Mean Difference:** {comparison_results['mean_difference']:.6f}"
            )

        content = "\n".join(content_parts)
        return self.add_section("Comparison Summary", content)

    def add_batch_results(
        self,
        batch_results: Dict[str, Any],
    ) -> "ReportGenerator":
        """Add batch processing results"""
        content = f"""
**Total Jobs:** {batch_results.get('total_jobs', 0)}
**Completed:** {batch_results.get('completed', 0)}
**Failed:** {batch_results.get('failed', 0)}
**Success Rate:** {batch_results.get('success_rate', 0):.1f}%
**Total Duration:** {batch_results.get('total_duration', 0):.2f}s
**Average Duration:** {batch_results.get('avg_duration', 0):.2f}s
"""

        if batch_results.get("failed_jobs"):
            content += "\n\n**Failed Jobs:**\n"
            for job in batch_results["failed_jobs"]:
                content += f"- `{job['file_path']}`: {job['error']}\n"

        return self.add_section("Batch Processing Results", content.strip())

    def generate_markdown(self) -> str:
        """Generate markdown report"""
        lines = [
            f"# {self.title}",
            "",
            f"*Generated: {self.metadata['generated_at']}*",
            "",
        ]

        for section in self.sections:
            lines.append(section.to_markdown())

        return "\n".join(lines)

    def generate_text(self) -> str:
        """Generate plain text report"""
        lines = [
            "=" * 70,
            self.title.center(70),
            "=" * 70,
            "",
            f"Generated: {self.metadata['generated_at']}",
            "",
        ]

        for section in self.sections:
            lines.append("-" * 70)
            lines.append(section.title)
            lines.append("-" * 70)
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def generate_html(self) -> str:
        """Generate HTML report"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"  <title>{self.title}</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }",
            "    h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }",
            "    h2 { color: #555; margin-top: 30px; }",
            "    table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "    th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "    th { background-color: #4CAF50; color: white; }",
            "    code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }",
            "    .metadata { color: #777; font-style: italic; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{self.title}</h1>",
            f"  <p class='metadata'>Generated: {self.metadata['generated_at']}</p>",
        ]

        for section in self.sections:
            html_parts.append(f"  <h{section.level}>{section.title}</h{section.level}>")
            # Convert markdown to HTML (basic)
            content_html = section.content.replace("\n", "<br>")
            html_parts.append(f"  <div>{content_html}</div>")

        html_parts.extend(
            [
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(html_parts)

    def save(
        self,
        output_path: Path,
        format: str = "markdown",
    ) -> None:
        """
        Save report to file

        Args:
            output_path: Output file path
            format: Output format (markdown, html, text)
        """
        output_path = Path(output_path)

        if format == "markdown" or format == "md":
            content = self.generate_markdown()
        elif format == "html":
            content = self.generate_html()
        elif format == "text" or format == "txt":
            content = self.generate_text()
        else:
            raise ValueError(f"Unsupported format: {format}")

        with open(output_path, "w") as f:
            f.write(content)

    def add_custom_section(
        self,
        title: str,
        data: Dict[str, Any],
        format_func: Optional[Callable[[Dict[str, Any]], str]] = None,
    ) -> "ReportGenerator":
        """
        Add custom section with data

        Args:
            title: Section title
            data: Data to include
            format_func: Optional function to format data
        """
        if format_func:
            content = format_func(data)
        else:
            content = json.dumps(data, indent=2)

        return self.add_section(title, content)
