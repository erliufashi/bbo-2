"""自定义脚本评分器。"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Dict

from .base import ScoreResult, Scorer


@dataclass
class CustomScriptScorer(Scorer):
    """通过模块路径加载的评分器。"""

    entrypoint: str

    def __post_init__(self) -> None:
        module_name, _, attr = self.entrypoint.partition(":")
        if not module_name or not attr:
            raise ValueError("entrypoint 必须形如 'module:function'")
        module = importlib.import_module(module_name)
        self._callable = getattr(module, attr)

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        result = self._callable(expected=expected, actual=actual, context=context)
        if not {"score", "pass_", "reasoning"} <= result.keys():  # pragma: no cover - 防御型
            raise ValueError("自定义脚本返回结构不符合 ScoreResult 要求")
        return ScoreResult(
            score=float(result["score"]),
            pass_=bool(result["pass_"]),
            reasoning=str(result["reasoning"]),
        )


__all__ = ["CustomScriptScorer"]
