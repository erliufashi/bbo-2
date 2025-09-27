"""精确匹配评分器实现。"""

from __future__ import annotations

from typing import Any, Dict, Iterable

from .base import ScoreResult, Scorer


class ExactMatchScorer(Scorer):
    """按照 JSON 路径执行精确匹配。"""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        cfg = config or {}
        paths = cfg.get("json_paths", [])
        self.paths = list(paths) if isinstance(paths, Iterable) else []

    @staticmethod
    def _extract(data: Any, path: str) -> Any:
        current = data
        for part in path.strip("$").strip(".").split("."):
            if part == "":
                continue
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise KeyError(f"路径 {path} 不存在")
        return current

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        paths = self.paths or ["$"]
        mismatches = []
        for path in paths:
            try:
                exp_value = expected if path == "$" else self._extract(expected, path)
                act_value = actual if path == "$" else self._extract(actual, path)
            except KeyError as exc:
                return ScoreResult(score=0.0, pass_=False, reasoning=str(exc))
            if exp_value != act_value:
                mismatches.append((path, exp_value, act_value))
        if mismatches:
            details = "; ".join(
                f"路径 {p} 期望 {e!r} 实际 {a!r}" for p, e, a in mismatches
            )
            return ScoreResult(score=0.0, pass_=False, reasoning=details)
        return ScoreResult(score=1.0, pass_=True, reasoning="所有字段完全匹配")


__all__ = ["ExactMatchScorer"]
