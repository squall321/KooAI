"""
Base exporter

Export simulation results to various formats
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict
import json
import csv
import numpy as np


class ExportFormat(Enum):
    """Supported export formats"""

    JSON = "json"
    CSV = "csv"
    NUMPY = "npy"
    TEXT = "txt"


class Exporter(ABC):
    """Abstract base exporter"""

    @abstractmethod
    def export(self, data: Any, output_path: Path) -> None:
        """Export data to file"""
        pass

    @abstractmethod
    def import_data(self, input_path: Path) -> Any:
        """Import data from file"""
        pass


class MultiFormatExporter:
    """
    Export simulation data to multiple formats

    Supports: JSON, CSV, NumPy
    """

    def export_simulation_data(
        self,
        simulation_data: Any,
        output_path: Path,
        format: ExportFormat = ExportFormat.JSON,
        include_metadata: bool = True,
    ) -> None:
        """
        Export simulation data

        Args:
            simulation_data: Simulation result object
            output_path: Output file path
            format: Export format
            include_metadata: Include metadata in export
        """
        output_path = Path(output_path)

        if format == ExportFormat.JSON:
            self._export_json(simulation_data, output_path, include_metadata)
        elif format == ExportFormat.CSV:
            self._export_csv(simulation_data, output_path)
        elif format == ExportFormat.NUMPY:
            self._export_numpy(simulation_data, output_path)
        elif format == ExportFormat.TEXT:
            self._export_text(simulation_data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(
        self,
        simulation_data: Any,
        output_path: Path,
        include_metadata: bool = True,
    ) -> None:
        """Export to JSON"""
        data_dict = {
            "simulation_id": getattr(simulation_data, "simulation_id", None),
            "name": getattr(simulation_data, "name", None),
            "fields": {},
        }

        # Export fields
        if hasattr(simulation_data, "data") and hasattr(simulation_data.data, "fields"):
            for field_name, field_data in simulation_data.data.fields.items():
                if isinstance(field_data, np.ndarray):
                    data_dict["fields"][field_name] = {
                        "shape": list(field_data.shape),
                        "dtype": str(field_data.dtype),
                        "min": float(np.min(field_data)),
                        "max": float(np.max(field_data)),
                        "mean": float(np.mean(field_data)),
                        # Data too large to export in JSON, use NumPy instead
                    }

        # Metadata
        if include_metadata and hasattr(simulation_data, "metadata"):
            data_dict["metadata"] = {
                "file_format": getattr(simulation_data.metadata, "file_format", None),
                "num_vertices": getattr(simulation_data.metadata, "num_vertices", None),
                "field_names": getattr(simulation_data.metadata, "field_names", []),
            }

        with open(output_path, "w") as f:
            json.dump(data_dict, f, indent=2)

    def _export_csv(
        self,
        simulation_data: Any,
        output_path: Path,
    ) -> None:
        """Export to CSV (flatten fields)"""
        if not hasattr(simulation_data, "data") or not hasattr(simulation_data.data, "fields"):
            raise ValueError("No fields to export")

        fields = simulation_data.data.fields

        # Get all field names
        field_names = list(fields.keys())

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(field_names)

            # Data rows
            num_points = next(iter(fields.values())).size
            for i in range(num_points):
                row = [float(fields[field_name].flat[i]) for field_name in field_names]
                writer.writerow(row)

    def _export_numpy(
        self,
        simulation_data: Any,
        output_path: Path,
    ) -> None:
        """Export fields to NumPy format"""
        if not hasattr(simulation_data, "data") or not hasattr(simulation_data.data, "fields"):
            raise ValueError("No fields to export")

        # Save all fields as a dictionary
        np.savez(output_path, **simulation_data.data.fields)

    def _export_text(
        self,
        simulation_data: Any,
        output_path: Path,
    ) -> None:
        """Export summary to text file"""
        lines = []

        lines.append(f"Simulation: {getattr(simulation_data, 'name', 'Unknown')}")
        lines.append(f"ID: {getattr(simulation_data, 'simulation_id', 'Unknown')}")
        lines.append("")

        if hasattr(simulation_data, "metadata"):
            meta = simulation_data.metadata
            lines.append("Metadata:")
            lines.append(f"  File Format: {getattr(meta, 'file_format', 'Unknown')}")
            lines.append(f"  Vertices: {getattr(meta, 'num_vertices', 0)}")
            lines.append(f"  Cells: {getattr(meta, 'num_cells', 0)}")
            lines.append(f"  Fields: {', '.join(getattr(meta, 'field_names', []))}")
            lines.append("")

        if hasattr(simulation_data, "data") and hasattr(simulation_data.data, "fields"):
            lines.append("Fields Summary:")
            for field_name, field_data in simulation_data.data.fields.items():
                if isinstance(field_data, np.ndarray):
                    lines.append(f"  {field_name}:")
                    lines.append(f"    Shape: {field_data.shape}")
                    lines.append(f"    Min: {np.min(field_data):.6f}")
                    lines.append(f"    Max: {np.max(field_data):.6f}")
                    lines.append(f"    Mean: {np.mean(field_data):.6f}")
                    lines.append(f"    Std: {np.std(field_data):.6f}")

        with open(output_path, "w") as f:
            f.write("\n".join(lines))

    def export_analysis_results(
        self,
        analysis_results: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        Export analysis results to JSON

        Args:
            analysis_results: Analysis results dictionary
            output_path: Output file path
        """
        with open(output_path, "w") as f:
            json.dump(analysis_results, f, indent=2, default=self._json_serialize)

    def _json_serialize(self, obj: Any) -> Any:
        """Custom JSON serializer for NumPy types"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
