"""
CLI 유틸리티 함수

테이블 출력, 진행상황 표시 등.
"""

from typing import Any, Callable, Dict, List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def print_success(message: str) -> None:
    """성공 메시지 출력"""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """에러 메시지 출력"""
    console.print(f"[red]✗[/red] {message}", style="red")


def print_warning(message: str) -> None:
    """경고 메시지 출력"""
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")


def print_info(message: str) -> None:
    """정보 메시지 출력"""
    console.print(f"[blue]ℹ[/blue] {message}", style="blue")


def create_table(title: str, columns: List[str]) -> Table:
    """테이블 생성"""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column)
    return table


def print_simulation_table(simulations: List[Dict[str, Any]]) -> None:
    """시뮬레이션 목록 테이블 출력"""
    table = create_table(
        "Simulations",
        ["ID", "Name", "Type", "Timesteps", "Created At"],
    )

    for sim in simulations:
        table.add_row(
            sim["simulation_id"][:8] + "...",
            sim["name"],
            sim["simulation_type"],
            str(sim["num_timesteps"]),
            sim["created_at"],
        )

    console.print(table)


def print_simulation_info(info: Dict[str, Any]) -> None:
    """시뮬레이션 정보 출력"""
    console.print("\n[bold cyan]Simulation Information[/bold cyan]")
    console.print(f"  ID: {info['simulation_id']}")
    console.print(f"  Name: {info['name']}")
    console.print(f"  Type: {info['simulation_type']}")
    console.print(f"  Vertices: {info['num_vertices']:,}")
    console.print(f"  Timesteps: {info['num_timesteps']}")
    console.print(f"  Time Range: {info['time_range'][0]} - {info['time_range'][1]}")
    console.print(f"  Fields: {', '.join(info['fields'])}")


def print_field_statistics(field_name: str, stats: Dict[str, float]) -> None:
    """필드 통계 출력"""
    console.print(f"\n[bold cyan]Field Statistics: {field_name}[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    for key, value in stats.items():
        if isinstance(value, float):
            table.add_row(key.capitalize(), f"{value:.6f}")
        else:
            table.add_row(key.capitalize(), str(value))

    console.print(table)


def print_convergence_data(field_name: str, convergence: List[Dict[str, float]]) -> None:
    """수렴성 데이터 출력"""
    console.print(f"\n[bold cyan]Convergence Analysis: {field_name}[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Timestep", justify="right")
    table.add_column("Time", justify="right")
    table.add_column("RMS Change", justify="right")
    table.add_column("Relative Change", justify="right")

    for data in convergence:
        table.add_row(
            str(data["timestep"]),
            f"{data['time']:.6f}",
            f"{data['rms_change']:.6e}",
            f"{data['relative_change']:.6e}",
        )

    console.print(table)


def with_progress(description: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """진행상황 표시 데코레이터"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description=description, total=None)
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator
