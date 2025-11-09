"""
Visualization API Routes

Endpoints for 3D rendering and chart generation.
"""

import io
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import numpy as np

from src.infrastructure.visualization.renderer import (
    create_renderer,
    RenderConfig,
)
from src.infrastructure.visualization.charts import (
    create_matplotlib_service,
    create_plotly_service,
    ChartConfig,
    ChartFormat,
)

router = APIRouter(prefix="/visualizations", tags=["visualization"])


# Request/Response models
class RenderRequest(BaseModel):
    """3D rendering request."""

    file_path: str
    scalar_field: Optional[str] = None
    resolution_width: int = 1920
    resolution_height: int = 1080
    camera_position: Optional[List[float]] = None
    camera_focal_point: Optional[List[float]] = None
    background_color: str = "white"
    show_edges: bool = False
    show_axes: bool = True


class SliceRenderRequest(BaseModel):
    """Slice rendering request."""

    file_path: str
    scalar_field: Optional[str] = None
    normal_x: float = 0.0
    normal_y: float = 0.0
    normal_z: float = 1.0
    origin_x: Optional[float] = None
    origin_y: Optional[float] = None
    origin_z: Optional[float] = None
    resolution_width: int = 1920
    resolution_height: int = 1080


class ChartRequest(BaseModel):
    """Chart generation request."""

    chart_type: str  # line, scatter, histogram, heatmap, contour
    data: List[List[float]]  # Data array
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    labels: Optional[List[str]] = None
    width: int = 10
    height: int = 6
    output_format: str = "png"  # png, html, json


class FieldsResponse(BaseModel):
    """Available fields response."""

    fields: List[str]
    file_path: str


# 3D Rendering Endpoints


@router.post(
    "/render/3d",
    summary="Render 3D Visualization",
    description="Generate 3D visualization from VTK file",
    responses={200: {"content": {"image/png": {}}}},
)
async def render_3d_visualization(request: RenderRequest) -> Response:
    """
    ## 3D Visualization Rendering

    Render simulation data as 3D visualization using PyVista.

    ### Features
    - VTK/VTU file support
    - Customizable camera position
    - Scalar field visualization
    - High-resolution output

    ### Request Body
    - **file_path**: Path to VTK file
    - **scalar_field**: Scalar field to visualize (optional)
    - **resolution_width**: Output width in pixels
    - **resolution_height**: Output height in pixels
    - **camera_position**: Camera position [x, y, z]
    - **camera_focal_point**: Camera focal point [x, y, z]
    - **background_color**: Background color
    - **show_edges**: Show mesh edges
    - **show_axes**: Show coordinate axes

    ### Example
    ```bash
    curl -X POST "http://localhost:8000/api/v1/visualizations/render/3d" \\
      -H "Content-Type: application/json" \\
      -d '{
        "file_path": "uploads/simulation.vtk",
        "scalar_field": "temperature",
        "resolution_width": 1920,
        "resolution_height": 1080,
        "camera_position": [1, 1, 1],
        "show_axes": true
      }' --output render.png
    ```

    ### Returns
    PNG image of 3D visualization
    """
    try:
        renderer = create_renderer()

        # Create render config
        config = RenderConfig(
            resolution=(request.resolution_width, request.resolution_height),
            camera_position=tuple(request.camera_position)
            if request.camera_position
            else None,
            camera_focal_point=tuple(request.camera_focal_point)
            if request.camera_focal_point
            else None,
            background_color=request.background_color,
            show_edges=request.show_edges,
            show_axes=request.show_axes,
        )

        # Render
        image_bytes = renderer.render_from_file(
            Path(request.file_path),
            scalar_field=request.scalar_field,
            config=config,
        )

        return Response(content=image_bytes, media_type="image/png")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@router.post(
    "/render/slice",
    summary="Render Slice Visualization",
    description="Generate slice through 3D data",
    responses={200: {"content": {"image/png": {}}}},
)
async def render_slice_visualization(request: SliceRenderRequest) -> Response:
    """
    ## Slice Visualization

    Render a 2D slice through 3D simulation data.

    ### Features
    - Customizable slice plane (normal and origin)
    - Scalar field visualization
    - High-resolution output

    ### Request Body
    - **file_path**: Path to VTK file
    - **scalar_field**: Scalar field to visualize
    - **normal_x, normal_y, normal_z**: Slice plane normal vector
    - **origin_x, origin_y, origin_z**: Slice plane origin (optional, defaults to center)

    ### Example
    ```bash
    # Z-plane slice at center
    curl -X POST "http://localhost:8000/api/v1/visualizations/render/slice" \\
      -H "Content-Type: application/json" \\
      -d '{
        "file_path": "uploads/simulation.vtk",
        "scalar_field": "velocity",
        "normal_x": 0,
        "normal_y": 0,
        "normal_z": 1
      }' --output slice.png
    ```

    ### Returns
    PNG image of slice visualization
    """
    try:
        renderer = create_renderer()
        import pyvista as pv

        # Load mesh
        mesh = pv.read(request.file_path)

        # Determine origin
        origin = None
        if all(
            v is not None
            for v in [request.origin_x, request.origin_y, request.origin_z]
        ):
            origin = (request.origin_x, request.origin_y, request.origin_z)

        # Create render config
        config = RenderConfig(
            resolution=(request.resolution_width, request.resolution_height),
        )

        # Render slice
        image_bytes = renderer.render_slice(
            mesh,
            normal=(request.normal_x, request.normal_y, request.normal_z),
            origin=origin,
            scalar_field=request.scalar_field,
            config=config,
        )

        return Response(content=image_bytes, media_type="image/png")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slice rendering failed: {str(e)}")


