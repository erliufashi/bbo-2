from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime

app = FastAPI(title="order-service")

# 数据模型
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class ShippingAddress(BaseModel):
    street: str
    city: str
    zip: str

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem]
    shipping_address: Optional[ShippingAddress] = None

class OrderResponse(BaseModel):
    order_id: str
    user_id: str
    items: List[OrderItem]
    total: float
    status: str
    created_at: str
    updated_at: Optional[str] = None

class OrderStatus(BaseModel):
    status: str

# 模拟数据库
orders_db: Dict[str, dict] = {}

# 添加测试数据
orders_db["order-abc123"] = {
    "order_id": "order-abc123",
    "user_id": "user-123",
    "items": [{"product_id": "prod-456", "quantity": 2, "price": 49.99}],
    "total": 99.98,
    "status": "PENDING",
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": None
}

@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate):
    """创建订单"""
    # 验证
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")
    
    order_id = str(uuid.uuid4())
    
    # 计算总价
    total = sum(item.quantity * item.price for item in order.items)
    
    now = datetime.utcnow().isoformat()
    
    orders_db[order_id] = {
        "order_id": order_id,
        "user_id": order.user_id,
        "items": [item.dict() for item in order.items],
        "total": total,
        "status": "PENDING",
        "created_at": now,
        "updated_at": None
    }
    
    return OrderResponse(
        order_id=order_id,
        user_id=order.user_id,
        items=order.items,
        total=total,
        status="PENDING",
        created_at=now
    )

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """获取订单详情"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    return OrderResponse(
        order_id=order["order_id"],
        user_id=order["user_id"],
        items=[OrderItem(**item) for item in order["items"]],
        total=order["total"],
        status=order["status"],
        created_at=order["created_at"],
        updated_at=order.get("updated_at")
    )

@app.get("/orders")
async def list_user_orders(user_id: str):
    """查询用户订单"""
    user_orders = [
        order for order in orders_db.values()
        if order["user_id"] == user_id
    ]
    
    return {
        "orders": user_orders,
        "total": len(user_orders)
    }

@app.patch("/orders/{order_id}")
async def update_order_status(order_id: str, status_update: OrderStatus):
    """更新订单状态"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    orders_db[order_id]["status"] = status_update.status
    orders_db[order_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return {
        "order_id": order_id,
        "status": status_update.status,
        "updated_at": orders_db[order_id]["updated_at"]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "order-service"}
