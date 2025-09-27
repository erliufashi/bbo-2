"""依赖管理模块。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Dependency:
    """依赖基础信息。"""

    name: str
    kind: str
    target: str

    def is_ready(self) -> bool:  # pragma: no cover - 由子类实现
        raise NotImplementedError


@dataclass
class MockDependency(Dependency):
    """Mock 依赖，始终就绪。"""

    def is_ready(self) -> bool:
        return True


@dataclass
class RealDependency(Dependency):
    """真实依赖，模拟健康检查。"""

    health_endpoint: Optional[str] = None
    healthy: bool = True

    def is_ready(self) -> bool:
        return self.healthy


class DependencyManager:
    """依赖注册与查询。"""

    def __init__(self) -> None:
        self._deps: Dict[str, Dependency] = {}

    def register(self, dep: Dependency) -> None:
        if dep.name in self._deps:
            raise ValueError(f"重复注册依赖：{dep.name}")
        self._deps[dep.name] = dep

    def get(self, name: str) -> Dependency:
        if name not in self._deps:
            raise KeyError(f"未注册依赖：{name}")
        return self._deps[name]

    def ready(self) -> Dict[str, bool]:
        return {name: dep.is_ready() for name, dep in self._deps.items()}


def provision_dependency(kind: str, **kwargs) -> Dependency:
    """根据类型创建依赖实例。"""

    if kind == "openapi_stub":
        return MockDependency(name=kwargs.get("name", "stub"), kind=kind, target=kwargs.get("contract", ""))
    if kind == "real_service":
        return RealDependency(
            name=kwargs.get("name", "service"),
            kind=kind,
            target=kwargs.get("image", ""),
            health_endpoint=kwargs.get("health"),
            healthy=kwargs.get("healthy", True),
        )
    raise ValueError(f"未知的依赖类型：{kind}")


__all__ = [
    "Dependency",
    "MockDependency",
    "RealDependency",
    "DependencyManager",
    "provision_dependency",
]
