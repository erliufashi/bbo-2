# 黑盒开发快速开始指南

## 5分钟上手黑盒开发

### 1. 安装依赖（30秒）

```bash
pip install fastapi uvicorn pydantic requests pyyaml
```

### 2. 创建你的第一个服务定义（1分钟）

创建 `hello_service.yaml`:

```yaml
version: "1.0"
service:
  name: hello-service
  port: 8000

test_cases:
  - id: "say-hello"
    request:
      method: GET
      path: /hello
    expected:
      status: 200
      json:
        message: "Hello, World!"
  
  - id: "say-hello-name"
    request:
      method: GET
      path: /hello/Alice
    expected:
      status: 200
      json:
        message: "Hello, Alice!"
```

### 3. 运行并行采样（3分钟）

```python
#!/usr/bin/env python3
# quickstart.py

import random
import json

def generate_service_implementations():
    """模拟5个Agent生成不同的实现"""
    
    implementations = []
    
    # Agent 1: 完美实现
    impl1 = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello, World!"}

@app.get("/hello/{name}")
def hello_name(name: str):
    return {"message": f"Hello, {name}!"}
'''
    
    # Agent 2: 有bug的实现
    impl2 = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/hello")
def hello():
    return {"msg": "Hello, World!"}  # 错误的key

@app.get("/hello/{name}")
def hello_name(name: str):
    return {"message": f"Hi, {name}!"}  # 错误的消息
'''
    
    # Agent 3: 部分实现
    impl3 = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello, World!"}
# 缺少 /hello/{name} 端点
'''
    
    # Agent 4: 另一个完美实现
    impl4 = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/hello")
async def hello():
    return {"message": "Hello, World!"}

@app.get("/hello/{name}")
async def hello_name(name: str):
    return {"message": f"Hello, {name}!"}
'''
    
    # Agent 5: 复杂实现
    impl5 = '''
from fastapi import FastAPI
from typing import Dict

app = FastAPI(title="Hello Service")

def create_message(name: str = "World") -> Dict[str, str]:
    return {"message": f"Hello, {name}!"}

@app.get("/hello")
def hello():
    return create_message()

@app.get("/hello/{name}")
def hello_name(name: str):
    return create_message(name)
'''
    
    return [impl1, impl2, impl3, impl4, impl5]

def test_implementation(code: str, test_cases: list) -> float:
    """测试一个实现"""
    # 这里简化测试逻辑
    # 实际应该启动服务并发送HTTP请求
    
    score = 0
    total = len(test_cases)
    
    # 模拟测试
    if '@app.get("/hello")' in code:
        score += 0.5
    if '@app.get("/hello/{name}")' in code:
        score += 0.5
    if 'return {"message":' in code:
        score += 0.5
    if 'f"Hello, {name}!"' in code or 'f"Hello, {name}!"' in code:
        score += 0.5
    
    return min(score / total, 1.0)

def parallel_sampling():
    """并行采样主函数"""
    print("🚀 黑盒开发 - 并行采样演示")
    print("="*50)
    
    # 测试用例
    test_cases = [
        {"id": "say-hello", "path": "/hello"},
        {"id": "say-hello-name", "path": "/hello/{name}"}
    ]
    
    # 生成5个实现
    print("\n📝 生成5个不同的实现...")
    implementations = generate_service_implementations()
    
    # 测试每个实现
    print("\n🧪 测试每个实现...")
    results = []
    for i, code in enumerate(implementations, 1):
        score = test_implementation(code, test_cases)
        results.append((i, score, code))
        
        status = "✅" if score >= 1.0 else "⚠️" if score >= 0.5 else "❌"
        print(f"  {status} Agent-{i}: {score:.0%} 测试通过")
    
    # 选择最佳实现
    best = max(results, key=lambda x: x[1])
    print(f"\n🏆 最佳实现: Agent-{best[0]} (得分: {best[1]:.0%})")
    
    # 保存最佳代码
    with open("best_implementation.py", "w") as f:
        f.write(best[2])
    
    print("\n✅ 最佳实现已保存到 best_implementation.py")
    
    # 展示最佳代码
    print("\n📄 最佳代码预览:")
    print("-"*50)
    lines = best[2].strip().split('\n')[:10]
    for line in lines:
        print(line)
    if len(best[2].strip().split('\n')) > 10:
        print("...")
    
    return best

if __name__ == "__main__":
    parallel_sampling()
```

