"""针对服务定义加载器的单元测试。"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from orchestrator.loader import ServiceDefinitionError, load_service_definition


def test_load_service_definition_success(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        {
          "version": "1.0",
          "service": {"name": "demo"},
          "tests": {"suite_file": "tests/test_cases.json"}
        }
        """
    )
    file_path = tmp_path / "service_definition.yaml"
    file_path.write_text(content, encoding="utf-8")

    definition = load_service_definition(file_path)

    assert definition.get("service.name") == "demo"
    assert definition.get("tests.suite_file") == "tests/test_cases.json"


def test_load_service_definition_validation_error(tmp_path: Path) -> None:
    file_path = tmp_path / "service_definition.yaml"
    file_path.write_text("{\"service\": {}}", encoding="utf-8")

    with pytest.raises(ServiceDefinitionError) as exc:
        load_service_definition(file_path)
    assert "version" in str(exc.value)
