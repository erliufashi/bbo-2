"""评分器基础接口。"""

from __future__ import annotations

from typing import Any, Dict, Protocol, TypedDict


class ScoreResult(TypedDict):
    """统一的评分结果结构。"""

    score: float
    pass_: bool
    reasoning: str


class Scorer(Protocol):
    """所有评分器需实现的接口。"""

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        """计算评分。"""

        ...


__all__ = ["ScoreResult", "Scorer"]
