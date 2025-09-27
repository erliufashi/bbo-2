"""报告生成模块。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .runner import SuiteResult


def write_reports(result: SuiteResult, outdir: Path) -> None:
    """输出 JSON 与 JUnit XML 报告。"""

    outdir.mkdir(parents=True, exist_ok=True)
    summary = result.summary
    json_path = outdir / "results.json"
    json_path.write_text(
        json.dumps(
            {
                "service": result.service,
                "summary": summary,
                "cases": [
                    {
                        "id": case.id,
                        "score": case.aggregate_result["score"],
                        "pass": case.aggregate_result["pass_"],
                        "reasoning": case.aggregate_result["reasoning"],
                    }
                    for case in result.cases
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    suite = ET.Element("testsuite", name=result.service, tests=str(summary["total"]), failures=str(summary["failed"]))
    for case in result.cases:
        case_el = ET.SubElement(suite, "testcase", name=case.id)
        if not case.aggregate_result["pass_"]:
            failure = ET.SubElement(case_el, "failure", message="评分未达标")
            failure.text = case.aggregate_result["reasoning"]
    tree = ET.ElementTree(suite)
    tree.write(outdir / "junit.xml", encoding="utf-8", xml_declaration=True)


__all__ = ["write_reports"]
