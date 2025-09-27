"""自定义脚本评分器。"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Callable

from .base import ScoreResult


class CustomScriptScorer:
    """动态加载用户提供的评分函数。"""

    def __init__(self, *, entrypoint: str):
        if ":" not in entrypoint:
            raise ValueError("entrypoint 需要形如 module:function")
        module_name, func_name = entrypoint.split(":", 1)
        self._module_name = module_name
        self._func_name = func_name

    def _load(self) -> Callable[[Any, Any, Dict[str, Any]], ScoreResult]:
        """加载用户函数。"""

        module = importlib.import_module(self._module_name)
        func = getattr(module, self._func_name)
        return func  # type: ignore[return-value]

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        scorer = self._load()
        result = scorer(expected, actual, context)
        if not isinstance(result, dict) or "score" not in result or "pass_" not in result:
            raise ValueError("自定义评分函数必须返回 ScoreResult 结构")
        return ScoreResult(
            score=float(result["score"]),
            pass_=bool(result["pass_"]),
            reasoning=str(result.get("reasoning", "")),
        )


__all__ = ["CustomScriptScorer"]
