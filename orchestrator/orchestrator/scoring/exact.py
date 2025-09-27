"""提供结构化数据的精确匹配打分器。"""
from __future__ import annotations

from typing import Any, Dict

from .base import ScoringError, ScoreResult


def _extract_path(data: Any, path: str) -> Any:
    """根据简化的点号路径提取值，例如 ``$.a.b``。"""
    if not path.startswith("$."):
        raise ScoringError(f"路径格式错误: {path}")
    parts = path[2:].split(".") if path != "$" else []
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ScoringError(f"路径 {path} 在数据中不存在")
    return current


class ExactMatchScorer:
    """通过字段匹配保证响应完全符合预期。"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.json_paths = config.get("json_paths") or []

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        try:
            if self.json_paths:
                for path in self.json_paths:
                    expected_value = _extract_path(expected, path)
                    actual_value = _extract_path(actual, path)
                    if expected_value != actual_value:
                        return ScoreResult(score=0.0, pass_=False, reasoning=f"字段 {path} 不匹配")
                return ScoreResult(score=1.0, pass_=True, reasoning="所有字段匹配")
            if expected != actual:
                return ScoreResult(score=0.0, pass_=False, reasoning="整体对象不匹配")
            return ScoreResult(score=1.0, pass_=True, reasoning="整体匹配")
        except ScoringError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ScoringError(f"精确匹配执行失败: {exc}") from exc


__all__ = ["ExactMatchScorer"]
