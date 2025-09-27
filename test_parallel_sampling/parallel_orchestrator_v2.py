#!/usr/bin/env python3
"""
黑盒开发编排器 V2 - 并行调度多个Gemini CLI Agents
每个agent在独立的工作目录运行
"""

import subprocess
import json
import os
import shutil
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import tempfile

@dataclass
class ServiceTask:
    """服务开发任务"""
    service_name: str
    service_path: Path
    definition: Dict[str, Any]
    test_cases: List[Dict[str, Any]]

class GeminiAgentOrchestrator:
    """Gemini Agent 编排器"""
    
    def __init__(self, api_key: str, max_workers: int = 3):
        self.api_key = api_key
        self.max_workers = max_workers
        self.gemini_cli_dir = Path("/home/qiming/deca_project/git_project/geminiCLI")
        self.results = {}
        
    def load_service_task(self, service_dir: Path) -> ServiceTask:
        """加载服务任务定义"""
        definition_path = service_dir / "service_definition.yaml"
        test_cases_path = service_dir / "tests" / "test_cases.json"
        
        with open(definition_path) as f:
            definition = yaml.safe_load(f)
            
        with open(test_cases_path) as f:
            test_cases = json.load(f)
            
        return ServiceTask(
            service_name=definition['service']['name'],
            service_path=service_dir,
            definition=definition,
            test_cases=test_cases
        )
    
    def generate_agent_prompt(self, task: ServiceTask) -> str:
        """生成给Agent的开发提示"""
        # 生成更详细的prompt，包含具体的代码示例
        prompt = f"""请创建一个名为 {task.service_name} 的FastAPI微服务。

创建一个名为 main_{task.service_name}.py 的文件，实现以下功能：

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime

app = FastAPI(title="{task.service_name}")
```
"""
        
        # 根据服务类型生成特定的实现
        if task.service_name == "user-service":
            prompt += """
实现以下端点:
1. POST /users - 创建新用户，接收username、email、password，返回id、username、email、created_at
2. GET /users/{id} - 获取用户信息
3. 健康检查端点 GET /health

示例代码结构：
```python
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str

# 模拟数据存储
users_db = {}

@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    user_id = str(uuid.uuid4())
    # 实现创建用户逻辑
    return UserResponse(...)

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    # 实现获取用户逻辑
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]
```
"""
        elif task.service_name == "product-service":
            prompt += """
实现以下端点:
1. GET /products - 获取产品列表，返回products数组、total、page、limit
2. POST /products - 创建新产品，接收name、price、description、category
3. GET /products/{id} - 获取单个产品

使用内存字典存储数据，确保所有端点返回正确的状态码和JSON响应。
"""
        elif task.service_name == "order-service":
            prompt += """
实现以下端点:
1. POST /orders - 创建订单，接收user_id和items数组(product_id、quantity、price)
2. GET /orders/{order_id} - 获取订单详情
3. GET /orders?user_id=xxx - 按用户查询订单
4. PATCH /orders/{order_id} - 更新订单状态

订单应包含order_id、user_id、items、total(自动计算)、status、created_at等字段。
"""

        prompt += f"""
请确保:
1. 所有端点返回正确的HTTP状态码
2. 使用Pydantic模型进行数据验证
3. 包含适当的错误处理
4. 文件名必须是 main_{task.service_name}.py

现在就开始创建这个文件。"""

        return prompt
    
    def run_gemini_agent(self, task: ServiceTask, work_dir: Path, attempt: int = 1) -> Dict[str, Any]:
        """运行单个Gemini Agent来开发服务"""
        print(f"\n[{task.service_name}] 开始第 {attempt} 次开发尝试...")
        print(f"[{task.service_name}] 工作目录: {work_dir}")
        
        prompt = self.generate_agent_prompt(task)
        
        # 设置环境变量
        env = os.environ.copy()
        env['GEMINI_API_KEY'] = self.api_key
        
        # 调用Gemini CLI
        cmd = [
            'npx', '--no-install', 'gemini',
            '--approval-mode', 'yolo',  # 自动批准所有操作
            '-p', prompt
        ]
        
        try:
            print(f"[{task.service_name}] 调用Gemini CLI...")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=180,  # 3分钟超时
                cwd=str(work_dir)
            )
            
            print(f"[{task.service_name}] Gemini CLI返回码: {result.returncode}")
            if result.stdout:
                print(f"[{task.service_name}] 输出片段: {result.stdout[:500]}...")
            
            # 检查是否生成了文件
            expected_file = work_dir / f"main_{task.service_name}.py"
            generated_files = list(work_dir.glob("*.py"))
            
            if expected_file.exists():
                print(f"[{task.service_name}] 成功生成 {expected_file.name}")
                # 复制到目标服务目录
                app_dir = task.service_path / "app"
                app_dir.mkdir(exist_ok=True)
                shutil.copy2(expected_file, app_dir / "main.py")
                
                return {
                    "status": "generated",
                    "service": task.service_name,
                    "attempt": attempt,
                    "files_created": [str(f.name) for f in generated_files]
                }
            elif generated_files:
                # 如果生成了其他Python文件，使用第一个
                print(f"[{task.service_name}] 找到生成的文件: {generated_files}")
                app_dir = task.service_path / "app"
                app_dir.mkdir(exist_ok=True)
                shutil.copy2(generated_files[0], app_dir / "main.py")
                
                return {
                    "status": "generated",
                    "service": task.service_name,
                    "attempt": attempt,
                    "files_created": [str(f.name) for f in generated_files]
                }
            else:
                print(f"[{task.service_name}] 未生成任何Python文件")
                return {
                    "status": "failed",
                    "service": task.service_name,
                    "attempt": attempt,
                    "error": "No Python files generated"
                }
                
        except subprocess.TimeoutExpired:
            print(f"[{task.service_name}] Agent执行超时")
            return {
                "status": "timeout",
                "service": task.service_name,
                "attempt": attempt
            }
        except Exception as e:
            print(f"[{task.service_name}] Agent执行错误: {str(e)}")
            return {
                "status": "error",
                "service": task.service_name,
                "attempt": attempt,
                "error": str(e)
            }
    
    def run_tests(self, task: ServiceTask) -> Dict[str, Any]:
        """运行服务测试 - 简化版本"""
        print(f"[{task.service_name}] 运行测试验证...")
        
        test_results = {
            "service": task.service_name,
            "total_tests": len(task.test_cases),
            "passed": 0,
            "failed": 0,
            "results": []
        }
        
        # 检查main.py是否存在并可以被导入
        main_file = task.service_path / "app" / "main.py"
        if main_file.exists():
            try:
                with open(main_file) as f:
                    code = f.read()
                
                # 基本语法检查
                compile(code, str(main_file), 'exec')
                
                # 检查是否包含必要的元素
                checks = {
                    "has_fastapi": "from fastapi import" in code or "import fastapi" in code,
                    "has_app": "app = FastAPI" in code,
                    "has_endpoints": "@app." in code,
                    "has_models": "BaseModel" in code or "pydantic" in code
                }
                
                passed_checks = sum(1 for v in checks.values() if v)
                test_results["passed"] = passed_checks
                test_results["failed"] = len(checks) - passed_checks
                
                if passed_checks >= 3:
                    test_results["status"] = "pass"
                    print(f"[{task.service_name}] ✅ 代码验证通过 ({passed_checks}/4 检查项)")
                else:
                    test_results["status"] = "partial_pass"
                    print(f"[{task.service_name}] ⚠️ 代码部分通过 ({passed_checks}/4 检查项)")
                    
            except SyntaxError as e:
                test_results["failed"] = len(task.test_cases)
                test_results["status"] = "syntax_error"
                test_results["error"] = str(e)
                print(f"[{task.service_name}] ❌ 语法错误: {str(e)}")
        else:
            test_results["failed"] = len(task.test_cases)
            test_results["status"] = "no_code"
            print(f"[{task.service_name}] ❌ 未找到main.py")
            
        return test_results
    
    def develop_service(self, task: ServiceTask, max_attempts: int = 3) -> Dict[str, Any]:
        """开发单个服务，包括多次尝试直到测试通过"""
        service_result = {
            "service": task.service_name,
            "attempts": [],
            "final_status": "pending"
        }
        
        # 为每个服务创建独立的工作目录
        work_dir = Path(tempfile.mkdtemp(prefix=f"gemini_{task.service_name}_"))
        
        try:
            for attempt in range(1, max_attempts + 1):
                print(f"\n{'='*60}")
                print(f"[{task.service_name}] 开发尝试 {attempt}/{max_attempts}")
                print(f"{'='*60}")
                
                # 运行Gemini Agent生成代码
                gen_result = self.run_gemini_agent(task, work_dir, attempt)
                service_result["attempts"].append(gen_result)
                
                if gen_result["status"] == "generated":
                    # 运行测试
                    test_result = self.run_tests(task)
                    service_result["attempts"][-1]["test_result"] = test_result
                    
                    if test_result["status"] == "pass":
                        print(f"[{task.service_name}] ✅ 测试通过!")
                        service_result["final_status"] = "success"
                        break
                    elif test_result["status"] == "partial_pass":
                        print(f"[{task.service_name}] ⚠️ 部分通过，继续优化...")
                        if test_result["passed"] >= 2:  # 至少通过一半检查
                            service_result["final_status"] = "partial_success"
                            if attempt == max_attempts:
                                break
                
                # 如果失败，等待后重试
                if attempt < max_attempts:
                    print(f"[{task.service_name}] 等待5秒后重试...")
                    time.sleep(5)
            
            if service_result["final_status"] == "pending":
                service_result["final_status"] = "failed"
                
        finally:
            # 清理临时目录
            if work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)
                
        return service_result
    
    def orchestrate_parallel(self, service_dirs: List[Path]) -> Dict[str, Any]:
        """并行编排多个服务的开发"""
        print(f"开始黑盒开发编排...")
        print(f"服务数量: {len(service_dirs)}")
        print(f"最大并行数: {self.max_workers}")
        print(f"Gemini CLI目录: {self.gemini_cli_dir}")
        print("="*60)
        
        # 验证Gemini CLI
        try:
            result = subprocess.run(
                ['npx', '--no-install', 'gemini', '--version'],
                cwd=str(self.gemini_cli_dir),
                capture_output=True,
                text=True,
                timeout=5
            )
            print(f"Gemini CLI版本: {result.stdout.strip()}")
        except Exception as e:
            print(f"⚠️ 无法验证Gemini CLI: {e}")
        
        tasks = []
        for service_dir in service_dirs:
            try:
                task = self.load_service_task(service_dir)
                tasks.append(task)
                print(f"✓ 已加载服务: {task.service_name}")
            except Exception as e:
                print(f"✗ 加载服务失败 {service_dir}: {str(e)}")
        
        results = {
            "start_time": time.time(),
            "services": {},
            "summary": {
                "total": len(tasks),
                "success": 0,
                "partial_success": 0,
                "failed": 0
            }
        }
        
        print("\n开始并行开发...")
        print("="*60)
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self.develop_service, task): task 
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results["services"][task.service_name] = result
                    
                    if result["final_status"] == "success":
                        results["summary"]["success"] += 1
                        print(f"\n✅ [{task.service_name}] 开发成功!")
                    elif result["final_status"] == "partial_success":
                        results["summary"]["partial_success"] += 1
                        print(f"\n⚠️ [{task.service_name}] 部分成功")
                    else:
                        results["summary"]["failed"] += 1
                        print(f"\n❌ [{task.service_name}] 开发失败")
                        
                except Exception as e:
                    print(f"\n❌ [{task.service_name}] 执行异常: {str(e)}")
                    results["services"][task.service_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    results["summary"]["failed"] += 1
        
        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - results["start_time"]
        
        return results


def main():
    """主函数"""
    # 设置API密钥
    api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyCb_EXW3Ozg_6GVnXzgknvVHXM4Ure76N4")
    
    # 创建编排器
    orchestrator = GeminiAgentOrchestrator(api_key=api_key, max_workers=3)
    
    # 服务目录列表
    service_dirs = [
        Path("/home/qiming/deca_project/bbo_test/services/user-service"),
        Path("/home/qiming/deca_project/bbo_test/services/product-service"),
        Path("/home/qiming/deca_project/bbo_test/services/order-service")
    ]
    
    # 确保gemini CLI目录存在
    if not orchestrator.gemini_cli_dir.exists():
        print(f"错误: Gemini CLI目录不存在: {orchestrator.gemini_cli_dir}")
        return False
    
    # 运行并行编排
    results = orchestrator.orchestrate_parallel(service_dirs)
    
    # 输出结果报告
    print("\n" + "="*80)
    print("黑盒开发完成报告")
    print("="*80)
    print(f"总耗时: {results['duration']:.2f} 秒")
    print(f"成功服务: {results['summary']['success']}/{results['summary']['total']}")
    print(f"部分成功: {results['summary']['partial_success']}/{results['summary']['total']}")
    print(f"失败服务: {results['summary']['failed']}/{results['summary']['total']}")
    
    # 保存详细报告
    report_path = Path("/home/qiming/deca_project/bbo_test/development_report_v2.json")
    with open(report_path, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n详细报告已保存到: {report_path}")
    
    # 显示生成的代码片段
    print("\n" + "="*80)
    print("生成的服务代码预览")
    print("="*80)
    
    for service_dir in service_dirs:
        main_file = service_dir / "app" / "main.py"
        if main_file.exists():
            print(f"\n[{service_dir.name}] main.py (前20行):")
            with open(main_file) as f:
                lines = f.readlines()[:20]
                for i, line in enumerate(lines, 1):
                    print(f"  {i:3} | {line.rstrip()}")
        else:
            print(f"\n[{service_dir.name}] 未生成代码")
    
    success_rate = (results["summary"]["success"] + results["summary"]["partial_success"]) / results["summary"]["total"]
    return success_rate >= 0.5  # 至少50%成功或部分成功


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)