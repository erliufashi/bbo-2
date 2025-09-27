"""聚合策略实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from .base import ScoreResult


@dataclass(slots=True)
class WeightedSumAggregator:
    """按权重加权求和并判断通过与否。"""

    weights: Mapping[str, float]
    pass_threshold: float
    fail_fast_on: tuple[str, ...] = ()

    def aggregate(self, partial: Mapping[str, ScoreResult]) -> ScoreResult:
        total = 0.0
        weight_sum = 0.0
        reasons: list[str] = []
        for name, result in partial.items():
            weight = float(self.weights.get(name, 0.0))
            weight_sum += weight
            total += result["score"] * weight
            reasons.append(f"{name}:{result['score']:.2f}")
            if name in self.fail_fast_on and not result["pass_"]:
                return ScoreResult(score=0.0, pass_=False, reasoning=f"{name} 触发 fail_fast")
        if weight_sum == 0:
            raise ValueError("权重和不能为 0")
        final_score = total / weight_sum
        passed = final_score >= self.pass_threshold
        reasoning = " | ".join(reasons)
        return ScoreResult(score=final_score, pass_=passed, reasoning=reasoning)


@dataclass(slots=True)
class PassThroughAggregator:
    """所有评分结果均需通过。"""

    def aggregate(self, partial: Mapping[str, ScoreResult]) -> ScoreResult:
        reasons = []
        for name, result in partial.items():
            if not result["pass_"]:
                return ScoreResult(score=0.0, pass_=False, reasoning=f"{name} 未通过")
            reasons.append(f"{name}:{result['score']:.2f}")
        return ScoreResult(score=1.0, pass_=True, reasoning=" | ".join(reasons))


__all__ = ["WeightedSumAggregator", "PassThroughAggregator"]
