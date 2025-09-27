"""报告生成模块。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping
from xml.etree import ElementTree as ET

from .runner import TestResult


@dataclass(slots=True)
class SuiteSummary:
    """测试汇总信息。"""

    total: int
    passed: int
    failed: int


class ReportWriter:
    """负责输出 JSON 与 JUnit 报告。"""

    def __init__(self, results: Iterable[TestResult]):
        self._results = list(results)

    def _summary(self) -> SuiteSummary:
        total = len(self._results)
        passed = sum(1 for result in self._results if result.passed)
        failed = total - passed
        return SuiteSummary(total=total, passed=passed, failed=failed)

    def write_json(self, path: str | Path) -> None:
        """输出结构化 JSON。"""

        report = {
            "summary": asdict(self._summary()),
            "results": [
                {
                    "case_id": result.case_id,
                    "passed": result.passed,
                    "score": result.score,
                    "details": {name: dict(detail) for name, detail in result.details.items()},
                }
                for result in self._results
            ],
        }
        Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_junit(self, path: str | Path) -> None:
        """生成最小化的 JUnit XML。"""

        suite = ET.Element("testsuite")
        summary = self._summary()
        suite.set("tests", str(summary.total))
        suite.set("failures", str(summary.failed))
        for result in self._results:
            case = ET.SubElement(suite, "testcase", attrib={"name": result.case_id})
            if not result.passed:
                failure = ET.SubElement(case, "failure", attrib={"message": "评分未达标"})
                detail_lines = [
                    f"{name}:{detail['score']:.2f}:{detail['reasoning']}" for name, detail in result.details.items()
                ]
                failure.text = "\n".join(detail_lines)
        tree = ET.ElementTree(suite)
        tree.write(path, encoding="utf-8", xml_declaration=True)

    def write_all(self, outdir: str | Path) -> Mapping[str, Path]:
        """同时输出 JSON 与 JUnit。"""

        directory = Path(outdir)
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / "results.json"
        junit_path = directory / "junit.xml"
        self.write_json(json_path)
        self.write_junit(junit_path)
        return {"json": json_path, "junit": junit_path}


__all__ = ["ReportWriter", "SuiteSummary"]
