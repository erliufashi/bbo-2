"""精确匹配评分器。"""

from __future__ import annotations

from typing import Any, Dict

from .base import ScoreResult


class ExactMatchScorer:
    """比较实际值与期望值是否完全一致。"""

    def __init__(self, *, json_paths: list[str] | None = None):
        self._paths = tuple(json_paths or [])

    def _extract(self, data: Any, path: str) -> Any:
        """通过简单路径语法提取嵌套字段。"""

        current = data
        for segment in path.strip("$").strip(".").split("."):
            if not segment:
                continue
            if isinstance(current, dict) and segment in current:
                current = current[segment]
            else:
                raise KeyError(segment)
        return current

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:  # noqa: D401
        """实现基础接口。"""

        try:
            if self._paths:
                expected_subset = {path: self._extract(expected, path) for path in self._paths}
                actual_subset = {path: self._extract(actual, path) for path in self._paths}
                success = expected_subset == actual_subset
            else:
                success = expected == actual
        except KeyError as exc:
            return ScoreResult(score=0.0, pass_=False, reasoning=f"字段缺失: {exc}")
        return ScoreResult(
            score=1.0 if success else 0.0,
            pass_=success,
            reasoning="完全匹配" if success else "字段值不相同",
        )


__all__ = ["ExactMatchScorer"]
