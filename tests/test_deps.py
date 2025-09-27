"""依赖提供器测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.deps import DependencyProvisioner


def test_provision_openapi_stub(tmp_path: Path) -> None:
    contract = tmp_path / "api.yaml"
    contract.write_text("openapi: 3.0.0", encoding="utf-8")
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    provisioner = DependencyProvisioner()

    dep = provisioner.provision(
        kind="openapi_stub",
        name="user-service",
        config={"contract": str(contract), "fixtures": str(fixtures)},
    )

    assert dep.is_ready()
    assert dep.metadata["contract"] == str(contract)


def test_provision_external_service_missing_image() -> None:
    provisioner = DependencyProvisioner()

    with pytest.raises(ValueError):
        provisioner.provision(kind="external_service", name="svc", config={})
