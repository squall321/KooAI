"""
Chart Generation Service

Generates 2D charts and plots using matplotlib and plotly.
"""

import io
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
except ImportError:
    plt = None
    Figure = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    go = None
    px = None


class ChartType(str, Enum):
    """Supported chart types."""

    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HISTOGRAM = "histogram"
    BOX = "box"
    HEATMAP = "heatmap"
    CONTOUR = "contour"
    SURFACE = "surface"


class ChartFormat(str, Enum):
    """Output format for charts."""

    PNG = "png"
    SVG = "svg"
    HTML = "html"  # For plotly interactive charts
    JSON = "json"  # For plotly JSON spec


class ChartConfig:
    """Chart configuration."""

    def __init__(
        self,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        width: int = 10,
        height: int = 6,
        dpi: int = 100,
        style: str = "default",
        grid: bool = True,
        legend: bool = True,
        colormap: str = "viridis",
    ):
        """
        Initialize chart configuration.

        Args:
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            width: Figure width in inches
            height: Figure height in inches
            dpi: Resolution (dots per inch)
            style: Matplotlib style
            grid: Whether to show grid
            legend: Whether to show legend
            colormap: Colormap name
        """
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.width = width
        self.height = height
        self.dpi = dpi
        self.style = style
        self.grid = grid
        self.legend = legend
        self.colormap = colormap


