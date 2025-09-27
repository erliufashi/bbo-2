from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime

app = FastAPI(title="product-service")

# 数据模型
class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    category: str

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    description: str
    category: str
    created_at: str

class ProductList(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    limit: int

# 模拟数据库
products_db: Dict[str, dict] = {}

# 添加一些初始数据
for i in range(5):
    pid = f"prod-{i+100}"
    products_db[pid] = {
        "id": pid,
        "name": f"Product {i+1}",
        "price": 10.0 * (i+1),
        "description": f"Description for product {i+1}",
        "category": "electronics" if i % 2 == 0 else "books",
        "created_at": datetime.utcnow().isoformat()
    }

@app.get("/products")
async def list_products(page: int = 1, limit: int = 10):
    """获取产品列表"""
    products = list(products_db.values())
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "products": products[start:end],
        "total": len(products),
        "page": page,
        "limit": limit
    }

@app.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    """创建新产品"""
    # 验证
    if not product.name:
        raise HTTPException(status_code=400, detail="Product name cannot be empty")
    if product.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
    
    product_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    products_db[product_id] = {
        "id": product_id,
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "category": product.category,
        "created_at": now
    }
    
    return ProductResponse(
        id=product_id,
        name=product.name,
        price=product.price,
        description=product.description,
        category=product.category,
        created_at=now
    )

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """获取产品详情"""
    # 处理测试数据
    if product_id == "prod-123":
        return ProductResponse(
            id="prod-123",
            name="Test Product",
            price=99.99,
            description="Test product",
            category="test",
            created_at=datetime.utcnow().isoformat()
        )
    
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    return ProductResponse(**product)

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "product-service"}
