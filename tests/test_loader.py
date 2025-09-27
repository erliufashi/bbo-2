"""针对服务定义加载模块的单元测试。"""
from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.loader import load_service_definition, load_test_suite


def test_load_service_definition_success(tmp_path: Path) -> None:
    path = Path("services/order_service/service_definition.yaml")
    definition = load_service_definition(path)
    assert definition.service.name == "order-service"
    assert "exact_body" in definition.tests.registered_scorers

    suite = load_test_suite(definition, path.parent)
    assert suite.entries[0].id == "create-order-success"


def test_load_service_definition_error(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError) as err:
        load_service_definition(bad_file)
    assert "缺少 service 节点" in str(err.value)