class MatplotlibChartService:
    """
    Chart generation using matplotlib.

    Generates static charts in PNG/SVG formats.
    """

    def __init__(self) -> None:
        """Initialize matplotlib chart service."""
        if plt is None:
            raise ImportError(
                "Matplotlib is not installed. Install with: pip install matplotlib"
            )

    def create_line_chart(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        config: Optional[ChartConfig] = None,
        labels: Optional[List[str]] = None,
    ) -> bytes:
        """
        Create line chart.

        Args:
            x_data: X-axis data
            y_data: Y-axis data (can be 2D for multiple lines)
            config: Chart configuration
            labels: Line labels for legend

        Returns:
            PNG image bytes

        Example:
            ```python
            service = MatplotlibChartService()

            x = np.linspace(0, 10, 100)
            y1 = np.sin(x)
            y2 = np.cos(x)

            config = ChartConfig(
                title="Trigonometric Functions",
                xlabel="X",
                ylabel="Y"
            )

            image = service.create_line_chart(
                x,
                np.vstack([y1, y2]).T,
                config=config,
                labels=["sin(x)", "cos(x)"]
            )
            ```
        """
        if config is None:
            config = ChartConfig()

        with plt.style.context(config.style):
            fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)

            # Handle multiple lines
            if y_data.ndim == 1:
                ax.plot(x_data, y_data, label=labels[0] if labels else None)
            else:
                for i in range(y_data.shape[1]):
                    label = labels[i] if labels and i < len(labels) else f"Line {i+1}"
                    ax.plot(x_data, y_data[:, i], label=label)

            if config.title:
                ax.set_title(config.title)
            if config.xlabel:
                ax.set_xlabel(config.xlabel)
            if config.ylabel:
                ax.set_ylabel(config.ylabel)
            if config.grid:
                ax.grid(True, alpha=0.3)
            if config.legend and labels:
                ax.legend()

            # Save to bytes
            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format="png", dpi=config.dpi, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            return buf.getvalue()

    def create_scatter_chart(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        config: Optional[ChartConfig] = None,
        colors: Optional[np.ndarray] = None,
        sizes: Optional[np.ndarray] = None,
    ) -> bytes:
        """
        Create scatter plot.

        Args:
            x_data: X coordinates
            y_data: Y coordinates
            config: Chart configuration
            colors: Point colors (optional)
            sizes: Point sizes (optional)

        Returns:
            PNG image bytes

        Example:
            ```python
            service = MatplotlibChartService()

            x = np.random.randn(100)
            y = np.random.randn(100)
            colors = np.random.rand(100)

            config = ChartConfig(title="Scatter Plot")
            image = service.create_scatter_chart(x, y, config, colors=colors)
            ```
        """
        if config is None:
            config = ChartConfig()

        with plt.style.context(config.style):
            fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)

            scatter = ax.scatter(
                x_data,
                y_data,
                c=colors if colors is not None else None,
                s=sizes if sizes is not None else 50,
                cmap=config.colormap,
                alpha=0.6,
            )

            if colors is not None:
                plt.colorbar(scatter, ax=ax)

            if config.title:
                ax.set_title(config.title)
            if config.xlabel:
                ax.set_xlabel(config.xlabel)
            if config.ylabel:
                ax.set_ylabel(config.ylabel)
            if config.grid:
                ax.grid(True, alpha=0.3)

            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format="png", dpi=config.dpi, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            return buf.getvalue()

    def create_histogram(
        self,
        data: np.ndarray,
        bins: int = 30,
        config: Optional[ChartConfig] = None,
    ) -> bytes:
        """
        Create histogram.

        Args:
            data: Data to histogram
            bins: Number of bins
            config: Chart configuration

        Returns:
            PNG image bytes

        Example:
            ```python
            service = MatplotlibChartService()
            data = np.random.normal(0, 1, 1000)
            config = ChartConfig(title="Distribution")
            image = service.create_histogram(data, bins=50, config=config)
            ```
        """
        if config is None:
            config = ChartConfig()

        with plt.style.context(config.style):
            fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)

            ax.hist(data, bins=bins, alpha=0.7, edgecolor="black")

            if config.title:
                ax.set_title(config.title)
            if config.xlabel:
                ax.set_xlabel(config.xlabel)
            if config.ylabel:
                ax.set_ylabel(config.ylabel or "Frequency")
            if config.grid:
                ax.grid(True, alpha=0.3)

            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format="png", dpi=config.dpi, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            return buf.getvalue()

    def create_heatmap(
        self,
        data: np.ndarray,
        config: Optional[ChartConfig] = None,
        x_labels: Optional[List[str]] = None,
        y_labels: Optional[List[str]] = None,
    ) -> bytes:
        """
        Create heatmap.

        Args:
            data: 2D array for heatmap
            config: Chart configuration
            x_labels: X-axis labels
            y_labels: Y-axis labels

        Returns:
            PNG image bytes

        Example:
            ```python
            service = MatplotlibChartService()
            data = np.random.rand(10, 10)
            config = ChartConfig(title="Correlation Matrix")
            image = service.create_heatmap(data, config)
            ```
        """
        if config is None:
            config = ChartConfig()

        with plt.style.context(config.style):
            fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)

            im = ax.imshow(data, cmap=config.colormap, aspect="auto")
            plt.colorbar(im, ax=ax)

            if x_labels:
                ax.set_xticks(range(len(x_labels)))
                ax.set_xticklabels(x_labels, rotation=45, ha="right")
            if y_labels:
                ax.set_yticks(range(len(y_labels)))
                ax.set_yticklabels(y_labels)

            if config.title:
                ax.set_title(config.title)

            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format="png", dpi=config.dpi, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            return buf.getvalue()

    def create_contour(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        config: Optional[ChartConfig] = None,
        levels: int = 10,
        filled: bool = True,
    ) -> bytes:
        """
        Create contour plot.

        Args:
            x: X coordinates (1D or 2D)
            y: Y coordinates (1D or 2D)
            z: Z values (2D)
            config: Chart configuration
            levels: Number of contour levels
            filled: Whether to fill contours

        Returns:
            PNG image bytes

        Example:
            ```python
            service = MatplotlibChartService()

            x = np.linspace(-5, 5, 100)
            y = np.linspace(-5, 5, 100)
            X, Y = np.meshgrid(x, y)
            Z = np.sin(np.sqrt(X**2 + Y**2))

            config = ChartConfig(title="Contour Plot")
            image = service.create_contour(X, Y, Z, config)
            ```
        """
        if config is None:
            config = ChartConfig()

        with plt.style.context(config.style):
            fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)

            if filled:
                contour = ax.contourf(x, y, z, levels=levels, cmap=config.colormap)
            else:
                contour = ax.contour(x, y, z, levels=levels, cmap=config.colormap)

            plt.colorbar(contour, ax=ax)

            if config.title:
                ax.set_title(config.title)
            if config.xlabel:
                ax.set_xlabel(config.xlabel)
            if config.ylabel:
                ax.set_ylabel(config.ylabel)
            if config.grid:
                ax.grid(True, alpha=0.3)

            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format="png", dpi=config.dpi, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)

            return buf.getvalue()


