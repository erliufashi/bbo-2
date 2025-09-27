"""命令行接口测试。"""

from pathlib import Path

from click.testing import CliRunner

from orchestrator.cli import cli


def test_cli_test_command(tmp_path: Path) -> None:
    """执行 test 子命令应生成报告文件。"""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "test",
            str(Path("tests/data/service/service_definition.yaml")),
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "junit.xml").exists()
