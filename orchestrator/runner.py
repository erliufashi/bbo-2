"""测试执行模块。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

from .loader import RegisteredScorer, ServiceDefinition
from .scoring import (
    CustomScriptScorer,
    DummyLLMScorer,
    ExactMatchScorer,
    PassThroughAggregator,
    ScoreResult,
    WeightedSumAggregator,
)


@dataclass(slots=True)
class TestResult:
    """单个测试用例执行结果。"""

    case_id: str
    passed: bool
    score: float
    details: Mapping[str, ScoreResult]


class TestRunner:
    """按照声明式配置执行测试。"""

    def __init__(self, definition: ServiceDefinition):
        self._definition = definition
        self._registered = definition.tests.registered_scorers

    def _build_scorer(self, name: str):
        if name not in self._registered:
            raise ValueError(f"未注册评分器 {name}")
        config = self._registered[name]
        if config.kind == "exact_match":
            return ExactMatchScorer(**config.config)
        if config.kind == "custom_script":
            return CustomScriptScorer(**config.config)
        if config.kind == "llm_scorer":
            return DummyLLMScorer(**config.config)
        raise ValueError(f"未知评分器类型 {config.kind}")

    def _build_aggregator(self, spec: Mapping[str, object] | None):
        if not spec:
            return PassThroughAggregator()
        kind = spec.get("kind")
        config = spec.get("config", {})
        if kind == "weighted_sum":
            weights = config.get("weights", {})
            threshold = float(config.get("pass_threshold", 1.0))
            fail_fast = tuple(config.get("fail_fast_on", []))
            return WeightedSumAggregator(weights=weights, pass_threshold=threshold, fail_fast_on=fail_fast)
        if kind == "pass_through":
            return PassThroughAggregator()
        raise ValueError(f"未知聚合器类型 {kind}")

    def _load_suite(self) -> List[Mapping[str, object]]:
        suite_path = self._definition.tests.suite_file
        with suite_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ValueError("测试套件应为列表")
        return data

    def run(self) -> List[TestResult]:
        """遍历测试套件并返回结果。"""

        results: List[TestResult] = []
        for case in self._load_suite():
            case_id = str(case.get("id"))
            expected = case.get("expected")
            actual = case.get("actual")
            scorers = case.get("scorers", [])
            aggregator = self._build_aggregator(case.get("aggregator"))
            partial: Dict[str, ScoreResult] = {}
            for scorer_name in scorers:
                scorer = self._build_scorer(str(scorer_name))
                partial[scorer_name] = scorer.score(
                    expected=expected,
                    actual=actual,
                    context={"case_id": case_id},
                )
            aggregate = aggregator.aggregate(partial)
            results.append(
                TestResult(
                    case_id=case_id,
                    passed=aggregate["pass_"],
                    score=aggregate["score"],
                    details=partial,
                )
            )
        return results


__all__ = ["TestRunner", "TestResult"]
