"""依赖管理模块，支持 mock 与 real 两种模式的虚拟实现。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class DependencyError(RuntimeError):
    """依赖装载异常。"""


@dataclass(slots=True)
class DependencyHandle:
    """依赖实例的抽象句柄。"""

    kind: str
    name: str
    endpoint: Optional[str]
    ready: bool

    def is_ready(self) -> bool:
        """提供统一的就绪检查接口。"""
        return self.ready


def provision_dependency(*, kind: str, name: str, mode: str = "mock", **kwargs) -> DependencyHandle:
    """根据类型与模式提供依赖，示例实现仅模拟状态。"""

    if mode not in {"mock", "real"}:
        raise DependencyError(f"不支持的依赖模式: {mode}")
    endpoint: Optional[str] = None
    ready = True
    if mode == "real":
        endpoint = kwargs.get("endpoint")
        if not endpoint:
            raise DependencyError("real 模式必须提供 endpoint")
    else:
        endpoint = f"mock://{name}"
    return DependencyHandle(kind=kind, name=name, endpoint=endpoint, ready=ready)


__all__ = ["DependencyError", "DependencyHandle", "provision_dependency"]
