"""针对配置加载模块的测试。"""

from pathlib import Path

import pytest

from orchestrator.loader import ValidationError, load_service_definition


def test_load_service_definition_success(tmp_path: Path) -> None:
    """应能成功解析规范示例中的配置。"""

    definition = load_service_definition(Path("tests/data/service/service_definition.yaml"))
    assert definition.service.name == "order-service"
    assert "exact_body" in definition.tests.registered_scorers


def test_load_service_definition_missing_field(tmp_path: Path) -> None:
    """缺失字段时应抛出校验异常。"""

    bad_file = tmp_path / "service_definition.yaml"
    bad_file.write_text("version: '1.0'", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_service_definition(bad_file)
