"""示例自定义评分脚本。"""

from __future__ import annotations

from typing import Any, Dict


def score(expected: Any, actual: Any, context: Dict[str, Any]):
    """检查订单总额必须为正。"""

    actual_total = actual.get("body", {}).get("total", 0)
    passed = actual_total > 0
    return {
        "score": 1.0 if passed else 0.0,
        "pass_": passed,
        "reasoning": f"订单总额 {actual_total}",
    }
