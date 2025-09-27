"""示例订单服务，使用简单函数模拟 HTTP 行为。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class Order:
    order_id: str
    status: str


class OrderService:
    """提供订单创建与健康检查能力。"""

    def __init__(self) -> None:
        self.orders: List[Order] = []

    def create_order(self, payload: Dict[str, object]) -> Dict[str, object]:
        items = payload.get("items") or []
        if not items:
            return {"status": 400, "body": {"detail": "订单必须包含商品"}}
        order_id = f"order-{len(self.orders)+1:04d}"
        order = Order(order_id=order_id, status="created")
        self.orders.append(order)
        return {"status": 201, "body": {"order_id": order.order_id, "status": order.status}}

    def health(self) -> Dict[str, object]:
        return {"status": 200, "body": {"status": "ok", "timestamp": datetime.utcnow().isoformat()}}

    def handle_request(self, request: Dict[str, object]) -> Dict[str, object]:
        method = str(request.get("method", "GET")).upper()
        path = request.get("path", "/")
        if method == "POST" and path == "/orders":
            return self.create_order(request.get("json") or {})
        if method == "GET" and path == "/healthz":
            return self.health()
        return {"status": 404, "body": {"detail": "未找到对应接口"}}


_SERVICE = OrderService()


def handle_request(request: Dict[str, object]) -> Dict[str, object]:
    """供编排器直接调用的入口。"""

    return _SERVICE.handle_request(request)


class _Transport:
    """提供给编排器的传输适配器。"""

    def perform(self, request: Dict[str, object]) -> Dict[str, object]:
        return handle_request(request)


def create_transport() -> _Transport:
    """编排器通过服务定义反射获得该工厂。"""

    return _Transport()
