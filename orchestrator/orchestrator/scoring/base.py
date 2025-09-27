"""评分模块基础设施，提供统一的打分器接口定义。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(slots=True)
class ScoreResult:
    """打分结果的数据结构。"""

    score: float
    pass_: bool
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """便于序列化的辅助方法。"""
        return {"score": self.score, "pass_": self.pass_, "reasoning": self.reasoning}


class Scorer(Protocol):
    """评分器协议，所有自定义评分器需要实现该接口。"""

    config: Dict[str, Any]

    def score(self, *, expected: Any, actual: Any, context: Dict[str, Any]) -> ScoreResult:
        """执行打分逻辑并返回评分结果。"""
        ...


@dataclass(slots=True)
class RegisteredScorer:
    """`service_definition.yaml` 中注册的评分器声明。"""

    name: str
    kind: str
    config: Dict[str, Any]


class ScoringError(RuntimeError):
    """评分流程中产生的异常。"""


__all__ = [
    "ScoreResult",
    "Scorer",
    "RegisteredScorer",
    "ScoringError",
]
