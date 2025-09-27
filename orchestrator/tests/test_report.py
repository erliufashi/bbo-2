"""报告生成模块测试。"""
from __future__ import annotations

from pathlib import Path

from orchestrator.report import write_reports
from orchestrator.runner import CaseResult, RunSummary
from orchestrator.scoring.aggregator import AggregationResult
from orchestrator.scoring.base import ScoreResult


def test_write_reports(tmp_path: Path) -> None:
    case = CaseResult(
        id="case-1",
        scores={"demo": ScoreResult(score=1.0, pass_=True, reasoning="ok")},
        aggregation=AggregationResult(score=1.0, passed=True, reasoning="all good"),
        passed=True,
    )
    summary = RunSummary(results=[case])
    files = list(write_reports(summary, tmp_path))
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "junit.xml").exists()
    assert set(files) == {tmp_path / "results.json", tmp_path / "junit.xml"}
