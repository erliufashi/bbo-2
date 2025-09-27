"""模拟 LLM 评分器。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import ScoreResult, Scorer


def _tokenize(text: str) -> set[str]:
    return {ch for ch in text if not ch.isspace()}


def _similarity(a: str, b: str) -> float:
    """基于 Jaccard 的简单相似度，避免外部依赖。"""

    set_a = _tokenize(a)
    set_b = _tokenize(b)
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


@dataclass
class SimulatedLLMScorer(Scorer):
    """使用字符串相似度近似 LLM 评分。"""

    pass_threshold: float = 0.85

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        expected_text = str(expected)
        actual_text = str(actual)
        similarity = _similarity(expected_text, actual_text)
        return ScoreResult(
            score=similarity,
            pass_=similarity >= self.pass_threshold,
            reasoning=f"文本相似度={similarity:.2f} 阈值={self.pass_threshold}",
        )


__all__ = ["SimulatedLLMScorer"]
