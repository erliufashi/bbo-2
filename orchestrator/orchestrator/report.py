"""报告生成模块，输出 JSON 与 JUnit XML。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .runner import RunSummary


def _build_junit(summary: RunSummary) -> ET.Element:
    testsuite = ET.Element("testsuite", attrib={
        "tests": str(len(summary.results)),
        "failures": str(summary.failed),
        "name": "orchestrator",
    })
    for case in summary.results:
        testcase = ET.SubElement(testsuite, "testcase", attrib={"name": case.id})
        if not case.passed:
            failure = ET.SubElement(testcase, "failure", attrib={"message": case.aggregation.reasoning})
            failure.text = json.dumps(case.to_dict(), ensure_ascii=False)
    return testsuite


def write_reports(summary: RunSummary, outdir: str | Path) -> Iterable[Path]:
    """将运行结果写入指定目录，返回生成文件列表。"""

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    results_json = outdir / "results.json"
    results_json.write_text(
        json.dumps([case.to_dict() for case in summary.results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    junit_xml = outdir / "junit.xml"
    tree = ET.ElementTree(_build_junit(summary))
    tree.write(junit_xml, encoding="utf-8", xml_declaration=True)
    return [results_json, junit_xml]


__all__ = ["write_reports"]
