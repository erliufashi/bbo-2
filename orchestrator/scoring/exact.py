"""精确匹配评分器。"""
from __future__ import annotations

from typing import Any, Dict, Iterable

from .base import ScoreResult, Scorer


def _extract_path(data: Any, path: str) -> Any:
    """支持简单语法的 JSONPath（仅支持 $.a.b[0]）。"""

    if not path.startswith("$"):
        raise ValueError(f"路径必须以 $ 开头：{path}")
    parts = path[2:].split(".") if path.startswith("$.") else [path[1:]]

    current = data
    for part in parts:
        if not part:
            continue
        if "[" in part:
            field, index_part = part.split("[")
            index = int(index_part.rstrip("]"))
            current = current[field][index]
        else:
            current = current[part]
    return current


class ExactMatchScorer(Scorer):
    """针对 JSON 内容的精确匹配。"""

    def __init__(self, json_paths: Iterable[str]):
        self.json_paths = list(json_paths)

    def score(self, *, expected: Dict[str, Any], actual: Dict[str, Any], context: Dict[str, Any]) -> ScoreResult:
        mismatches = []
        for path in self.json_paths:
            try:
                exp_value = _extract_path(expected, path)
                act_value = _extract_path(actual, path)
            except (KeyError, IndexError, ValueError) as exc:
                mismatches.append(f"路径 {path} 解析失败：{exc}")
                continue

            if exp_value != act_value:
                mismatches.append(f"路径 {path} 期望 {exp_value} 实际 {act_value}")

        if mismatches:
            return ScoreResult(score=0.0, pass_=False, reasoning="; ".join(mismatches))
        return ScoreResult(score=1.0, pass_=True, reasoning="所有字段完全一致")


__all__ = ["ExactMatchScorer"]
