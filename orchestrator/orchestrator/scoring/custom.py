"""自定义脚本评分器，通过动态导入执行用户逻辑。"""
from __future__ import annotations

import importlib
from typing import Any, Dict

from .base import ScoreResult, ScoringError


class CustomScriptScorer:
    """以模块路径加载的自定义评分器。"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        try:
            self.module_path, self.func_name = config["entrypoint"].split(":", 1)
        except Exception as exc:  # noqa: BLE001
            raise ScoringError("自定义评分器 entrypoint 配置错误") from exc

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        try:
            module = importlib.import_module(self.module_path)
            func = getattr(module, self.func_name)
        except Exception as exc:  # noqa: BLE001
            raise ScoringError(f"加载自定义评分器失败: {exc}") from exc
        result = func(expected=expected, actual=actual, context=context)
        if not isinstance(result, dict):
            raise ScoringError("自定义评分器返回值必须是 dict")
        try:
            return ScoreResult(
                score=float(result["score"]),
                pass_=bool(result["pass_"]),
                reasoning=str(result.get("reasoning", "")),
            )
        except Exception as exc:  # noqa: BLE001
            raise ScoringError(f"自定义评分器返回值格式错误: {exc}") from exc


__all__ = ["CustomScriptScorer"]
