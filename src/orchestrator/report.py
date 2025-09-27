"""报告生成模块。"""

from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

from .runner import SuiteResult


def write_reports(results: SuiteResult, outdir: Path) -> None:
    """生成 JSON 与 JUnit 报告。"""

    outdir.mkdir(parents=True, exist_ok=True)
    summary = results.summary
    json_result = {
        "summary": summary,
        "cases": [
            {
                "id": r.id,
                "passed": r.passed,
                "score": r.score,
                "reasoning": r.reasoning,
            }
            for r in results.results
        ],
    }
    (outdir / "results.json").write_text(
        json.dumps(json_result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    testsuite = ET.Element(
        "testsuite",
        name="orchestrator",
        tests=str(summary["total"]),
        failures=str(summary["total"] - summary["passed"]),
    )
    for case in results.results:
        testcase = ET.SubElement(testsuite, "testcase", name=case.id)
        if not case.passed:
            failure = ET.SubElement(testcase, "failure", message=case.reasoning)
            failure.text = case.reasoning
    tree = ET.ElementTree(testsuite)
    tree.write(outdir / "junit.xml", encoding="utf-8", xml_declaration=True)


__all__ = ["write_reports"]
