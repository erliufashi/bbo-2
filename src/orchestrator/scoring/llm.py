"""模拟 LLM 语义评分器。"""

from __future__ import annotations

import difflib
from typing import Any, Dict

from .base import ScoreResult, Scorer


class SimpleLLMScorer(Scorer):
    """基于文本相似度的轻量级评分器，用于离线测试。"""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self.pass_threshold = float(cfg.get("pass_threshold", 0.8))
        self.normalize = bool(cfg.get("normalize", True))

    @staticmethod
    def _to_text(value: Any) -> str:
        if isinstance(value, (dict, list)):
            return str(value)
        return str(value or "")

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        exp_text = self._to_text(expected)
        act_text = self._to_text(actual)
        if self.normalize:
            exp_text = exp_text.strip().lower()
            act_text = act_text.strip().lower()
        ratio = difflib.SequenceMatcher(None, exp_text, act_text).ratio()
        passed = ratio >= self.pass_threshold
        reasoning = f"相似度 {ratio:.2f}，阈值 {self.pass_threshold:.2f}"
        return ScoreResult(score=ratio, pass_=passed, reasoning=reasoning)


__all__ = ["SimpleLLMScorer"]
