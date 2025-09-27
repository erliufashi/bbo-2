"""依赖管理模块测试。"""
from __future__ import annotations

import pytest

from orchestrator.deps import DependencyManager, provision_dependency


def test_dependency_manager_register_and_ready() -> None:
    manager = DependencyManager()
    mock_dep = provision_dependency(kind="openapi_stub", name="user-service", contract="api.yaml")
    manager.register(mock_dep)
    real_dep = provision_dependency(kind="real_service", name="payment", image="payment:1.0", healthy=False)
    manager.register(real_dep)

    status = manager.ready()
    assert status["user-service"] is True
    assert status["payment"] is False

    with pytest.raises(ValueError):
        manager.register(mock_dep)

    with pytest.raises(KeyError):
        manager.get("missing")
