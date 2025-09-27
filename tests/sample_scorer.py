"""测试用自定义评分器。"""

from __future__ import annotations

from typing import Any, Dict

from orchestrator.scoring.base import ScoreResult


def score(expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
    """若实际结果包含期望的 ``important`` 字段即判定通过。"""

    if actual.get("important") == expected.get("important"):
        return ScoreResult(score=1.0, pass_=True, reasoning="字段匹配")
    return ScoreResult(score=0.0, pass_=False, reasoning="字段不匹配")
