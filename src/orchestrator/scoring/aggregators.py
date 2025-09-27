"""聚合策略实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Protocol

from .base import ScoreResult


class Aggregator(Protocol):
    """聚合器需要实现的接口。"""

    def aggregate(self, results: Dict[str, ScoreResult]) -> ScoreResult:
        ...


@dataclass
class AllMustPass(Aggregator):
    """所有子评分器均通过才算通过。"""

    reasoning: str = "所有评分器通过"

    def aggregate(self, results: Dict[str, ScoreResult]) -> ScoreResult:
        passed = all(result.pass_ for result in results.values())
        avg_score = sum(result.score for result in results.values()) / max(len(results), 1)
        if not passed:
            failures = [name for name, result in results.items() if not result.pass_]
            return ScoreResult(score=avg_score, pass_=False, reasoning=f"以下评分失败: {failures}")
        return ScoreResult(score=avg_score, pass_=True, reasoning=self.reasoning)


@dataclass
class WeightedSum(Aggregator):
    """按照权重求和并支持失败即终止策略。"""

    weights: Dict[str, float]
    pass_threshold: float
    fail_fast_on: Iterable[str] | None = None

    def aggregate(self, results: Dict[str, ScoreResult]) -> ScoreResult:
        fail_fast = set(self.fail_fast_on or [])
        total = 0.0
        weight_sum = 0.0
        reasons = []
        for name, result in results.items():
            if name in fail_fast and not result.pass_:
                return ScoreResult(score=0.0, pass_=False, reasoning=f"评分器 {name} 标记为 fail-fast")
            weight = self.weights.get(name, 0.0)
            total += result.score * weight
            weight_sum += weight
            reasons.append(f"{name}:{result.score:.2f}")
        normalized = total / weight_sum if weight_sum else 0.0
        passed = normalized >= self.pass_threshold
        reasoning = f"加权得分 {normalized:.2f} ({', '.join(reasons)})"
        return ScoreResult(score=normalized, pass_=passed, reasoning=reasoning)


__all__ = ["Aggregator", "AllMustPass", "WeightedSum"]