@router.post(
    "/render/multi-slice",
    summary="Render Multiple Slices",
    description="Generate multiple slices through 3D data",
    responses={200: {"content": {"image/png": {}}}},
)
async def render_multi_slice(
    file_path: str = Query(..., description="Path to VTK file"),
    scalar_field: Optional[str] = Query(None, description="Scalar field to visualize"),
    n_slices: int = Query(5, description="Number of slices", ge=1, le=20),
    normal_x: float = Query(0.0, description="Slice plane normal X"),
    normal_y: float = Query(0.0, description="Slice plane normal Y"),
    normal_z: float = Query(1.0, description="Slice plane normal Z"),
    resolution_width: int = Query(1920, description="Width in pixels"),
    resolution_height: int = Query(1080, description="Height in pixels"),
) -> Response:
    """
    ## Multiple Slice Visualization

    Render multiple evenly-spaced slices through 3D data.

    ### Query Parameters
    - **file_path**: Path to VTK file
    - **scalar_field**: Scalar field to visualize
    - **n_slices**: Number of slices (1-20)
    - **normal_x, normal_y, normal_z**: Slice direction normal vector

    ### Example
    ```bash
    curl "http://localhost:8000/api/v1/visualizations/render/multi-slice?file_path=uploads/sim.vtk&scalar_field=temperature&n_slices=10" \\
      --output multi_slice.png
    ```

    ### Returns
    PNG image showing multiple slices
    """
    try:
        renderer = create_renderer()
        import pyvista as pv

        mesh = pv.read(file_path)

        config = RenderConfig(resolution=(resolution_width, resolution_height))

        image_bytes = renderer.render_multi_slice(
            mesh,
            n_slices=n_slices,
            normal=(normal_x, normal_y, normal_z),
            scalar_field=scalar_field,
            config=config,
        )

        return Response(content=image_bytes, media_type="image/png")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Multi-slice rendering failed: {str(e)}"
        )


@router.get(
    "/fields/{file_path:path}",
    response_model=FieldsResponse,
    summary="Get Available Fields",
    description="List scalar fields available in VTK file",
)
async def get_available_fields(file_path: str) -> "FieldsResponse":
    """
    ## Get Available Fields

    List all scalar fields available in a VTK file for visualization.

    ### Path Parameters
    - **file_path**: Path to VTK file

    ### Example
    ```bash
    curl "http://localhost:8000/api/v1/visualizations/fields/uploads/simulation.vtk"
    ```

    ### Returns
    ```json
    {
        "fields": ["temperature", "pressure", "velocity"],
        "file_path": "uploads/simulation.vtk"
    }
    ```
    """
    try:
        import pyvista as pv

        mesh = pv.read(file_path)
        renderer = create_renderer()
        fields = renderer.get_available_fields(mesh)

        return FieldsResponse(fields=fields, file_path=file_path)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read fields: {str(e)}"
        )


# Chart Generation Endpoints


