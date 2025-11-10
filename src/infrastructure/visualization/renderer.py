"""
3D Rendering Service

Provides 3D visualization rendering using PyVista for simulation data.
"""

import io
from pathlib import Path
from typing import Optional, Tuple, List, Any
import numpy as np
from PIL import Image

try:
    import pyvista as pv
except ImportError:
    pv = None  # Graceful degradation if PyVista not installed


class RenderConfig:
    """3D rendering configuration."""

    def __init__(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        camera_position: Optional[Tuple[float, float, float]] = None,
        camera_focal_point: Optional[Tuple[float, float, float]] = None,
        background_color: str = "white",
        show_edges: bool = False,
        show_axes: bool = True,
        lighting: bool = True,
        anti_aliasing: bool = True,
    ):
        """
        Initialize rendering configuration.

        Args:
            resolution: Output image resolution (width, height)
            camera_position: Camera position (x, y, z)
            camera_focal_point: Camera focal point (x, y, z)
            background_color: Background color
            show_edges: Whether to show mesh edges
            show_axes: Whether to show coordinate axes
            lighting: Whether to enable lighting
            anti_aliasing: Whether to enable anti-aliasing
        """
        self.resolution = resolution
        self.camera_position = camera_position
        self.camera_focal_point = camera_focal_point
        self.background_color = background_color
        self.show_edges = show_edges
        self.show_axes = show_axes
        self.lighting = lighting
        self.anti_aliasing = anti_aliasing


class PyVistaRenderer:
    """
    3D rendering service using PyVista.

    Renders simulation data as 3D visualizations with various options.
    """

    def __init__(self) -> None:
        """Initialize renderer."""
        if pv is None:
            raise ImportError(
                "PyVista is not installed. Install with: pip install pyvista"
            )

    def render_mesh(
        self,
        mesh: pv.DataSet,
        scalar_field: Optional[str] = None,
        config: Optional[RenderConfig] = None,
    ) -> bytes:
        """
        Render a PyVista mesh to PNG image.

        Args:
            mesh: PyVista mesh or dataset
            scalar_field: Name of scalar field to visualize
            config: Rendering configuration

        Returns:
            PNG image as bytes

        Example:
            ```python
            renderer = PyVistaRenderer()
            mesh = pv.read("simulation.vtk")

            config = RenderConfig(
                resolution=(1920, 1080),
                camera_position=(1, 1, 1),
                show_axes=True
            )

            image_bytes = renderer.render_mesh(
                mesh,
                scalar_field="temperature",
                config=config
            )
            ```
        """
        if config is None:
            config = RenderConfig()

        # Create plotter
        plotter = pv.Plotter(off_screen=True, window_size=config.resolution)
        plotter.set_background(config.background_color)

        # Add mesh
        if scalar_field and scalar_field in mesh.array_names:
            plotter.add_mesh(
                mesh,
                scalars=scalar_field,
                show_edges=config.show_edges,
                lighting=config.lighting,
            )
        else:
            plotter.add_mesh(
                mesh,
                show_edges=config.show_edges,
                lighting=config.lighting,
            )

        # Configure camera
        if config.camera_position:
            plotter.camera_position = [
                config.camera_position,
                config.camera_focal_point or mesh.center,
                (0, 0, 1),  # View up
            ]
        else:
            plotter.camera_position = "iso"

        # Add axes
        if config.show_axes:
            plotter.add_axes()

        # Render to image
        screenshot = plotter.screenshot(return_img=True)
        plotter.close()

        # Convert to PNG bytes
        img = Image.fromarray(screenshot)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes.getvalue()

    def render_from_file(
        self,
        file_path: Path,
        scalar_field: Optional[str] = None,
        config: Optional[RenderConfig] = None,
    ) -> bytes:
        """
        Render visualization from VTK file.

        Args:
            file_path: Path to VTK/VTU file
            scalar_field: Scalar field to visualize
            config: Rendering configuration

        Returns:
            PNG image bytes

        Example:
            ```python
            renderer = PyVistaRenderer()
            image = renderer.render_from_file(
                Path("simulation.vtk"),
                scalar_field="pressure"
            )

            with open("output.png", "wb") as f:
                f.write(image)
            ```
        """
        mesh = pv.read(str(file_path))
        return self.render_mesh(mesh, scalar_field, config)

    def render_volume(
        self,
        volume_data: np.ndarray,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        config: Optional[RenderConfig] = None,
    ) -> bytes:
        """
        Render volumetric data.

        Args:
            volume_data: 3D numpy array
            spacing: Voxel spacing (dx, dy, dz)
            config: Rendering configuration

        Returns:
            PNG image bytes

        Example:
            ```python
            # Create sample volume data
            x, y, z = np.mgrid[:100, :100, :100]
            values = np.sin(x/10) * np.cos(y/10) * np.sin(z/10)

            renderer = PyVistaRenderer()
            image = renderer.render_volume(values)
            ```
        """
        if config is None:
            config = RenderConfig()

        # Create image data
        grid = pv.ImageData()
        grid.dimensions = volume_data.shape
        grid.spacing = spacing
        grid["values"] = volume_data.flatten(order="F")

        # Create plotter
        plotter = pv.Plotter(off_screen=True, window_size=config.resolution)
        plotter.set_background(config.background_color)

        # Add volume
        plotter.add_volume(
            grid,
            scalars="values",
            opacity="sigmoid",
        )

        # Configure camera
        if config.camera_position:
            plotter.camera_position = [
                config.camera_position,
                config.camera_focal_point or grid.center,
                (0, 0, 1),
            ]
        else:
            plotter.camera_position = "iso"

        if config.show_axes:
            plotter.add_axes()

        # Render
        screenshot = plotter.screenshot(return_img=True)
        plotter.close()

        # Convert to PNG
        img = Image.fromarray(screenshot)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes.getvalue()

    def render_slice(
        self,
        mesh: pv.DataSet,
        normal: Tuple[float, float, float] = (0, 0, 1),
        origin: Optional[Tuple[float, float, float]] = None,
        scalar_field: Optional[str] = None,
        config: Optional[RenderConfig] = None,
    ) -> bytes:
        """
        Render a slice through 3D data.

        Args:
            mesh: PyVista dataset
            normal: Slice plane normal vector
            origin: Slice plane origin (default: mesh center)
            scalar_field: Scalar field to visualize
            config: Rendering configuration

        Returns:
            PNG image bytes

        Example:
            ```python
            mesh = pv.read("simulation.vtk")
            renderer = PyVistaRenderer()

            # Z-plane slice
            image = renderer.render_slice(
                mesh,
                normal=(0, 0, 1),
                scalar_field="temperature"
            )
            ```
        """
        if config is None:
            config = RenderConfig()

        if origin is None:
            origin = mesh.center

        # Create slice
        slice_mesh = mesh.slice(normal=normal, origin=origin)

        # Render slice
        return self.render_mesh(slice_mesh, scalar_field, config)

    def render_multi_slice(
        self,
        mesh: pv.DataSet,
        n_slices: int = 5,
        normal: Tuple[float, float, float] = (0, 0, 1),
        scalar_field: Optional[str] = None,
        config: Optional[RenderConfig] = None,
    ) -> bytes:
        """
        Render multiple slices through dataset.

        Args:
            mesh: PyVista dataset
            n_slices: Number of slices
            normal: Slice plane normal
            scalar_field: Scalar field to visualize
            config: Rendering configuration

        Returns:
            PNG image bytes

        Example:
            ```python
            mesh = pv.read("simulation.vtk")
            renderer = PyVistaRenderer()

            # 10 slices along Z axis
            image = renderer.render_multi_slice(
                mesh,
                n_slices=10,
                normal=(0, 0, 1),
                scalar_field="velocity"
            )
            ```
        """
        if config is None:
            config = RenderConfig()

        # Create plotter
        plotter = pv.Plotter(off_screen=True, window_size=config.resolution)
        plotter.set_background(config.background_color)

        # Add multiple slices
        slices = mesh.slice_along_axis(n=n_slices, axis=normal)

        if scalar_field and scalar_field in mesh.array_names:
            plotter.add_mesh(
                slices,
                scalars=scalar_field,
                show_edges=config.show_edges,
                lighting=config.lighting,
            )
        else:
            plotter.add_mesh(
                slices,
                show_edges=config.show_edges,
                lighting=config.lighting,
            )

        # Configure camera
        if config.camera_position:
            plotter.camera_position = [
                config.camera_position,
                config.camera_focal_point or mesh.center,
                (0, 0, 1),
            ]
        else:
            plotter.camera_position = "iso"

        if config.show_axes:
            plotter.add_axes()

        # Render
        screenshot = plotter.screenshot(return_img=True)
        plotter.close()

        # Convert to PNG
        img = Image.fromarray(screenshot)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes.getvalue()

    def get_available_fields(self, mesh: pv.DataSet) -> List[str]:
        """
        Get list of available scalar fields in mesh.

        Args:
            mesh: PyVista dataset

        Returns:
            List of field names

        Example:
            ```python
            mesh = pv.read("simulation.vtk")
            renderer = PyVistaRenderer()
            fields = renderer.get_available_fields(mesh)
            print(f"Available fields: {fields}")
            ```
        """
        return mesh.array_names  # type: ignore[no-any-return]


