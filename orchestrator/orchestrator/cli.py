"""命令行入口，模拟 `bb` 工具的核心命令。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .loader import load_service_definition
from .report import write_reports
from .runner import TestRunner


def _cmd_test(args: argparse.Namespace) -> int:
    definition = load_service_definition(args.definition)
    runner = TestRunner(definition)
    summary = runner.run()
    write_reports(summary, args.output)
    print(f"共执行 {len(summary.results)} 条用例，通过 {summary.passed} 条，失败 {summary.failed} 条")
    return 0 if summary.failed == 0 else 1


def _cmd_up(args: argparse.Namespace) -> int:
    print("启动服务的详细实现依赖真实环境，此处提供占位输出。")
    return 0


def _cmd_pack(args: argparse.Namespace) -> int:
    print("打包服务功能未在示例中实现。")
    return 0


def _cmd_release(args: argparse.Namespace) -> int:
    print("发布流程需要接入制品仓库，此处仅保留命令形式。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bb", description="示例测试编排器 CLI")
    sub = parser.add_subparsers(dest="command")

    cmd_test = sub.add_parser("test", help="运行测试套件")
    cmd_test.add_argument("definition", type=Path, help="service_definition.yaml 路径")
    cmd_test.add_argument("--output", type=Path, default=Path("reports"), help="报告输出目录")
    cmd_test.set_defaults(func=_cmd_test)

    cmd_up = sub.add_parser("up", help="启动服务（示例占位）")
    cmd_up.set_defaults(func=_cmd_up)

    cmd_pack = sub.add_parser("pack", help="打包服务（示例占位）")
    cmd_pack.set_defaults(func=_cmd_pack)

    cmd_release = sub.add_parser("release", help="发布服务（示例占位）")
    cmd_release.set_defaults(func=_cmd_release)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
