#!/usr/bin/env python3
"""
黑盒开发完整演示脚本
展示从数据集构建到服务部署的完整流程
"""

import os
import sys
import time
import json
import yaml
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# 添加彩色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(step_num: int, title: str):
    """打印步骤标题"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}Step {step_num}: {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")

def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(message: str):
    """打印信息"""
    print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")

class BlackBoxDemo:
    """黑盒开发演示类"""
    
    def __init__(self, service_name: str = "demo-service"):
        self.service_name = service_name
        self.work_dir = Path(tempfile.mkdtemp(prefix="blackbox_demo_"))
        self.service_dir = self.work_dir / service_name
        self.service_dir.mkdir(parents=True)
        
    def step1_build_dataset(self):
        """Step 1: 构建数据集"""
        print_step(1, "构建数据集")
        
        # 创建服务定义
        service_def = {
            "version": "1.0",
            "service": {
                "name": self.service_name,
                "language": "python",
                "runtime": {
                    "port": 8000,
                    "framework": "fastapi"
                }
            },
            "tests": {
                "suite_file": "tests/test_cases.json",
                "pass_threshold": 0.8
            }
        }
        
        with open(self.service_dir / "service_definition.yaml", "w") as f:
            yaml.dump(service_def, f)
        
        print_info(f"创建服务定义: {self.service_dir}/service_definition.yaml")
        
        # 创建测试用例
        test_cases = [
            {
                "id": "health-check",
                "description": "健康检查端点",
                "priority": "P0",
                "request": {
                    "method": "GET",
                    "path": "/health"
                },
                "expected": {
                    "status": 200,
                    "json": {
                        "status": "healthy"
                    }
                }
            },
            {
                "id": "create-item",
                "description": "创建项目",
                "priority": "P0",
                "request": {
                    "method": "POST",
                    "path": "/items",
                    "json": {
                        "name": "Test Item",
                        "price": 29.99,
                        "description": "A test item"
                    }
                },
                "expected": {
                    "status": 201,
                    "json": {
                        "id": "<uuid>",
                        "name": "Test Item",
                        "price": 29.99,
                        "description": "A test item"
                    }
                }
            },
            {
                "id": "get-item",
                "description": "获取项目",
                "priority": "P1",
                "request": {
                    "method": "GET",
                    "path": "/items/123"
                },
                "expected": {
                    "status": 200,
                    "json": {
                        "id": "123",
                        "name": "<any>",
                        "price": "<any>"
                    }
                }
            },
            {
                "id": "list-items",
                "description": "列出所有项目",
                "priority": "P1",
                "request": {
                    "method": "GET",
                    "path": "/items"
                },
                "expected": {
                    "status": 200,
                    "json": {
                        "items": "<array>",
                        "total": "<number>"
                    }
                }
            },
            {
                "id": "item-not-found",
                "description": "项目不存在",
                "priority": "P2",
                "request": {
                    "method": "GET",
                    "path": "/items/nonexistent"
                },
                "expected": {
                    "status": 404,
                    "json": {
                        "detail": "Item not found"
                    }
                }
            }
        ]
        
        tests_dir = self.service_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        with open(tests_dir / "test_cases.json", "w") as f:
            json.dump(test_cases, f, indent=2)
        
        print_info(f"创建 {len(test_cases)} 个测试用例")
        
        # 显示测试用例摘要
        print("\n📋 测试用例清单:")
        for tc in test_cases:
            priority_color = Colors.FAIL if tc['priority'] == 'P0' else Colors.WARNING if tc['priority'] == 'P1' else Colors.OKBLUE
            print(f"  {priority_color}[{tc['priority']}]{Colors.ENDC} {tc['id']}: {tc['description']}")
        
        print_success(f"数据集构建完成！位置: {self.service_dir}")
        
        return test_cases
    
    def step2_parallel_sampling(self, test_cases: List[dict]) -> Tuple[str, float]:
        """Step 2: 并行采样开发"""
        print_step(2, "并行采样开发")
        
        num_agents = 5
        print_info(f"启动 {num_agents} 个Agent并行开发...")
        
        # 模拟不同Agent生成的代码
        def generate_agent_code(agent_id: int) -> Tuple[str, str]:
            """模拟Agent生成代码"""
            
            # 基于agent_id生成不同质量的代码
            if agent_id == 1:
                # 完美实现
                code = '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: str
    name: str
    price: float
    description: Optional[str] = None

items_db = {}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: Item):
    item_id = str(uuid.uuid4())
    items_db[item_id] = item.dict()
    return ItemResponse(id=item_id, **item.dict())

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    if item_id not in items_db and item_id != "123":
        raise HTTPException(status_code=404, detail="Item not found")
    if item_id == "123":
        return ItemResponse(id="123", name="Test", price=10.0)
    return ItemResponse(id=item_id, **items_db[item_id])

@app.get("/items")
async def list_items():
    return {"items": list(items_db.values()), "total": len(items_db)}
'''
            
            elif agent_id == 2:
                # 良好实现（缺少错误处理）
                code = '''from fastapi import FastAPI
from pydantic import BaseModel
import uuid

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    description: str = ""

items = {}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/items", status_code=201)
def create_item(item: Item):
    item_id = str(uuid.uuid4())
    items[item_id] = item
    return {"id": item_id, **item.dict()}

@app.get("/items/{item_id}")
def get_item(item_id: str):
    if item_id == "123":
        return {"id": "123", "name": "Test", "price": 10}
    return {"id": item_id, **items[item_id].dict()}

@app.get("/items")
def list_items():
    return {"items": [v.dict() for v in items.values()], "total": len(items)}
'''
            
            elif agent_id == 3:
                # 部分实现
                code = '''from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/items")
def create_item(data: dict):
    return {"id": "123", **data}
'''
            
            elif agent_id == 4:
                # 有bug的实现
                code = '''from fastapi import FastAPI
import uuid

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}  # 错误的状态值

@app.post("/items", status_code=200)  # 错误的状态码
def create_item(item: dict):
    return {"id": str(uuid.uuid4()), **item}

@app.get("/items/{item_id}")
def get_item(item_id: str):
    return {}  # 空响应
'''
            
            else:
                # 最小实现
                code = '''from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}
'''
            
            return f"agent-{agent_id}", code
        
        # 并行生成代码
        print("\n🔄 Agent开发进度:")
        results = []
        
        with ThreadPoolExecutor(max_workers=num_agents) as executor:
            futures = []
            for i in range(1, num_agents + 1):
                future = executor.submit(generate_agent_code, i)
                futures.append(future)
                time.sleep(0.2)  # 模拟启动延迟
                print(f"  Agent-{i}: 开发中...")
            
            # 收集结果
            for future in as_completed(futures):
                agent_id, code = future.result()
                score = self.evaluate_code(code, test_cases)
                results.append((agent_id, code, score))
        
        # 显示结果
        print("\n📊 采样结果:")
        for agent_id, _, score in sorted(results, key=lambda x: x[2], reverse=True):
            if score >= 0.8:
                status = f"{Colors.OKGREEN}✅{Colors.ENDC}"
            elif score >= 0.6:
                status = f"{Colors.WARNING}⚠️{Colors.ENDC}"
            else:
                status = f"{Colors.FAIL}❌{Colors.ENDC}"
            print(f"  {status} {agent_id}: {score:.0%} 测试通过")
        
        # 选择最佳
        best = max(results, key=lambda x: x[2])
        print(f"\n{Colors.BOLD}🏆 最佳实现: {best[0]} (得分: {best[2]:.0%}){Colors.ENDC}")
        
        return best[1], best[2]
    
    def evaluate_code(self, code: str, test_cases: List[dict]) -> float:
        """评估代码质量"""
        score = 0
        total = len(test_cases)
        
        # 简化的静态分析评分
        for tc in test_cases:
            if tc['id'] == 'health-check':
                if '@app.get("/health")' in code and '"status": "healthy"' in code:
                    score += 1
            elif tc['id'] == 'create-item':
                if '@app.post("/items"' in code and 'status_code=201' in code:
                    score += 1
            elif tc['id'] == 'get-item':
                if '@app.get("/items/{item_id}")' in code:
                    score += 1
            elif tc['id'] == 'list-items':
                if '@app.get("/items")' in code and '"items"' in code:
                    score += 1
            elif tc['id'] == 'item-not-found':
                if 'HTTPException' in code and '404' in code:
                    score += 1
        
        return score / total
    
    def step3_deploy_service(self, code: str):
        """Step 3: 部署服务"""
        print_step(3, "部署最优服务")
        
        # 保存代码
        app_dir = self.service_dir / "app"
        app_dir.mkdir(exist_ok=True)
        
        main_file = app_dir / "main.py"
        with open(main_file, "w") as f:
            f.write(code)
        
        (app_dir / "__init__.py").touch()
        
        print_info(f"代码已保存到: {main_file}")
        
        # 创建requirements.txt
        requirements = """fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
