"""顶层包入口，提供懒加载的子模块访问。"""
from __future__ import annotations

from importlib import import_module
from typing import Any

_SUBMODULES = {
    "assets": "orchestrator.orchestrator.assets",
    "datasets": "orchestrator.orchestrator.datasets",
    "deps": "orchestrator.orchestrator.deps",
    "loader": "orchestrator.orchestrator.loader",
    "report": "orchestrator.orchestrator.report",
    "runner": "orchestrator.orchestrator.runner",
    "scoring": "orchestrator.orchestrator.scoring",
    "cli": "orchestrator.orchestrator.cli",
    "_yaml": "orchestrator.orchestrator._yaml",
}


def __getattr__(name: str) -> Any:
    if name in _SUBMODULES:
        module = import_module(_SUBMODULES[name])
        globals()[name] = module
        return module
    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_SUBMODULES))
