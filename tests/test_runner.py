"""测试运行器整体流程。"""
from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.loader import load_service_definition, load_test_suite
from orchestrator.runner import TestRunner
from services.order_service.app import main as service_main


@pytest.fixture
def runner() -> TestRunner:
    definition = load_service_definition(Path("services/order_service/service_definition.yaml"))
    suite = load_test_suite(definition, Path("services/order_service"))
    transport = service_main.create_transport()
    return TestRunner(definition, suite, transport=transport)


def test_runner_execute_suite(runner: TestRunner) -> None:
    result = runner.run()
    summary = result.summary
    assert summary["total"] == 2
    assert summary["failed"] >= 1


def test_runner_filter_case(runner: TestRunner) -> None:
    result = runner.run(selected_ids=["create-order-success"])
    assert len(result.cases) == 1
    assert result.cases[0].id == "create-order-success"
