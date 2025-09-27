"""聚合策略实现。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .base import Aggregator, ScoreResult


@dataclass
class WeightedSum(Aggregator):
    """加权求和聚合器，支持 fail-fast。"""

    weights: Dict[str, float]
    pass_threshold: float
    fail_fast_on: Iterable[str] | None = None
    reasoning_prefix: str = field(default="加权求和")

    def aggregate(self, scorer_results: Dict[str, ScoreResult]) -> ScoreResult:
        missing = set(self.weights) - set(scorer_results)
        if missing:
            raise KeyError(f"缺少评分器结果：{', '.join(sorted(missing))}")

        logs: List[str] = []
        total = 0.0
        fail_fast = set(self.fail_fast_on or [])
        for name, weight in self.weights.items():
            res = scorer_results[name]
            logs.append(f"{name}={res['score']}*{weight}")
            if name in fail_fast and not res["pass_"]:
                return ScoreResult(score=0.0, pass_=False, reasoning=f"{name} 未通过触发 fail-fast")
            total += res["score"] * weight

        return ScoreResult(
            score=total,
            pass_=total >= self.pass_threshold,
            reasoning=f"{self.reasoning_prefix}: {' + '.join(logs)} >= {self.pass_threshold}",
        )


def build_aggregator(name: str, config: Dict[str, object]) -> Aggregator:
    """根据名称构建聚合器。"""

    if name == "weighted_sum":
        return WeightedSum(
            weights=config.get("weights", {}),
            pass_threshold=float(config.get("pass_threshold", 1.0)),
            fail_fast_on=config.get("fail_fast_on"),
        )
    raise ValueError(f"未知聚合器：{name}")


__all__ = ["WeightedSum", "build_aggregator"]
