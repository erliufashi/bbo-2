"""模拟 LLM 打分器以便单元测试覆盖。"""

from __future__ import annotations

from typing import Any, Dict

from .base import ScoreResult


class DummyLLMScorer:
    """通过词集合重叠度模拟语义评分。"""

    def __init__(self, *, pass_threshold: float = 0.8):
        self._threshold = pass_threshold

    def _tokenize(self, text: str) -> set[str]:
        return {token for token in text.replace("\n", " ").split(" ") if token}

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        expected_text = str(expected)
        actual_text = str(actual)
        expected_tokens = self._tokenize(expected_text)
        actual_tokens = self._tokenize(actual_text)
        if not expected_tokens:
            overlap = 1.0 if not actual_tokens else 0.0
        else:
            intersection = len(expected_tokens & actual_tokens)
            union = len(expected_tokens | actual_tokens)
            overlap = intersection / union if union else 0.0
        passed = overlap >= self._threshold
        reasoning = (
            f"重叠率 {overlap:.2f}，阈值 {self._threshold:.2f}"
        )
        return ScoreResult(score=overlap, pass_=passed, reasoning=reasoning)


__all__ = ["DummyLLMScorer"]
