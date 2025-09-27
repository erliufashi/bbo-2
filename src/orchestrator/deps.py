"""依赖管理模块，支持 mock 与 real 两种模式。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional


@dataclass
class Dependency:
    """表示一次依赖实例化结果。"""

    name: str
    kind: str
    endpoint: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    ready: bool = True

    def is_ready(self) -> bool:
        """判断依赖是否可用。"""

        return self.ready


Provider = Callable[[str, Dict[str, Any]], Dependency]


class DependencyProvisioner:
    """简单的依赖提供器注册中心。"""

    def __init__(self) -> None:
        self._providers: Dict[str, Provider] = {}
        self._register_builtin()

    def _register_builtin(self) -> None:
        self.register_provider("openapi_stub", self._provision_openapi_stub)
        self.register_provider("external_service", self._provision_external_service)

    def register_provider(self, kind: str, provider: Provider) -> None:
        """注册新的依赖提供器。"""

        self._providers[kind] = provider

    def provision(self, *, kind: str, name: str, config: Optional[Dict[str, Any]] = None) -> Dependency:
        """创建依赖实例。"""

        if kind not in self._providers:
            raise KeyError(f"未注册的依赖类型: {kind}")
        provider = self._providers[kind]
        cfg = config or {}
        return provider(name, cfg)

    @staticmethod
    def _provision_openapi_stub(name: str, config: Dict[str, Any]) -> Dependency:
        """内置 OpenAPI Stub 提供器。"""

        contract = Path(config.get("contract", ""))
        if not contract.exists():
            raise FileNotFoundError(f"OpenAPI 合同文件不存在: {contract}")
        fixtures = config.get("fixtures")
        if fixtures is not None and not Path(fixtures).exists():
            raise FileNotFoundError(f"fixtures 路径不存在: {fixtures}")
        metadata = {"contract": str(contract), "fixtures": fixtures}
        endpoint = f"stub://{name}"
        return Dependency(name=name, kind="openapi_stub", endpoint=endpoint, metadata=metadata)

    @staticmethod
    def _provision_external_service(name: str, config: Dict[str, Any]) -> Dependency:
        """模拟真实服务启动结果。"""

        image = config.get("image")
        if not image:
            raise ValueError("external_service 需要提供镜像信息")
        health = config.get("health", "/")
        endpoint = f"http://{name}.local"
        metadata = {"image": image, "health": health}
        return Dependency(name=name, kind="external_service", endpoint=endpoint, metadata=metadata)


__all__ = ["Dependency", "DependencyProvisioner"]
