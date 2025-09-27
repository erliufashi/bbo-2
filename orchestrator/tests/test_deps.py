"""依赖管理模块测试。"""
from __future__ import annotations

import pytest

from orchestrator.deps import DependencyError, provision_dependency


def test_provision_dependency_mock() -> None:
    dep = provision_dependency(kind="openapi_stub", name="user-service", mode="mock")
    assert dep.endpoint == "mock://user-service"
    assert dep.is_ready()


def test_provision_dependency_real_missing_endpoint() -> None:
    with pytest.raises(DependencyError):
        provision_dependency(kind="http", name="user-service", mode="real")
