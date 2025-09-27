"""评分器基础定义。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass
class ScoreResult:
    """评分结果封装。"""

    score: float
    pass_: bool
    reasoning: str = ""


class Scorer(Protocol):
    """所有评分器必须实现的接口。"""

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        ...


__all__ = ["ScoreResult", "Scorer"]
