"""测试运行器，实现对测试用例的逐条打分。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

from .loader import ServiceDefinition, resolve_scorer
from .scoring.aggregator import AggregationResult, Aggregator, WeightedSum
from .scoring.base import ScoreResult, ScoringError


@dataclass(slots=True)
class CaseResult:
    """单条用例的执行结果。"""

    id: str
    scores: Dict[str, ScoreResult]
    aggregation: AggregationResult
    passed: bool

    def to_dict(self) -> Dict[str, object]:
        """便于报告生成的序列化方法。"""
        return {
            "id": self.id,
            "scores": {key: score.to_dict() for key, score in self.scores.items()},
            "aggregation": {
                "score": self.aggregation.score,
                "passed": self.aggregation.passed,
                "reasoning": self.aggregation.reasoning,
            },
            "passed": self.passed,
        }


@dataclass(slots=True)
class RunSummary:
    """测试执行整体统计。"""

    results: List[CaseResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for case in self.results if case.passed)

    @property
    def failed(self) -> int:
        return sum(1 for case in self.results if not case.passed)


class TestRunner:
    """按 service_definition 运行测试套件。"""

    def __init__(self, definition: ServiceDefinition):
        self.definition = definition

    def _build_aggregator(self, config: Mapping[str, object]) -> Aggregator:
        kind = config.get("kind")
        if kind == "weighted_sum":
            weights_raw = config.get("weights", {})
            if not isinstance(weights_raw, Mapping):
                raise ScoringError("weighted_sum.weights 必须为字典")
            weights = {str(k): float(v) for k, v in weights_raw.items()}
            fail_fast = config.get("fail_fast_on")
            if fail_fast is not None and not isinstance(fail_fast, Iterable):
                raise ScoringError("weighted_sum.fail_fast_on 必须可迭代")
            return WeightedSum(
                weights=weights,
                pass_threshold=float(config.get("pass_threshold", 1.0)),
                fail_fast_on=list(fail_fast) if fail_fast is not None else None,
            )
        raise ScoringError(f"未知的聚合器类型: {kind}")

    def _load_suite(self) -> Iterable[Mapping[str, object]]:
        suite_path = self.definition.tests.suite_file
        with Path(suite_path).open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ScoringError("测试套件文件必须为列表")
        return data

    def run(self) -> RunSummary:
        summary = RunSummary()
        for case in self._load_suite():
            case_id = str(case.get("id"))
            scorer_configs = case.get("scorers", [])
            if not isinstance(scorer_configs, list):
                raise ScoringError("scorers 字段必须为列表")
            scores: Dict[str, ScoreResult] = {}
            for scorer_def in scorer_configs:
                alias = str(scorer_def.get("alias"))
                scorer_name = scorer_def.get("use")
                scorer = resolve_scorer(scorer_name, self.definition)
                expected = scorer_def.get("expected")
                actual = scorer_def.get("actual")
                context = dict(scorer_def.get("context", {}))
                scores[alias] = scorer.score(expected=expected, actual=actual, context=context)
            aggregator_conf = case.get("aggregator") or {}
            if not aggregator_conf:
                raise ScoringError("每个用例必须声明 aggregator")
            aggregator = self._build_aggregator(aggregator_conf)
            aggregation = aggregator.aggregate(scores)
            summary.results.append(
                CaseResult(id=case_id, scores=scores, aggregation=aggregation, passed=aggregation.passed)
            )
        return summary


__all__ = ["CaseResult", "RunSummary", "TestRunner"]
