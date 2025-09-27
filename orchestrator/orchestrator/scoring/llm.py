"""LLM 评分器的轻量模拟实现。"""
from __future__ import annotations

from typing import Any, Dict

from .base import ScoreResult


class SimpleLLMScorer:
    """通过字符串相似度模拟 LLM 评分，便于在本地单元测试中运行。"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pass_threshold = float(config.get("pass_threshold", 0.5))

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        expected_text = str(expected)
        actual_text = str(actual)
        if not expected_text:
            return ScoreResult(score=1.0, pass_=True, reasoning="无需比较")
        overlap = len(set(expected_text.split()) & set(actual_text.split()))
        total = len(set(expected_text.split()) | set(actual_text.split())) or 1
        score = overlap / total
        reasoning = f"重合词占比 {score:.2f}"
        return ScoreResult(score=score, pass_=score >= self.pass_threshold, reasoning=reasoning)


__all__ = ["SimpleLLMScorer"]
