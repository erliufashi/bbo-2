"""报告生成功能测试。"""
from __future__ import annotations

from pathlib import Path

from orchestrator.report import write_reports
from orchestrator.runner import SuiteResult, TestCaseResult
from orchestrator.scoring import ScoreResult


def test_write_reports(tmp_path: Path) -> None:
    case = TestCaseResult(
        id="case-1",
        scorer_results={"a": ScoreResult(score=1.0, pass_=True, reasoning="ok")},
        aggregate_result=ScoreResult(score=1.0, pass_=True, reasoning="ok"),
        request={},
        expected={},
    )
    suite = SuiteResult(service="demo", cases=[case])
    write_reports(suite, tmp_path)
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "junit.xml").exists()
