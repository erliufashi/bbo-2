"""命令行入口，使用 argparse 实现。"""
from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path

from .loader import load_service_definition, load_test_suite
from .report import write_reports
from .runner import TestRunner


def cmd_test(args: argparse.Namespace) -> None:
    service_path = Path(args.service_definition)
    definition = load_service_definition(service_path)
    suite = load_test_suite(definition, service_path.parent)
    runner = TestRunner(definition, suite)
    selected = [args.case_id] if args.case_id else None
    result = runner.run(selected_ids=selected)
    print(json.dumps(result.summary, ensure_ascii=False))
    report_dir = Path(args.report_dir)
    write_reports(result, report_dir)
    print(f"报告已生成：{report_dir.resolve()}")


def cmd_up(args: argparse.Namespace) -> None:
    definition = load_service_definition(Path(args.service_definition))
    runtime = definition.service.runtime
    if runtime and runtime.start_cmd:
        print(f"模拟执行启动命令：{' '.join(runtime.start_cmd)}")
    else:
        print("服务未声明启动命令，视为外部托管")


def cmd_pack(args: argparse.Namespace) -> None:
    base_dir = Path(args.service_definition).parent
    output = Path(args.output)
    print(f"打包 {base_dir} -> {output}")
    with tarfile.open(output, "w") as tar:
        tar.add(base_dir, arcname=base_dir.name)
    print("打包完成")


def cmd_release(args: argparse.Namespace) -> None:
    print(f"记录发布标签：{args.tag}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bb", description="BBO 编排器命令行")
    sub = parser.add_subparsers(dest="command", required=True)

    parser_test = sub.add_parser("test", help="运行测试")
    parser_test.add_argument("service_definition", help="service_definition.yaml 的路径")
    parser_test.add_argument("--case-id", help="仅运行指定用例", default=None)
    parser_test.add_argument("--report-dir", default=".bb/reports", help="报告输出目录")
    parser_test.set_defaults(func=cmd_test)

    parser_up = sub.add_parser("up", help="模拟服务启动")
    parser_up.add_argument("service_definition")
    parser_up.set_defaults(func=cmd_up)

    parser_pack = sub.add_parser("pack", help="打包服务目录")
    parser_pack.add_argument("service_definition")
    parser_pack.add_argument("--output", default="service-package.tar")
    parser_pack.set_defaults(func=cmd_pack)

    parser_release = sub.add_parser("release", help="记录发布信息")
    parser_release.add_argument("tag")
    parser_release.set_defaults(func=cmd_release)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


__all__ = ["main", "build_parser"]
