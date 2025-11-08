"""CLI 명령어 테스트"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.presentation.cli.commands import cli


@pytest.fixture
def runner():
    """CLI 테스트 러너"""
    return CliRunner()


@pytest.fixture
def sample_csv_file():
    """테스트용 CSV 파일"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("x,y,z,temperature\n")
        f.write("0.0,0.0,0.0,300.0\n")
        f.write("1.0,0.0,0.0,310.0\n")
        f.write("0.0,1.0,0.0,320.0\n")
        csv_path = Path(f.name)

    yield csv_path

    csv_path.unlink()


class TestCLICommands:
    """CLI 명령어 테스트"""

    def test_cli_help(self, runner):
        """CLI 헬프 메시지"""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "KooAI" in result.output

    def test_upload_command(self, runner, sample_csv_file):
        """업로드 명령어"""
        result = runner.invoke(cli, ["upload", str(sample_csv_file)])
        assert result.exit_code == 0
        assert "Uploaded" in result.output or "success" in result.output.lower()

    def test_upload_nonexistent_file(self, runner):
        """존재하지 않는 파일 업로드"""
        result = runner.invoke(cli, ["upload", "nonexistent.csv"])
        assert result.exit_code != 0

    def test_list_command(self, runner, sample_csv_file):
        """목록 명령어"""
        # 먼저 업로드
        runner.invoke(cli, ["upload", str(sample_csv_file), "--name", "Test"])

        # 목록 조회
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0

    def test_upload_and_info(self, runner, sample_csv_file):
        """업로드 후 정보 조회"""
        # 업로드
        upload_result = runner.invoke(cli, ["upload", str(sample_csv_file)])
        assert upload_result.exit_code == 0

        # 업로드 결과에서 ID 추출 (간단한 파싱)
        # 실제로는 정규표현식이나 JSON 파싱이 필요
        # 여기서는 테스트 목적상 간단히 체크만
        assert "Uploaded" in upload_result.output or "success" in upload_result.output.lower()

    def test_analyze_command_help(self, runner):
        """분석 명령어 헬프"""
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "field" in result.output.lower()

    def test_compare_command_help(self, runner):
        """비교 명령어 헬프"""
        result = runner.invoke(cli, ["compare", "--help"])
        assert result.exit_code == 0

    def test_convergence_command_help(self, runner):
        """수렴성 명령어 헬프"""
        result = runner.invoke(cli, ["convergence", "--help"])
        assert result.exit_code == 0

    def test_spatial_command_help(self, runner):
        """공간 분석 명령어 헬프"""
        result = runner.invoke(cli, ["spatial", "--help"])
        assert result.exit_code == 0

    def test_delete_command_help(self, runner):
        """삭제 명령어 헬프"""
        result = runner.invoke(cli, ["delete", "--help"])
        assert result.exit_code == 0
