"""命令行接口，提供 `bb test` 等命令。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from .loader import ValidationError, load_service_definition
from .report import ReportWriter
from .runner import TestRunner


@click.group()
def cli() -> None:
    """开发编排器命令入口。"""


@cli.command()
@click.argument("definition", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "output_dir", type=click.Path(dir_okay=True, file_okay=False), default="reports")
def test(definition: str, output_dir: str) -> None:
    """执行服务包测试并生成报告。"""

    try:
        service_def = load_service_definition(definition)
    except ValidationError as exc:  # pragma: no cover - CLI 错误路径
        raise click.ClickException(str(exc)) from exc
    runner = TestRunner(service_def)
    results = runner.run()
    writer = ReportWriter(results)
    paths = writer.write_all(output_dir)
    click.echo(f"已生成报告: {paths['json']} 与 {paths['junit']}")


def main(argv: Optional[list[str]] = None) -> None:
    """支持通过 Python -m 调用。"""

    cli.main(args=argv, prog_name="bb")


if __name__ == "__main__":  # pragma: no cover - 手动执行入口
    main()