@router.post(
    "/charts/generate",
    summary="Generate Chart",
    description="Generate 2D chart from data",
)
async def generate_chart(request: ChartRequest) -> Response:
    """
    ## Chart Generation

    Generate 2D charts from numerical data.

    ### Supported Chart Types
    - **line**: Line chart
    - **scatter**: Scatter plot
    - **histogram**: Histogram
    - **heatmap**: Heatmap
    - **contour**: Contour plot

    ### Request Body
    - **chart_type**: Chart type
    - **data**: Data array (format depends on chart type)
    - **title**: Chart title
    - **xlabel**: X-axis label
    - **ylabel**: Y-axis label
    - **labels**: Data series labels
    - **output_format**: Output format (png, html, json)

    ### Example - Line Chart
    ```bash
    curl -X POST "http://localhost:8000/api/v1/visualizations/charts/generate" \\
      -H "Content-Type: application/json" \\
      -d '{
        "chart_type": "line",
        "data": [[0, 1, 2, 3, 4], [0, 1, 4, 9, 16]],
        "title": "Quadratic Function",
        "xlabel": "X",
        "ylabel": "Y",
        "output_format": "png"
      }' --output chart.png
    ```

    ### Example - Scatter Plot
    ```bash
    curl -X POST "http://localhost:8000/api/v1/visualizations/charts/generate" \\
      -H "Content-Type: application/json" \\
      -d '{
        "chart_type": "scatter",
        "data": [[1, 2, 3, 4, 5], [2, 4, 1, 5, 3]],
        "title": "Scatter Plot",
        "output_format": "png"
      }' --output scatter.png
    ```

    ### Returns
    Chart in requested format (PNG image, HTML, or JSON)
    """
    try:
        # Parse data
        data_array = np.array(request.data, dtype=float)

        # Create config
        config = ChartConfig(
            title=request.title,
            xlabel=request.xlabel,
            ylabel=request.ylabel,
            width=request.width,
            height=request.height,
        )

        # Route to appropriate chart type
        if request.output_format in ["html", "json"]:
            # Use Plotly for interactive charts
            plotly_service = create_plotly_service()

            if request.chart_type == "line":
                if data_array.shape[0] == 2:
                    x_data = data_array[0]
                    y_data = data_array[1]
                else:
                    raise ValueError("Line chart requires 2 rows: [x, y]")

                output = plotly_service.create_line_chart(
                    x_data,
                    y_data.reshape(-1, 1),
                    config=config,
                    labels=request.labels,
                    output_format=ChartFormat(request.output_format),
                )

                if request.output_format == "html":
                    return Response(content=output, media_type="text/html")
                else:
                    return Response(content=output, media_type="application/json")

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Chart type '{request.chart_type}' not supported for {request.output_format}",
                )

        else:
            # Use Matplotlib for static charts
            matplotlib_service = create_matplotlib_service()

            if request.chart_type == "line":
                if data_array.shape[0] == 2:
                    x_data = data_array[0]
                    y_data = data_array[1]
                else:
                    raise ValueError("Line chart requires 2 rows: [x, y]")

                image_bytes = matplotlib_service.create_line_chart(
                    x_data, y_data, config=config, labels=request.labels
                )

            elif request.chart_type == "scatter":
                if data_array.shape[0] >= 2:
                    x_data = data_array[0]
                    y_data = data_array[1]
                    colors = data_array[2] if data_array.shape[0] > 2 else None
                else:
                    raise ValueError("Scatter plot requires at least 2 rows: [x, y]")

                image_bytes = matplotlib_service.create_scatter_chart(
                    x_data, y_data, config=config, colors=colors
                )

            elif request.chart_type == "histogram":
                if data_array.shape[0] == 1:
                    data = data_array[0]
                else:
                    data = data_array.flatten()

                image_bytes = matplotlib_service.create_histogram(
                    data, bins=30, config=config
                )

            elif request.chart_type == "heatmap":
                if data_array.ndim != 2:
                    raise ValueError("Heatmap requires 2D data")

                image_bytes = matplotlib_service.create_heatmap(data_array, config=config)

            elif request.chart_type == "contour":
                if data_array.ndim != 2:
                    raise ValueError("Contour requires 2D data")

                # Create meshgrid
                x = np.arange(data_array.shape[1])
                y = np.arange(data_array.shape[0])
                X, Y = np.meshgrid(x, y)

                image_bytes = matplotlib_service.create_contour(
                    X, Y, data_array, config=config
                )

            else:
                raise HTTPException(
                    status_code=400, detail=f"Unknown chart type: {request.chart_type}"
                )

            return Response(content=image_bytes, media_type="image/png")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@router.post(
    "/charts/from-file",
    summary="Generate Chart from File",
    description="Generate chart from uploaded CSV/text file",
    responses={200: {"content": {"image/png": {}}}},
)
async def generate_chart_from_file(
    file: UploadFile = File(..., description="CSV or text file with numerical data"),
    chart_type: str = Query("line", description="Chart type"),
    title: Optional[str] = Query(None, description="Chart title"),
    xlabel: Optional[str] = Query(None, description="X-axis label"),
    ylabel: Optional[str] = Query(None, description="Y-axis label"),
    output_format: str = Query("png", description="Output format"),
) -> Response:
    """
    ## Chart from File

    Generate chart directly from uploaded CSV/text file.

    ### Query Parameters
    - **chart_type**: Chart type (line, scatter, histogram, etc.)
    - **title**: Chart title
    - **xlabel**: X-axis label
    - **ylabel**: Y-axis label
    - **output_format**: Output format (png, html, json)

    ### Example
    ```bash
    # Create data file
    echo -e "0,0\\n1,1\\n2,4\\n3,9\\n4,16" > data.csv

    # Upload and generate chart
    curl -X POST "http://localhost:8000/api/v1/visualizations/charts/from-file?chart_type=line&title=Data" \\
      -F "file=@data.csv" \\
      --output chart.png
    ```

    ### Returns
    Chart in requested format
    """
    try:
        # Read file
        content = await file.read()
        text = content.decode("utf-8")

        # Parse CSV (simple parser)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        data = []
        for line in lines:
            row = [float(x.strip()) for x in line.split(",")]
            data.append(row)

        data_array = np.array(data, dtype=float).T  # Transpose to get [x, y, ...]

        # Create chart request
        request = ChartRequest(
            chart_type=chart_type,
            data=data_array.tolist(),
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            output_format=output_format,
        )

        # Reuse generate_chart logic
        return await generate_chart(request)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate chart from file: {str(e)}"
        )
