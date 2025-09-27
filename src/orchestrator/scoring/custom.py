"""自定义脚本评分器。"""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any, Callable, Dict

from .base import ScoreResult, Scorer


class CustomScriptScorer(Scorer):
    """通过动态加载入口函数执行自定义评分逻辑。"""

    def __init__(self, config: Dict[str, Any]) -> None:
        entrypoint = config.get("entrypoint")
        if not entrypoint or ":" not in entrypoint:
            raise ValueError("entrypoint 必须采用 module:function 形式")
        self.entrypoint = entrypoint

    @staticmethod
    @lru_cache(maxsize=16)
    def _load_callable(entrypoint: str) -> Callable[[Any, Any, Dict[str, Any]], ScoreResult]:
        module_name, func_name = entrypoint.split(":", 1)
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        return func

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        func = self._load_callable(self.entrypoint)
        result = func(expected, actual, context)
        if isinstance(result, ScoreResult):
            return result
        if isinstance(result, dict):
            return ScoreResult(
                score=float(result.get("score", 0.0)),
                pass_=bool(result.get("pass_", False)),
                reasoning=str(result.get("reasoning", "")),
            )
        raise TypeError("自定义评分函数必须返回 ScoreResult 或字典")


__all__ = ["CustomScriptScorer"]
