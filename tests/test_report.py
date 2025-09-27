"""报告生成测试。"""

from __future__ import annotations

from pathlib import Path

from orchestrator.report import write_reports
from orchestrator.runner import SuiteResult, CaseResult
from orchestrator.scoring.base import ScoreResult


def test_write_reports(tmp_path: Path) -> None:
    suite = SuiteResult(
        results=[
            CaseResult(
                id="case-1",
                passed=True,
                score=1.0,
                reasoning="ok",
                scorer_results={"exact": ScoreResult(score=1.0, pass_=True)},
            ),
            CaseResult(
                id="case-2",
                passed=False,
                score=0.0,
                reasoning="fail",
                scorer_results={"exact": ScoreResult(score=0.0, pass_=False)},
            ),
        ]
    )

    write_reports(suite, tmp_path)

    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "junit.xml").exists()