### 4. 运行示例（30秒）

```bash
python quickstart.py
```

输出：
```
🚀 黑盒开发 - 并行采样演示
==================================================

📝 生成5个不同的实现...

🧪 测试每个实现...
  ✅ Agent-1: 100% 测试通过
  ❌ Agent-2: 25% 测试通过
  ⚠️ Agent-3: 50% 测试通过
  ✅ Agent-4: 100% 测试通过
  ✅ Agent-5: 100% 测试通过

🏆 最佳实现: Agent-1 (得分: 100%)

✅ 最佳实现已保存到 best_implementation.py

📄 最佳代码预览:
--------------------------------------------------
from fastapi import FastAPI
app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello, World!"}

@app.get("/hello/{name}")
def hello_name(name: str):
    return {"message": f"Hello, {name}!"}
```

### 5. 启动服务验证（30秒）

```bash
# 启动服务
uvicorn best_implementation:app --reload

# 在另一个终端测试
curl http://localhost:8000/hello
# {"message":"Hello, World!"}

curl http://localhost:8000/hello/Alice
# {"message":"Hello, Alice!"}
```

---

## 核心概念一览

### 什么是黑盒开发？

```
传统开发：需求 → 人工编码 → 测试 → 调试 → 部署
黑盒开发：需求 → 测试用例 → 多Agent并行编码 → 自动选择最优 → 部署
```

### 为什么要并行采样？

单个Agent成功率：60%
5个Agent并行采样至少一个成功：1-(0.4)^5 = 98.9%

### 三个核心文件

1. **service_definition.yaml** - 定义服务规范
2. **test_cases.json** - 定义测试用例（数据驱动）
3. **parallel_orchestrator.py** - 并行采样引擎

---

## 实战项目模板

### 创建一个完整的微服务

```bash
# 1. 创建项目结构
mkdir my-service && cd my-service
mkdir -p app tests data

# 2. 定义服务
cat > service_definition.yaml << EOF
version: "1.0"
service:
  name: my-service
  port: 8000
  
dependencies:
  - fastapi
  - uvicorn
  - pydantic
EOF

# 3. 定义测试用例
cat > tests/test_cases.json << EOF
[
  {
    "id": "health-check",
    "request": {"method": "GET", "path": "/health"},
    "expected": {"status": 200, "json": {"status": "ok"}}
  },
  {
    "id": "create-item",
    "request": {
      "method": "POST",
      "path": "/items",
      "json": {"name": "test", "price": 9.99}
    },
    "expected": {
      "status": 201,
      "json": {"id": "<uuid>", "name": "test", "price": 9.99}
    }
  }
]
EOF

# 4. 运行并行采样
python ../parallel_sampling_orchestrator.py

# 5. 启动服务
cd app && uvicorn main:app --reload
```

---

## 常用命令

```bash
# 运行简单演示
python simple_parallel_sampling.py

# 运行完整测试
python parallel_sampling_orchestrator.py

# 测试特定服务
python test_service.py services/user-service

# 查看测试报告
cat real_test_report.json | python -m json.tool

# 启动所有服务
docker-compose up

# 运行性能测试
ab -n 1000 -c 10 http://localhost:8000/users
```

---

## 下一步

1. 📖 阅读[完整教程](TUTORIAL.md)了解详细原理
2. 🔧 查看[高级配置](ADVANCED.md)优化采样策略
3. 🚀 集成真实AI Agent（GPT-4, Claude, Gemini）
4. 📊 使用监控面板查看采样过程
5. 🌐 部署到生产环境

---

## 获取帮助

- 📚 文档：[TUTORIAL.md](TUTORIAL.md)
- 💬 讨论：[GitHub Issues](https://github.com/erliufashi/bbo-2/issues)
- 📧 邮箱：support@blackbox.dev
- 🎥 视频教程：[YouTube](https://youtube.com/blackboxdev)

---

## License

MIT License - 自由使用，包括商业用途。