"""服务定义加载与校验模块。

该模块负责解析 ``service_definition.yaml``，并基于 JSON Schema 进行必要的结构校验。
所有错误信息均转换为易读的中文描述，方便排查问题。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .utils import load_yaml_text


@dataclass
class ServiceDefinition:
    """内存中的服务定义模型。

    该数据类仅在测试中使用部分字段，因此保持宽松的字典包装形式。
    """

    raw: Dict[str, Any]

    def get(self, path: str, default: Any = None) -> Any:
        """按照 ``a.b.c`` 形式的路径访问嵌套字段。"""

        parts = path.split(".")
        current: Any = self.raw
        for part in parts:
            if not isinstance(current, dict):
                return default
            current = current.get(part, default)
            if current is default:
                return default
        return current


class ServiceDefinitionError(RuntimeError):
    """服务定义文件不合法时抛出的异常。"""


def load_service_definition(path: str | Path) -> ServiceDefinition:
    """读取并校验 ``service_definition.yaml``。

    参数:
        path: 文件路径。

    返回:
        :class:`ServiceDefinition` 实例。

    异常:
        ServiceDefinitionError: 当文件不存在、格式无法解析或违反 Schema 时抛出。
    """

    file_path = Path(path)
    if not file_path.exists():
        raise ServiceDefinitionError(f"服务定义文件不存在: {file_path}")

    raw_text = file_path.read_text(encoding="utf-8")
    try:
        data = load_yaml_text(raw_text)
    except Exception as exc:  # pragma: no cover - 仅在解析失败时触发
        raise ServiceDefinitionError(f"无法解析 YAML/JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ServiceDefinitionError("服务定义文件的根节点必须是字典")

    _validate_structure(data)

    return ServiceDefinition(raw=data)


def _validate_structure(data: Dict[str, Any]) -> None:
    """执行轻量级结构校验。"""

    required_top = ["version", "service", "tests"]
    missing = [key for key in required_top if key not in data]
    if missing:
        raise ServiceDefinitionError(f"缺少必需字段: {', '.join(missing)}")

    service = data["service"]
    if not isinstance(service, dict) or "name" not in service:
        raise ServiceDefinitionError("service 节点必须包含 name")

    tests = data["tests"]
    if not isinstance(tests, dict) or "suite_file" not in tests:
        raise ServiceDefinitionError("tests 节点必须包含 suite_file")

    scorers = tests.get("registered_scorers", {})
    if scorers and not isinstance(scorers, dict):
        raise ServiceDefinitionError("registered_scorers 必须是字典")
    for name, cfg in scorers.items():
        if not isinstance(cfg, dict) or "kind" not in cfg:
            raise ServiceDefinitionError(f"评分器 {name} 必须声明 kind")


__all__ = ["ServiceDefinition", "ServiceDefinitionError", "load_service_definition"]
