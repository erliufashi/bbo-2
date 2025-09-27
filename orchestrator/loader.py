"""负责解析与校验 `service_definition.yaml` 的模块。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

import yaml


class ValidationError(Exception):
    """声明式配置校验失败时抛出的异常。"""


@dataclass(slots=True)
class RegisteredScorer:
    """注册评分器的配置对象。"""

    name: str
    kind: str
    config: Mapping[str, Any]


@dataclass(slots=True)
class TestConfig:
    """测试配置描述。"""

    suite_file: Path
    registered_scorers: Dict[str, RegisteredScorer] = field(default_factory=dict)


@dataclass(slots=True)
class ServiceRuntime:
    """服务运行期配置。"""

    image: Optional[str] = None
    start_cmd: Optional[List[str]] = None
    port: Optional[int] = None


@dataclass(slots=True)
class ServiceConfig:
    """服务本体的基本元信息。"""

    name: str
    language: str
    runtime: ServiceRuntime = field(default_factory=ServiceRuntime)


@dataclass(slots=True)
class ServiceDefinition:
    """完整的服务声明。"""

    version: str
    service: ServiceConfig
    tests: TestConfig


def _ensure_keys(data: Mapping[str, Any], *, required: List[str], context: str) -> None:
    """校验字典是否包含特定键，缺失时给出可读错误。"""

    missing = [key for key in required if key not in data]
    if missing:
        raise ValidationError(f"{context} 缺少必要字段: {', '.join(missing)}")


def _parse_registered_scorers(raw: Mapping[str, Any]) -> Dict[str, RegisteredScorer]:
    """将原始评分器配置转换为强类型结构。"""

    scorers: Dict[str, RegisteredScorer] = {}
    for name, entry in raw.items():
        if not isinstance(entry, MutableMapping):
            raise ValidationError(f"评分器 '{name}' 配置应为映射类型")
        _ensure_keys(entry, required=["kind", "config"], context=f"评分器 {name}")
        scorers[name] = RegisteredScorer(
            name=name,
            kind=str(entry["kind"]),
            config=dict(entry["config"]),
        )
    return scorers


def load_service_definition(path: str | Path) -> ServiceDefinition:
    """读取并校验服务定义文件。"""

    file_path = Path(path)
    if not file_path.exists():
        raise ValidationError(f"配置文件 {file_path} 不存在")
    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - PyYAML 会产生详细错误
        raise ValidationError(f"解析 YAML 失败: {exc}") from exc
    if not isinstance(data, MutableMapping):
        raise ValidationError("顶层结构必须是映射类型")

    _ensure_keys(data, required=["version", "service", "tests"], context="service_definition")

    service_data = data["service"]
    if not isinstance(service_data, MutableMapping):
        raise ValidationError("service 字段必须是映射类型")
    _ensure_keys(service_data, required=["name", "language"], context="service")

    runtime_cfg = service_data.get("runtime") or {}
    if not isinstance(runtime_cfg, MutableMapping):
        raise ValidationError("service.runtime 必须是映射类型")
    runtime = ServiceRuntime(
        image=runtime_cfg.get("image"),
        start_cmd=list(runtime_cfg.get("start_cmd", []) or []) or None,
        port=runtime_cfg.get("port"),
    )

    service = ServiceConfig(
        name=str(service_data["name"]),
        language=str(service_data["language"]),
        runtime=runtime,
    )

    tests_data = data["tests"]
    if not isinstance(tests_data, MutableMapping):
        raise ValidationError("tests 字段必须是映射类型")
    _ensure_keys(tests_data, required=["suite_file"], context="tests")

    suite_file = (file_path.parent / str(tests_data["suite_file"])).resolve()
    registered_scorers = _parse_registered_scorers(tests_data.get("registered_scorers", {}))

    tests = TestConfig(suite_file=suite_file, registered_scorers=registered_scorers)

    return ServiceDefinition(
        version=str(data["version"]),
        service=service,
        tests=tests,
    )


__all__ = [
    "load_service_definition",
    "ValidationError",
    "ServiceDefinition",
    "ServiceConfig",
    "ServiceRuntime",
    "TestConfig",
    "RegisteredScorer",
]
