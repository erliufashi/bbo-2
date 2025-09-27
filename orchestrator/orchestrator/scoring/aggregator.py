"""聚合策略实现。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .base import ScoreResult, ScoringError


@dataclass(slots=True)
class AggregationResult:
    """聚合结果的数据载体。"""

    score: float
    passed: bool
    reasoning: str


class Aggregator:
    """聚合器的抽象基类。"""

    def aggregate(self, scores: Mapping[str, ScoreResult]) -> AggregationResult:
        raise NotImplementedError


@dataclass(slots=True)
class WeightedSum(Aggregator):
    """按照权重线性加权的聚合策略。"""

    weights: Mapping[str, float]
    pass_threshold: float
    fail_fast_on: Iterable[str] | None = None

    def aggregate(self, scores: Mapping[str, ScoreResult]) -> AggregationResult:
        missing = set(self.weights) - set(scores)
        if missing:
            raise ScoringError(f"缺失评分器结果: {', '.join(sorted(missing))}")

        reasoning_parts: list[str] = []
        total = 0.0
        for name, weight in self.weights.items():
            result = scores[name]
            reasoning_parts.append(f"{name}={result.score:.2f}*{weight:.2f}")
            total += result.score * weight
            if self.fail_fast_on and name in self.fail_fast_on and not result.pass_:
                return AggregationResult(
                    score=0.0,
                    passed=False,
                    reasoning="聚合前失败：" + result.reasoning,
                )
        passed = total >= self.pass_threshold
        reasoning = ", ".join(reasoning_parts)
        return AggregationResult(score=total, passed=passed, reasoning=reasoning)


__all__ = ["AggregationResult", "Aggregator", "WeightedSum"]
