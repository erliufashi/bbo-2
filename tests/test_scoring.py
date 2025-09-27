"""评分器与聚合器测试。"""
from __future__ import annotations

from orchestrator.scoring import ScoreResult, build_aggregator, build_scorer


def test_exact_match_scorer_success() -> None:
    scorer = build_scorer("exact_match", {"json_paths": ["$.name", "$.scores[0]"]})
    result = scorer.score(expected={"name": "A", "scores": [1]}, actual={"name": "A", "scores": [1]}, context={})
    assert result["pass_"] is True


def test_exact_match_scorer_failure() -> None:
    scorer = build_scorer("exact_match", {"json_paths": ["$.name"]})
    result = scorer.score(expected={"name": "A"}, actual={"name": "B"}, context={})
    assert result["pass_"] is False


def test_custom_script_scorer(tmp_path) -> None:
    module = tmp_path / "custom_mod.py"
    module.write_text(
        "from orchestrator.scoring.base import ScoreResult\n"
        "def score(*, expected, actual, context):\n"
        "    return ScoreResult(score=0.8, pass_=True, reasoning='ok')\n",
        encoding="utf-8",
    )
    import sys

    sys.path.insert(0, str(tmp_path))
    try:
        scorer = build_scorer("custom_script", {"entrypoint": "custom_mod:score"})
        result = scorer.score(expected={}, actual={}, context={})
        assert result["score"] == 0.8
    finally:
        sys.path.remove(str(tmp_path))


def test_llm_scorer_similarity() -> None:
    scorer = build_scorer("llm_scorer", {"pass_threshold": 0.3})
    result = scorer.score(expected="订单创建成功", actual="订单 创建 成功", context={})
    assert result["pass_"] is True


def test_weighted_sum_with_fail_fast() -> None:
    agg = build_aggregator(
        "weighted_sum",
        {"weights": {"a": 0.5, "b": 0.5}, "pass_threshold": 0.8, "fail_fast_on": ["a"]},
    )
    a = ScoreResult(score=1.0, pass_=True, reasoning="a")
    b = ScoreResult(score=0.6, pass_=True, reasoning="b")
    result = agg.aggregate({"a": a, "b": b})
    assert result["pass_"] is True

    b_fail = ScoreResult(score=0.6, pass_=False, reasoning="b")
    result_fail = agg.aggregate({"a": a, "b": b_fail})
    assert result_fail["pass_"] is True

    a_fail = ScoreResult(score=0.0, pass_=False, reasoning="a")
    result_fast = agg.aggregate({"a": a_fail, "b": b})
    assert result_fast["pass_"] is False
