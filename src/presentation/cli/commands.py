"""
CLI 명령어

시뮬레이션 후처리 CLI 명령어 구현.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from src.application.services import SimulationService
from src.application.use_cases import (
    AnalyzeFieldRequest,
    CompareTimestepsRequest,
    ComputeConvergenceRequest,
    GetSimulationRequest,
    ListSimulationsRequest,
    NotFoundError,
    SpatialAnalysisRequest,
    UploadSimulationRequest,
    UseCaseError,
)
from src.infrastructure.repositories.memory_simulation_repository import (
    InMemorySimulationResultRepository,
)

from .utils import (
    console,
    print_convergence_data,
    print_error,
    print_field_statistics,
    print_info,
    print_simulation_info,
    print_simulation_table,
    print_success,
    print_warning,
)

# 글로벌 서비스 인스턴스 (싱글톤)
_service: Optional[SimulationService] = None


def get_service() -> SimulationService:
    """서비스 인스턴스 가져오기"""
    global _service
    if _service is None:
        repository = InMemorySimulationResultRepository()
        _service = SimulationService(repository)
    return _service


@click.group()
@click.version_option(version="1.0.0", prog_name="kooai")
def cli():
    """
    KooAI - AI-powered Simulation Post-Processing CLI

    시뮬레이션 결과 분석 및 처리 명령줄 도구
    """
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--name", "-n", help="시뮬레이션 이름")
@click.option("--type", "-t", "sim_type", help="시뮬레이션 타입")
@click.option("--analyze", "-a", is_flag=True, help="업로드 후 자동 분석")
def upload(file: Path, name: Optional[str], sim_type: Optional[str], analyze: bool):
    """
    시뮬레이션 파일 업로드

    Examples:
        kooai upload simulation.csv
        kooai upload simulation.csv --name "My Simulation" --analyze
    """
    try:
        service = get_service()

        print_info(f"Uploading {file.name}...")

        result = service.upload_and_analyze(
            file_path=file,
            name=name or file.stem,
            analyze_all_fields=analyze,
        )

        print_success(f"Uploaded: {result.simulation_info.simulation_id}")
        print_info(f"Name: {result.simulation_info.name}")
        print_info(f"Type: {result.simulation_info.simulation_type}")
        print_info(f"Vertices: {result.simulation_info.num_vertices:,}")
        print_info(f"Timesteps: {result.simulation_info.num_timesteps}")
        print_info(f"Fields: {', '.join(result.simulation_info.fields)}")

        if analyze and result.field_analyses:
            console.print("\n[bold]Field Analysis:[/bold]")
            for field_name, analysis in result.field_analyses.items():
                print_info(
                    f"  {field_name}: "
                    f"min={analysis.statistics['min']:.2f}, "
                    f"max={analysis.statistics['max']:.2f}, "
                    f"mean={analysis.statistics['mean']:.2f}"
                )

    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        sys.exit(1)
    except UseCaseError as e:
        print_error(f"Upload failed: {e}")
        sys.exit(1)


@cli.command()
@click.option("--page", "-p", default=1, help="페이지 번호")
@click.option("--size", "-s", default=20, help="페이지 크기")
def list(page: int, size: int):
    """
    시뮬레이션 목록 조회

    Examples:
        kooai list
        kooai list --page 2 --size 10
    """
    try:
        service = get_service()

        result = service.list_simulations(page=page, page_size=size)

        if result.total == 0:
            print_warning("No simulations found.")
            return

        print_simulation_table(
            [
                {
                    "simulation_id": sim.simulation_id,
                    "name": sim.name,
                    "simulation_type": sim.simulation_type,
                    "num_timesteps": sim.num_timesteps,
                    "created_at": sim.created_at,
                }
                for sim in result.simulations
            ]
        )

        console.print(
            f"\n[dim]Page {page} of {result.total // size + 1} "
            f"(Total: {result.total})[/dim]"
        )

    except UseCaseError as e:
        print_error(f"Failed to list simulations: {e}")
        sys.exit(1)


@cli.command()
@click.argument("simulation_id")
def info(simulation_id: str):
    """
    시뮬레이션 정보 조회

    Examples:
        kooai info abc123
    """
    try:
        service = get_service()

        result = service.get_use_case.execute(
            GetSimulationRequest(simulation_id=simulation_id)
        )

        print_simulation_info(
            {
                "simulation_id": result.simulation_id,
                "name": result.name,
                "simulation_type": result.simulation_type,
                "num_vertices": result.num_vertices,
                "num_timesteps": result.num_timesteps,
                "time_range": result.time_range,
                "fields": result.fields,
                "metadata": result.metadata,
            }
        )

    except NotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except UseCaseError as e:
        print_error(f"Failed to get simulation info: {e}")
        sys.exit(1)


@cli.command()
@click.argument("simulation_id")
@click.argument("field_name")
@click.option("--timestep", "-t", default=0, help="타임스텝 번호")
@click.option("--extremes", "-e", is_flag=True, help="극값 계산")
@click.option("--outliers", "-o", is_flag=True, help="이상치 탐지")
@click.option("--histogram", "-h", is_flag=True, help="히스토그램 계산")
def analyze(
    simulation_id: str,
    field_name: str,
    timestep: int,
    extremes: bool,
    outliers: bool,
    histogram: bool,
):
    """
    필드 분석

    Examples:
        kooai analyze abc123 temperature
        kooai analyze abc123 temperature --extremes --outliers
    """
    try:
        service = get_service()

        print_info(f"Analyzing field '{field_name}' at timestep {timestep}...")

        result = service.analyze_field_use_case.execute(
            AnalyzeFieldRequest(
                simulation_id=simulation_id,
                timestep=timestep,
                field_name=field_name,
                compute_extremes=extremes,
                detect_outliers=outliers,
                compute_histogram=histogram,
            )
        )

        print_success(f"Analysis complete for '{result.field_name}'")
        print_info(f"Field type: {result.field_type}")

        print_field_statistics(result.field_name, result.statistics)

        if result.extremes:
            console.print("\n[bold]Extremes:[/bold]")
            console.print(f"  Max values: {len(result.extremes['max'])} found")
            console.print(f"  Min values: {len(result.extremes['min'])} found")

        if result.outliers:
            console.print(f"\n[bold]Outliers:[/bold] {len(result.outliers)} detected")

        if result.histogram:
            console.print(
                f"\n[bold]Histogram:[/bold] {len(result.histogram['counts'])} bins"
            )

    except NotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except UseCaseError as e:
        print_error(f"Analysis failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("simulation_id")
@click.argument("field_name")
@click.option("--timestep1", "-t1", default=0, help="첫 번째 타임스텝")
@click.option("--timestep2", "-t2", default=1, help="두 번째 타임스텝")
def compare(simulation_id: str, field_name: str, timestep1: int, timestep2: int):
    """
    타임스텝 비교

    Examples:
        kooai compare abc123 temperature --timestep1 0 --timestep2 1
    """
    try:
        service = get_service()

        print_info(
            f"Comparing '{field_name}' between timesteps {timestep1} and {timestep2}..."
        )

        result = service.compare_timesteps_use_case.execute(
            CompareTimestepsRequest(
                simulation_id=simulation_id,
                timestep1=timestep1,
                timestep2=timestep2,
                field_name=field_name,
            )
        )

        print_success("Comparison complete")

        console.print("\n[bold cyan]Comparison Results[/bold cyan]")
        console.print(f"  Field: {result.field_name}")
        console.print(
            f"  Timestep {result.timestep1} (t={result.time1}) → "
            f"Timestep {result.timestep2} (t={result.time2})"
        )

        console.print("\n[bold]Metrics:[/bold]")
        for key, value in result.comparison_metrics.items():
            console.print(f"  {key}: {value:.6e}")

    except NotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except UseCaseError as e:
        print_error(f"Comparison failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("simulation_id")
@click.argument("field_name")
def convergence(simulation_id: str, field_name: str):
    """
    수렴성 분석

    Examples:
        kooai convergence abc123 temperature
    """
    try:
        service = get_service()

        print_info(f"Computing convergence for '{field_name}'...")

        result = service.compute_convergence_use_case.execute(
            ComputeConvergenceRequest(
                simulation_id=simulation_id,
                field_name=field_name,
            )
        )

        if not result.convergence_data:
            print_warning("Not enough timesteps for convergence analysis.")
            return

        print_success("Convergence analysis complete")

        print_convergence_data(result.field_name, result.convergence_data)

    except NotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except UseCaseError as e:
        print_error(f"Convergence analysis failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("simulation_id")
@click.argument("field_name")
@click.option("--timestep", "-t", default=0, help="타임스텝 번호")
@click.option("--min", "min_value", type=float, help="최솟값 (범위)")
@click.option("--max", "max_value", type=float, help="최댓값 (범위)")
def spatial(
    simulation_id: str,
    field_name: str,
    timestep: int,
    min_value: Optional[float],
    max_value: Optional[float],
):
    """
    공간 영역 분석

    Examples:
        kooai spatial abc123 temperature --min 400.0
        kooai spatial abc123 pressure --min 100.0 --max 200.0
    """
    try:
        service = get_service()

        print_info(f"Analyzing spatial region for '{field_name}'...")

        result = service.spatial_analysis_use_case.execute(
            SpatialAnalysisRequest(
                simulation_id=simulation_id,
                timestep=timestep,
                field_name=field_name,
                min_value=min_value,
                max_value=max_value,
            )
        )

        print_success("Spatial analysis complete")

        console.print("\n[bold cyan]Spatial Region Analysis[/bold cyan]")
        console.print(f"  Field: {result.field_name}")
        console.print(f"  Region size: {result.region_size} points")

        if min_value is not None:
            console.print(f"  Min value filter: >= {min_value}")
        if max_value is not None:
            console.print(f"  Max value filter: <= {max_value}")

        print_field_statistics(
            f"{result.field_name} (Region)", result.region_statistics
        )

    except NotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except UseCaseError as e:
        print_error(f"Spatial analysis failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("simulation_id")
@click.confirmation_option(prompt="Are you sure you want to delete this simulation?")
def delete(simulation_id: str):
    """
    시뮬레이션 삭제

    Examples:
        kooai delete abc123
    """
    try:
        service = get_service()

        deleted = service.repository.delete(simulation_id)

        if deleted:
            print_success(f"Deleted simulation: {simulation_id}")
        else:
            print_error(f"Simulation not found: {simulation_id}")
            sys.exit(1)

    except UseCaseError as e:
        print_error(f"Failed to delete simulation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
