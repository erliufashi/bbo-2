"""评分器基础定义。"""
from __future__ import annotations

from typing import Any, Dict, Protocol, TypedDict


class ScoreResult(TypedDict):
    """统一的评分结果结构。"""

    score: float
    pass_: bool
    reasoning: str


class Scorer(Protocol):
    """评分器通用接口。"""

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        ...


class Aggregator(Protocol):
    """聚合器接口。"""

    def aggregate(self, scorer_results: Dict[str, ScoreResult]) -> ScoreResult:
        ...


__all__ = ["ScoreResult", "Scorer", "Aggregator"]
