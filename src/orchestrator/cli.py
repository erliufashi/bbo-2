"""命令行入口，封装常见工作流。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import click

from .loader import load_service_definition
from .report import write_reports
from .runner import TestSuiteRunner


def _mock_executor(request: Mapping[str, Any]) -> Any:
    """简单的请求执行器，在示例中复用测试用例自带的 ``mock_response``。"""

    if "mock_response" in request:
        return request["mock_response"]
    return request.get("expected")


@click.group()
def cli() -> None:
    """开发编排器命令行工具。"""


@cli.command()
@click.option("--service-dir", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("--reports", type=click.Path(file_okay=False), default="reports")
def test(service_dir: str, reports: str) -> None:
    """执行服务包内的测试套件。"""

    service_path = Path(service_dir)
    definition = load_service_definition(service_path / "service_definition.yaml")
    scorer_configs = definition.get("tests.registered_scorers", {})
    suite_file = service_path / definition.get("tests.suite_file")
    runner = TestSuiteRunner(scorer_configs=scorer_configs, request_executor=_mock_executor)
    result = runner.run(suite_file)
    write_reports(result, Path(reports))
    summary = result.summary
    click.echo(
        f"共 {summary['total']} 个用例，通过 {summary['passed']} 个，平均得分 {summary['avg_score']:.2f}"
    )


@cli.command()
@click.option("--service-dir", type=click.Path(exists=True, file_okay=False), required=True)
def up(service_dir: str) -> None:
    """模拟启动服务运行时。"""

    click.echo(f"服务 {service_dir} 已在本地假定启动")


@cli.command()
@click.option("--service-dir", type=click.Path(exists=True, file_okay=False), required=True)
def pack(service_dir: str) -> None:
    """模拟打包服务。"""

    click.echo(f"已将 {service_dir} 打包为本地制品")


@cli.command()
@click.option("--service-dir", type=click.Path(exists=True, file_okay=False), required=True)
def release(service_dir: str) -> None:
    """模拟发布流程。"""

    click.echo(f"服务 {service_dir} 已触发发布")


if __name__ == "__main__":  # pragma: no cover
    cli()
