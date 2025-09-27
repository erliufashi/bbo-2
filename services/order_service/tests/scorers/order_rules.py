"""示例业务规则评分脚本。"""
from __future__ import annotations

from orchestrator.scoring.base import ScoreResult


def score(*, expected, actual, context):
    """简单校验订单号格式与状态。"""

    order_id = actual.get("order_id") if isinstance(actual, dict) else None
    status = actual.get("status") if isinstance(actual, dict) else None
    if isinstance(order_id, str) and order_id.startswith("order-") and status == "created":
        return ScoreResult(score=1.0, pass_=True, reasoning="订单号格式正确")
    return ScoreResult(score=0.0, pass_=False, reasoning="订单号或状态不合法")
