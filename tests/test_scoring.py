"""评分与聚合逻辑测试。"""

import pytest

from orchestrator.scoring import (
    DummyLLMScorer,
    ExactMatchScorer,
    PassThroughAggregator,
    WeightedSumAggregator,
)


def test_exact_match_with_paths() -> None:
    """当字段缺失时应返回失败。"""

    scorer = ExactMatchScorer(json_paths=["$.status", "$.body.order_id"])
    expected = {"status": 200, "body": {"order_id": "o-1"}}
    actual = {"status": 200, "body": {}}
    result = scorer.score(expected=expected, actual=actual, context={})
    assert not result["pass_"]
    assert "字段缺失" in result["reasoning"]


def test_weighted_sum_aggregator() -> None:
    """加权求和应按权重计算分数。"""

    agg = WeightedSumAggregator(weights={"a": 0.5, "b": 0.5}, pass_threshold=0.6)
    result = agg.aggregate(
        {
            "a": {"score": 1.0, "pass_": True, "reasoning": ""},
            "b": {"score": 0.2, "pass_": True, "reasoning": ""},
        }
    )
    assert pytest.approx(result["score"]) == 0.6
    assert result["pass_"]


def test_dummy_llm_scorer() -> None:
    """LLM 模拟器应基于词重叠率计算。"""

    scorer = DummyLLMScorer(pass_threshold=0.5)
    result = scorer.score(expected="你好 世界", actual="你好 Orchestrator", context={})
    assert 0.0 <= result["score"] <= 1.0
    assert result["reasoning"].startswith("重叠率")


def test_pass_through_aggregator_fail() -> None:
    """任一评分不通过时聚合结果应失败。"""

    agg = PassThroughAggregator()
    result = agg.aggregate({"a": {"score": 0.0, "pass_": False, "reasoning": ""}})
    assert not result["pass_"]
