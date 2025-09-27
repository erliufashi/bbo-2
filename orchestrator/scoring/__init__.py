"""评分模块入口。"""
from __future__ import annotations

from typing import Dict

from .aggregator import WeightedSum, build_aggregator
from .base import Aggregator, ScoreResult, Scorer
from .custom import CustomScriptScorer
from .exact import ExactMatchScorer
from .llm import SimulatedLLMScorer


def build_scorer(kind: str, config: Dict[str, object]) -> Scorer:
    """根据类型构建评分器实例。"""

    if kind == "exact_match":
        return ExactMatchScorer(json_paths=config.get("json_paths", []))
    if kind == "custom_script":
        return CustomScriptScorer(entrypoint=config.get("entrypoint", ""))
    if kind == "llm_scorer":
        return SimulatedLLMScorer(pass_threshold=float(config.get("pass_threshold", 0.85)))
    raise ValueError(f"未知的评分器类型：{kind}")


__all__ = [
    "ScoreResult",
    "Scorer",
    "Aggregator",
    "WeightedSum",
    "build_aggregator",
    "build_scorer",
]