class MockRenderer:
    """Mock renderer for when PyVista is not available."""

    def __init__(self) -> None:
        """Initialize mock renderer."""
        pass

    def render_mesh(self, *args: Any, **kwargs: Any) -> bytes:
        """Mock render method."""
        raise NotImplementedError(
            "PyVista is not installed. Install with: pip install pyvista"
        )

    def render_from_file(self, *args: Any, **kwargs: Any) -> bytes:
        """Mock render method."""
        raise NotImplementedError(
            "PyVista is not installed. Install with: pip install pyvista"
        )

    def render_volume(self, *args: Any, **kwargs: Any) -> bytes:
        """Mock render method."""
        raise NotImplementedError(
            "PyVista is not installed. Install with: pip install pyvista"
        )

    def render_slice(self, *args: Any, **kwargs: Any) -> bytes:
        """Mock render method."""
        raise NotImplementedError(
            "PyVista is not installed. Install with: pip install pyvista"
        )

    def render_multi_slice(self, *args: Any, **kwargs: Any) -> bytes:
        """Mock render method."""
        raise NotImplementedError(
            "PyVista is not installed. Install with: pip install pyvista"
        )

    def get_available_fields(self, *args: Any, **kwargs: Any) -> List[str]:
        """Mock method."""
        return []


# Factory function
def create_renderer() -> PyVistaRenderer:
    """
    Create renderer instance.

    Returns:
        PyVistaRenderer instance (or MockRenderer if PyVista unavailable)
    """
    if pv is None:
        return MockRenderer()  # type: ignore[return-value]
    return PyVistaRenderer()
