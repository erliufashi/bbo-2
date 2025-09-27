"""评分器与聚合器测试。"""

from __future__ import annotations

import math

import pytest

from orchestrator.scoring.aggregators import AllMustPass, WeightedSum
from orchestrator.scoring.custom import CustomScriptScorer
from orchestrator.scoring.exact import ExactMatchScorer
from orchestrator.scoring.llm import SimpleLLMScorer


def test_exact_match_scorer_paths() -> None:
    scorer = ExactMatchScorer({"json_paths": ["$.a", "$.b"]})
    result = scorer.score(expected={"a": 1, "b": 2}, actual={"a": 1, "b": 2}, context={})
    assert result.pass_
    assert math.isclose(result.score, 1.0)


def test_custom_script_scorer(tmp_path) -> None:
    scorer = CustomScriptScorer({"entrypoint": "tests.sample_scorer:score"})
    result = scorer.score(
        expected={"important": "x"}, actual={"important": "x"}, context={}
    )
    assert result.pass_


def test_simple_llm_scorer_similarity() -> None:
    scorer = SimpleLLMScorer({"pass_threshold": 0.5})
    result = scorer.score(expected="你好世界", actual="你好 世界", context={})
    assert result.pass_
    assert 0.5 <= result.score <= 1.0


def test_weighted_sum_with_fail_fast() -> None:
    agg = WeightedSum(weights={"a": 0.5, "b": 0.5}, pass_threshold=0.8, fail_fast_on=["a"])
    a = type("SR", (), {"score": 1.0, "pass_": False})
    b = type("SR", (), {"score": 1.0, "pass_": True})
    result = agg.aggregate({"a": a, "b": b})
    assert not result.pass_
    assert "fail-fast" in result.reasoning


def test_weighted_sum_average() -> None:
    agg = WeightedSum(weights={"a": 0.5, "b": 0.5}, pass_threshold=0.7)
    a = type("SR", (), {"score": 1.0, "pass_": True})
    b = type("SR", (), {"score": 0.2, "pass_": True})
    result = agg.aggregate({"a": a, "b": b})
    assert not result.pass_
    assert pytest.approx(result.score, rel=1e-3) == 0.6


def test_all_must_pass() -> None:
    agg = AllMustPass()
    a = type("SR", (), {"score": 1.0, "pass_": True})
    b = type("SR", (), {"score": 1.0, "pass_": True})
    result = agg.aggregate({"a": a, "b": b})
    assert result.pass_
