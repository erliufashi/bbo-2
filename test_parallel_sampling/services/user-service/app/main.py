from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Optional
import uuid
from datetime import datetime

app = FastAPI(title="user-service")

# 数据模型
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str

# 模拟数据库
users_db: Dict[str, dict] = {}

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """创建新用户"""
    # 检查邮箱格式
    if "@" not in user.email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    users_db[user_id] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password": user.password,  # 实际应用中应该hash
        "created_at": now
    }
    
    return UserResponse(
        id=user_id,
        username=user.username,
        email=user.email,
        created_at=now
    )

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """获取用户信息"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"]
    )

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "user-service"}
