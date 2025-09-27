"""依赖管理模块测试。"""

import pytest

from orchestrator.deps import DependencyConfig, DependencyError, DependencyProvisioner


def test_openapi_stub_provision() -> None:
    """应能成功拉起 OpenAPI 桩服务。"""

    provisioner = DependencyProvisioner()
    config = DependencyConfig(
        name="user-service",
        kind="openapi_stub",
        options={
            "contract": "tests/data/service/api/openapi.yaml",
            "fixtures": "tests/data/service/tests/fixtures",
        },
    )
    handle = provisioner.provision(config)
    assert handle.is_ready()
    assert handle.endpoint.startswith("stub://")


def test_real_service_missing_health() -> None:
    """缺失健康检查配置时应报错。"""

    provisioner = DependencyProvisioner()
    config = DependencyConfig(name="payment", kind="real_service", options={})
    with pytest.raises(DependencyError):
        provisioner.provision(config)
