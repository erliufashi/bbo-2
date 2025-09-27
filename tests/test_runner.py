"""测试执行与汇总逻辑。"""

from pathlib import Path

from orchestrator.loader import load_service_definition
from orchestrator.runner import TestRunner


def test_runner_executes_cases(tmp_path) -> None:
    """应当正确执行示例测试套件。"""

    definition = load_service_definition(Path("tests/data/service/service_definition.yaml"))
    runner = TestRunner(definition)
    results = runner.run()
    assert {result.case_id for result in results} == {"create-order-success", "create-order-failure"}
    # 成功用例应通过，失败用例应失败
    status = {result.case_id: result.passed for result in results}
    assert status["create-order-success"] is True
    assert status["create-order-failure"] is False