class PlotlyChartService:
    """
    Chart generation using Plotly.

    Generates interactive charts in HTML/JSON formats.
    """

    def __init__(self) -> None:
        """Initialize Plotly chart service."""
        if go is None:
            raise ImportError(
                "Plotly is not installed. Install with: pip install plotly"
            )

    def create_line_chart(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        config: Optional[ChartConfig] = None,
        labels: Optional[List[str]] = None,
        output_format: ChartFormat = ChartFormat.HTML,
    ) -> str:
        """
        Create interactive line chart.

        Args:
            x_data: X-axis data
            y_data: Y-axis data (can be 2D)
            config: Chart configuration
            labels: Line labels
            output_format: Output format (HTML or JSON)

        Returns:
            HTML string or JSON string

        Example:
            ```python
            service = PlotlyChartService()

            x = np.linspace(0, 10, 100)
            y = np.sin(x)

            config = ChartConfig(title="Interactive Line Chart")
            html = service.create_line_chart(x, y, config)

            with open("chart.html", "w") as f:
                f.write(html)
            ```
        """
        if config is None:
            config = ChartConfig()

        fig = go.Figure()

        # Handle multiple lines
        if y_data.ndim == 1:
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode="lines",
                    name=labels[0] if labels else "Line 1",
                )
            )
        else:
            for i in range(y_data.shape[1]):
                label = labels[i] if labels and i < len(labels) else f"Line {i+1}"
                fig.add_trace(
                    go.Scatter(x=x_data, y=y_data[:, i], mode="lines", name=label)
                )

        fig.update_layout(
            title=config.title,
            xaxis_title=config.xlabel,
            yaxis_title=config.ylabel,
            showlegend=config.legend,
            width=config.width * config.dpi,
            height=config.height * config.dpi,
        )

        if output_format == ChartFormat.HTML:
            return fig.to_html(include_plotlyjs="cdn")  # type: ignore[no-any-return]
        elif output_format == ChartFormat.JSON:
            return fig.to_json()  # type: ignore[no-any-return]
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def create_3d_surface(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        config: Optional[ChartConfig] = None,
        output_format: ChartFormat = ChartFormat.HTML,
    ) -> str:
        """
        Create 3D surface plot.

        Args:
            x: X coordinates
            y: Y coordinates
            z: Z values (2D array)
            config: Chart configuration
            output_format: Output format

        Returns:
            HTML or JSON string

        Example:
            ```python
            service = PlotlyChartService()

            x = np.linspace(-5, 5, 50)
            y = np.linspace(-5, 5, 50)
            X, Y = np.meshgrid(x, y)
            Z = np.sin(np.sqrt(X**2 + Y**2))

            config = ChartConfig(title="3D Surface")
            html = service.create_3d_surface(X, Y, Z, config)
            ```
        """
        if config is None:
            config = ChartConfig()

        fig = go.Figure(
            data=[go.Surface(x=x, y=y, z=z, colorscale=config.colormap)]
        )

        fig.update_layout(
            title=config.title,
            scene=dict(
                xaxis_title=config.xlabel,
                yaxis_title=config.ylabel,
                zaxis_title="Z",
            ),
            width=config.width * config.dpi,
            height=config.height * config.dpi,
        )

        if output_format == ChartFormat.HTML:
            return fig.to_html(include_plotlyjs="cdn")  # type: ignore[no-any-return]
        elif output_format == ChartFormat.JSON:
            return fig.to_json()  # type: ignore[no-any-return]
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class MockChartService:
    """Mock chart service when libraries unavailable."""

    def __init__(self) -> None:
        """Initialize mock service."""
        pass

    def create_line_chart(self, *args: Any, **kwargs: Any) -> Any:
        """Mock method."""
        raise NotImplementedError(
            "Matplotlib/Plotly not installed. Install with: pip install matplotlib plotly"
        )

    def create_scatter_chart(self, *args: Any, **kwargs: Any) -> Any:
        """Mock method."""
        raise NotImplementedError("Matplotlib not installed")

    def create_histogram(self, *args: Any, **kwargs: Any) -> Any:
        """Mock method."""
        raise NotImplementedError("Matplotlib not installed")

    def create_heatmap(self, *args: Any, **kwargs: Any) -> Any:
        """Mock method."""
        raise NotImplementedError("Matplotlib not installed")

    def create_contour(self, *args: Any, **kwargs: Any) -> Any:
        """Mock method."""
        raise NotImplementedError("Matplotlib not installed")

    def create_3d_surface(self, *args: Any, **kwargs: Any) -> Any:
        """Mock method."""
        raise NotImplementedError("Plotly not installed")


# Factory functions
def create_matplotlib_service() -> MatplotlibChartService:
    """Create matplotlib chart service."""
    if plt is None:
        return MockChartService()  # type: ignore[return-value]
    return MatplotlibChartService()


def create_plotly_service() -> PlotlyChartService:
    """Create plotly chart service."""
    if go is None:
        return MockChartService()  # type: ignore[return-value]
    return PlotlyChartService()
