"""评分相关模块测试。"""
from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.scoring.aggregator import WeightedSum
from orchestrator.scoring.base import ScoreResult, ScoringError
from orchestrator.scoring.custom import CustomScriptScorer
from orchestrator.scoring.exact import ExactMatchScorer
from orchestrator.scoring.llm import SimpleLLMScorer


def test_weighted_sum_with_fail_fast() -> None:
    agg = WeightedSum(weights={"a": 0.5, "b": 0.5}, pass_threshold=0.8, fail_fast_on=["a"])
    scores = {
        "a": ScoreResult(score=1.0, pass_=True, reasoning="ok"),
        "b": ScoreResult(score=0.6, pass_=True, reasoning="partial"),
    }
    result = agg.aggregate(scores)
    assert result.passed
    assert result.score == pytest.approx(0.8)


def test_weighted_sum_missing_score() -> None:
    agg = WeightedSum(weights={"a": 1.0}, pass_threshold=0.5)
    with pytest.raises(ScoringError):
        agg.aggregate({})


def test_exact_match_json_paths() -> None:
    scorer = ExactMatchScorer({"json_paths": ["$.foo", "$.bar"]})
    result = scorer.score(expected={"foo": 1, "bar": 2}, actual={"foo": 1, "bar": 2}, context={})
    assert result.pass_


def test_custom_script_scorer(tmp_path: Path) -> None:
    scorer = CustomScriptScorer({"entrypoint": "orchestrator.tests.data.scorers.custom_rules:score"})
    result = scorer.score(expected=10, actual=12, context={})
    assert result.pass_


def test_llm_scorer_similarity() -> None:
    scorer = SimpleLLMScorer({"pass_threshold": 0.2})
    result = scorer.score(expected="hello world", actual="hello ai", context={})
    assert result.score > 0
