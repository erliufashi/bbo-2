"""依赖管理模块，实现 mock 与 real 两种模式的占位逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol


class DependencyError(Exception):
    """依赖拉起失败时的异常。"""


@dataclass(slots=True)
class DependencyConfig:
    """单个依赖的声明。"""

    name: str
    kind: str
    options: Mapping[str, object]


class DependencyHandle(Protocol):
    """依赖实例应实现的接口。"""

    def is_ready(self) -> bool:  # pragma: no cover - Protocol 本身不执行
        ...

    @property
    def endpoint(self) -> str:  # pragma: no cover
        ...


@dataclass(slots=True)
class _SimpleHandle:
    """用于测试的简化依赖句柄。"""

    _ready: bool
    _endpoint: str

    def is_ready(self) -> bool:
        return self._ready

    @property
    def endpoint(self) -> str:
        return self._endpoint


class DependencyProvisioner:
    """根据依赖类型生成句柄。"""

    def provision(self, config: DependencyConfig) -> DependencyHandle:
        """根据配置返回一个可检测状态的句柄。"""

        if config.kind == "openapi_stub":
            contract = Path(str(config.options.get("contract", "")))
            fixtures = Path(str(config.options.get("fixtures", "")))
            if not contract.exists():
                raise DependencyError(f"OpenAPI 契约 {contract} 不存在")
            if not fixtures.exists():
                raise DependencyError(f"桩数据目录 {fixtures} 不存在")
            return _SimpleHandle(True, f"stub://{config.name}")
        if config.kind == "real_service":
            health = config.options.get("health", "")
            if not isinstance(health, str) or not health:
                raise DependencyError("real_service 必须提供 health 字段")
            # 为保证测试可预测，模拟 ready 状态
            return _SimpleHandle(True, health)
        raise DependencyError(f"暂不支持的依赖类型 {config.kind}")


__all__ = ["DependencyProvisioner", "DependencyConfig", "DependencyError"]