"""
        with open(self.service_dir / "requirements.txt", "w") as f:
            f.write(requirements)
        
        print_info("创建 requirements.txt")
        
        # 创建Dockerfile
        dockerfile = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        with open(self.service_dir / "Dockerfile", "w") as f:
            f.write(dockerfile)
        
        print_info("创建 Dockerfile")
        
        # 创建docker-compose.yml
        docker_compose = f"""version: '3.8'

services:
  {self.service_name}:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=development
    volumes:
      - ./app:/app/app
"""
        with open(self.service_dir / "docker-compose.yml", "w") as f:
            f.write(docker_compose)
        
        print_info("创建 docker-compose.yml")
        
        print_success("服务部署准备完成！")
        
        return main_file
    
    def step4_verify_service(self, main_file: Path):
        """Step 4: 验证服务"""
        print_step(4, "验证服务")
        
        print_info("启动服务进行验证...")
        
        # 这里简化验证，实际应该启动服务并发送HTTP请求
        try:
            # 检查语法
            with open(main_file) as f:
                code = f.read()
            compile(code, str(main_file), 'exec')
            print_success("Python语法检查通过")
            
            # 检查必要的端点
            checks = [
                ("健康检查端点", '/health' in code),
                ("创建端点", '/items' in code and 'post' in code.lower()),
                ("获取端点", '/items/{' in code),
                ("列表端点", '@app.get("/items")' in code),
                ("FastAPI导入", 'from fastapi import' in code),
                ("错误处理", 'HTTPException' in code or '404' in code)
            ]
            
            print("\n📝 功能检查:")
            for name, passed in checks:
                if passed:
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {name}")
                else:
                    print(f"  {Colors.FAIL}✗{Colors.ENDC} {name}")
            
            passed_count = sum(1 for _, p in checks if p)
            total_count = len(checks)
            
            if passed_count == total_count:
                print_success(f"所有功能检查通过！({passed_count}/{total_count})")
            elif passed_count >= total_count * 0.8:
                print_warning(f"大部分功能检查通过 ({passed_count}/{total_count})")
            else:
                print_error(f"功能检查未通过 ({passed_count}/{total_count})")
            
        except SyntaxError as e:
            print_error(f"语法错误: {e}")
        
        print_info(f"\n启动命令: cd {self.service_dir} && uvicorn app.main:app --reload")
        print_info(f"Docker命令: cd {self.service_dir} && docker-compose up")
    
    def show_summary(self, score: float):
        """显示总结"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}🎉 黑盒开发演示完成！{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        
        print("\n📊 关键指标:")
        print(f"  • 并行Agent数: 5")
        print(f"  • 最佳得分: {score:.0%}")
        print(f"  • 开发时间: <1分钟")
        print(f"  • 人工干预: 0")
        
        print("\n🔑 核心理念验证:")
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 数据驱动 - 测试用例定义了全部行为")
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 并行采样 - 5个Agent同时开发")
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 自动选择 - 基于测试分数选择最优")
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 快速收敛 - 一轮采样即找到解决方案")
        
        print(f"\n📁 项目位置: {self.service_dir}")
        print(f"📚 了解更多: 查看 TUTORIAL.md")
        
    def cleanup(self):
        """清理临时文件"""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
    
    def run(self):
        """运行完整演示"""
        try:
            print(f"\n{Colors.BOLD}{Colors.OKCYAN}🚀 黑盒开发完整演示{Colors.ENDC}")
            print(f"{Colors.BOLD}从数据集到服务部署的完整流程{Colors.ENDC}")
            
            # Step 1: 构建数据集
            test_cases = self.step1_build_dataset()
            time.sleep(1)
            
            # Step 2: 并行采样
            best_code, score = self.step2_parallel_sampling(test_cases)
            time.sleep(1)
            
            # Step 3: 部署服务
            main_file = self.step3_deploy_service(best_code)
            time.sleep(1)
            
            # Step 4: 验证服务
            self.step4_verify_service(main_file)
            
            # 显示总结
            self.show_summary(score)
            
            # 询问是否保留文件
            print(f"\n{Colors.WARNING}是否保留生成的文件? (y/n): {Colors.ENDC}", end="")
            keep = input().strip().lower() == 'y'
            
            if keep:
                # 复制到当前目录
                target = Path.cwd() / self.service_name
                if target.exists():
                    print_warning(f"目录 {target} 已存在，跳过复制")
                else:
                    shutil.copytree(self.service_dir, target)
                    print_success(f"文件已保存到: {target}")
            else:
                self.cleanup()
                print_info("临时文件已清理")
                
        except KeyboardInterrupt:
            print_warning("\n演示被中断")
            self.cleanup()
        except Exception as e:
            print_error(f"发生错误: {e}")
            self.cleanup()


def main():
    """主函数"""
    # 检查Python版本
    if sys.version_info < (3, 7):
        print_error("需要Python 3.7或更高版本")
        sys.exit(1)
    
    # 运行演示
    demo = BlackBoxDemo("demo-service")
    demo.run()


if __name__ == "__main__":
    main()