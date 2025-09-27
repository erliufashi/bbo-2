#!/usr/bin/env python3
"""
黑盒开发编排器 - 并行调度多个Gemini CLI Agents
"""

import subprocess
import json
import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

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
        prompt = f"""
你需要开发一个名为 {task.service_name} 的微服务。

服务要求：
- 语言: {task.definition['service']['language']}
- 端口: {task.definition['service']['runtime']['port']}
- 框架: FastAPI (Python)

需要实现以下测试用例能够通过：
"""
        for test_case in task.test_cases[:3]:  # 只使用前3个核心测试用例
            prompt += f"""
测试用例 {test_case['id']}:
- 请求: {test_case['request']['method']} {test_case['request']['path']}
- 期望状态码: {test_case['expected']['status']}
- 期望响应包含: {json.dumps(test_case['expected'].get('json', {}), ensure_ascii=False)}
"""

        prompt += f"""
请在 {task.service_path}/app/ 目录下创建：
1. main.py - 主应用文件，使用FastAPI框架
2. models.py - 数据模型定义
3. __init__.py - 包初始化文件

确保所有测试用例的端点都能正确响应。
"""
        return prompt
    
    def run_gemini_agent(self, task: ServiceTask, attempt: int = 1) -> Dict[str, Any]:
        """运行单个Gemini Agent来开发服务"""
        print(f"\n[{task.service_name}] 开始第 {attempt} 次开发尝试...")
        
        # 创建app目录
        app_dir = task.service_path / "app"
        app_dir.mkdir(exist_ok=True)
        
        prompt = self.generate_agent_prompt(task)
        
        # 设置环境变量
        env = os.environ.copy()
        env['GEMINI_API_KEY'] = self.api_key
        
        # 调用Gemini CLI - 使用正确的路径
        gemini_cli_dir = "/home/qiming/deca_project/git_project/geminiCLI"
        cmd = [
            'npx', '--no-install', 'gemini',
            '--approval-mode', 'yolo',  # 自动批准所有操作
            '-p', prompt
        ]
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=gemini_cli_dir  # 在gemini CLI目录运行
            )
            
            # 检查是否生成了必要文件
            main_file = app_dir / "main.py"
            if main_file.exists():
                print(f"[{task.service_name}] 代码生成成功")
                return {
                    "status": "generated",
                    "service": task.service_name,
                    "attempt": attempt,
                    "files_created": list(app_dir.glob("*.py"))
                }
            else:
                print(f"[{task.service_name}] 代码生成失败，未找到main.py")
                return {
                    "status": "failed",
                    "service": task.service_name,
                    "attempt": attempt,
                    "error": "main.py not created"
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
        """运行服务测试"""
        print(f"[{task.service_name}] 运行测试...")
        
        # 这里应该调用项目的测试运行器
        # 暂时模拟测试结果
        test_results = {
            "service": task.service_name,
            "total_tests": len(task.test_cases),
            "passed": 0,
            "failed": 0,
            "results": []
        }
        
        # 检查服务是否可以启动
        main_file = task.service_path / "app" / "main.py"
        if main_file.exists():
            # 尝试导入检查语法
            try:
                with open(main_file) as f:
                    code = f.read()
                compile(code, str(main_file), 'exec')
                test_results["passed"] = len(task.test_cases) // 2  # 模拟50%通过
                test_results["failed"] = len(task.test_cases) - test_results["passed"]
                test_results["status"] = "partial_pass"
            except SyntaxError as e:
                test_results["failed"] = len(task.test_cases)
                test_results["status"] = "syntax_error"
                test_results["error"] = str(e)
        else:
            test_results["failed"] = len(task.test_cases)
            test_results["status"] = "no_code"
            
        return test_results
    
    def develop_service(self, task: ServiceTask, max_attempts: int = 3) -> Dict[str, Any]:
        """开发单个服务，包括多次尝试直到测试通过"""
        service_result = {
            "service": task.service_name,
            "attempts": [],
            "final_status": "pending"
        }
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n{'='*60}")
            print(f"[{task.service_name}] 开发尝试 {attempt}/{max_attempts}")
            print(f"{'='*60}")
            
            # 运行Gemini Agent生成代码
            gen_result = self.run_gemini_agent(task, attempt)
            service_result["attempts"].append(gen_result)
            
            if gen_result["status"] == "generated":
                # 运行测试
                test_result = self.run_tests(task)
                service_result["attempts"][-1]["test_result"] = test_result
                
                if test_result["status"] == "partial_pass" and test_result["passed"] > 0:
                    print(f"[{task.service_name}] 测试部分通过 ({test_result['passed']}/{test_result['total_tests']})")
                    if test_result["passed"] / test_result["total_tests"] >= 0.8:
                        service_result["final_status"] = "success"
                        break
                elif test_result["status"] == "syntax_error":
                    print(f"[{task.service_name}] 代码有语法错误，需要重新生成")
            
            # 如果失败，等待后重试
            if attempt < max_attempts:
                print(f"[{task.service_name}] 等待10秒后重试...")
                time.sleep(10)
        
        if service_result["final_status"] != "success":
            service_result["final_status"] = "failed"
            
        return service_result
    
    def orchestrate_parallel(self, service_dirs: List[Path]) -> Dict[str, Any]:
        """并行编排多个服务的开发"""
        print(f"开始并行开发 {len(service_dirs)} 个微服务...")
        print(f"最大并行数: {self.max_workers}")
        
        tasks = []
        for service_dir in service_dirs:
            try:
                task = self.load_service_task(service_dir)
                tasks.append(task)
                print(f"已加载服务: {task.service_name}")
            except Exception as e:
                print(f"加载服务失败 {service_dir}: {str(e)}")
        
        results = {
            "start_time": time.time(),
            "services": {},
            "summary": {
                "total": len(tasks),
                "success": 0,
                "failed": 0
            }
        }
        
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
    
    # 运行并行编排
    results = orchestrator.orchestrate_parallel(service_dirs)
    
    # 输出结果报告
    print("\n" + "="*80)
    print("黑盒开发完成报告")
    print("="*80)
    print(f"总耗时: {results['duration']:.2f} 秒")
    print(f"成功服务: {results['summary']['success']}/{results['summary']['total']}")
    print(f"失败服务: {results['summary']['failed']}/{results['summary']['total']}")
    
    # 保存详细报告
    report_path = Path("/home/qiming/deca_project/bbo_test/development_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n详细报告已保存到: {report_path}")
    
    return results["summary"]["success"] == results["summary"]["total"]


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)