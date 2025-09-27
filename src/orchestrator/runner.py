"""测试执行模块。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .scoring.aggregators import AllMustPass, WeightedSum
from .scoring.base import ScoreResult
from .scoring.custom import CustomScriptScorer
from .scoring.exact import ExactMatchScorer
from .scoring.llm import SimpleLLMScorer


@dataclass
class CaseResult:
    """记录单个测试用例的执行结果。"""

    id: str
    passed: bool
    score: float
    reasoning: str
    scorer_results: Dict[str, ScoreResult]


@dataclass
class SuiteResult:
    """测试套件执行后的汇总。"""

    results: List[CaseResult] = field(default_factory=list)

    @property
    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        avg_score = sum(r.score for r in self.results) / total if total else 0.0
        return {"total": total, "passed": passed, "avg_score": avg_score}


class TestSuiteRunner:
    """根据测试用例定义文件执行请求并聚合评分。"""

    __test__ = False  # 避免被 pytest 误识别为测试类

    def __init__(
        self,
        *,
        scorer_configs: Mapping[str, Mapping[str, Any]],
        request_executor: Callable[[Mapping[str, Any]], Any],
    ) -> None:
        self.scorer_configs = dict(scorer_configs)
        self.request_executor = request_executor

    def _instantiate_scorer(self, name: str):
        if name not in self.scorer_configs:
            raise KeyError(f"未注册评分器: {name}")
        config = self.scorer_configs[name]
        kind = config.get("kind")
        cfg = config.get("config", {})
        if kind == "exact_match":
            return ExactMatchScorer(cfg)
        if kind == "custom_script":
            return CustomScriptScorer(cfg)
        if kind == "llm_scorer":
            return SimpleLLMScorer(cfg)
        raise ValueError(f"未知评分器类型: {kind}")

    @staticmethod
    def _build_aggregator(config: Mapping[str, Any] | None):
        if not config:
            return AllMustPass()
        kind = config.get("kind")
        if kind == "all_must_pass":
            return AllMustPass()
        if kind == "weighted_sum":
            return WeightedSum(
                weights=config.get("weights", {}),
                pass_threshold=float(config.get("pass_threshold", 1.0)),
                fail_fast_on=config.get("fail_fast_on"),
            )
        raise ValueError(f"未知聚合器类型: {kind}")

    def run(self, suite_file: Path) -> SuiteResult:
        data = json.loads(suite_file.read_text(encoding="utf-8"))
        if not isinstance(data, Iterable):
            raise ValueError("测试用例文件必须是列表")
        suite_result = SuiteResult()
        for case in data:
            if not isinstance(case, Mapping):
                raise ValueError("测试用例必须是字典")
            case_id = str(case.get("id"))
            request = case.get("request", {})
            expected = case.get("expected")
            scorer_names: List[str] = case.get("scorers", [])
            aggregator_cfg = case.get("aggregator")
            context = {"case_id": case_id, "raw": case}
            actual = self.request_executor(request)
            scorer_results: Dict[str, ScoreResult] = {}
            for scorer_name in scorer_names:
                scorer = self._instantiate_scorer(scorer_name)
                result = scorer.score(expected=expected, actual=actual, context=context)
                scorer_results[scorer_name] = result
            aggregator = self._build_aggregator(aggregator_cfg)
            aggregated = aggregator.aggregate(scorer_results)
            suite_result.results.append(
                CaseResult(
                    id=case_id,
                    passed=aggregated.pass_,
                    score=aggregated.score,
                    reasoning=aggregated.reasoning,
                    scorer_results=scorer_results,
                )
            )
        return suite_result


__all__ = ["TestSuiteRunner", "SuiteResult", "CaseResult"]
